package main

import (
	"bytes"
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"slices"
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
	for _, entry := range childEnvironment() {
		if len(entry) >= len("HOST_BRIDGE_TOKEN=") && entry[:len("HOST_BRIDGE_TOKEN=")] == "HOST_BRIDGE_TOKEN=" {
			t.Fatal("bridge token leaked into CLI child environment")
		}
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
