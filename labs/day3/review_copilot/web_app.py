"""Dependency-free localhost UI for the Day 3 final-period demo."""

from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
from threading import Thread
from typing import Any
from urllib.request import Request, urlopen
from urllib.parse import urlparse

from .exports import render_review_markdown
from .codex_cli import CodexCLIReviewProvider
from .exercise import (
    DEFAULT_EXERCISE, checkout_fixture_provider, prepare_exercise, review_exercise,
    run_exercise_demo, run_exercise_tests,
)
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

    if payload.get("provider", "fixture") not in {"fixture", "codex_cli"}:
        return {"status": "EXPECTED_FAILURE", "error_code": "PROVIDER_NOT_SUPPORTED", "external_write": False}

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
        provider=CodexCLIReviewProvider(
            model=os.getenv("CODEX_MODEL") or None,
            live_opt_in=payload.get("live_opt_in") is True,
        ) if payload.get("provider") == "codex_cli" else None,
        allow_fallback=payload.get("allow_fallback") is True,
    )
    return {**result, "markdown": render_review_markdown(result)}


def exercise_request(payload: dict[str, Any], *, root: Path, exercise_dir: str = DEFAULT_EXERCISE) -> dict[str, Any]:
    """Fixed public checkout exercise; no caller-controlled execution path."""
    options = {"workspace_root": root, "exercise_dir": exercise_dir}
    try:
        prepare_exercise(workspace_root=root, output_dir=exercise_dir)
        action = payload.get("action", "demo")
        if action == "demo":
            total = payload.get("total_won", 10_000)
            coupon = payload.get("coupon_won", 15_000)
            if isinstance(total, bool) or isinstance(coupon, bool) or not isinstance(total, int) or not isinstance(coupon, int):
                raise ValueError("MONEY_INTEGER_REQUIRED")
            result = {
                version: run_exercise_demo(**options, version=version, total_won=total, coupon_won=coupon)
                for version in ("starter", "solution")
            }
            return {"status": "SUCCESS", "receipts": result, "actual_payment": False}
        if action == "test":
            return {"status": "SUCCESS", "tests": {
                version: run_exercise_tests(**options, version=version)
                for version in ("starter", "solution")
            }}
        if action == "review":
            name = payload.get("provider", "codex_cli")
            if name not in {"codex_cli", "fixture"}:
                raise ValueError("PROVIDER_NOT_SUPPORTED")
            provider = checkout_fixture_provider(**options) if name == "fixture" else CodexCLIReviewProvider(
                model=os.getenv("CODEX_MODEL") or None,
                live_opt_in=payload.get("live_opt_in") is True,
            )
            return review_exercise(**options, provider=provider, allow_fallback=False)
        if action == "previous_review":
            stored = read_workspace_json(Path(exercise_dir) / "review.json", workspace_root=root)
            return {**stored, "replayed": True}
        raise ValueError("EXERCISE_ACTION_INVALID")
    except (OSError, ValueError, TypeError) as exc:
        return {"status": "EXPECTED_FAILURE", "error_code": stable_error_code(exc)}


def _handler(root: Path, exercise_dir: str = DEFAULT_EXERCISE) -> type[BaseHTTPRequestHandler]:
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
            path = urlparse(self.path).path
            if path not in {"/api/review", "/api/exercise"}:
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
            # Reject cross-site requests before model execution or exercise setup.
            origin = self.headers.get("Origin")
            if origin and urlparse(origin).netloc != self.headers.get("Host"):
                self._send_json(403, {"status": "EXPECTED_FAILURE", "error_code": "CROSS_ORIGIN_BLOCKED"})
                return
            result = exercise_request(payload, root=root, exercise_dir=exercise_dir) if path == "/api/exercise" else review_request(payload, root=root)
            self._send_json(200 if result["status"] == "SUCCESS" else 422, result)

        def log_message(self, format: str, *args: object) -> None:
            del format, args

    return Handler


def create_server(
    *,
    root: Path | None = None,
    host: str = "127.0.0.1",
    port: int = 8765,
    exercise_dir: str = DEFAULT_EXERCISE,
) -> ThreadingHTTPServer:
    """Bind to loopback by default; no external interface is exposed."""

    return ThreadingHTTPServer((host, port), _handler((root or repository_root()).resolve(), exercise_dir))


def main() -> None:
    parser = argparse.ArgumentParser(description="Day 3 Review Copilot localhost UI")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--exercise-dir", default=DEFAULT_EXERCISE, help="Notebook에서 준비한 쿠폰 서비스 경로")
    parser.add_argument(
        "--smoke-and-exit",
        action="store_true",
        help="health와 sample review를 localhost HTTP로 확인한 뒤 종료",
    )
    args = parser.parse_args()
    server = create_server(host=args.host, port=args.port, exercise_dir=args.exercise_dir)
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
    print("Codex CLI 버튼으로 모델 실행 · 합성 쿠폰 서비스 · 종료: Ctrl+C")
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
    #checkout-findings{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:16px}#checkout-findings .finding{border:1px solid var(--line);border-radius:8px;padding:16px}#checkout-findings p{margin:8px 0}#checkout-findings p:first-child{font-weight:700;font-size:17px;margin-top:0}#checkout-findings p:nth-child(2){color:var(--muted);font-family:ui-monospace,monospace}#checkout-test-summary{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:16px}.test-list{padding:14px;border:1px solid var(--line);border-radius:8px}.test-row{display:flex;justify-content:space-between;gap:12px;border-top:1px solid var(--line);padding:5px 0;font-size:14px}.test-list h3{margin:0 0 10px;font-size:18px}@media(max-width:820px){#checkout-findings,#checkout-test-summary{grid-template-columns:1fr}}
  </style>
</head>
<body>
<header><b>Review Copilot</b><span>Day 3 · Codex CLI · 코드와 테스트</span></header>
<main>
  <section class="card wide"><h1>쿠폰 결제 서비스 리뷰</h1><p class="note">같은 입력으로 초안과 수정본의 실제 Python 코드를 실행합니다. 계산 → 실패 테스트 → Codex 리뷰 → 코드 수정 → 재검증 순서입니다.</p>
  <label>상품 금액 <input id="total" type="number" value="10000" style="width:120px;padding:10px"></label>
  <label>쿠폰 금액 <input id="coupon" type="number" value="15000" style="width:120px;padding:10px"></label>
  <button id="checkout-demo">결제 예정액 비교</button><button id="checkout-test" class="ghost">같은 테스트 실행</button>
  <div id="receipts" style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:16px"></div>
  <div id="checkout-status" class="status" style="margin-top:16px">상품 금액보다 큰 쿠폰을 적용하면 어떤 결과가 나올까요?</div>
  <div id="checkout-test-summary" hidden></div><details id="checkout-test-details" hidden><summary>실제 테스트 출력</summary><pre id="checkout-tests"></pre></details></section>
  <section class="card wide"><h2>Codex 코드 리뷰</h2><p class="note">로컬에 설치한 Codex CLI와 ChatGPT 로그인을 사용합니다. 모델 추론은 온라인에서 진행됩니다. 선택된 모델을 지정하지 않으면 CLI 기본값을 사용합니다.</p>
  <button id="checkout-review">Codex CLI 리뷰 실행</button><button id="checkout-previous" class="ghost">최근 리뷰 불러오기</button><button id="checkout-replay" class="ghost">수업용 예시 다시 보기</button><button id="checkout-md" class="ghost">리뷰 Markdown 저장</button>
  <div id="checkout-review-status" class="status" style="margin-top:16px">정책 · 실제 변경 코드 · 테스트 결과를 함께 전달합니다.</div><div id="checkout-findings"></div></section>
  <details class="card wide"><summary style="font-weight:700;cursor:pointer">회의 문서 코드 예제 · Workflow 단계 확인</summary><div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:16px">
  <section class="card"><h2>Unified Diff</h2><p class="note">샘플을 불러오거나 본인의 diff를 붙여 넣습니다. 입력은 서버에 저장되지 않습니다.</p><textarea id="diff"></textarea><button id="sample" class="ghost">샘플 불러오기</button><button id="approve">분석 시작</button></section>
  <section class="card"><h2>Human Review</h2><p class="note">Finding을 고치거나 체크를 해제한 뒤 반영합니다. 실제 GitHub 게시 명령은 실행되지 않습니다.</p><div id="status" class="status">샘플을 불러온 뒤 분석을 시작하세요.</div><div id="findings"></div><button id="edit" class="secondary">선택·수정 반영</button><button id="reject" class="ghost">전체 제외</button></section>
  <section class="card wide"><h2>평가와 Export</h2><div id="metrics"></div><button id="json" class="ghost">JSON 저장</button><button id="md" class="ghost">Markdown 저장</button><pre id="raw">아직 결과가 없습니다.</pre></section>
  </div></details>
</main>
<script>
let latest=null;
let checkoutReview=null;
const q=s=>document.querySelector(s);
function showReceipts(receipts){
  q('#receipts').replaceChildren();
  for(const key of ['starter','solution']){
    const receipt=receipts[key], box=document.createElement('div');
    box.style.cssText='border:1px solid #dfe4ea;padding:18px;border-radius:8px';
    const title=document.createElement('b');title.textContent=key==='starter'?'초안 · 수정 전':'참고 구현 · 수정 후';
    const amount=document.createElement('p');amount.style.cssText='font-size:32px;font-weight:800;margin:10px 0';
    amount.textContent=receipt.status==='SUCCESS'?`${receipt.result.payable_won.toLocaleString()}원`:receipt.error_code;
    const details=document.createElement('div');
    if(receipt.result)details.textContent=`적용 할인 ${receipt.result.coupon_applied_won.toLocaleString()}원 · 배송비 ${receipt.result.shipping_won.toLocaleString()}원`;
    box.append(title,amount,details);q('#receipts').append(box);
  }
  q('#checkout-status').textContent='실제 Python 함수 실행 완료 · 실제 결제 없음';
}
const testNames={
  test_normal_coupon:'일반 쿠폰', test_coupon_larger_than_total_is_capped:'상품 금액을 넘는 쿠폰',
  test_negative_total_is_rejected:'음수 상품 금액',test_negative_coupon_is_rejected:'음수 쿠폰',
  test_fractional_won_is_rejected:'소수 금액',test_bool_is_not_money:'bool 입력',
  test_shipping_uses_discounted_amount:'할인 후 배송비',test_free_shipping_at_threshold:'무료 배송 기준 금액',
  test_receipt_records_applied_discount:'영수증 할인액',
};
function showTests(tests){
  q('#checkout-test-summary').hidden=false;q('#checkout-test-summary').replaceChildren();
  q('#checkout-test-details').hidden=false;
  q('#checkout-tests').textContent=Object.entries(tests).map(([key,value])=>`${key} · ${value.status} · exit ${value.exit_code}\n${value.stderr}`).join('\n\n');
  for(const key of ['starter','solution']){
    const data=tests[key], box=document.createElement('div');box.className='test-list';
    const title=document.createElement('h3'), passed=(data.cases||[]).filter(x=>x.status==='PASSED').length;
    title.textContent=`${key==='starter'?'초안':'참고 구현'} · ${passed}/${data.test_count} 통과`;box.append(title);
    for(const item of data.cases||[]){
      const row=document.createElement('div');row.className='test-row';
      const label=document.createElement('span');label.textContent=testNames[item.name]||item.name;
      const status=document.createElement('b');status.textContent=item.status==='PASSED'?'✓ 통과':'× 실패';
      row.append(label,status);box.append(row);
    }
    q('#checkout-test-summary').append(box);
  }
  q('#checkout-status').textContent=`동일한 테스트 · 초안 ${tests.starter.status} / 참고 구현 ${tests.solution.status}`;
}
function showCheckoutReview(data){
  checkoutReview=data;
  q('#checkout-review-status').textContent=`${data.replayed?'저장된 실행 · ':''}실제 Provider ${data.provider.provider_used} · 모델 선택 ${data.provider.model} · 검토 ${data.review.findings.length}건`;
  q('#checkout-findings').replaceChildren();
  for(const finding of data.review.findings){
    const box=document.createElement('div');box.className='finding';
    for(const text of [`[${finding.severity}] ${finding.title}`,`${finding.path}:${finding.line}`,finding.impact,`수정 제안: ${finding.correction}`]){
      const paragraph=document.createElement('p');paragraph.textContent=text;box.append(paragraph);
    }
    q('#checkout-findings').append(box);
  }
}
async function checkout(action,provider){
  const payload={action,total_won:Number(q('#total').value),coupon_won:Number(q('#coupon').value)};
  const buttons=[q('#checkout-review'),q('#checkout-replay'),q('#checkout-previous')];
  if(provider){
    payload.provider=provider;payload.live_opt_in=provider==='codex_cli';
    q('#checkout-review-status').textContent=provider==='codex_cli'?'Codex CLI 실행 중 · 응답을 기다리고 있습니다.':'수업용 예시 불러오는 중';
  }
  try{
    if(action==='review')buttons.forEach(button=>button.disabled=true);
    const response=await fetch('/api/exercise',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    const data=await response.json();
    if(data.status!=='SUCCESS'){
      q('#checkout-review-status').textContent=`실행 중단 · ${data.error_code||data.provider?.error_code||'UNKNOWN'}`;return;
    }
    if(action==='demo')showReceipts(data.receipts);
    if(action==='test')showTests(data.tests);
    if(action==='review'||action==='previous_review')showCheckoutReview(data);
  }catch(error){q('#checkout-review-status').textContent='서버 연결을 확인한 뒤 다시 실행해 주세요.'}
  finally{buttons.forEach(button=>button.disabled=false)}
}
q('#checkout-demo').onclick=()=>checkout('demo');
q('#checkout-test').onclick=()=>checkout('test');
q('#checkout-review').onclick=()=>checkout('review','codex_cli');
q('#checkout-previous').onclick=()=>checkout('previous_review');
q('#checkout-replay').onclick=()=>checkout('review','fixture');
q('#checkout-md').onclick=()=>checkoutReview&&download('checkout-review.md',checkoutReview.markdown,'text/markdown');
async function loadSample(){const r=await fetch('/api/sample');const d=await r.json();q('#diff').value=d.diff_text||''}
function download(name,text,type){const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([text],{type}));a.download=name;a.click();URL.revokeObjectURL(a.href)}
function edits(){return [...document.querySelectorAll('.finding')].filter(x=>x.querySelector('[type=checkbox]').checked).map(x=>{const original=JSON.parse(x.dataset.item);for(const k of ['title','impact','correction'])original[k]=x.querySelector(`[data-k=${k}]`).value;return original})}
function render(d){latest=d;q('#raw').textContent=JSON.stringify(d,null,2);q('#findings').replaceChildren();if(d.status!=='SUCCESS'){q('#status').textContent=`실행 중단 · ${d.error_code}`;return}const s=d.stages;q('#status').textContent=`${s['06_human_review'].status} · Focused Test ${s['05_hybrid_review'].test_evidence.status} · GitHub ${s['08_release_evidence'].github_dry_run.status}\nRelease ${s['08_release_evidence'].decision} · 외부 서비스 변경: 없음`;for(const f of s['06_human_review'].findings){const box=document.createElement('div');box.className='finding';box.dataset.item=JSON.stringify(f);const top=document.createElement('label');const check=document.createElement('input');check.type='checkbox';check.checked=true;top.append(check,` ${f.severity} · ${f.path}:${f.line} · ${f.rule_id}`);box.append(top);for(const k of ['title','impact','correction']){const input=document.createElement('input');input.dataset.k=k;input.value=f[k];box.append(input)}q('#findings').append(box)}const m=s['07_evaluation'];q('#metrics').textContent=`Golden ${m.case_passed}/${m.case_count} · Precision ${m.precision} · Recall ${m.recall} · F1 ${m.f1} · ${m.release_decision}`}
async function run(decision){const payload={diff_text:q('#diff').value,decision,reviewer:'localhost-user',rationale:'화면에서 근거와 최소 교정을 확인했습니다.',run_tests:true};if(decision==='edit')payload.edited_findings=edits();const r=await fetch('/api/review',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});render(await r.json())}
q('#sample').onclick=loadSample;q('#approve').onclick=()=>run(null);q('#edit').onclick=()=>run('edit');q('#reject').onclick=()=>run('reject');q('#json').onclick=()=>latest&&download('day3-review.json',JSON.stringify(latest,null,2),'application/json');q('#md').onclick=()=>latest&&download('day3-review.md',latest.markdown||'','text/markdown');loadSample();
</script>
</body></html>"""


if __name__ == "__main__":
    main()
