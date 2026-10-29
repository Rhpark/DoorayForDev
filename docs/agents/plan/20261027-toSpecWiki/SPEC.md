# Dooray 위키 읽기·쓰기 Skill — SPEC

## PRD

### Problem Statement

개발자는 터미널과 Claude Code·Codex 안에서 Dooray 업무를 조회하고 댓글을 남길 수 있다. 하지만 같은 프로젝트의 Dooray 위키는 웹 UI로만 다룰 수 있다. 회의록이나 정리 문서를 참고하려 해도, 코드 구조·실행 방법·용어를 위키에 남기려 해도 작업 흐름을 벗어나 브라우저로 이동해야 한다.

Dooray 위키 API는 `wikiId`·`pageId` 같은 ID로만 페이지를 가리키고 하위 페이지를 한 깊이씩만 돌려준다. 그래서 원시 API를 직접 쓰면 원하는 페이지 하나를 찾는 데도 여러 번 호출하며 ID를 옮겨 적어야 한다. 현재 도구는 업무만 다루고, README에는 위키를 의도적으로 제외했다고 적혀 있다.

### Solution

기존 업무 CLI와 같은 방식으로 위키 명령 3개와 Skill 3개를 추가한다.

- `/dooray-wiki-list [경로]` — 프로젝트 위키의 페이지를 중간 페이지까지 포함해 `Snoopy > 회의록 > …` 같은 전체 경로 한 줄씩, 번호를 붙여 보여준다. 경로를 주면 그 하위만 보여준다.
- `/dooray-wiki-read [경로][>]` — 경로를 주면 그 페이지 본문을 보여준다. 경로가 없거나 끝에 `>`를 붙이면 하위 페이지를 번호 목록으로 보여주고, 사용자가 한 단계씩 골라 내려가 읽는다.
- `/dooray-wiki-write [경로][>] <내용|.md파일>` — 받은 내용을 그대로 올린다. 대상 페이지가 있으면 날짜 헤더(`## YYYY-MM-DD`)를 붙여 이어쓰고, 없으면 부모 아래에 새로 만든다. 실행 전에 생성/이어쓰기, 대상 경로, 내용을 보여주고 확인을 받는다.

페이지는 ID가 아니라 제목 경로(`>` 구분)로 가리키고, 위키는 `REPOSITORY` 설정으로 자동 선택된다. 업무를 가공해 위키로 쓰는 `/dooray-task-to-wiki`는 이 기능 위에 후속으로 만든다.

### User Stories

1. As a 개발자, I want `/dooray-wiki-list`로 프로젝트 위키의 모든 페이지를 전체 경로 한 줄씩 보고 싶다, so that 위키 구조를 웹을 열지 않고 한 번에 파악할 수 있다
2. As a 개발자, I want 목록에 중간 페이지(하위를 가진 페이지)도 한 줄로 나오기를 원한다, so that 중간 페이지도 읽기·쓰기 대상으로 바로 지정할 수 있다
3. As a 개발자, I want 목록이 트리 순서(부모 바로 아래에 그 자식들)로 나오기를 원한다, so that 경로 줄만 읽어도 계층을 따라갈 수 있다
4. As a 개발자, I want 목록 각 줄에 번호가 붙기를 원한다, so that 페이지 수와 위치를 쉽게 가리킬 수 있다
5. As a 개발자, I want `/dooray-wiki-list 회의록`처럼 시작 경로를 지정해 그 하위만 보고 싶다, so that 페이지가 많은 위키에서도 필요한 부분만 빠르게 볼 수 있다
6. As a 개발자, I want 목록 줄(`Snoopy > 회의록 > …`)을 그대로 복사해 read·write 경로로 쓰고 싶다, so that 제목을 다시 타이핑하다 틀리지 않는다
7. As a 개발자, I want 경로 입력에서 맨 앞 `Snoopy >`(위키 이름)를 붙여도 빼도 같은 페이지로 해석되기를 원한다, so that 복사한 줄과 직접 쓴 경로가 모두 동작한다
8. As a 개발자, I want 경로의 `>` 앞뒤 공백 유무와 관계없이 같은 경로로 해석되기를 원한다, so that `Visualizer>test`와 `Visualizer > test`를 구분할 필요가 없다
9. As a 개발자, I want `/dooray-wiki-read Visualizer`로 그 페이지 본문을 바로 읽고 싶다, so that 경로를 알 때는 한 번에 내용을 볼 수 있다
10. As a 개발자, I want 인자 없이 `/dooray-wiki-read`를 호출하면 Home 바로 아래 페이지들이 번호 목록으로 나오기를 원한다, so that 경로를 몰라도 탐색을 시작할 수 있다
11. As a 개발자, I want `/dooray-wiki-read Visualizer>`처럼 끝에 `>`를 붙이면 그 페이지 하위부터 번호 목록으로 탐색하고 싶다, so that 아는 위치까지는 경로로 건너뛰고 나머지만 고를 수 있다
12. As a 개발자, I want 번호 목록에서 번호나 제목으로 답해 한 단계씩 내려가고 싶다, so that 하위 페이지가 몇 개든 한 화면에서 고를 수 있다
13. As a 개발자, I want 하위가 없는 페이지에 도달하면 자동으로 본문이 보이기를 원한다, so that 끝까지 내려간 뒤 따로 읽기 명령을 내리지 않아도 된다
14. As a 개발자, I want 탐색 중 "여기 읽기"를 골라 중간 페이지 본문을 읽고 싶다, so that 하위가 있는 페이지의 내용도 확인할 수 있다
15. As a 개발자, I want 하위가 없는 페이지에 `>`를 붙여도 그 페이지 본문이 보이기를 원한다, so that 실수로 `>`를 붙여도 막히지 않는다
16. As a 개발자, I want 본문이 빈 페이지를 읽으면 경로 머리줄만 보이고 별도 표시는 없기를 원한다, so that 출력이 간결하면서도 오류와 구분된다
17. As a 개발자, I want 읽은 본문이 요약·재작성 없이 원본 그대로 보이기를 원한다, so that 위키에 적힌 내용을 정확히 확인할 수 있다
18. As a 개발자, I want 경로의 한 단계가 없으면 그 위치에서 고를 수 있는 하위 페이지 목록과 함께 오류가 나기를 원한다, so that 오타를 바로 고칠 수 있다
19. As a 개발자, I want 같은 제목의 형제 페이지가 여럿이면 후보를 보여주고 종료하기를 원한다, so that 엉뚱한 페이지를 읽거나 쓰지 않는다
20. As a 터미널 사용자, I want AI 없이 `dooray wiki-list`, `dooray wiki-read 경로`, `dooray wiki-read 경로>`를 실행하고 싶다, so that AI 토큰을 쓰지 않고 위키를 조회할 수 있다
21. As a 터미널 사용자, I want `dooray-wiki-list`·`dooray-wiki-read`·`dooray-wiki-write` 단축 명령을 쓰고 싶다, so that 기존 업무 단축 명령과 같은 방식으로 짧게 실행할 수 있다
22. As a 개발자, I want `/dooray-wiki-write Visualizer>test <내용>`을 실행했을 때 test가 있으면 그 페이지에 이어쓰기를 원한다, so that 기존 문서를 지우지 않고 내용을 쌓을 수 있다
23. As a 개발자, I want 같은 명령에서 test가 없으면 Visualizer 아래에 test 페이지가 새로 만들어져 내용이 쓰이기를 원한다, so that 생성과 이어쓰기를 명령 하나로 처리할 수 있다
24. As a 개발자, I want 이어쓸 때마다 `## YYYY-MM-DD` 날짜 헤더가 붙기를 원한다, so that 언제 무엇이 추가됐는지 페이지 안에서 이력을 추적할 수 있다
25. As a 개발자, I want 같은 날 두 번 이어써도 헤더가 하나 더 붙기를 원한다, so that 추가 단위가 섞이지 않는다
26. As a 개발자, I want 새 페이지에는 날짜 헤더 없이 내용만 쓰이기를 원한다, so that 첫 문서가 깔끔하게 시작된다
27. As a 개발자, I want 내가 준 내용이 다듬어지지 않고 그대로 올라가기를 원한다, so that 의도한 문구와 형식이 그대로 위키에 남는다
28. As a 개발자, I want 긴 내용을 로컬 `.md` 파일로 넘겨 올리고 싶다, so that 코드 구조·실행 방법·용어 정리처럼 긴 문서도 인자 입력 없이 올릴 수 있다
29. As a 개발자, I want 내용에 따옴표·줄바꿈·특수문자가 있어도 깨지지 않고 올라가기를 원한다, so that 셸 이스케이프 문제를 신경 쓰지 않아도 된다
30. As a 개발자, I want 내용의 `@한글이름`이 실제 멘션으로 바뀌기를 원한다, so that 위키에서 동료에게 알림을 보낼 수 있다
31. As a 개발자, I want 쓰기 전에 "새 페이지 생성"인지 "기존 페이지 이어쓰기"인지와 대상 전체 경로, 올릴 내용을 확인하고 싶다, so that 오타로 원치 않는 페이지가 생기거나 엉뚱한 페이지에 쓰는 일을 막을 수 있다
32. As a 개발자, I want 확인 단계에서 거절하면 아무것도 쓰이지 않기를 원한다, so that 안심하고 미리 볼 수 있다
33. As a 개발자, I want `/dooray-wiki-write Visualizer>`처럼 끝에 `>`를 붙이면 번호 목록으로 쓸 위치를 고르고 싶다, so that 경로를 몰라도 쓸 곳을 찾을 수 있다
34. As a 개발자, I want 경로 없이 `/dooray-wiki-write`를 호출하면 Home 바로 아래부터 쓸 위치를 고르고 싶다, so that read와 같은 방식으로 시작할 수 있다
35. As a 개발자, I want 탐색 중 "여기에 이어쓰기"를 골라 현재 페이지에 이어쓰고 싶다, so that 더 내려가지 않고 그 자리에서 쓸 수 있다
36. As a 개발자, I want 탐색 중 "하위에 새 페이지"를 골라 제목을 입력해 새 페이지를 만들고 싶다, so that 원하는 위치에 새 문서를 시작할 수 있다
37. As a 개발자, I want "하위에 새 페이지"로 입력한 제목이 이미 있으면 그 페이지에 이어쓰기로 처리되기를 원한다, so that 경로 지정이든 탐색이든 같은 규칙이 적용된다
38. As a 개발자, I want 경로 중간 페이지가 없으면 아무것도 만들지 않고 오류로 끝나기를 원한다, so that 오타 하나로 엉뚱한 페이지 체인이 생기지 않는다
39. As a 개발자, I want 쓰기가 끝나면 "생성 완료" 또는 "이어쓰기 완료"와 대상 경로가 표시되기를 원한다, so that 결과를 바로 확인할 수 있다
40. As a 개발자, I want 위키 페이지 웹 주소를 함께 보고 싶다(주소 형식이 확인된 경우), so that 브라우저에서 바로 열 수 있다
41. As a 개발자, I want 위키가 `Config.md`의 `REPOSITORY`로 자동 선택되기를 원한다, so that 위키 ID를 따로 찾거나 설정하지 않아도 된다
42. As a 개발자, I want 위키 API 오류(권한, 네트워크, 시간 초과)가 성공처럼 보이지 않고 원인과 함께 표시되기를 원한다, so that 실패를 놓치지 않는다
43. As a Codex 사용자, I want `$dooray-wiki-list`, `$dooray-wiki-read`, `$dooray-wiki-write`가 Claude Code와 같은 방식으로 동작하기를 원한다, so that 도구를 바꿔도 사용법이 같다
44. As a 위키 독자(동료), I want 이어쓴 내용이 날짜 섹션으로 구분되기를 원한다, so that 기존 내용과 새로 추가된 내용을 쉽게 구분할 수 있다
45. As a 도구 유지보수자, I want 위키 명령의 동작을 네트워크 없이 테스트로 확인하고 싶다, so that 수정 후 회귀를 Dooray 계정 없이 잡을 수 있다
46. As a 도구 유지보수자, I want 위키 기능이 표준 라이브러리만으로 동작하기를 원한다, so that 기존처럼 `pip install` 없이 폴더 복사만으로 배포할 수 있다

### Out of Scope

- `/dooray-task-to-wiki` (업무 내용을 위키에 맞게 가공해 쓰기) — 후속 작업
- `wiki-write`에서 Claude가 작성 지시를 받아 내용을 쓰거나 다듬는 기능 — 받은 그대로만 올린다
- 위키 첨부파일·이미지의 다운로드와 업로드
- 페이지 덮어쓰기(전체 교체), 삭제, 이동, 제목 변경
- 위키 댓글
- `REPOSITORY` 프로젝트 위키 외의 다른 위키 조회, 접근 가능한 위키 목록 출력
- `wiki-list`의 깊이 제한 옵션
- 기존 `tests/` 실패(현재 `dooray.py`에 없는 `init`·`help`·`body_text` 등) 수정

## SPEC

### Implementation Decisions

**모듈 구성**

- 기존 단일 파일 CLI(`dooray.py`)에 명령 3개(`wiki-list`, `wiki-read`, `wiki-write`)를 추가하고, 알려진 명령 목록과 모듈 도움말(docstring)에 반영한다. 표준 라이브러리만 사용한다.
- `Dooray` 클래스에 위키 메서드를 추가한다. 모든 HTTP 호출은 기존 `_api`를 거친다. 오류 처리(HTTP 오류·접속 실패·시간 초과 시 메시지를 출력하고 종료)도 기존과 같다.
  - 위키 ID 해석: 위키 목록을 `totalCount` 기준으로 페이지네이션하고, `project.id`가 기존 projectId(`pid`)와 같은 위키를 고른다. 없으면 종료한다. 기존 `_project_id`와 같은 패턴이다. 위키 이름(예: `Snoopy`)과 Home pageId도 함께 보관한다.
  - 하위 페이지 목록: `parentPageId`로 한 깊이를 조회하고 `totalCount`까지 페이지네이션한다.
  - 페이지 상세: 본문(`body.content`)과 `version`.
  - 페이지 생성·본문 수정: 쓰기 API(아래 미검증 계약).
- Skill 어댑터: Claude Code와 Codex 각각에 `dooray-wiki-list`, `dooray-wiki-read`, `dooray-wiki-write`를 추가한다. Codex에는 openai 메타를 포함한다.
  - Claude 쪽은 기존과 같이 `disable-model-invocation: true`로 두고, 허용 도구는 `dooray wiki-*` 실행으로 한정한다.
  - model/effort: list는 sonnet/low(단순 조회), read는 sonnet/medium(대화형, `status-change`와 같은 등급), write는 sonnet/medium(`reply`와 같은 등급).
  - Codex 쪽은 `allow_implicit_invocation: false`로 둔다.
- 문서 갱신
  - DOORAY.md: Skill 선택 표, CLI 대응표, 쓰기 규칙.
  - README: 명령 표, Skill 표, 명령 개수, "위키를 의도적으로 뺐다"는 서술.
  - 초기화 Skill(Claude·Codex)의 PowerShell·bash 단축 명령 블록에 `dooray-wiki-list`, `dooray-wiki-read`, `dooray-wiki-write`를 추가한다.

**API 계약**

실측으로 확인한 것(읽기 전용 GET, 2026-10-27):

- `GET /wiki/v1/wikis?page&size` → `result[]`: `id, name, type, scope, project.id, home.pageId` / `totalCount`
- `GET /wiki/v1/wikis/{wikiId}/pages` (parentPageId 없음) → 최상위 `Home` 1개
- `GET /wiki/v1/wikis/{wikiId}/pages?parentPageId={id}` → 바로 아래 한 깊이. `result[]`: `id, subject, version, creator, root, wikiId` / `totalCount`
- `GET /wiki/v1/wikis/{wikiId}/pages/{pageId}` → `subject, body{mimeType: text/x-markdown, content}, version, files, images, referrers, createdAt, updatedAt`

미검증(구현 단계에서 사용자 승인 후 실제 호출 또는 공식 문서로 확정):

- 페이지 생성: `POST /wiki/v1/wikis/{wikiId}/pages`에 `parentPageId, subject, body{mimeType: text/x-markdown, content}`(비공식 클라이언트 근거)
- 본문 수정: PUT 계열 엔드포인트와 요청 형식, `version` 필요 여부
- 위키 페이지 웹 주소 형식(`TENANT` 기반)

**경로 해석 (list·read·write 공통)**

1. 인자 문자열을 `>`로 나누고 각 조각의 앞뒤 공백을 제거한다.
2. 마지막 조각이 비어 있으면(끝이 `>`) 탐색 모드 표시로 보고 제거한다. 인자가 없으면 경로는 비어 있고 탐색 모드이다.
3. 첫 조각이 위키 이름과 같으면 제거한다(`Snoopy >` 접두어 허용). 한계: Home 바로 아래에 위키 이름과 같은 제목의 페이지가 있으면 그 페이지를 가리킬 수 없다. 실제로 생기면 그때 보완한다.
4. 기준점은 Home이다. 빈 경로는 Home을 뜻하며, 경로 조각은 Home 아래부터 차례로 하위 목록에서 제목을 찾는다.
5. 제목 비교는 앞뒤 공백을 제거한 뒤 완전 일치로 한다. 상태명 해석처럼 대소문자·공백을 느슨하게 비교하지 않는다. 쓰기가 엉뚱한 페이지로 가는 것을 막기 위해서다.
6. 어느 단계에서 일치하는 페이지가 없으면, 그 단계의 하위 제목 목록을 보여주고 종료한다. 기존 상태명·첨부파일 미일치 메시지와 같은 관례다.
7. 일치하는 페이지가 둘 이상이면 후보를 보여주고 종료한다.

**`wiki-list [경로]`**

- 시작 페이지(기본 Home) 아래를 전위 순회(부모 다음에 그 자식들)하며 모든 페이지를 출력한다. 중간 페이지도 포함한다. 시작 페이지 자신은 출력하지 않는다.
- 각 줄은 `N. <위키이름> > <제목> > … > <제목>` 형식이다.
- 하위 목록 조회는 페이지마다 1회 필요하므로 같은 깊이의 형제 하위 트리를 병렬로 조회한다(기존 `member_names`의 ThreadPoolExecutor 관례). 출력 순서는 API가 돌려준 형제 순서를 유지한다.
- 시작 경로 아래에 페이지가 없으면 한 줄 안내 메시지를 출력한다. 기존 `list`가 빈 결과를 안내하는 관례를 따른 가정이다.

**`wiki-read [경로][>]`**

- 읽기 모드(끝 `>` 없음, 경로 있음): 첫 줄에 전체 경로 머리줄을 출력하고 빈 줄 뒤에 본문을 그대로 출력한다. 본문이 비어 있어도 별도 표시를 하지 않는다. 주소 형식이 확인되면 마지막에 페이지 주소를 출력한다.
- 탐색 모드(끝 `>` 또는 인자 없음): 머리줄 다음에 바로 아래 하위 페이지를 `N. 제목` 번호 목록으로 출력한다. 하위가 없으면 읽기 모드와 같이 본문을 출력한다.
- Skill 흐름
  1. CLI 탐색 결과를 번호 목록으로 사용자에게 보여주고 "여기 읽기" 선택지를 덧붙인다.
  2. 사용자가 번호나 제목으로 고르면 경로를 늘려 다시 탐색 모드로 호출한다. "여기 읽기"를 고르면 읽기 모드로 호출한다. 하위가 없어 본문이 나오면 종료한다.
  3. 최종 본문은 원본 그대로 보여준다(DOORAY.md의 조회 규칙).
- 선택 UI(AskUserQuestion)는 쓰지 않는다. 번호 목록 텍스트로 제시해 하위 개수 제한을 없애고 Claude/Codex 동작을 같게 한다.

**`wiki-write <경로> (<내용> | --file <파일>) [--dry-run]`**

- 경로의 마지막 조각을 대상 제목으로, 그 앞을 부모 경로로 본다. 부모 경로는 반드시 존재해야 하며, 없으면 경로 해석 6·7번 규칙으로 종료한다. 끝 `>`나 빈 경로처럼 대상 제목이 없으면 오류로 종료한다(탐색은 Skill이 read의 탐색 모드로 수행).
- 내용은 기존 `comment`와 같이 인자 또는 `--file`(UTF-8)로 받는다. `@한글이름` 치환은 기존 `apply_mentions`를 재사용한다(위키에서 같은 멘션 형식이 동작하는지는 미검증).
- 부모 아래에 대상 제목이 있으면 이어쓰기, 없으면 생성이다.
  - 이어쓰기: 기존 본문을 조회해 `기존 본문 + 빈 줄 + "## YYYY-MM-DD"(실행한 날의 로컬 날짜) + 빈 줄 + 새 내용`으로 본문 전체를 수정 요청한다. 같은 날이어도 매번 헤더를 붙인다.
  - 생성: 부모 아래에 대상 제목으로 페이지를 만들고 본문은 새 내용 그대로 둔다(헤더 없음).
- 이어쓰기 API가 따로 없으면 조회와 수정 사이에 다른 사람의 편집이 사라질 수 있다. 수정 요청이 `version`을 받으면 함께 보내 충돌을 감지하고, 받지 않으면 이 한계를 코드 주석으로 명시한다.
- `--dry-run`은 경로 해석과 생성/이어쓰기 판단까지만 하고, `생성 예정: <전체 경로>` 또는 `이어쓰기 예정: <전체 경로>`를 출력한다. 쓰기 요청은 보내지 않는다. Skill의 확인 화면이 실제 쓰기와 같은 판단 코드를 쓰게 하려는 것이다(AI 제안).
- 성공하면 `생성 완료: <전체 경로>` 또는 `이어쓰기 완료: <전체 경로>`를 출력하고, 주소 형식이 확인되면 주소도 출력한다. 작성자는 API 토큰 소유자다.
- Skill 흐름
  1. 경로가 없거나 끝이 `>`이면 read와 같은 탐색을 한다. 끝 선택지는 "여기에 이어쓰기"(현재 경로가 대상)와 "하위에 새 페이지"(제목을 입력받아 현재 경로 + 제목이 대상)이다.
  2. 사용자가 준 내용을 다듬지 않고 스크래치패드 임시 파일에 그대로 쓴다. 로컬 `.md` 파일을 받았으면 그 파일을 그대로 쓴다.
  3. `--dry-run`으로 생성/이어쓰기를 판단하고, 판단 결과·전체 경로·내용을 보여준 뒤 명시적 확인을 받는다.
  4. 확인되면 실제 쓰기를 실행하고 결과 메시지를 전달한다. 거절되면 아무것도 쓰지 않는다. 임시 파일은 제거한다.
- 제목에 공백이 있어 Skill 인자에서 경로와 내용의 경계가 모호할 수 있다. Skill은 해석한 경로를 확인 화면에 보여주는 것으로 대응하고, CLI는 경로를 따옴표로 감싸 하나의 인자로 받는다.

### Testing Decisions

- **좋은 테스트의 기준:** 외부 동작만 검증한다. 입력은 CLI 인자, 출력은 stdout 줄, 종료 메시지, fake가 기록한 쓰기 요청(대상 부모·제목·본문)이다. 내부 헬퍼 함수의 호출 여부나 호출 순서는 검증하지 않는다.
- **seam은 하나다:** CLI 진입점(`main`)을 인자와 함께 실행하고, 모든 HTTP가 지나가는 `Dooray._api`만 메모리 위키 트리 fake로 교체한다.
  - fake가 응답하는 것: 프로젝트 목록, 위키 목록, 하위 페이지 목록(페이지네이션 포함), 페이지 상세, 페이지 생성·수정, 멘션용 멤버 조회.
  - 쓰기 요청을 기록한다.
  - 테스트가 Config.md(토큰 포함, git 제외)에 의존하지 않도록 설정 로드도 고정값으로 대체한다.
- **대상 모듈:** 위키 명령 3개와 경로 해석. Skill의 대화형 부분(번호 선택, "여기 읽기"/"여기에 이어쓰기"/"하위에 새 페이지", 쓰기 확인)은 자동 테스트하지 않고 Claude Code와 Codex에서 수동으로 확인한다.
- **테스트 사례**
  - list: 전위 순회 순서와 번호, 중간 페이지 포함, 시작 경로 하위만 출력, `Snoopy >` 접두어 허용, `totalCount`가 한 페이지보다 큰 하위 목록의 페이지네이션, 없는 시작 경로는 그 단계의 후보와 함께 종료
  - read: 경로 → 머리줄 + 본문, 빈 본문에 표시 없음, `Visualizer>`와 `Visualizer >`가 같은 하위 목록, 인자 없음 → Home 하위 목록, 하위 없는 페이지 + `>` → 본문, 같은 이름 형제 → 후보와 함께 종료, `>` 앞뒤 공백 무시
  - write
    - 기존 페이지 → 수정 요청 본문이 "기존 + `## <오늘 날짜>` + 새 내용"
    - 없는 대상 → 부모 아래 생성 요청, 헤더 없음
    - 중간 페이지 없음 → 쓰기 요청 0건과 오류
    - 같은 이름 형제 → 쓰기 요청 0건과 오류
    - `--dry-run` → 쓰기 요청 0건과 `생성 예정`/`이어쓰기 예정`
    - `--file` 입력
    - `@이름` 치환 결과가 본문에 반영
    - 끝 `>`나 빈 경로 → 오류
  - 오류: `_api`가 종료(SystemExit)하면 성공 메시지가 출력되지 않는다
- **기존 사례:** `tests/`의 기존 unittest가 importlib로 `dooray.py`를 로드해 호출한다. 로드 방식과 unittest(표준 라이브러리)는 이를 따른다. HTTP fake로 CLI 전체를 실행하는 테스트는 기존 사례가 없어 새로 도입한다.
- **실제 API 검증:** 생성·수정 요청 형식, `version`, 위키 멘션 형식, 페이지 주소 형식은 구현 단계에서 사용자가 승인한 위치에 실제 호출로 한 번 확인한다. 자동 테스트에는 포함하지 않는다.

## Further Notes

- **기존 테스트 실패(범위 밖):** 2026-10-27 기준 `tests/`는 13개 중 12개가 실패한다. 현재 `dooray.py`에 `body_text`·`html_to_text`·`install_launcher`·`init`·`help`가 없고, README와 초기화 Skill이 안내하는 `dooray.py init`도 동작하지 않는다. `dooray.py`가 테스트·문서보다 이전 버전일 가능성이 있다. 위키 테스트는 이와 독립적으로 실행되게 하고, 이 불일치는 별도로 결정해야 한다. 단축 명령 갱신이 init 동작에 의존한다는 점도 함께 고려해야 한다.
- **공식 문서 미열람:** API 계약은 실측 GET과 비공식 클라이언트에 근거한다. 공식 `서비스 API` 문서 본문으로 쓰기 계약을 교차 확인하는 것이 좋다.
- **같은 제목의 형제 페이지:** Dooray가 허용하는지 확인하지 못했다. 허용하지 않으면 후보 출력 분기는 실제로 쓰이지 않지만, 유지 비용이 작아 둔다.
- **후속 `/dooray-task-to-wiki <업무번호> <경로>`:** `dooray-report` 공통 절차의 자료 확인 단계(`full`·`download`)를 재사용해 위키용 내용을 만들고, 업로드는 이 SPEC의 `wiki-write`를 쓴다. 가공이 필요하므로 opus급 에이전트형 Skill이 된다.
- **비용 특성:** list와 경로 해석은 경로 깊이 또는 페이지 수만큼 API를 호출한다. 회의록처럼 계속 늘어나는 페이지가 많아져 느려지면 그때 시작 경로 사용을 안내하거나 깊이 제한을 추가한다.

## 2026-10-27 갱신 — 위키 구현 전 dooray.py 합치기 완료

위 Further Notes의 "기존 테스트 실패(범위 밖)" 항목은 이 시점부터 사실과 다르다. 위키 구현 전에 별도 작업으로 `dooray.py`를 합쳤다.

- **합친 출처:** 현재 저장소 코드(인수인계 Snoopy 프로젝트의 `Dooray/dooray.py`와 같음)를 기준으로, DoorayTest의 `DoorayForDev-main_01`(불러오는 단계에서 오류가 나는 사본)에서 의도를 파악해 옮겨 왔다. 옮긴 것은 `init`·`help`·launcher 설치, HTML 본문 변환, `full` 태그 표시, Config.md 줄 끝 주석 처리다.
- **함께 결정한 것**
  - `download`는 첨부·본문·댓글 이미지를 모아 `<파일ID>_<파일명>`으로 저장하는 방식을 유지하고, 번호·`all` 선택을 추가했다. 대상을 생략하면 전체를 받는다.
  - `WORKING`·`COMPLETED` 별칭은 삭제했다.
  - 인수인계 프로젝트의 `test_inline_files.py`는 `tests/`로 옮겨 unittest로 감쌌다. `Dooray/`는 작업 프로젝트로 통째로 복사되므로 개발용 테스트는 두지 않는다.
- **검증:** `python -B -m unittest discover -s tests` 결과 20개 중 19개 통과, 1개는 POSIX 전용이라 건너뜀(기존 13개 포함). 실제 Dooray에서 읽기 전용 명령(`help`·`workflows`·`list`·`full`·`download` 번호 선택)을 확인했다. `dooray init` 실제 실행과 macOS·Linux 확인은 하지 않았다.
- **위키 구현에 주는 영향**
  - 테스트 기존 사례에 `tests/test_download.py`·`tests/test_inline_files.py`가 더해졌다. 로드 방식은 같다(importlib + unittest).
  - 알려진 명령 목록에는 이제 `init`·`help`가 있다. 위키 명령은 그 뒤에 추가한다.
  - 초기화 Skill의 단축 명령 블록 갱신은 이제 실제 `init` 동작 위에서 확인할 수 있다.
  - 위키 테스트를 기존 테스트 실패와 분리할 필요가 없어졌다. 전체 테스트가 통과하는 상태에서 시작한다.

## 2026-10-27 갱신 — 이어쓰기 헤더에 시:분 추가

위 PRD·SPEC의 이어쓰기 헤더 `## YYYY-MM-DD`는 이 시점부터 `## YYYY-MM-DD HH:MM`(실행한 PC의 로컬 시각, 24시간제)으로 바뀐다.

- **결정(사용자):** CLI로 이어쓰기를 써 본 뒤 날짜만 보여서 시·분까지 넣기로 했다. 같은 날 여러 번 이어쓴 섹션을 구분하기 위해서다.
- **그대로인 것:** 이어쓸 때마다 헤더를 붙이는 규칙과 새 페이지에는 헤더를 붙이지 않는 규칙.
- **테스트:** 이어쓰기 테스트는 시계를 `2026-10-27 09:05`로 고정해 `## 2026-10-27 09:05`를 기대값으로 검증한다.
- **함께 바꾼 문서:** CLI 도움말, README, `DOORAY.md`, Claude·Codex `dooray-wiki-write` Skill.
- **이미 위키에 쓴 섹션:** `Snoopy > Visualizer > CLI 쓰기 테스트`의 기존 날짜 헤더는 그대로 남는다.

## 2026-10-27 갱신 — 이어쓰기 헤더 형식을 YY-MM-DD, HH:mm으로

바로 위 섹션의 `## YYYY-MM-DD HH:MM`은 이 시점부터 `## YY-MM-DD, HH:mm`으로 바뀐다(예: `## 26-10-27, 14:05`). 연도는 두 자리, 날짜와 시각 사이에 쉼표와 공백을 둔다. 결정은 사용자가 했다. 테스트 기대값은 `## 26-10-27, 09:05`이고, 함께 바꾼 문서는 `DOORAY.md`와 Claude·Codex `dooray-wiki-write` Skill이다.

## 2026-10-27 갱신 — 위키 페이지 주소 출력

위 SPEC의 "페이지 웹 주소는 형식이 확인되면 출력"이 이 시점에 확정됐다.

- **형식:** `https://{TENANT}.dooray.com/wiki/{위키ID}/{페이지ID}`. API 상세 응답에는 주소 필드가 없어 만들어 쓴다. 후보 두 개(`/wiki/{위키ID}/{페이지ID}`, `/wiki/{페이지ID}`) 중 앞의 것이 브라우저에서 열리는 것을 사용자가 확인했다.
- **출력 위치:** `wiki-read` 읽기 결과와 `wiki-write`의 `생성 완료`·`이어쓰기 완료` 아래에 `위키 주소: …` 줄을 붙인다. 업무 명령의 `이력 주소`와 같은 형식(`fmt_link`를 라벨만 바꿔 재사용)이다. 탐색 목록과 `--dry-run`에는 붙이지 않는다.
- **TENANT가 없을 때:** `(위키 주소 확인 불가 — Dooray/Config.md 에 TENANT= 설정 없음)`을 출력한다.
- **미검증:** 생성 응답의 `result.id`로 새 페이지 주소를 만든다. 실제 생성 응답에 id가 오는지는 다시 생성해 보지 않아 확인하지 않았다. 없으면 주소 줄을 생략한다.

## 2026-10-27 갱신 — 위키 댓글·파일 읽기와 wiki-download 추가

위 PRD Out of Scope의 "위키 첨부파일·이미지의 다운로드"와 "위키 댓글"은 이 시점부터 범위 안이다.

- **계기:** 사용자가 CLI로 `wiki-read`를 써 보고 댓글(히스토리)과 파일을 볼 수 없다고 지적했다. `dooray-read-full`과 같은 동작을 요청했다. 실측(21페이지)에서 `주간 미팅 노트`는 본문이 0자이고 댓글이 3개였다. 즉 내용이 댓글에만 있는 페이지가 있다. 댓글은 3페이지, 첨부·본문 이미지는 7페이지에 있었다.
- **결정(사용자)**
  - 명령은 하나로 둔다. `wiki-read`가 본문과 함께 댓글과 파일 목록을 항상 보여준다. `wiki-read-full`은 만들지 않는다.
  - `wiki-download "경로" [파일명|번호|all]`을 추가한다. 생략하면 전체를 받는다.
- **API(실측, 읽기 전용)**
  - 댓글: `GET /wiki/v1/wikis/{위키ID}/pages/{페이지ID}/comments?page&size` → `result[]`: `id, body{content, mimeType}, createdAt, modifiedAt, creator{type, member{organizationMemberId, name}}, page` / `totalCount`. 기본 순서가 최신순이라 출력 전에 `createdAt` 오름차순으로 정렬한다. 작성자 이름이 응답에 있어 멤버 조회가 필요 없다.
  - 파일 목록: 페이지 상세의 `files`(첨부)와 `images`(본문 이미지). 항목은 `id, attachFileId, name, size`. 본문에는 이미지 참조가 없다.
  - 다운로드: `GET /wiki/v1/wikis/{위키ID}/pages/{페이지ID}/files/{id}?media=raw` → 원본 바이트(첨부 xlsx 9,765,088B, 이미지 png 1,226,845B 일치). `attachFileId`로는 404다.
- **출력:** `wiki-read` 읽기 결과는 머리줄, 본문, `--- 댓글 ---`(시간순, 업무 댓글과 같은 형식), `--- 파일 ---`(번호·ID·이름·출처 `첨부`/`본문 이미지`), `위키 주소` 순이다. 댓글이나 파일이 없으면 그 구역을 빼고, 탐색 목록에는 붙이지 않는다.
- **다운로드 번호와 저장 위치:** 번호는 첨부 → 본문 이미지 순서로 `wiki-read` 파일 목록 번호와 같다. 선택 규칙은 업무 `download`와 같다(생략·`all` 전체, 번호 하나, 파일명은 같은 이름 전부). 저장 위치는 `Dooray/report/wiki-<페이지ID>/download/<파일ID>_<파일명>`이다. 기존 `.gitignore` 규칙 `Dooray/report/*/download/`에 걸린다.
- **테스트 seam:** 바이너리 다운로드는 `_api`(JSON)가 아닌 별도 경로를 지나므로, 다운로드 저수준 함수와 저장 기준 폴더도 fake·임시 폴더로 바꾼다.
- **구현 중 조정 — 출처 라벨:** 실측에서 `주간 미팅 노트`는 본문이 0자인데 `images`가 2개였다. 이미지가 본문이 아닌 댓글에 있을 수 있으므로, 위의 출처 라벨 `본문 이미지`를 `이미지`로 바꿨다(출력·문서·테스트 모두).
- **검증(실측):** `주간 미팅 노트`에서 댓글 3개가 시간순으로, 이미지 2개가 파일 목록에 나왔다. `AI BSM > GNSS 측위 시험`에서는 파일 5개(첨부 2 → 이미지 3)가 나왔고, `wiki-download … 5`가 `Dooray/report/wiki-4402307302953357775/download/4403033385216950156_Inline-image-2026-08-20 09.41.21.442.png`(203,949B)를 저장했다.

## 2026-10-27 갱신 — 저장 폴더를 task·wiki로 분리

위 섹션의 위키 저장 위치 `Dooray/report/wiki-<페이지ID>/download/`와 업무 저장 위치 `Dooray/report/<업무번호>/download/`는 이 시점부터 아래로 바뀐다.

- **결정(사용자)**
  - 업무: 기존 `report` 구조를 그대로 `task/` 아래로 옮긴다 → `Dooray/task/report/<업무번호>/REPORT.md`, `Dooray/task/report/<업무번호>/download/<파일ID>_<파일명>`.
  - 위키: 페이지 ID가 아니라 제목 경로로 폴더를 만든다 → `Dooray/wiki/<위키이름>/<제목>/.../download/<파일ID>_<파일명>`. 폴더 이름에 못 쓰는 문자는 `_`로 바꾸고(`HD Map > SUMO Network` → `HD Map _ SUMO Network`), 하위 페이지 폴더와 섞이지 않게 `download/`를 둔다.
  - git 제외는 받은 파일만 한다 → `Dooray/task/report/*/download/`, `Dooray/wiki/**/download/`. 옛 규칙 `Dooray/report/*/download/`는 아직 옮기지 않은 프로젝트를 위해 남긴다.
- **구현 메모:** 위키 폴더는 사용자가 입력한 경로 조각이 아니라 실제로 찾은 페이지의 제목 목록으로 만든다(`wiki_walk`가 페이지에 `path`를 담는다). 그래야 제목에 `>`가 있는 페이지가 중첩 경로 폴더로 잘못 저장되지 않는다.
- **알려진 한계(사용자 동의):** Dooray에서 제목을 바꾸면 새 폴더가 생긴다. 트리가 매우 깊으면 Windows 경로 260자 제한에 걸릴 수 있다. 제목이 정확히 `download`인 페이지는 다운로드 폴더와 이름이 겹친다.
- **기존 사용 프로젝트:** README에 업데이트 안내를 넣었다. `Dooray/report/`의 업무 폴더들을 `Dooray/task/report/`로 옮겨야 `dooray-report`가 기존 `REPORT.md`를 찾는다(인수인계 Snoopy 프로젝트에는 업무 폴더 56개가 있다).
- **함께 바꾼 것:** `.gitignore`, `DOORAY.md`, README(설치 구조·명령 표·보고서 경로), `dooray-report` Skill 권한(`Write/Edit(Dooray/task/report/**)`), `report-workflow.md`, CLI 도움말, 테스트(위키 다운로드 폴더 기대값, 제목에 `>`가 있는 페이지의 폴더 이름).
- **검증:** 전체 오프라인 테스트 통과. 실측에서 `dooray download 124 1`은 `Dooray/task/report/124/download/`에 저장했고, `dooray wiki-download "AI BSM > SUMO > HD Map > SUMO Network"`는 `Dooray/wiki/Snoopy/AI BSM/SUMO/HD Map _ SUMO Network/download/`에 3개를 저장했다. 검증 때 옛 위치에 받았던 파일 6개는 새 위치로 옮겼다.
