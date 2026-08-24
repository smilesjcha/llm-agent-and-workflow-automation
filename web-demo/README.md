# Agent Service Labs

Day 1은 LangChain LCEL과 LangGraph interrupt/resume 결과를 검토한다. Day 2~5는 각 Notebook과 Python service가 만든 `output/course-demos/dayN/demo_result.json`을 같은 화면 계약으로 보여준다.

## 로컬 실행

저장소 최상위에서 실행 결과를 갱신한다.

```bash
python scripts/build_langchain_langgraph_demo.py
cd web-demo
npm run check
npm run build
npm run dev
```

브라우저에서 Day 1은 `http://localhost:4173`, Day 2~5는 `http://localhost:4173/course.html?day=2`처럼 연다.

## Vercel 배포

```bash
cd web-demo
npx vercel
npx vercel --prod
```

이 UI는 정적 결과 검토 화면이다. 실제 LCEL·StateGraph 실행과 테스트는 저장소의 Python 코드와 Notebook에서 수행한다. Demo는 이메일·외부 데이터 변경을 실행하지 않는다.
