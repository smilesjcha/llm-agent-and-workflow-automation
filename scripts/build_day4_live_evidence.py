"""Render the saved real CLI response, without inventing a desktop chat UI."""
from pathlib import Path
import html

ROOT = Path(__file__).resolve().parents[1]
folder = ROOT / "assets/components/day4"
raw = (folder / "codex-live-review.raw.md").read_text(encoding="utf-8")
page = """<!doctype html><html lang="ko"><meta charset="utf-8">
<title>Codex CLI 실제 리뷰 응답</title>
<style>body{max-width:1100px;margin:40px auto;padding:0 28px;font:22px/1.6 sans-serif;color:#161616}h1{font-size:36px}header{border-bottom:2px solid #161616;margin-bottom:26px}.meta{color:#555;font-size:18px}pre{font:20px/1.6 sans-serif;white-space:pre-wrap}aside{padding:20px;background:#f1f2f3}</style>
<header><h1>Codex CLI 실제 리뷰 응답</h1><p class="meta">2026-09-12 · codex-cli 0.151.0 · gpt-5.6-sol · read-only</p>
<p>저장한 실제 모델 응답의 브라우저 보기입니다. Desktop 대화 화면이 아닙니다.</p></header>
<aside>사람 확인: 응답의 checkout.py:5는 docstring 위치입니다.<br>실제 계산식은 6행입니다. 아래 원문은 수정하지 않았습니다.</aside><pre>""" + html.escape(raw) + "</pre></html>"
(folder / "codex-live-review.html").write_text(page, encoding="utf-8")
print(folder / "codex-live-review.html")
