---
name: dooray-report
description: 사용자가 $dooray-report로 지정한 Dooray 업무의 코드 적용 방안 보고서를 생성하거나 갱신한다. 구현은 수행하지 않는다. 스킬 설명·검토 요청에는 보고서를 작성하지 않는다.
---
# Dooray 적용 방안 보고서

Dooray 본문·댓글·첨부의 요구사항을 현재 코드와 대조하여, 무엇을 어디에서 어떻게 바꿀지와 확인 방법을 보고서로 작성한다. 구현은 수행하지 않는다.

1. 저장소 루트의 `DOORAY.md`를 읽는다.
2. `.claude/skills/dooray-report/references/report-workflow.md`의 자료 확인 → 코드 분석 → 적용 방안 작성 → 근거·명확성 검수를 따른다. 신규 보고서는 같은 디렉터리의 `report-template.md`를 사용한다. 경로는 저장소 루트 기준이다.
3. 보고서는 `apply_patch`로 생성·갱신한다. 이미지는 이미지 보기 도구로 직접 확인한다. PDF와 기타 첨부는 현재 도구로 내용을 판독할 수 있을 때만 처리한다.
4. 저장한 파일을 다시 읽고 경로와 전문을 전달한다.
