# Dooray 위키 읽기·쓰기 Skill (wiki-list / wiki-read / wiki-write)

## 근거 자료

- `README.md`, `AGENTS.md`, `CLAUDE.md`, `DOORAY.md` — 도구 구조와 작업 규칙. README에는 "위키·메일·메신저 같은 기획/PM성 기능은 의도적으로 뺐다", "업무 명령 9개"라는 서술이 있다.
- `.claude/skills/dooray-*`, `.agents/skills/dooray-*` — 기존 Skill 패턴. 단순 조회(`read`·`link`·`status`·`list`: CLI 한 줄 + 원본 출력, sonnet/low), 받은 그대로 쓰기(`reply`: 임시 파일 + `--file`, sonnet/medium), 대화형·분석형(`status-change`: 목록 제시 후 선택, sonnet/medium / `report`: opus/high).
- `Dooray/dooray.py` — 모든 HTTP 호출이 `Dooray._api`를 지난다. `_project_id`는 `totalCount` 기준 페이지네이션, `apply_mentions`는 `@한글이름`을 멘션 markdown으로 치환, `add_comment`는 `text/x-markdown` 본문을 보낸다.
- `tests/` — importlib로 `dooray.py`를 로드해 순수 함수를 직접 호출하는 unittest. API를 부르는 명령의 테스트와 HTTP fake는 없다. 2026-10-27 실행 결과 13개 중 12개 실패(`body_text`·`html_to_text`·`install_launcher` 등이 현재 `dooray.py`에 없음).
- Dooray 공식 가이드(helpdesk.dooray.com) — 위키 API 설명은 `🔌 Dooray! API > 서비스 API` 페이지(ID 2939987647631384419)에 있다. 페이지가 JS로 렌더링돼 본문은 읽지 못했다. 가이드 내비게이션 트리의 제목 804개 중 `/` 포함 43개, `>` 포함 1개(`<iframe> 태그…`).
- 커뮤니티 `dooray-mcp`의 `wiki.ts`(비공식) — base `/wiki/v1`, `/wikis` 페이지네이션, `/wikis/{wikiId}/pages`는 한 깊이만 조회하며 `parentPageId`는 선택, POST로 페이지 생성.
- 실측(읽기 전용 GET, 2026-10-27, 사용자 토큰)
  - `GET /wiki/v1/wikis` — 42개. 항목 필드 `id, name, type, scope, project.id, home.pageId`. `project.id`가 REPOSITORY의 projectId와 일치하는 위키는 Snoopy 1개.
  - `GET /wiki/v1/wikis/{wikiId}/pages`(parentPageId 없음) — 최상위 `Home` 1개만.
  - `GET …/pages?parentPageId=<Home>` — 한 깊이 5개(주간 미팅 노트, 회의록, AI BSM, Visualizer, QULINK-OBU). 응답에 `header, result, totalCount`. 항목 필드 `id, subject, version, creator, root, wikiId`.
  - `GET …/pages/{pageId}` — 필드 `body(mimeType=text/x-markdown, content), version, files, images, referrers, subject, createdAt, updatedAt…`.
  - Home 하위 5개 페이지는 본문 0자. 회의록 하위 트리: `회의록 > LG ICON25 프로젝트 > 260402_…` 2개, `회의록 > ublox 한국지사 X20K 제공관련 논의`.
- 가정·해석
  - 페이지 생성(POST)·수정(PUT) 계약, `version`의 용도, 위키 본문에서 멘션 형식 동작 여부, 위키 페이지 웹 주소 형식은 확인하지 않았다.
  - 이어쓰기 전용 API가 없다면 GET(기존 본문) + PUT(전체 본문)으로 구현해야 한다고 가정한다.

## 결정사항

- 위키 Skill은 `dooray-wiki-list`, `dooray-wiki-read`, `dooray-wiki-write`를 먼저 만들고 `dooray-task-to-wiki`는 후속으로 미룬다 — task-to-wiki는 wiki-write의 CLI 위에 올라가므로.
- 쓰기를 받은 그대로 올리는 `wiki-write`와 업무를 가공해 쓰는 `task-to-wiki`로 나눈다 — 기존 `reply`/`report` 구분과 같고, Skill별 model/effort를 다르게 둘 수 있으므로.
- 위키는 REPOSITORY 프로젝트와 연결된 위키(`project.id` 일치)로 자동 선택한다 — 실측으로 1:1 대응 확인, Config.md 추가 설정 불필요.
- 경로 구분자는 `>`, 각 조각의 앞뒤 공백은 무시 — 실제 제목에 `/`가 흔하고(43/804) `>`는 드묾(1/804).
- 경로는 Home 아래부터 시작한다(Home 생략). 입력 맨 앞의 `Snoopy >`(위키 이름)는 있어도 없어도 된다 — list 출력 줄을 그대로 복사해 쓰도록.
- 끝에 `>`가 있거나 경로가 없으면 탐색 모드, 그 페이지(또는 Home) 하위부터 번호 목록으로 한 단계씩 선택한다.
- 선택지는 AskUserQuestion이 아니라 번호 목록 텍스트로 제시하고 번호나 이름으로 답을 받는다 — 도구 제한(선택지 2~4개)을 피하고 Claude/Codex 동작을 같게 하려고.
- `wiki-read <경로>`는 본문만 출력한다. "(본문 없음)" 같은 표시는 하지 않는다. 하위가 없는 페이지에 `>`를 붙이면 본문을 보여준다.
- 탐색 중 멈추는 선택지: read는 "여기 읽기", write는 "여기에 이어쓰기" / "하위에 새 페이지(제목 입력)".
- `wiki-write` 규칙은 하나다: 대상 페이지가 있으면 이어쓰기, 없으면 부모 아래 생성 — 셸 `>>`와 같은 동작. 탐색으로 만든 경로도 같은 규칙을 탄다.
- 이어쓰기는 매번 `## YYYY-MM-DD` 날짜 헤더를 붙인다(같은 날 두 번 써도 헤더 하나 더). 새 페이지에는 헤더를 붙이지 않는다.
- 경로 중간 페이지가 없으면 오류로 종료하고, 새로 만드는 것은 마지막 페이지 하나뿐이다. 같은 이름의 형제가 여럿이면 후보를 보여주고 종료한다.
- 쓰기 전에 "생성/이어쓰기", 대상 경로, 내용을 보여주고 사용자 확인 후 실행한다 — DOORAY.md 쓰기 규칙, 오타로 페이지가 생기는 것을 막기 위해.
- `wiki-write`의 내용은 받은 그대로(문구 또는 로컬 `.md` 파일) 올린다. Claude가 작성·가공하지 않는다.
- 첨부파일·이미지는 1차 범위에서 제외한다.
- `@이름` 멘션 치환을 지원한다(`apply_mentions` 재사용). 사용자 판단: 거의 필요 없겠지만 일단 지원.
- `wiki-list`는 모든 페이지(중간 페이지 포함)를 트리 순서로 `Snoopy > …` 전체 경로 한 줄씩 번호를 붙여 출력한다. 시작 경로를 주면 그 하위만 출력한다.
- 페이지 웹 주소는 형식이 확인되면 read/write 결과에 출력하고, 확인되지 않으면 뺀다(기본값, 이의 없음).
- 테스트 seam은 B안: CLI 진입점을 실행하고 `Dooray._api`만 메모리 위키 트리 fake로 교체한다. Skill의 대화형 부분은 수동 확인.
- 쓰기 API 실호출 검증은 기획 단계가 아니라 구현 단계에서, 사용자 승인 후 진행한다.
- 작업 폴더 slug는 `toSpecWiki`(Dooray 업무번호 없음).

## Q&A

- **Q:** (사용자) Dooray 위키 페이지를 읽고 쓰는 Skill을 추가하려 한다. 업무 내용을 기반으로 위키를 작성하거나 코드·실행 방법·용어 정리를 남기는 목적이다. 이해했나?
  **A:** 위키를 읽고 쓰는 `dooray-*` Skill이며, 쓰기는 업무 기반 작성과 업무와 무관한 정리 두 가지, 읽기는 기존 페이지 참고로 이해했다.

- **Q:** (사용자) 기존 작업을 분석해 보자. `/dooray-wiki-read <경로명>`, `/dooray-wiki-write <내용 혹은 업무 이력 번호>` 형식이면 될까?
  **A:** 기존 Skill 구조(단순 조회 / 받은 그대로 쓰기 / 에이전트형)와 수정해야 할 곳(Skill 어댑터 2종, DOORAY.md, KNOWN_CMDS, init 단축 명령, README)을 정리했다. read는 가능하나 위키 API가 ID 기반이라 경로는 단계별 하위 조회로 해석해야 한다(당시 근거는 비공식 코드). write는 쓸 위치가 없고, "내용"이 받은 그대로인지 작성 지시인지 다르고, 덮어쓰기 위험이 있고, 인자가 모호하다. `<경로> <업무번호|작성 지시>` 형식을 제안했다.

- **Q:** (사용자) Dooray API 공식 문서에서 찾아봐야 하지 않나? 그게 가장 신빙성 있을 텐데.
  **A:** 맞다. 공식 위키 API 설명이 있는 페이지 위치(`🔌 Dooray! API > 서비스 API`)는 찾았지만 JS 렌더링이라 본문을 받지 못했고, 크롤러로 위장해 받는 방법은 권한이 막혀 중단했다. 사용자가 본문을 붙여넣거나 Chrome 확장으로 직접 여는 두 가지 방법을 제안했다(회신 없음 — 미해결).

- **Q:** (사용자) write를 둘로 나눠 `/dooray-task-to-wiki <업무번호>`로 업무를 정리하고 `/dooray-wiki-write <경로> <내용>`으로 쓰면 어떤가? 위키는 읽기·쓰기·업무 정리 3개가 된다. 업무 조회·댓글이 가능하니 위키도 가능할 것 같다. Config.md에 API 키를 추가했다. 근거 기반 의견은?
  **A:** Config.md 키는 기존 5개 그대로라 토큰 값을 바꾼 것으로 보고 읽기 전용 GET으로 실측했다. 같은 토큰으로 위키 API가 동작하고, `project.id`로 Snoopy 위키를 자동 선택할 수 있고, 페이지는 Home 아래 한 깊이씩 조회되며, 본문은 `text/x-markdown`이다. 분리에 찬성한다. 근거: `reply`/`report` 구분과 같고, model/effort가 Skill마다 하나라 합치면 비용 또는 품질을 손해 보고, 인자 모호성이 사라진다. 보완점으로 task-to-wiki도 경로가 필요하고, wiki-write는 받은 그대로(+ `.md` 파일 입력)를 권하고, 같은 경로에 페이지가 있을 때의 동작을 정해야 한다고 했다. 쓰기 테스트 위치(`Dooray-Test001` 등)를 물었다.

- **Q:** (사용자) `/dooray-wiki-read`에 경로가 없으면 선택안을 줘서 깊이 들어가게 하자. Snoopy에서는 주간 미팅 노트, 회의록, AI BSM, Visualizer, QULINK-OBU가 첫 선택안이다. 끝까지 가면 읽을 수 있도록 하자. task-to-wiki는 위키에 맞게 내용을 가공할 것이고, 그 전에 read·write를 먼저 진행하자. 같은 경로에 이미 있으면 이어쓰기로 하자. 어떤가?
  **A:** 모두 찬성한다. 실측상 최상위는 Home 하나이고 첫 깊이가 말한 5개와 일치하며, 중간 페이지 본문이 0자라 끝까지 내려가 읽는 방식이 구조와 맞는다. `status-change`와 같은 패턴이다. 설계 제약: 선택 UI는 질문당 선택지 4개(Home 하위가 이미 5개), 최소 2개(하위 1개면 바로 진입 제안), 구분자는 `>` 권장, `totalCount`가 있으니 페이지네이션, 빈 본문 처리. read/write 우선 순서는 report가 full/download CLI에 의존하는 것과 같은 구조라 맞다. 이어쓰기는 덮어쓰기보다 안전하고 CLAUDE.md의 날짜 섹션 이력 보존과 일관되지만, 이어쓰기 API가 없으면 GET+PUT 사이에 다른 사람의 수정이 사라질 수 있고 `version` 필드 용도 확인이 필요하다. 경로 중간 페이지가 없으면 오류로 종료하자고 제안했다.

- **Q:** (사용자) 선택지 4개 제약은 어디에 있나? 더 보여주면 안 되나? 더 들어가지 않으려면 "여기에 작성" 선택지가 있어야 한다. "(본문 없음)" 같은 건 지금 필요 없다. `/dooray-wiki-read Visualizer`는 Visualizer 내용을 보여주고, `Visualizer>` 또는 `Visualizer >`처럼 끝에 `>`가 있으면 Visualizer 하위부터 탐색한다. 지금은 테스트 단계가 아니라 기획 단계다.
  **A:** 제약은 Claude Code `AskUserQuestion` 도구 정의(질문당 선택지 2~4개 + 자동 "Other")이고 기존 `status-change` Skill에도 적혀 있다. 번호 목록 텍스트를 권했다(하위가 계속 늘어나고, 고정 선택지가 칸을 차지하며, Claude/Codex 동작이 같아짐). 중간에 멈추는 경우는 실측상 주로 쓰기이므로 탐색을 read/write가 공유하고 끝 선택지만 read는 "여기 읽기", write는 "여기에 작성"으로 하자고 제안했다. "여기에 작성"이 (a) 이어쓰기인지 (b) 하위 새 페이지인지 물었다. 경로·제목 머리줄을 출력하면 빈 본문 표시가 필요 없다. 끝 `>` 규칙은 셸 `ls dir/` 관례와 같고 `>`가 제목에 드물다는 근거로 찬성했다. 인자가 없으면 Home 하위부터 탐색, 하위 없는 페이지에 `>`면 본문 표시를 제안했다. 테스트 질문은 철회했다.

- **Q:** (사용자) 번호 목록으로 하자. 여기에 작성할지 새 페이지에 작성할지를 보자. 결국 이어쓰기·새로 쓰기가 된다. write도 read와 같은 방식으로: `/dooray-wiki-write Visualizer>test`면 test가 있으면 이어쓰기, 없으면 생성 후 쓰기 아닌가?
  **A:** 동의한다. 탐색은 경로를 만드는 과정이고 쓰기 규칙은 "있으면 이어쓰기, 없으면 생성" 하나다(셸 `>>`). CLI는 `wiki-write "<경로>" --file` 하나로 충분하다. 확인 화면에 생성/이어쓰기를 표시해 `Visualizer>tset` 같은 오타를 막는다. 중간 페이지가 없으면 오류, 같은 이름의 형제가 여럿이면 후보를 보여주고 종료한다(Dooray가 같은 이름을 허용하는지는 미확인). 제목에 공백이 있어 경로와 내용 경계가 모호하므로 Skill은 해석한 경로를 확인 화면에 보여주고 CLI는 따옴표로 해결한다. 이어쓰기 구분 방식(날짜 헤더/구분 없음)을 물었다.

- **Q:** (사용자) 날짜 헤더를 붙여 이어쓰기로 하자. `/dooray-wiki-list`도 만들어 지금 위키의 목록이 나오게 하자. 어떤가?
  **A:** 날짜 헤더를 확정했다. 나열 대상은 (a) 접근 가능한 위키 42개가 아니라 (b) Snoopy 페이지 전체 트리를 권했다(위키는 REPOSITORY로 자동 선택되므로). 탐색은 한 단계씩이고 list는 한 번에 보여주므로 겹치지 않는다. read/write에 복사해 넣을 수 있게 전체 경로 형태 출력을 권했다. 하위 조회가 한 깊이씩이라 API 호출 수가 페이지 수만큼 늘어나므로 병렬 호출하고, 시작 경로를 선택 인자로 받자고 제안했다. 깊이 제한은 필요할 때 추가한다.

- **Q:** (사용자) (b)로 하자. 전체 경로 형태로 출력. 또 질문이 있나?
  **A:** 결정이 필요한 세 가지를 물었다. 1) wiki-write 내용을 받은 그대로 올릴지 / Claude가 작성할지 / 둘 다인지, 2) 위키 첨부·이미지를 다룰지(제외 권장), 3) `@이름` 멘션 치환을 할지. 기본값: 이어쓸 때마다 `## YYYY-MM-DD` 헤더, 새 페이지에는 헤더 없음, `wiki-read <경로>`는 본문만, Claude·Codex 양쪽 Skill과 DOORAY.md·README·init 단축 명령 갱신.

- **Q:** (사용자) 1은 일단 그대로 작성, 2는 그래(제외), 3은 거의 필요 없을 것 같지만 일단 지원하자. 또 질문이 있나?
  **A:** 결정할 질문은 더 없다. 페이지 웹 주소는 형식이 확인되면 출력하고 아니면 빼는 것을 기본값으로 하고, 확정 기획을 요약했다. 쓰기 API(POST/PUT·`version`), 위키 멘션, 주소 형식은 구현 때 실제 호출로 확인하며 그때 승인을 받는다.

- **Q:** (사용자) `/dooray-wiki-list`는 전체 경로를 보여주고, `/dooray-wiki-list 회의록`처럼 상위 경로를 지정하면 그 아래 것만 보여준다. 예: `1. Snoopy > 회의록 > U…`, `2. Snoopy > LG I… > 260…`. 이렇게 이해했나?
  **A:** 맞다. 다만 실측상 `LG ICON25 프로젝트`는 회의록 하위라서 2·3번은 `Snoopy > 회의록 > LG ICON25 프로젝트 > 260402_…`이 된다. 중간 페이지(`… > LG ICON25 프로젝트`)를 따로 한 줄로 넣을지 물었고(넣기 권장), 입력에서 `Snoopy >` 접두어는 있어도 없어도 되게 하는 것을 기본값으로 했다.

- **Q:** (사용자) 중간 페이지도 포함하자.
  **A:** 확정했다. 남은 질문 없음.

- **Q:** (에이전트, /to-spec seam 확인) CLI 진입점을 실행하고 `Dooray._api`만 메모리 위키 트리 fake로 교체하며, Skill 대화형 부분은 수동 확인하려 한다. 맞나?
  **A:** (사용자) 지금까지는 어떻게 되어 있었나? → (에이전트) 기존 테스트는 순수 함수를 직접 호출하고 API 명령 테스트와 HTTP fake는 없으며, 현재 12/13이 실패한다. A안(순수 함수만 분리해 테스트, 기존 방식)과 B안(CLI + `_api` fake, 트리 탐색·생성/이어쓰기 판단까지 검증)을 제시하고 B를 권했다. → (사용자) B로 하자.

- **Q:** (에이전트) 작업 폴더 이름에 쓸 Dooray 업무번호가 있나?
  **A:** (사용자) 왜 필요한가? → (에이전트) `/to-spec` 규칙상 `docs/agents/plan/<날짜>-<업무번호>/` 폴더 이름을 정하는 용도이고, 업무가 없으면 주제 slug를 쓴다. → (사용자) 폴더명은 `toSpecWiki`로 하자.

## 미해결 질문

- 공식 API 문서(서비스 API 페이지) 본문을 아직 읽지 못했다. 본문 붙여넣기 / Chrome 확장 열람 제안에 회신이 없다.
- 페이지 생성(POST)·수정(PUT) 요청 형식, `version` 필드 용도(낙관적 잠금 여부), 위키 본문의 멘션 형식 동작, 위키 페이지 웹 주소 형식 — 구현 단계에서 사용자 승인 후 실제 호출로 확인해야 한다.
- Dooray가 같은 부모 아래 같은 제목의 페이지를 허용하는지 확인하지 못했다.
- 기존 `tests/` 12/13 실패(현재 `dooray.py`에 `init`/`help`/`body_text` 등이 없음)는 이번 범위 밖이다. 별도 결정이 필요하다.
