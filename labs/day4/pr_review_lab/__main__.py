"""Run from the repository root: python -m labs.day4.pr_review_lab --help."""

import argparse
import json

from .service import (
    LabError, approve_preview, build_review, check_exercise,
    fetch_public_pr, load_fixture, prepare_exercise, preview_publication,
    render_outputs, workspace_path,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="4주차 PR 리뷰 작업대 · 기본 실행은 합성 fixture, 원격 게시 없음")
    parser.add_argument("--workspace", default=".", help="허용할 작업 폴더")
    subs = parser.add_subparsers(dest="command", required=True)
    prepare = subs.add_parser("prepare", help="학생이 직접 수정할 코드와 테스트 생성")
    prepare.add_argument("--out", default="output/day4-pr/my-exercise")
    check = subs.add_parser("check", help="학생이 선택한 실습 폴더의 테스트 실행")
    check.add_argument("--exercise-dir", default="output/day4-pr/my-exercise")
    demo = subs.add_parser("demo", help="합성 PR의 diff·리뷰 Markdown·HTML 생성")
    demo.add_argument("--out", default="output/day4-pr/review")
    demo.add_argument("--exercise-dir", help="선택: 이 폴더의 테스트 결과를 화면에 표시")
    preview = subs.add_parser("preview", help="기존 Markdown 검토 후 게시 payload만 생성")
    preview.add_argument("--out", default="output/day4-pr/review")
    preview.add_argument("--approve", action="store_true", help="review.md를 읽고 확인한 사람이 직접 선택")
    preview.add_argument("--reviewer", default="")
    preview.add_argument("--simulate-stale", action="store_true")
    preview.add_argument("--simulate-duplicate", action="store_true")
    fetch = subs.add_parser("fetch", help="선택: GitHub 공개 PR GET-only 읽기")
    fetch.add_argument("--repo", required=True)
    fetch.add_argument("--pr", required=True, type=int)
    fetch.add_argument("--allow-network", action="store_true")
    fetch.add_argument("--out", default="output/day4-pr/public-snapshot.json")
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            result = prepare_exercise(args.workspace, args.out)
        elif args.command == "check":
            result = check_exercise(args.workspace, args.exercise_dir)
            print(result["output"])
            return result["exit_code"]
        elif args.command == "fetch":
            snapshot = fetch_public_pr(args.repo, args.pr, allow_network=args.allow_network)
            path = workspace_path(args.workspace, args.out)
            if path.exists():
                raise LabError("OUTPUT_EXISTS", "새 출력 파일명을 지정하세요.")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
            result = {"status": "READ_ONLY_FETCHED", "path": str(path), "remote_write_performed": False}
        else:
            snapshot = load_fixture()
            review = build_review(snapshot)
            test_result = None
            publication = None
            if args.command == "preview":
                folder = workspace_path(args.workspace, args.out)
                source_md = workspace_path(args.workspace, folder / "review.md")
                if not source_md.is_file() or source_md.read_text(encoding="utf-8") != review["markdown"]:
                    raise LabError("REVIEW_DOCUMENT_MISMATCH", "demo로 만든 review.md를 먼저 읽으세요. 수정한 초안은 API에서 다시 검토합니다.")
                approval = approve_preview(snapshot, review, approved=args.approve, reviewer=args.reviewer)
                head = "3" * 40 if args.simulate_stale else snapshot["head_sha"]
                existing = [{"body": f"<!-- day4-review:{review['review_sha256']} -->"}] if args.simulate_duplicate else []
                publication = preview_publication(snapshot, review, approval, current_head_sha=head, existing_reviews=existing)
            elif args.exercise_dir:
                test_result = check_exercise(args.workspace, args.exercise_dir)
            paths = render_outputs(args.workspace, args.out, snapshot, review, publication, test_result)
            result = {"status": "PREVIEW_ONLY" if publication else "AWAITING_HUMAN_REVIEW",
                      "provider": "fixture", "remote_write_performed": False, "files": paths}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except LabError as exc:
        print(json.dumps(exc.as_dict(), ensure_ascii=False, indent=2))
        return 2
    except OSError:
        print(json.dumps({"status": "BLOCKED", "error_code": "FILE_ACCESS_FAILED",
                          "message": "선택한 실습 파일의 위치와 읽기·쓰기 권한을 확인하세요."}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
