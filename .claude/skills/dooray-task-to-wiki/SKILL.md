---
name: dooray-task-to-wiki
description: 사용자가 /dooray-task-to-wiki를 직접 호출하면 업무 본문·히스토리·첨부를 개발자·엔지니어용 위키 초안으로 정리한다. 검토 후 위치와 첨부를 확인받아 게시한다. 스킬 설명·검토 요청에는 실행하지 않는다.
disable-model-invocation: true
model: opus
effort: high
allowed-tools:
  - Read
  - Grep
  - Glob
  - Write(Dooray/wiki/**)
  - Edit(Dooray/wiki/**)
  - PowerShell(dooray full *)
  - PowerShell(dooray download *)
  - PowerShell(dooray link *)
  - PowerShell(dooray wiki-list)
  - PowerShell(dooray wiki-list *)
  - PowerShell(dooray wiki-read)
  - PowerShell(dooray wiki-read *)
  - Bash(dooray full *)
  - Bash(dooray download *)
  - Bash(dooray link *)
  - Bash(dooray wiki-list)
  - Bash(dooray wiki-list *)
  - Bash(dooray wiki-read)
  - Bash(dooray wiki-read *)
---
# Dooray 업무 → 위키 문서

업무 하나를 읽고, 그 업무를 모르는 개발자·엔지니어가 사용할 위키 문서를 작성한다.

1. 저장소 루트의 `DOORAY.md`를 읽는다.
2. [공통 절차](references/task-to-wiki-workflow.md)의 자료 확인 → 초안 작성·검토 → 위치 선정 → 게시 확인·업로드 절차를 따른다.
3. 초안은 Write/Edit로 생성·수정한다. 첨부·이미지는 Read로 실제 확인한 범위만 근거로 사용한다. 일부 페이지만 읽은 PDF 등은 읽지 못한 부분을 추측하지 않는다.

자료 조회와 게시에는 저장소 루트의 `dooray` CLI를 사용한다. 위키 위치를 고를 때는 전체 번호 목록을 보여주고 선택 UI(AskUserQuestion)는 쓰지 않는다.

`dooray wiki-write`는 일부러 allowed-tools에 넣지 않았다. 공통 절차의 판단·게시 단계에서 실행 전 권한 확인을 한 번 더 받는 것이 의도된 동작이다(위키 쓰기 이중 확인).
