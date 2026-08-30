// Meeting Intelligence launcher starts a localhost-only CLI bridge and the Docker application.
// It never reads browser cookies or ChatGPT/Claude credential files.
package main

import (
	"context"
	"crypto/rand"
	"crypto/subtle"
	"embed"
	"encoding/base64"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"io/fs"
	"log"
	"net"
	"net/http"
	"os"
	"os/exec"
	"os/signal"
	"path/filepath"
	"runtime"
	"strings"
	"syscall"
	"time"
)

// The compiled Windows and macOS launchers contain the complete Docker context.
//
//go:embed Dockerfile docker-compose.yml requirements.txt app static fixtures
var dockerBundle embed.FS

const (
	bridgeAddress = "127.0.0.1:8765"
	appURL        = "http://127.0.0.1:8766"
	maxPromptSize = 128 * 1024
	maxOutputSize = 2 * 1024 * 1024
)

type bridgeRequest struct {
	Provider string `json:"provider"`
	Prompt   string `json:"prompt"`
}

type bridgeResponse struct {
	Status    string `json:"status"`
	Provider  string `json:"provider"`
	Output    string `json:"output,omitempty"`
	ErrorCode string `json:"error_code,omitempty"`
}

type bridge struct {
	token     string
	runCLI    func(context.Context, string, string) (string, string)
	semaphore chan struct{}
}

func main() {
	appDirFlag := flag.String("app-dir", "", "development Docker context; omitted in packaged builds")
	bridgeOnly := flag.Bool("bridge-only", false, "run only the localhost CLI bridge")
	enableCLIBridge := flag.Bool("enable-cli-bridge", false, "enable the synthetic-data-only Codex/Claude bridge")
	noBrowser := flag.Bool("no-browser", false, "do not open the local UI")
	flag.Parse()

	token := "disabled"
	bridgeRequested := *enableCLIBridge || *bridgeOnly
	if bridgeRequested {
		generatedToken, err := randomToken()
		if err != nil {
			log.Fatalf("launcher initialization failed: %v", err)
		}
		token = generatedToken
		b := &bridge{token: token, runCLI: runOfficialCLI, semaphore: make(chan struct{}, 1)}
		server, listener, err := startBridge(b)
		if err != nil {
			log.Fatalf("localhost bridge could not start: %v", err)
		}
		defer server.Shutdown(context.Background())
		defer listener.Close()
		fmt.Println("Meeting Intelligence host bridge: READY (synthetic-data instructor extension)")
	} else {
		fmt.Println("Meeting Intelligence host bridge: DISABLED (default safe mode)")
	}

	if *bridgeOnly {
		fmt.Println("Bridge-only mode does not start Docker. No credential data was inspected.")
		waitForSignal()
		return
	}

	appDir := *appDirFlag
	if appDir == "" {
		materializedDir, materializeErr := materializeDockerBundle()
		if materializeErr != nil {
			log.Fatalf("embedded application could not be prepared: %v", materializeErr)
		}
		appDir = materializedDir
	}
	composePath := filepath.Join(appDir, "docker-compose.yml")
	if _, err := os.Stat(composePath); err != nil {
		log.Fatalf("docker-compose.yml was not found in %s", appDir)
	}

	ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer cancel()
	if !*noBrowser {
		go openWhenReady(ctx, appURL)
	}
	if err := runDockerCompose(ctx, appDir, token); err != nil && !errors.Is(err, context.Canceled) {
		showLaunchError("Docker 실행 경로를 확인하지 못했습니다. 수강생 기본 경로는 repository의 run-local.command 또는 run-local.cmd입니다.")
		log.Fatalf("Docker application stopped: %v", err)
	}
}

func randomToken() (string, error) {
	raw := make([]byte, 32)
	if _, err := rand.Read(raw); err != nil {
		return "", err
	}
	return base64.RawURLEncoding.EncodeToString(raw), nil
}

func startBridge(b *bridge) (*http.Server, net.Listener, error) {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /v1/health", func(w http.ResponseWriter, _ *http.Request) {
		writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
	})
	mux.HandleFunc("POST /v1/generate", b.handleGenerate)
	listener, err := net.Listen("tcp", bridgeAddress)
	if err != nil {
		return nil, nil, err
	}
	server := &http.Server{
		Addr:              bridgeAddress,
		Handler:           mux,
		ReadHeaderTimeout: 5 * time.Second,
		ReadTimeout:       10 * time.Second,
		WriteTimeout:      150 * time.Second,
		IdleTimeout:       30 * time.Second,
	}
	go func() {
		if serveErr := server.Serve(listener); serveErr != nil && !errors.Is(serveErr, http.ErrServerClosed) {
			log.Printf("bridge stopped: %v", serveErr)
		}
	}()
	return server, listener, nil
}

func (b *bridge) handleGenerate(w http.ResponseWriter, r *http.Request) {
	provided := r.Header.Get("X-Meeting-Bridge-Token")
	if len(provided) != len(b.token) || subtle.ConstantTimeCompare([]byte(provided), []byte(b.token)) != 1 {
		writeJSON(w, http.StatusUnauthorized, bridgeResponse{Status: "EXPECTED_FAILURE", ErrorCode: "BRIDGE_AUTH_REQUIRED"})
		return
	}
	r.Body = http.MaxBytesReader(w, r.Body, maxPromptSize+4096)
	decoder := json.NewDecoder(r.Body)
	decoder.DisallowUnknownFields()
	var request bridgeRequest
	if err := decoder.Decode(&request); err != nil {
		writeJSON(w, http.StatusBadRequest, bridgeResponse{Status: "EXPECTED_FAILURE", ErrorCode: "INVALID_REQUEST"})
		return
	}
	request.Provider = strings.ToLower(strings.TrimSpace(request.Provider))
	if request.Provider != "codex" && request.Provider != "claude" {
		writeJSON(w, http.StatusBadRequest, bridgeResponse{Status: "EXPECTED_FAILURE", ErrorCode: "PROVIDER_NOT_ALLOWED"})
		return
	}
	if len(strings.TrimSpace(request.Prompt)) < 20 || len(request.Prompt) > maxPromptSize {
		writeJSON(w, http.StatusBadRequest, bridgeResponse{Status: "EXPECTED_FAILURE", ErrorCode: "PROMPT_SIZE_INVALID"})
		return
	}

	select {
	case b.semaphore <- struct{}{}:
		defer func() { <-b.semaphore }()
	default:
		writeJSON(w, http.StatusTooManyRequests, bridgeResponse{Status: "EXPECTED_FAILURE", ErrorCode: "CLI_BUSY"})
		return
	}

	ctx, cancel := context.WithTimeout(r.Context(), 120*time.Second)
	defer cancel()
	output, code := b.runCLI(ctx, request.Provider, request.Prompt)
	if code != "" {
		status := http.StatusBadGateway
		if code == "CLI_NOT_FOUND" {
			status = http.StatusFailedDependency
		} else if code == "CLI_TIMEOUT" {
			status = http.StatusGatewayTimeout
		}
		writeJSON(w, status, bridgeResponse{Status: "EXPECTED_FAILURE", Provider: request.Provider, ErrorCode: code})
		return
	}
	writeJSON(w, http.StatusOK, bridgeResponse{Status: "SUCCESS", Provider: request.Provider, Output: output})
}

func runOfficialCLI(ctx context.Context, provider, prompt string) (string, string) {
	tempDir, err := os.MkdirTemp("", "meeting-intelligence-cli-")
	if err != nil {
		return "", "CLI_TEMP_DIR_FAILED"
	}
	defer os.RemoveAll(tempDir)

	path, err := officialCLIPath(provider)
	if err != nil {
		return "", "CLI_NOT_FOUND"
	}

	var command *exec.Cmd
	var outputPath string
	if provider == "codex" {
		outputPath = filepath.Join(tempDir, "result.json")
		command = officialCLICommand(ctx, provider, path, tempDir, outputPath)
	} else {
		command = officialCLICommand(ctx, provider, path, tempDir, "")
	}
	command.Dir = tempDir
	command.Stdin = strings.NewReader(prompt)
	command.Env = childEnvironment()
	var stdout strings.Builder
	stdoutWriter := &limitedWriter{writer: &stdout, remaining: maxOutputSize}
	command.Stdout = stdoutWriter
	command.Stderr = io.Discard // Avoid relaying tokens, paths, hooks, or provider diagnostics.
	if err := command.Run(); err != nil {
		if errors.Is(ctx.Err(), context.DeadlineExceeded) {
			return "", "CLI_TIMEOUT"
		}
		return "", "CLI_EXECUTION_FAILED"
	}

	var raw []byte
	if provider == "codex" {
		raw, err = os.ReadFile(outputPath)
		if err != nil {
			return "", "CLI_OUTPUT_EMPTY"
		}
	} else {
		if stdoutWriter.exceeded {
			return "", "CLI_OUTPUT_TOO_LARGE"
		}
		raw = []byte(stdout.String())
	}
	if len(raw) == 0 {
		return "", "CLI_OUTPUT_EMPTY"
	}
	if len(raw) > maxOutputSize {
		return "", "CLI_OUTPUT_TOO_LARGE"
	}
	return strings.TrimSpace(string(raw)), ""
}

func officialCLICommand(ctx context.Context, provider, path, tempDir, outputPath string) *exec.Cmd {
	if provider == "codex" {
		return exec.CommandContext(
			ctx,
			path,
			"exec",
			"--skip-git-repo-check",
			"--ephemeral",
			"--ignore-rules",
			"--ignore-user-config",
			"--sandbox", "read-only",
			"--color", "never",
			"-C", tempDir,
			"--output-last-message", outputPath,
			"-",
		)
	}
	return exec.CommandContext(
		ctx,
		path,
		"-p",
		"--tools", "",
		"--permission-mode", "dontAsk",
		"--no-session-persistence",
		"--disable-slash-commands",
		"--no-chrome",
		"--setting-sources", "",
		"--strict-mcp-config",
		"--mcp-config", `{"mcpServers":{}}`,
		"--output-format", "text",
	)
}

func officialCLIPath(provider string) (string, error) {
	envName := "CODEX_CLI_PATH"
	binary := "codex"
	defaults := []string{"/Applications/ChatGPT.app/Contents/Resources/codex"}
	if provider == "claude" {
		envName = "CLAUDE_CLI_PATH"
		binary = "claude"
		defaults = []string{"/opt/homebrew/bin/claude", "/usr/local/bin/claude"}
	}
	if configured := strings.TrimSpace(os.Getenv(envName)); configured != "" {
		if info, err := os.Stat(configured); err == nil && !info.IsDir() {
			return configured, nil
		}
		return "", fmt.Errorf("configured CLI was not found")
	}
	if found, err := exec.LookPath(binary); err == nil {
		return found, nil
	}
	for _, candidate := range defaults {
		if info, err := os.Stat(candidate); err == nil && !info.IsDir() {
			return candidate, nil
		}
	}
	return "", fmt.Errorf("%s not found", binary)
}

func childEnvironment() []string {
	allowed := map[string]bool{
		"PATH":          true,
		"HOME":          true,
		"USER":          true,
		"LOGNAME":       true,
		"USERPROFILE":   true,
		"APPDATA":       true,
		"LOCALAPPDATA":  true,
		"SYSTEMROOT":    true,
		"COMSPEC":       true,
		"PATHEXT":       true,
		"TMPDIR":        true,
		"TMP":           true,
		"TEMP":          true,
		"LANG":          true,
		"LC_ALL":        true,
		"LC_CTYPE":      true,
		"TERM":          true,
		"SSL_CERT_FILE": true,
		"SSL_CERT_DIR":  true,
	}
	filtered := make([]string, 0, len(os.Environ()))
	for _, value := range os.Environ() {
		name, _, _ := strings.Cut(value, "=")
		upperName := strings.ToUpper(name)
		if allowed[upperName] && !strings.Contains(upperName, "TOKEN") && !strings.Contains(upperName, "KEY") && !strings.Contains(upperName, "SECRET") && !strings.Contains(upperName, "PASSWORD") {
			filtered = append(filtered, value)
		}
	}
	return filtered
}

type limitedWriter struct {
	writer    io.Writer
	remaining int
	exceeded  bool
}

func (w *limitedWriter) Write(data []byte) (int, error) {
	originalLength := len(data)
	if len(data) > w.remaining {
		w.exceeded = true
		data = data[:w.remaining]
	}
	if len(data) > 0 {
		if _, err := w.writer.Write(data); err != nil {
			return 0, err
		}
		w.remaining -= len(data)
	}
	return originalLength, nil
}

func writeJSON(w http.ResponseWriter, status int, value any) {
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Cache-Control", "no-store")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(value)
}

func materializeDockerBundle() (string, error) {
	cacheDir, err := os.UserCacheDir()
	if err != nil {
		return "", err
	}
	target := filepath.Join(cacheDir, "MeetingIntelligence", "runtime-v2")
	if err := os.MkdirAll(target, 0o700); err != nil {
		return "", err
	}
	return target, fs.WalkDir(dockerBundle, ".", func(path string, entry fs.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		if path == "." {
			return nil
		}
		destination := filepath.Join(target, filepath.FromSlash(path))
		if entry.IsDir() {
			return os.MkdirAll(destination, 0o700)
		}
		content, err := dockerBundle.ReadFile(path)
		if err != nil {
			return err
		}
		return os.WriteFile(destination, content, 0o600)
	})
}

func runDockerCompose(ctx context.Context, appDir, token string) error {
	dockerPath, err := officialDockerPath()
	if err != nil {
		return fmt.Errorf("Docker Desktop is required: docker command not found")
	}
	defer stopDockerCompose(dockerPath, appDir)
	command := exec.CommandContext(ctx, dockerPath, dockerComposeArgs(appDir, "up")...)
	command.Dir = appDir
	command.Env = append(
		os.Environ(),
		"HOST_BRIDGE_TOKEN="+token,
		"HOST_BRIDGE_URL=http://host.docker.internal:8765",
	)
	command.Stdout = os.Stdout
	command.Stderr = os.Stderr
	command.Stdin = os.Stdin
	fmt.Printf("Local application: %s\n", appURL)
	return command.Run()
}

func officialDockerPath() (string, error) {
	if found, err := exec.LookPath("docker"); err == nil {
		return found, nil
	}
	candidates := []string{
		"/Applications/Docker.app/Contents/Resources/bin/docker",
		"/opt/homebrew/bin/docker",
		"/usr/local/bin/docker",
	}
	if runtime.GOOS == "windows" {
		candidates = append(candidates, `C:\Program Files\Docker\Docker\resources\bin\docker.exe`)
	}
	for _, candidate := range candidates {
		if info, err := os.Stat(candidate); err == nil && !info.IsDir() {
			return candidate, nil
		}
	}
	return "", errors.New("docker command not found")
}

func showLaunchError(message string) {
	if runtime.GOOS != "darwin" {
		return
	}
	command := exec.Command(
		"osascript",
		"-e", "on run argv",
		"-e", `display alert "Meeting Intelligence" message (item 1 of argv) as critical`,
		"-e", "end run",
		message,
	)
	_ = command.Run()
}

func dockerComposeArgs(appDir, action string) []string {
	base := []string{"compose", "--project-directory", appDir}
	if action == "down" {
		return append(base, "down", "--remove-orphans")
	}
	return append(base, "up", "--build", "--remove-orphans")
}

func stopDockerCompose(dockerPath, appDir string) {
	cleanupContext, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	command := exec.CommandContext(cleanupContext, dockerPath, dockerComposeArgs(appDir, "down")...)
	command.Dir = appDir
	command.Stdout = os.Stdout
	command.Stderr = os.Stderr
	if err := command.Run(); err != nil && !errors.Is(cleanupContext.Err(), context.DeadlineExceeded) {
		log.Printf("Docker cleanup failed: %v", err)
	}
}

func openWhenReady(ctx context.Context, url string) {
	client := http.Client{Timeout: 2 * time.Second}
	for attempt := 0; attempt < 90; attempt++ {
		select {
		case <-ctx.Done():
			return
		case <-time.After(time.Second):
		}
		response, err := client.Get(url + "/health")
		if err == nil {
			response.Body.Close()
			if response.StatusCode == http.StatusOK {
				_ = openBrowser(url)
				return
			}
		}
	}
}

func openBrowser(url string) error {
	var command *exec.Cmd
	switch runtime.GOOS {
	case "darwin":
		command = exec.Command("open", url)
	case "windows":
		command = exec.Command("rundll32", "url.dll,FileProtocolHandler", url)
	default:
		command = exec.Command("xdg-open", url)
	}
	return command.Start()
}

func waitForSignal() {
	channel := make(chan os.Signal, 1)
	signal.Notify(channel, os.Interrupt, syscall.SIGTERM)
	<-channel
}
