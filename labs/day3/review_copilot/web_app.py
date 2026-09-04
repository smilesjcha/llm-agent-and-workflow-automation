"""Dependency-free localhost UI for the Day 3 final-period demo."""

from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from threading import Thread
from typing import Any
from urllib.request import Request, urlopen
from urllib.parse import urlparse

from .exports import render_review_markdown
from .errors import stable_error_code
from .workflow import run_review_text_workflow
from .workspace import read_workspace_json, read_workspace_text
from .test_evidence import collect_focused_test_evidence


MAX_REQUEST_BYTES = 500_000


def repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


def review_request(payload: dict[str, Any], *, root: Path) -> dict[str, Any]:
    """Pure API boundary used by the HTTP handler and smoke test."""

    diff_text = payload.get("diff_text")
    if not isinstance(diff_text, str) or not diff_text.strip():
        return {
            "status": "EXPECTED_FAILURE",
            "error_code": "DIFF_TEXT_REQUIRED",
            "external_write": False,
        }
    edited_findings = payload.get("edited_findings")
    if edited_findings is not None and not isinstance(edited_findings, list):
        return {
            "status": "EXPECTED_FAILURE",
            "error_code": "EDITED_FINDINGS_LIST_REQUIRED",
            "external_write": False,
        }
    try:
        context = read_workspace_json(
            "labs/day3/review_copilot/fixtures/project_context.json",
            workspace_root=root,
        )
        fixture = read_workspace_json(
            "labs/day3/review_copilot/fixtures/provider_fixture.json",
            workspace_root=root,
        )
    except ValueError as exc:
        return {
            "status": "EXPECTED_FAILURE",
            "error_code": stable_error_code(exc),
            "external_write": False,
        }
    test_evidence = (
        collect_focused_test_evidence(workspace_root=root)
        if payload.get("run_tests") is True
        else None
    )
    result = run_review_text_workflow(
        workspace_root=root,
        diff_text=diff_text,
        project_context=context,
        fixture_payload=fixture,
        decision=(str(payload["decision"]) if payload.get("decision") is not None else None),
        reviewer=str(payload.get("reviewer", "localhost-user")),
        rationale=str(payload.get("rationale", "화면에서 근거와 교정을 확인했습니다.")),
        edited_findings=edited_findings,
        test_evidence=test_evidence,
    )
    return {**result, "markdown": render_review_markdown(result)}


def _handler(root: Path) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def _send(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def _send_json(self, status: int, payload: dict[str, Any]) -> None:
            self._send(status, _json_bytes(payload), "application/json; charset=utf-8")

        def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
            path = urlparse(self.path).path
            if path == "/":
                self._send(200, _HTML.encode("utf-8"), "text/html; charset=utf-8")
                return
            if path == "/api/health":
                self._send_json(
                    200,
                    {
                        "status": "ok",
                        "service": "day3-review-copilot",
                        "provider": "fixture",
                        "external_write": False,
                    },
                )
                return
            if path == "/api/sample":
                try:
                    sample = read_workspace_text(
                        "labs/day3/review_copilot/fixtures/meeting_export_pr.diff",
                        workspace_root=root,
                    )
                except ValueError as exc:
                    self._send_json(500, {"status": "EXPECTED_FAILURE", "error_code": str(exc)})
                    return
                self._send_json(200, {"status": "SUCCESS", "diff_text": sample})
                return
            self._send_json(404, {"status": "EXPECTED_FAILURE", "error_code": "ROUTE_NOT_FOUND"})

        def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
            if urlparse(self.path).path != "/api/review":
                self._send_json(404, {"status": "EXPECTED_FAILURE", "error_code": "ROUTE_NOT_FOUND"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self._send_json(400, {"status": "EXPECTED_FAILURE", "error_code": "CONTENT_LENGTH_INVALID"})
                return
            if length < 1 or length > MAX_REQUEST_BYTES:
                self._send_json(413, {"status": "EXPECTED_FAILURE", "error_code": "REQUEST_SIZE_BLOCKED"})
                return
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                self._send_json(400, {"status": "EXPECTED_FAILURE", "error_code": "JSON_INVALID"})
                return
            if not isinstance(payload, dict):
                self._send_json(400, {"status": "EXPECTED_FAILURE", "error_code": "JSON_OBJECT_REQUIRED"})
                return
            result = review_request(payload, root=root)
            self._send_json(200 if result["status"] == "SUCCESS" else 422, result)

        def log_message(self, format: str, *args: object) -> None:
            del format, args

    return Handler


def create_server(
    *,
    root: Path | None = None,
    host: str = "127.0.0.1",
    port: int = 8765,
) -> ThreadingHTTPServer:
    """Bind to loopback by default; no external interface is exposed."""

    return ThreadingHTTPServer((host, port), _handler((root or repository_root()).resolve()))


def main() -> None:
    parser = argparse.ArgumentParser(description="Day 3 Review Copilot localhost UI")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--smoke-and-exit",
        action="store_true",
        help="health와 sample review를 localhost HTTP로 확인한 뒤 종료",
    )
    args = parser.parse_args()
    server = create_server(host=args.host, port=args.port)
    if args.smoke_and_exit:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        host, port = server.server_address
        try:
            with urlopen(f"http://{host}:{port}/api/health", timeout=3) as response:
                health = json.loads(response.read())
            with urlopen(f"http://{host}:{port}/api/sample", timeout=3) as response:
                sample = json.loads(response.read())
            request = Request(
                f"http://{host}:{port}/api/review",
                data=json.dumps(
                    {"diff_text": sample["diff_text"], "decision": "approve"}
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(request, timeout=5) as response:
                result = json.loads(response.read())
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
        print(
            json.dumps(
                {
                    "status": "SUCCESS"
                    if health["status"] == "ok" and result["status"] == "SUCCESS"
                    else "EXPECTED_FAILURE",
                    "health": health,
                    "review_status": result["status"],
                    "finding_count": len(
                        result.get("stages", {}).get("05_hybrid_review", {}).get("findings", [])
                    ),
                    "evaluation": result.get("stages", {}).get("07_evaluation", {}),
                    "external_write": False,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return
    print(f"Review Copilot: http://{args.host}:{args.port}")
    print("Fixture mode · external_write=false · 종료: Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


_HTML = r"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Review Copilot · Day 3</title>
  <style>
    :root{--ink:#111;--muted:#687386;--navy:#173b69;--line:#dfe4ea;--paper:#fff;--soft:#f5f7fa}
    *{box-sizing:border-box} body{margin:0;background:var(--soft);color:var(--ink);font:15px/1.55 Arial,"Apple SD Gothic Neo",sans-serif}
    header{background:#080808;color:#fff;padding:24px max(24px,calc((100vw - 1180px)/2))} header b{font-size:22px} header span{float:right;color:#b8c7db}
    main{max-width:1180px;margin:24px auto;padding:0 20px;display:grid;grid-template-columns:1fr 1fr;gap:18px}.card{background:var(--paper);border:1px solid var(--line);border-radius:12px;padding:20px;box-shadow:0 6px 20px #17243b0a}.wide{grid-column:1/-1}
    h1,h2{margin:0 0 12px} h2{font-size:18px} .note{color:var(--muted);margin:0 0 12px} textarea{width:100%;min-height:340px;padding:14px;border:1px solid #bbc3ce;border-radius:8px;font:13px/1.5 ui-monospace,SFMono-Regular,monospace;resize:vertical}
    button{border:0;border-radius:7px;padding:10px 14px;font-weight:700;cursor:pointer;background:#111;color:#fff;margin:8px 6px 0 0}.secondary{background:var(--navy)}.ghost{background:#e9edf2;color:#222}.metric{display:inline-block;margin:4px 10px 4px 0;padding:7px 10px;border:1px solid var(--line);border-radius:8px}.finding{border-top:1px solid var(--line);padding:14px 0}.finding input{width:100%;padding:7px;margin:3px 0;border:1px solid var(--line);border-radius:5px}.tag{color:var(--navy);font-weight:800}.status{padding:10px;background:#edf3fa;border-left:4px solid var(--navy);white-space:pre-wrap}pre{max-height:360px;overflow:auto;background:#101318;color:#edf2f8;padding:14px;border-radius:8px;font-size:12px}@media(max-width:820px){main{grid-template-columns:1fr}.wide{grid-column:auto}header span{float:none;display:block}}
  </style>
</head>
<body>
<header><b>Review Copilot</b><span>Day 3 · fixture · external_write=false</span></header>
<main>
  <section class="card"><h2>Unified Diff</h2><p class="note">샘플을 불러오거나 본인의 diff를 붙여 넣습니다. 입력은 서버에 저장되지 않습니다.</p><textarea id="diff"></textarea><button id="sample" class="ghost">샘플 불러오기</button><button id="approve">분석 · 전체 유지</button></section>
  <section class="card"><h2>Human Review</h2><p class="note">Finding을 고치거나 체크를 해제한 뒤 반영합니다. 실제 GitHub 게시 명령은 실행되지 않습니다.</p><div id="status" class="status">샘플을 불러온 뒤 분석을 시작하세요.</div><div id="findings"></div><button id="edit" class="secondary">선택·수정 반영</button><button id="reject" class="ghost">전체 제외</button></section>
  <section class="card wide"><h2>평가와 Export</h2><div id="metrics"></div><button id="json" class="ghost">JSON 저장</button><button id="md" class="ghost">Markdown 저장</button><pre id="raw">아직 결과가 없습니다.</pre></section>
</main>
<script>
let latest=null;
const q=s=>document.querySelector(s);
async function loadSample(){const r=await fetch('/api/sample');const d=await r.json();q('#diff').value=d.diff_text||''}
function download(name,text,type){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([text],{type}));a.download=name;a.click();URL.revokeObjectURL(a.href)}
function edits(){return [...document.querySelectorAll('.finding')].filter(x=>x.querySelector('[type=checkbox]').checked).map(x=>{const original=JSON.parse(x.dataset.item);for(const k of ['title','impact','correction'])original[k]=x.querySelector(`[data-k=${k}]`).value;return original})}
function render(d){latest=d;q('#raw').textContent=JSON.stringify(d,null,2);q('#findings').replaceChildren();if(d.status!=='SUCCESS'){q('#status').textContent=`실행 중단 · ${d.error_code}`;return}const s=d.stages;q('#status').textContent=`${s['06_human_review'].status} · Focused Test ${s['05_hybrid_review'].test_evidence.status} · GitHub ${s['08_release_evidence'].github_dry_run.status}\nRelease ${s['08_release_evidence'].decision} · 외부 서비스 변경: 없음`;for(const f of s['06_human_review'].findings){const box=document.createElement('div');box.className='finding';box.dataset.item=JSON.stringify(f);const top=document.createElement('label');const check=document.createElement('input');check.type='checkbox';check.checked=true;top.append(check,` ${f.severity} · ${f.path}:${f.line} · ${f.rule_id}`);box.append(top);for(const k of ['title','impact','correction']){const input=document.createElement('input');input.dataset.k=k;input.value=f[k];box.append(input)}q('#findings').append(box)}const m=s['07_evaluation'];q('#metrics').textContent=`Golden ${m.case_passed}/${m.case_count} · Precision ${m.precision} · Recall ${m.recall} · F1 ${m.f1} · ${m.release_decision}`}
async function run(decision){const payload={diff_text:q('#diff').value,decision,reviewer:'localhost-user',rationale:'화면에서 근거와 최소 교정을 확인했습니다.',run_tests:true};if(decision==='edit')payload.edited_findings=edits();const r=await fetch('/api/review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});render(await r.json())}
q('#sample').onclick=loadSample;q('#approve').onclick=()=>run('approve');q('#edit').onclick=()=>run('edit');q('#reject').onclick=()=>run('reject');q('#json').onclick=()=>latest&&download('day3-review.json',JSON.stringify(latest,null,2),'application/json');q('#md').onclick=()=>latest&&download('day3-review.md',latest.markdown||'','text/markdown');loadSample();
</script>
</body></html>"""


if __name__ == "__main__":
    main()
