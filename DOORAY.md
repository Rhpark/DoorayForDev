# Dooray 연동 지침

이 문서는 Dooray 관련 요청을 처리할 때만 읽는다. 일반 개발 작업에는 적용하지 않는다.

## 구성

- 공용 CLI: `Dooray/dooray.py`
- 로컬 설정: `Dooray/Config.md`
- 업무 폴더: `Dooray/task/report/<업무번호>/` — `REPORT.md`와 받은 파일(`download/`)
- 위키 폴더: `Dooray/wiki/<위키이름>/<제목>/.../download/` — 위키 트리와 같은 모양
- Claude Code Skill: `.claude/skills/dooray-*`
- Codex Skill: `.agents/skills/dooray-*`

`Dooray/Config.md`의 API 토큰과 인증 정보는 출력하거나 커밋하지 않는다.

## Skill 선택

| 요청 | Skill | 기능 |
|---|---|---|
| 최초 설치 또는 실행 명령 복구 | `dooray-init` | OS를 확인해 launcher, PATH, 셸 단축 명령 설정 |
| 미완료 담당 업무 목록 | `dooray-list` | 최신 등록순으로 지정 개수 조회 |
| 업무 내용 | `dooray-read` | 제목, 상태, 본문, 첨부파일 조회 |
| 전체 맥락 또는 댓글 이력 | `dooray-read-full` | 업무 내용과 댓글 조회 |
| 업무 주소 | `dooray-link` | 웹 주소 조회 |
| 현재 상태 | `dooray-status` | 제목과 상태만 조회 |
| 상태 변경 | `dooray-status-change` | 현재 상태와 상태 목록 확인 후 변경 |
| 댓글 등록 | `dooray-reply` | 사용자가 지정한 댓글 등록 |
| 위키 페이지 목록 | `dooray-wiki-list` | 프로젝트 위키 페이지를 전체 경로로 조회 |
| 위키 읽기 | `dooray-wiki-read` | 본문·댓글·파일 목록 조회. 경로가 없으면 하위 페이지 번호 목록에서 골라 읽기 |
| 위키 쓰기 | `dooray-wiki-write` | 받은 내용을 그대로 생성하거나 날짜 헤더로 이어쓰기. 쓰기 전 확인 |
| 업무를 위키 문서로 정리 | `dooray-task-to-wiki` | 업무 본문·히스토리·첨부를 목적에 맞게 정리한 초안을 `Dooray/wiki/<업무번호>_<목적>.md`에 쓰고, 검토 후 위치를 정해 이미지·자료와 함께 올림 |
| 코드 적용 방안 보고서 | `dooray-report` | 업무 전체를 분석해 `Dooray/task/report/<업무번호>/REPORT.md` 작성·갱신. 구현은 하지 않음 |

현재 실행 환경에 맞는 Skill의 `SKILL.md`를 읽고 그 절차를 우선 적용한다. Claude Code에서는 `.claude/skills/`, Codex에서는 `.agents/skills/`를 사용한다.

## 공통 실행 규칙

- CLI 명령은 저장소 루트에서 실행한다. 상대경로가 `Dooray/dooray.py`를 기준으로 한다.
- 일반 Skill은 초기화된 `dooray` launcher를 사용하며 OS를 다시 판별하지 않는다.
- `dooray` 명령이 없으면 자동으로 PATH나 프로필을 수정하지 말고, Codex에서는 `$dooray-init`, Claude Code에서는 `/dooray-init`을 직접 호출하도록 안내한다.
- 조회 결과는 Skill 지시에 따라 원본 그대로 즉시 보여주고 임의로 요약하거나 재작성하지 않는다. 예외로 `dooray-report`와 `dooray-task-to-wiki`는 조회 원본을 분석 근거로 사용하고 작성한 보고서·위키 초안의 전문을 전달한다.
- 댓글 내용은 사용자가 준 문구를 임의로 다듬지 않는다.
- 상태 변경은 현재 상태와 워크플로 목록을 먼저 보여주고 사용자가 선택한 뒤 실행한다.
- 댓글 등록, 상태 변경, 위키 쓰기 같은 쓰기 작업은 사용자의 명시적인 요청 없이 실행하지 않는다.
- 위키 쓰기는 `--dry-run`으로 생성/이어쓰기 판단과 내용(업로드할 파일 포함)을 먼저 보여주고 확인을 받은 뒤 실행한다.
- `dooray-task-to-wiki`는 초안(`Dooray/wiki/` 아래)과 필요한 업무 첨부 다운로드만 로컬에 쓰고, 위키 업로드는 확인 후에만 한다. 생성 문서에 `@이름`을 쓰지 않는다.
- 위키 경로는 `>` 앞뒤를 공백 한 칸으로 맞추고 따옴표로 감싸 전달한다. Windows `dooray` launcher(cmd)는 공백 없는 `>`를 리다이렉션으로 해석한다.
- CLI 오류를 성공으로 해석하지 말고 오류 내용을 그대로 알린다.

## CLI 대응표

`dooray`는 `python Dooray/dooray.py`(macOS·Linux는 `python3 Dooray/dooray.py`)를 실행하는 launcher다. 초기화 전에 사람이 직접 실행할 때는 이 형태를 쓸 수 있지만, Skill은 `dooray`만 사용한다.

```text
dooray list 개수
dooray read 업무번호
dooray full 업무번호 선택적-댓글-개수
dooray link 업무번호
dooray status 업무번호
dooray workflows
dooray setstatus 업무번호 "상태명"
dooray comment 업무번호 --file 임시파일경로
dooray download 업무번호 선택적-파일명-또는-번호-또는-all
dooray wiki-list 선택적-"경로"
dooray wiki-read 선택적-"경로"
dooray wiki-write "경로" --file 임시파일경로 선택적---dry-run 선택적---move-draft
dooray wiki-download "경로" 선택적-파일명-또는-번호-또는-all
```

위키는 `REPOSITORY` 프로젝트에 연결된 위키를 자동으로 쓴다. 경로는 Home 아래부터 제목을 `>`로 이은 것이고,
맨 앞의 위키 이름(`Snoopy >`)은 있어도 없어도 된다. 각 단계에서 남은 조각을 가장 길게 붙인 것부터 제목과
맞추므로 제목에 `>`가 있는 페이지도 가리킬 수 있다. `wiki-read`는 끝에 `>`가 있거나 경로가 없으면 하위 페이지
번호 목록을 출력한다(하위가 없으면 본문). 읽기 결과에는 본문 뒤에 댓글(시간순)과 파일 목록(첨부 → 이미지,
번호)이 붙는다. 본문 없이 댓글에만 내용이 있는 페이지가 있으므로 댓글까지 읽는다. `wiki-download`의 번호는 이
파일 목록 번호와 같고, 저장 위치는 `Dooray/wiki/<위키이름>/<제목>/.../download/<파일ID>_<파일명>`이다(실제 제목 기준, 폴더 이름에 못 쓰는 문자는 `_`). 본문을 읽거나 쓰기를 마치면 맨 아래에
`위키 주소: https://{TENANT}.dooray.com/wiki/{위키ID}/{페이지ID}`를 붙인다(`TENANT=` 설정 필요). `wiki-write`는 대상이 있으면 `## YY-MM-DD, HH:mm`(로컬 시각, 예: `## 26-10-27, 14:05`) 헤더를 붙여
이어쓰고, 없으면 부모 아래에 만든다. 중간 페이지는 만들지 않으며 HTML 본문 페이지에는 이어쓰지 않는다.
내용 속 로컬 `![이미지](경로)`·`[파일](경로)`(공백이 있으면 `(<경로>)`, 기준은 `--file`의 폴더)는 실제 형식으로 대상 페이지에
올리고(이미지 `inline_image`, 그 밖 `general`) `/wikis/<프로젝트ID>/files/<attachFileId>` 참조로 바꾼다. 로컬 파일이 하나라도
없으면 아무것도 쓰지 않는다. 새 페이지는 생성 → 업로드 → 본문 수정 순서다. `--move-draft`는 성공 후 초안을 그 페이지 폴더
(`Dooray/wiki/<위키이름>/<제목>/…/`)로 옮기고, 같은 이름이 있으면 `_2`… 를 붙인다.
옮긴 초안 속 로컬 이미지·파일 경로는 새 위치 기준으로 다시 맞춰, 옮긴 뒤에도 미리보기와 재업로드가 된다.
이어쓰기 저장 직전에 본문 내용과 형식을 다시 조회해 처음 조회한 값과 비교한다. 변경되었거나 재조회에
실패하면 저장하지 않고 종료한다. 변경 오류가 나면 최신 내용을 다시 읽고 확인한 뒤 실행한다.
이 검사는 충돌 위험을 줄이지만, 마지막 재조회와 저장 사이의 동시 수정까지 막지는 못한다.

`download`는 첨부파일과 **본문·댓글의 인라인 이미지**를 함께 받는다. 생략하거나 `all`이면 전체를,
번호를 주면 그 파일 하나를, 파일명을 주면 그 이름의 파일을 모두 받는다. 번호는 첨부 → 본문 → 댓글
순서이며 `read`의 첨부 번호, `full`의 파일 목록 번호와 같다. 저장 경로가
`Dooray/task/report/<업무번호>/download/<파일ID>_<파일명>`이라 같은 이름이어도 서로 덮어쓰지 않는다.
댓글 조회에 실패하면 다운로드를 시작하지 않는다.

`full`은 조회한 본문·댓글의 파일 목록을 파일 ID·이름·출처로 함께 출력한다. 댓글 개수를 제한하면
파일 목록도 그 댓글 범위에 한정되고 번호를 붙이지 않으므로, 파일을 빠짐없이 보려면 개수를 지정하지 않는다.
`download`는 항상 전체 댓글을 조회한다.

`dooray-report`의 공통 절차는 `.claude/skills/dooray-report/references/report-workflow.md`다.
`dooray-task-to-wiki`의 공통 절차는 `.claude/skills/dooray-task-to-wiki/references/task-to-wiki-workflow.md`다.
각 스킬의 Claude/Codex 어댑터가 같은 절차를 참조하고, 파일 작성·자료 판독 도구만 환경에 맞게 지정한다.
Codex의 Dooray 스킬은 `agents/openai.yaml`의 `allow_implicit_invocation: false`로 명시적 호출을 유지한다.
게시 전 내용·대상·첨부 확인과 도구 실행 권한은 별개이며, 추가 실행 승인창의 표시 여부는 실행 환경의 권한 정책을 따른다.

댓글을 등록할 때는 셸 인젝션과 인코딩 문제를 피하도록 댓글을 임시 파일에 기록하고 `--file`로 전달한 뒤 임시 파일을 제거한다.

## 셸 단축 명령

`dooray-init`이 설치한 launcher와 단축 명령은 현재 디렉터리를 기준으로 `Dooray/dooray.py`를 찾는다. 따라서 저장소 루트에서 실행한다. `Dooray` 폴더 안에서 실행하면 `Dooray/Dooray/dooray.py`를 찾게 되어 실패한다.

`dooray-status-change`는 대화형 Skill이므로 단일 셸 함수가 없다. 터미널에서는 다음 순서로 실행한다.

```text
dooray-status 업무번호
dooray-workflows
dooray-setstatus 업무번호 "상태명"
```
