---
name: dooray-wiki-read
description: 프로젝트 Dooray 위키 페이지의 본문·댓글·파일 목록을 읽는다. 경로가 없거나 끝에 > 가 있으면 하위 페이지를 번호 목록으로 보여주고 한 단계씩 골라 내려간다. 사용법 /dooray-wiki-read [경로][>]. 사용자가 이 명령을 직접 호출했을 때 사용.
disable-model-invocation: true
model: sonnet
effort: medium
allowed-tools:
  - PowerShell(dooray wiki-read)
  - PowerShell(dooray wiki-read *)
  - Bash(dooray wiki-read)
  - Bash(dooray wiki-read *)
---

1. 저장소 루트로 이동한 뒤 실행한다. 경로는 `>` 앞뒤를 공백 한 칸으로 맞추고(`Visualizer>` → `Visualizer >`) 따옴표로 감싼다. Windows `dooray` launcher는 공백 없는 `>`를 리다이렉션으로 해석한다. 경로가 없으면 인자 없이 실행한다.

```
dooray wiki-read ["<경로>"]
```

2. 출력의 둘째 줄이 `  1. 제목` 형태면 탐색 단계다. 첫 줄(현재 경로)과 번호 목록을 그대로 보여주고, 목록 끝에 `0. 여기 읽기`를 덧붙여 번호나 제목으로 고르게 한다. 선택 UI(AskUserQuestion)는 쓰지 않는다 — 선택지 개수 제한이 있다.
   - 하위 페이지를 고르면 `"<첫 줄 경로> > <고른 제목> >"`로 다시 실행하고 2번을 반복한다.
   - `0. 여기 읽기`를 고르면 `"<첫 줄 경로>"`(끝 `>` 없이)로 실행한다.
3. 첫 줄 다음이 빈 줄과 본문이거나 첫 줄만 있으면 읽기 결과다(본문 뒤에 댓글·파일 목록·위키 주소가 붙는다). 원본 그대로 보여준다. 요약하지 않는다. 도구 출력 상자는 터미널이 접을 수 있으니, 결과 전체를 답변 본문 코드블록에 붙여넣는다.

파일 다운로드를 원하면 `dooray wiki-download "<첫 줄 경로>" [파일명|번호|all]`을 실행한다. 번호는 파일 목록 번호이고, 생략하면 전체를 받는다.

없는 경로나 같은 제목이 여럿인 오류는 그대로 알린다. 오류에 하위 페이지 목록이 있으면 그 목록에서 다시 고르게 할 수 있다.
