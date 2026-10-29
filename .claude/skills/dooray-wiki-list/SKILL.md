---
name: dooray-wiki-list
description: 프로젝트 Dooray 위키의 페이지를 전체 경로로 한 줄씩 보여준다. 사용법 /dooray-wiki-list [경로]. 사용자가 이 명령을 직접 호출했을 때 사용.
disable-model-invocation: true
model: sonnet
effort: low
allowed-tools:
  - PowerShell(dooray wiki-list)
  - PowerShell(dooray wiki-list *)
  - Bash(dooray wiki-list)
  - Bash(dooray wiki-list *)
---

저장소 루트로 이동한 뒤 실행 (경로를 주면 그 아래만):

```
dooray wiki-list ["<경로>"]
```

경로는 `>` 앞뒤를 공백 한 칸으로 맞추고(`회의록>LG` → `회의록 > LG`) 따옴표로 감싼다. Windows `dooray` launcher는 공백 없는 `>`를 리다이렉션으로 해석한다.

원본 결과만 그대로 즉시 보여준다. 요약하지 않는다. 도구 출력 상자는 터미널이 접을 수 있으니, 결과 전체를 답변 본문 코드블록에 붙여넣는다.
