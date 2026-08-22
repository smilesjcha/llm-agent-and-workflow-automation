# Meeting Agent Review Lab

Python의 LangChain LCEL과 LangGraph interrupt/resume 실행 결과를 검토하는 정적 UI다. 브라우저에서 승인·수정·거절을 바꾸고 최종 state를 JSON으로 내려받는다.

## 로컬 실행

저장소 최상위에서 실행 결과를 갱신한다.

```bash
python scripts/build_langchain_langgraph_demo.py
cd web-demo
npm run check
npm run build
npm run dev
```

브라우저에서 `http://localhost:4173`을 연다.

## Vercel 배포

```bash
cd web-demo
npx vercel
npx vercel --prod
```

이 UI는 정적 결과 검토 화면이다. 실제 LCEL·StateGraph 실행과 테스트는 저장소의 Python 코드와 Notebook에서 수행한다. Demo는 이메일·외부 데이터 변경을 실행하지 않는다.
