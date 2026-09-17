---
name: dooray-report
description: 사용자가 /dooray-report로 지정한 Dooray 업무의 코드 적용 방안 보고서를 생성하거나 갱신한다. 구현은 수행하지 않는다. 스킬 설명·검토 요청에는 보고서를 작성하지 않는다.
disable-model-invocation: true
model: opus
effort: high
allowed-tools:
  - Read
  - Grep
  - Glob
  - Write(Dooray/report/**)
  - Edit(Dooray/report/**)
  - PowerShell(python Dooray/dooray.py full *)
  - PowerShell(python Dooray/dooray.py download *)
  - Bash(python Dooray/dooray.py full *)
  - Bash(python Dooray/dooray.py download *)
  - Bash(date *)
  - PowerShell(Get-Date *)
---
# Dooray 적용 방안 보고서

Dooray 본문·댓글·첨부의 요구사항을 현재 코드와 대조하여, 무엇을 어디에서 어떻게 바꿀지와 확인 방법을 보고서로 작성한다. 구현은 수행하지 않는다.

1. 저장소 루트의 `DOORAY.md`를 읽는다.
2. [공통 절차](references/report-workflow.md)의 자료 확인 → 코드 분석 → 적용 방안 작성 → 근거·명확성 검수를 따른다. 신규 보고서는 [템플릿](references/report-template.md)을 사용한다.
3. 보고서는 Write/Edit로 생성·갱신한다. 첨부는 Read로 실제 내용을 확인한 범위만 근거로 사용한다. PDF의 일부 페이지만 읽었으면 읽지 못한 페이지를 미확인으로 기록한다.
4. 저장한 파일을 다시 읽고 경로와 전문을 전달한다.
