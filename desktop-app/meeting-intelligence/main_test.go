package main

import (
	"bytes"
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"runtime"
	"slices"
	"strings"
	"testing"
)

func TestBridgeAllowsAnAuthenticatedAllowlistedProvider(t *testing.T) {
	b := &bridge{
		token:     "test-token",
		semaphore: make(chan struct{}, 1),
		runCLI: func(_ context.Context, provider, prompt string) (string, string) {
			if provider != "codex" || len(prompt) < 20 {
				t.Fatalf("unexpected CLI input")
			}
			return `{"title":"회의 결과"}`, ""
		},
	}
	body, _ := json.Marshal(bridgeRequest{Provider: "codex", Prompt: "한국어 회의를 근거 기반 JSON으로 정리해 주세요."})
	request := httptest.NewRequest(http.MethodPost, "/v1/generate", bytes.NewReader(body))
	request.Header.Set("X-Meeting-Bridge-Token", "test-token")
	response := httptest.NewRecorder()

	b.handleGenerate(response, request)

	if response.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d: %s", response.Code, response.Body.String())
	}
	var payload bridgeResponse
	if err := json.Unmarshal(response.Body.Bytes(), &payload); err != nil {
		t.Fatal(err)
	}
	if payload.Status != "SUCCESS" || payload.Provider != "codex" {
		t.Fatalf("unexpected response: %+v", payload)
	}
}

func TestBridgeBlocksMissingTokenBeforeCLIExecution(t *testing.T) {
	called := false
	b := &bridge{
		token:     "test-token",
		semaphore: make(chan struct{}, 1),
		runCLI: func(_ context.Context, _, _ string) (string, string) {
			called = true
			return "", ""
		},
	}
	body, _ := json.Marshal(bridgeRequest{Provider: "codex", Prompt: "한국어 회의를 근거 기반 JSON으로 정리해 주세요."})
	request := httptest.NewRequest(http.MethodPost, "/v1/generate", bytes.NewReader(body))
	response := httptest.NewRecorder()

	b.handleGenerate(response, request)

	if response.Code != http.StatusUnauthorized {
		t.Fatalf("expected 401, got %d", response.Code)
	}
	if called {
		t.Fatal("CLI must not run without the bridge token")
	}
}

func TestBridgeBlocksUnapprovedProvider(t *testing.T) {
	b := &bridge{token: "test-token", semaphore: make(chan struct{}, 1), runCLI: runOfficialCLI}
	body, _ := json.Marshal(bridgeRequest{Provider: "shell", Prompt: "한국어 회의를 근거 기반 JSON으로 정리해 주세요."})
	request := httptest.NewRequest(http.MethodPost, "/v1/generate", bytes.NewReader(body))
	request.Header.Set("X-Meeting-Bridge-Token", "test-token")
	response := httptest.NewRecorder()

	b.handleGenerate(response, request)

	if response.Code != http.StatusBadRequest {
		t.Fatalf("expected 400, got %d", response.Code)
	}
}

func TestChildEnvironmentRemovesBridgeToken(t *testing.T) {
	t.Setenv("HOST_BRIDGE_TOKEN", "must-not-reach-cli")
	t.Setenv("OPENAI_API_KEY", "example-secret-must-not-reach-cli")
	t.Setenv("LANGSMITH_API_KEY", "example-secret-must-not-reach-cli")
	t.Setenv("DAY2_PASSWORD", "example-secret-must-not-reach-cli")
	t.Setenv("PATH", "/usr/bin:/bin")
	seenPath := false
	for _, entry := range childEnvironment() {
		name, _, _ := strings.Cut(entry, "=")
		upperName := strings.ToUpper(name)
		if strings.Contains(upperName, "TOKEN") || strings.Contains(upperName, "KEY") || strings.Contains(upperName, "SECRET") || strings.Contains(upperName, "PASSWORD") {
			t.Fatalf("secret-like environment variable reached the CLI: %s", name)
		}
		if upperName == "PATH" {
			seenPath = true
		}
	}
	if !seenPath {
		t.Fatal("safe PATH environment is required for the official CLI")
	}
}

func TestOfficialCLICommandsDisableUserToolsAndConfiguration(t *testing.T) {
	codex := officialCLICommand(context.Background(), "codex", "codex", "/tmp/empty", "/tmp/output")
	for _, required := range []string{"--ephemeral", "--ignore-rules", "--ignore-user-config", "--sandbox", "read-only"} {
		if !slices.Contains(codex.Args, required) {
			t.Fatalf("Codex argv missing %q: %v", required, codex.Args)
		}
	}

	claude := officialCLICommand(context.Background(), "claude", "claude", "/tmp/empty", "")
	for _, required := range []string{"--tools", "--no-session-persistence", "--setting-sources", "--strict-mcp-config", "--mcp-config", `{"mcpServers":{}}`} {
		if !slices.Contains(claude.Args, required) {
			t.Fatalf("Claude argv missing %q: %v", required, claude.Args)
		}
	}
}

func TestDockerLauncherAlwaysDefinesCleanupCommand(t *testing.T) {
	up := dockerComposeArgs("/tmp/meeting-app", "up")
	down := dockerComposeArgs("/tmp/meeting-app", "down")

	if !slices.Contains(up, "--build") || !slices.Contains(up, "--remove-orphans") {
		t.Fatalf("unexpected compose up args: %v", up)
	}
	if !slices.Contains(down, "down") || !slices.Contains(down, "--remove-orphans") {
		t.Fatalf("cleanup command is missing: %v", down)
	}
	if slices.Contains(down, "-v") {
		t.Fatalf("normal cleanup must preserve the downloaded model volume: %v", down)
	}
}

func TestDockerLauncherIncludesFinderSafeMacCandidate(t *testing.T) {
	if runtime.GOOS != "darwin" {
		t.Skip("macOS package path check")
	}
	path, err := officialDockerPath()
	if err != nil {
		t.Fatal(err)
	}
	if !strings.HasSuffix(path, "/docker") {
		t.Fatalf("unexpected Docker path: %s", path)
	}
}
