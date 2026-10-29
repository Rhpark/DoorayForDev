# 구현 계획 — Dooray 위키 wiki-list / wiki-read / wiki-write

기준: 같은 폴더의 `SPEC.md`(2026-10-27 갱신 섹션 포함). 순서대로 진행하고 끝난 항목은 체크한다.

## CLI (`Dooray/dooray.py`) — TDD, seam: CLI main + `Dooray._api` fake

- [x] 1. 테스트 seam 준비: `tests/test_wiki.py`에 메모리 위키 트리 fake(`_api` 대체), 설정 로드 대체, `main` 실행 후 stdout·종료 메시지·쓰기 요청 기록을 돌려주는 헬퍼
- [x] 2. 위키 ID 해석(위키 목록 페이지네이션, `project.id` 일치), 하위 목록 페이지네이션, 경로 해석(`>` 분리·공백 제거·끝 `>` 탐색 모드·`위키이름 >` 접두어·완전 일치·미일치 시 후보·동명 시 후보)
- [x] 3. `wiki-list [경로]`: 전위 순회, 중간 페이지 포함, `N. 위키이름 > …` 출력, 시작 경로 하위만, 빈 결과 안내, 형제 하위 트리 병렬 조회
- [x] 4. `wiki-read [경로][>]`: 읽기 모드(경로 머리줄 + 본문 그대로, 빈 본문 표시 없음), 탐색 모드(하위 `N. 제목` 목록, 하위 없으면 본문)
- [x] 5. `wiki-write <경로> (<내용>|--file <파일>) [--dry-run]`: 부모 필수, 있으면 `## YYYY-MM-DD` 헤더로 이어쓰기, 없으면 생성(헤더 없음), `--dry-run`은 판단만, `@이름` 멘션 치환, 끝 `>`·빈 대상은 오류
- [x] 6. `KNOWN_CMDS`·도움말(docstring)에 위키 명령 추가
- [x] 7. 전체 오프라인 테스트 실행(`python -B -m unittest discover -s tests`)

## 실제 Dooray 확인

- [x] 8. 읽기 확인(Snoopy, GET만): `wiki-list`, `wiki-list 회의록`, `wiki-read 경로`, `wiki-read 경로>`
  - 확인됨: 전체 19페이지 트리, 회의록 하위, 인자 없는 탐색, 없는 경로 후보 표시, 실제 본문 읽기, `wiki-write --dry-run`
  - 발견 1: 실제 제목에 `>`가 있다(`AI BSM > SUMO` 아래 `HD Map > SUMO Network`). 이 페이지는 현재 경로로 가리킬 수 없다 — 사용자 결정 필요
  - 발견 2: Windows launcher(`dooray.cmd`)에서 공백 없는 `"Visualizer>"`는 cmd.exe가 `>`를 리다이렉션으로 해석해 `The syntax of the command is incorrect.`로 실패. `"A>B"` 형태면 파일 리다이렉션 + 다른 페이지에 쓰기 위험 — 사용자 결정 필요
  - 결정(사용자): 발견 1은 제목 우선 매칭(남은 조각을 길게 붙인 것부터 제목과 비교, `>` 앞뒤 공백 무시)으로 해결 → 구현·테스트 완료, 실제 `HD Map > SUMO Network` 읽기 확인. 발견 2는 `>`·` > ` 둘 다 허용 — Skill이 경로를 ` > `로 정리하고 따옴표로 감싸 호출한다
- [x] 9. 쓰기 API 실측 — 사용자 승인, 위치 `Snoopy > Visualizer > CLI 쓰기 테스트`
  - `--dry-run` 생성 예정 → 생성(POST `/pages`) → `--dry-run` 이어쓰기 예정 → 이어쓰기(PUT `/pages/{id}/content`, `## 2026-10-27` 헤더) → 다시 읽기 모두 정상. `version` 불필요
  - 멘션: 본문에 `[@박랑호](dooray://…/members/… "me")`로 저장됨(자기 자신이라 Dooray가 `member`→`me`로 바꿈). 웹 화면의 멘션 표시는 사용자 확인 필요
  - 페이지 웹 주소 형식: 미확인 → SPEC 기본값대로 출력하지 않음
  - 테스트 페이지는 위키에 남아 있다(삭제는 도구 범위 밖)

## Skill·문서

- [x] 10. Claude Skill 3개(`dooray-wiki-list`·`dooray-wiki-read`·`dooray-wiki-write`)
- [x] 11. Codex Skill 3개 + `agents/openai.yaml`
- [x] 12. `DOORAY.md`(Skill 표, CLI 대응표), README(명령·Skill 표, 위키 제외 서술), `dooray-init` 단축 명령(Claude·Codex, PowerShell·bash)
- [x] 13. Skill 수동 확인(번호 목록 탐색, 쓰기 전 확인, 임시 파일 정리) — `disable-model-invocation`이라 사용자가 `/dooray-wiki-*`를 직접 호출해야 한다
  - 2026-10-28 사용자 실행: `/dooray-wiki-list 회의록`, `/dooray-wiki-read`(경로 지정, 번호 목록 탐색으로 `AI BSM > 데이터셋 초안`까지, 공백 없는 `Visualizer>CLI 쓰기 테스트`), `/dooray-wiki-write`(경로 지정 이어쓰기, `Visualizer>` 번호 목록에서 `b. 하위에 새 페이지` 생성) 모두 정상. 쓰기는 `--dry-run` 확인 후에만 실행, 임시 파일 정리 확인. 참고: 번호 답을 `/dooray-wiki-read 3`처럼 슬래시 명령으로 보내면 새 호출이 되므로 일반 메시지로 답해야 이어진다

## 마무리

- [x] 14. `/code-review`(medium)로 검토 후 반영 — 지적 10건
  - 반영: 제목 쪽이 막다른 길이면 짧게 나눈 쪽으로 되돌아가 찾음(엉뚱한 부모 아래 생성 방지), `--dry-run`도 멘션 해석을 거침, 빈 내용 거절. 각각 테스트 추가
  - 반영 안 함(이유): 제목 우선이라 같은 글자의 중첩 페이지는 경로로 못 가리킴·list에 같은 줄이 둘 나옴(사용자 결정 "우선순위는 제목", 실제 Snoopy에는 충돌 없음) / 위키 이름과 같은 최상위 페이지(SPEC에 기록된 한계) / 내용 중 `--dry-run` 글자(Skill은 항상 끝에 붙임) / 깊이마다 스레드 풀(ponytail 주석으로 한계 기록, 현재 19페이지) / 따옴표 없는 write 경로(문서에 따옴표 필수 명시, Skill은 항상 감쌈) / 페이지네이션 루프 중복(동작 동일, 리팩터링 보류)
- [ ] 15. 커밋 — 이 폴더는 git 저장소가 아니다(`git rev-parse` 실패). 사용자에게 알리고 지시를 따른다

## 추가 — 위키 댓글·파일 (SPEC 2026-10-27 "위키 댓글·파일 읽기와 wiki-download 추가")

- [x] 16. `wiki-read` 읽기 결과에 댓글(시간순)·파일 목록(첨부 → 본문 이미지, 번호) 추가, 없으면 구역 생략, 주소는 맨 아래 — 테스트 먼저
- [x] 17. `wiki-download "경로" [파일명|번호|all]` — 저장 `Dooray/report/wiki-<페이지ID>/download/<파일ID>_<파일명>`, 업무 `download`와 같은 선택 규칙 — 테스트 먼저
- [x] 18. 도움말·`KNOWN_CMDS`, `DOORAY.md`, README, Skill(wiki-read 안내), `dooray-init` 단축 명령(`dooray-wiki-download`)
- [x] 19. 전체 테스트 + 실제 위키 확인(`주간 미팅 노트` 댓글, 파일 목록, 작은 파일 1개 다운로드)

## 추가 — 저장 폴더 task·wiki 분리 (SPEC 2026-10-27 "저장 폴더를 task·wiki로 분리")

- [x] 20. 업무 `Dooray/task/report/<번호>/download/`, 위키 `Dooray/wiki/<위키>/<제목>/.../download/`(실제 제목, 금지 문자 `_`) — 테스트 먼저
- [x] 21. `.gitignore`, `DOORAY.md`, README(업데이트 안내 포함), `dooray-report` Skill·절차, 도움말
- [x] 22. 전체 테스트 + 실측(업무 #124, 제목에 `>`가 있는 위키 페이지), 검증용 기존 파일 이동
