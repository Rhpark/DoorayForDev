# DoorayForDev

우리 팀 워크플로에 맞춘 **가벼운 Dooray 업무 CLI + AI 에이전트 Skill**.
터미널이나 Claude Code / Codex 안에서 Dooray 업무를 조회·관리한다.

## 요구 사항

- **Python 3.8 이상** — 유일한 실행 요구 사항. 별도 `pip install` 없음
  (`urllib`·`json`·`concurrent.futures` 등 표준 라이브러리만 사용)
  - 확인: `python --version` (macOS·Linux는 `python3 --version`)
  - 없으면 설치
    - Windows: `winget install Python.Python.3.12`
    - macOS: `brew install python`
    - Ubuntu·Debian: `sudo apt install python3`
    - Fedora·RHEL 계열: `sudo dnf install python3`
    - 기타 환경: 운영체제의 패키지 관리자 또는 <https://www.python.org/downloads/>
- **Dooray 개인 API 토큰** — Dooray 설정에서 발급해 `Config.md`에 기입
- 네트워크: `api.dooray.com` 접근 가능해야 함

### 선택 도구

Claude Code 또는 Codex가 있으면 `dooray-init`으로 최초 설정을 자동화하고 Dooray Skill을 사용할 수 있다.
터미널에서 CLI만 사용할 경우에는 필요하지 않다.

## 설치

> **작업 프로젝트마다 따로 설치한다.** Dooray 프로젝트가 다르면 `REPOSITORY=` 값도 달라지므로,
> 각 작업 프로젝트 루트에 `Dooray/`를 따로 배치하고 별도의 `Config.md`를 작성한다.

이 도구는 단독으로 쓰는 게 아니라, **Dooray 프로젝트와 연계된 작업 프로젝트 안에 넣어서** 쓴다. 
그 프로젝트 루트에 아래처럼 배치한다.

```text
MyApp/                      ← Dooray와 연계된 내 작업 프로젝트 (여기서 명령을 실행)
├── src/ ...                ← 원래 있던 프로젝트 코드
├── Dooray/                 ← 폴더째로 복사
│   ├── dooray.py
│   ├── Config.md           ← 로컬 설정(직접 생성, 커밋 금지)
│   └── report/             ← 자동 생성 (REPORT.md·첨부 다운로드)
├── DOORAY.md               ← 복사
├── .claude/skills/dooray-* ← 복사 (Claude Code를 쓸 경우)
├── .agents/skills/dooray-* ← 복사 (Codex를 쓸 경우)
├── CLAUDE.md               ← 이미 있다면, 복사하지 말고 내용만 추가
└── AGENTS.md               ← 이미 있다면, 복사하지 말고 내용만 추가
```

`Dooray/`는 **폴더째로** 옮긴다 — `dooray.py`가 자기 옆(`Path(__file__).parent`)에서 `Config.md`를 찾기 때문이다.

## 설정

`Dooray/Config.md`를 직접 만들고 아래 키를 프로젝트에 맞게 채운다 (`KEY=VALUE`, 주석 `#`는 참고용이니 빼도 된다).

```text
DOORAY_API_TOKEN=발급받은_토큰   # 필수: Dooray 개인 API 토큰
REPOSITORY=프로젝트명            # 필수: 프로젝트 코드
TENANT=회사테넌트                # 필수: 업무 웹 주소 생성용 (/dooray-link 등)
COMPANY=회사명                   # 선택: @멘션을 이 회사 이메일 도메인으로 한정
RESPONSE_TIME=10                 # 선택: API 응답 대기 초 (기본 10)
```

> `DOORAY_API_TOKEN`은 개인 자격 증명이다. `Dooray/Config.md`는 `.gitignore`로 제외되며 **커밋하지 않는다**.
> 팀원마다 각자 토큰으로 `Config.md`를 만든다.

## 터미널에서 사용법

초기화 후 터미널에서 실행하는 `dooray ...` 명령은 **AI 토큰을 전혀 쓰지 않는다.** 파이썬이
Dooray API를 직접 호출할 뿐 모델을 거치지 않기 때문이다. 
조회·상태 변경·댓글 같은 일상 작업은 터미널에서 쓰는 게 가장 싸고, 모델의 판단이 필요할 때만 [에이전트](#에이전트에서-사용)로 넘기면 된다.

### 어디서 실행하나

명령창을 열고 [설치](#설치)한 작업 프로젝트 폴더로 이동한다.
Windows는 PowerShell(시작메뉴에서 "PowerShell" 검색), macOS·Linux는 터미널을 쓴다.

### `dooray` 명령 최초 설정

처음 사용하기 전에 어느 운영체제에서든 `dooray` 명령을 실행할 수 있도록 **최초 설정을 한 번 해야 한다.**
이 과정은 현재 OS에 맞는 `dooray` 실행 파일을 만들고 명령 검색 경로(PATH)에 등록한다. 
설정 방법은 다음 두 가지이며, AI 사용은 필수가 아니다.

#### AI로 편하게 초기화하기 (권장)

현재 OS와 셸을
판별하고 `dooray` 실행 명령, PATH와 단축 명령을 설정한 뒤 실제 실행까지 확인한다. 
PATH나 단축 명령이 손상되거나 변경된 경우에도 같은 Skill을 다시 호출해 복구할 수 있다.
 - Claude Code: `/dooray-init`
 - Codex: `$dooray-init`

#### AI 없이 직접 초기화하기

저장소 루트에서 현재 OS에 맞는 명령을 실행한다.

```powershell
# Windows PowerShell
cd C:\Users\내계정\Desktop\git\MyApp
python Dooray\dooray.py init
```

```bash
# macOS·Linux
cd ~/git/MyApp
python3 Dooray/dooray.py init
```

Windows에서는 `dooray` 실행 파일을 만들고 사용자 PATH를 함께 갱신한다. macOS·Linux에서는 `~/.local/bin/dooray`를 만들므로, 
`~/.bashrc` 또는 `~/.zshrc`에 `export PATH="$HOME/.local/bin:$PATH"`를 직접 추가한 뒤 터미널을 다시 연다. 
AI 없이 초기화한 경우에도 아래의 `dooray ...` 명령과 일반 Dooray Skill을 사용할 수 있다. 
다만 `dooray-read` 같은 단축 명령이 필요하면 셸 함수를 직접 등록하거나 AI의 `dooray-init` Skill을 사용해야 한다.

최초 설정 후에는 모든 OS에서 같은 명령을 사용한다. 
`dooray` 명령은 현재 디렉터리의`Dooray/dooray.py`를 찾아 실행하므로 항상 작업 프로젝트 루트에서 실행한다.

```text
dooray list 개수                     미완료 담당 업무를 최신순으로 N개
dooray read 업무번호                   제목 + 상태 + 본문 + 첨부
dooray full 업무번호 개수                read + 태그 + 댓글 이력 (생략 시 전체)
dooray status 업무번호                 현재 상태
dooray link 업무번호                   업무 웹 주소
dooray workflows                   프로젝트의 상태 목록
dooray setstatus 업무번호 상태명          상태 변경
dooray comment 업무번호 내용             댓글 등록 (--file <경로> 로 파일에서 읽기 가능)
dooray download 업무번호 [파일명|번호|all]  첨부를 Dooray/report/<업무번호>/download/ 에 저장
```

### 단축 명령으로 짧게 쓰기

AI의 `/dooray-init` 또는 `$dooray-init` Skill은 현재 셸 프로필에 기존 이름의 단축 함수도 함께 등록한다. 
PowerShell은 `$PROFILE`, bash는 `~/.bashrc`, zsh는 `~/.zshrc`를 사용한다. 
프로필을 다시 불러오거나 터미널을 새로 연 뒤부터 사용할 수 있다.

AI로 초기화하면 최초 설정 또는 복구 시에만 토큰을 사용한다. 초기화 이후 터미널에서 
`dooray`와 단축 명령을 직접 실행할 때는 AI 토큰을 사용하지 않는다.

```text
dooray-list 5            = dooray list 5
dooray-read 1287         
dooray-read-full 1287       
dooray-status 1287
dooray-link 1287         
dooray-workflows            
dooray-download 1287 all
dooray-setstatus 1287 "DEV 완료"                     
dooray-reply 1287 "확인했습니다"
```


### 출력 형식

출력은 사람·AI가 그대로 읽는 텍스트다.

```console
$ dooray list 3
PROJ / 1287 - DEV 진행중 - 토큰 갱신 실패 처리 (작성자: 홍길동)
PROJ / 1274 - DEV 대기 - 목록 정렬 기준 변경 (작성자: 김영희)
PROJ / 1260 - DEV 리뷰 - 첨부 다운로드 경로 정리 (작성자: 홍길동)

$ dooray full 1287
#1287 토큰 갱신 실패 처리
상태: DEV 진행중
태그: BUG

만료된 refresh token으로 재발급을 시도하면 500이 반환됩니다.

첨부파일: 로그.txt (12.4KB) — 다운로드할까요?

이력 주소: https://회사테넌트.dooray.com/task/to/4029301827364

--- 댓글 ---
[2026-07-20 14:02] 김영희: 401로 내려주는 게 맞습니다.
[2026-07-21 09:31] 홍길동: 확인했습니다. @김영희 수정 후 리뷰 부탁드립니다.
```

## 에이전트에서 사용

Claude Code와 Codex는 각각 `.claude/skills/`, `.agents/skills/`의 `dooray-*` Skill로 위 CLI를 호출한다.
Claude Code Skill은 `disable-model-invocation` 설정 때문에 `/dooray-*`로 직접 호출한다. Codex에서는
`$dooray-*`로 명시적으로 호출할 수 있으며, 명확한 Dooray 자연어 요청에도 해당 Skill을 사용할 수 있다.

`dooray-init`을 제외한 일반 Dooray Skill은 최초 설정을 마친 `dooray` 명령을 사용한다. 따라서 먼저
AI의 `/dooray-init`·`$dooray-init` 또는 [수동 초기화](#ai-없이-직접-초기화하기) 중 하나를 완료해야 한다. 
수동 초기화를 마쳤다면 `dooray-init` Skill을 별도로 호출할 필요는 없다.

| Claude / Codex 호출 | 기능 |
|---|---|
| `/dooray-init` / `$dooray-init` | OS·셸 확인 후 `dooray` 명령, PATH와 단축 명령 최초 설정·복구 |
| `/dooray-list` / `$dooray-list <개수>` | 미완료 담당 업무를 최신순으로 N개 |
| `/dooray-read` / `$dooray-read <업무번호>` | 제목·상태·본문 조회 |
| `/dooray-read-full` / `$dooray-read-full <업무번호> [개수]` | 위 + 태그 + 댓글 이력 |
| `/dooray-status` / `$dooray-status <업무번호>` | 현재 상태만 확인 |
| `/dooray-link` / `$dooray-link <업무번호>` | 업무 웹 주소 |
| `/dooray-reply` / `$dooray-reply <업무번호> <댓글 내용>` | 댓글 등록 |

댓글 등록·상태 변경 같은 쓰기 작업은 사용자의 명시적 요청 없이 실행하지 않는다. 
공통 지침은 `DOORAY.md`, 도구별 지침은 `CLAUDE.md`와 `AGENTS.md`를 참고한다.

### 에이전트가 필요한 것 ⭐

이 둘은 **터미널로 대체할 수 없다.** 여러 명령을 엮거나 모델의 판단이 필요해서, 이 도구를 에이전트에서 쓰는 진짜 이유에 해당한다.

| Claude / Codex 호출 | 왜 에이전트여야 하나 |
|---|---|
| **`/dooray-status-change` / `$dooray-status-change <업무번호>`** | 현재 상태와 프로젝트의 상태 목록을 먼저 조회해 **선택지로 제시하고**, 고른 이름으로 변경까지 한다. 대화형이라 셸 함수로 만들 수 없다 — 단축 명령에 유일하게 빠져 있는 항목이다. 터미널로 하면 `dooray-status` → `dooray-workflows` → `dooray-setstatus "상태명"`을 직접 이어 실행하며 상태명을 정확히 옮겨 적어야 한다. |
| **`/dooray-report` / `$dooray-report <업무번호>`** | **대응하는 CLI 명령이 없다.** 본문·댓글을 읽고, 첨부(`.md`·`.csv`·`.json`·`.png`·`.jpg`·`.pdf`)를 내려받아 직접 읽고, 프로젝트 코드를 탐색해 **"이 저장소에 어떻게 적용할지" 방안을 `Dooray/report/<번호>/REPORT.md`로 작성·갱신**한다. 확인한 사실만 쓰고, 못 정한 것은 "열린 질문"으로 남긴다. 구현은 하지 않는다. |

`dooray-report`는 규모 있는 작업을 시작할 때의 입구다 — 이력을 파악해 방안 문서를 만들고, 실제 구현은 사람이 확인한 뒤 별도로 진행한다.


## 왜 이 도구인가

Dooray는 REST API만 제공하고 터미널용 1차(공식) CLI는 없다. 선택지는 세 가지였다.

1. 원시 REST API를 매번 직접 호출
2. 서드파티 CLI [`@bifos/dooray-cli`](https://github.com/jon890/dooray-cli) 사용
3. 우리 워크플로에 맞는 얇은 도구를 직접 만들기

3번을 골랐고, 아래가 그 판단 근거다.

### 원시 Dooray REST API와 비교

이 도구는 Dooray REST API를 감싼 얇은 래퍼다. 직접 호출 대비 이점:

| 관점 | 이 도구 (`dooray.py`) | 원시 Dooray REST API 직접 호출 |
|---|---|---|
| 형태 | 명령어 9개짜리 CLI | HTTP 엔드포인트를 직접 조립 |
| 의존성 | 파이썬 표준 라이브러리만 | 클라이언트 직접 구현 or 서드파티 |
| 출력 | 사람·AI가 읽기 쉬운 정리된 텍스트 | 장황한 원시 JSON |
| **AI 토큰** | **정리된 최소 텍스트 → 적게 소비** | 큰 JSON 파싱 → 많이 소비 |
| 프로젝트 지정 | `REPOSITORY` 코드로 프로젝트 ID 자동 탐색 | `projectId`를 직접 알아야 함 |
| 업무 목록 | "내가 담당자인 미완료 업무 최신순" 한 번에 | 담당자·워크플로·정렬 필터 직접 조합 |
| @멘션 | `@한글이름` → 실제 멘션으로 자동 치환 | memberId 직접 조회·조립 |
| 태그 | tagId를 이름으로 자동 치환 | 태그 목록 별도 조회·매핑 |
| 성능 | 상세·첨부·댓글을 병렬 호출 | 직접 최적화 |

즉 projectId·workflowId·memberId·tagId를 몰라도 **코드·이름·상태명만으로** 쓸 수 있게
다듬은, 에이전트 친화·토큰 효율 도구다.

### 서드파티 CLI와 비교 (개발자 관점)

우열이 아니라 **성격 차이**다.

| 항목 | 이 도구 (`dooray.py`) | `@bifos/dooray-cli` |
|---|---|---|
| 언어 / 런타임 | Python 3.8+ | TypeScript / Node.js 20+ |
| 설치 | 파일 복사 후 `dooray` 명령 최초 설정 (파이썬 필요) | `npm install -g @bifos/dooray-cli` |
| 외부 의존성 | **0개** (표준 라이브러리만) | **11개** (`commander`·`ky`·`nodemailer`·`imapflow` 등) |
| 코드 형태 | 단일 파일 | 멀티파일 프로젝트 |
| 기능 범위 | 업무 조회·상태·댓글·첨부 (업무 명령 9개 + init/help) | 위키·이메일·메신저까지 포함한 범용 |
| 출력 | 정리된 텍스트 | 표 / `--json` / `--quiet` |
| 커스터마이징 | 파일 직접 수정, 빌드 없음 | 포크·빌드 또는 upstream PR |
| 유지보수 주체 | 우리(사내) | 외부 오픈소스 |
| 성숙도 | 최소한 | v0.14.1, 릴리스·CI/CD·캐싱·시크릿 마스킹 |
| 라이선스 | MIT | MIT |
| AI 연동 | Claude Code + Codex Skill | Claude 연동 지원 |

**판단:** 이 도구는 처음부터 **개발자의 업무 루프**(내 미완료 업무 확인 → 내용·댓글 읽기 → 상태 변경 → 댓글 → 첨부 다운로드)만 겨냥해 설계했다. 
개발자가 자기 업무를 처리하는 데는 이 9개 명령으로 충분하며, 업무 생성·수정이나 위키·메일·메신저 같은 기획/PM성 기능은 의도적으로 뺐다.

그래서 순수 기능 폭·성숙도·유지보수 규모는 `@bifos/dooray-cli`가 앞선다. 
이 도구가 가진 것은 **추가 의존성이 없고, 단일 파일이라 손대기 쉽고, 개발자 워크플로에 정확히 맞다**는 점이다. 
범용 관리 기능이나 다양한 출력 포맷이 필요하면 서드파티가 낫고, 최소 설치로 개발자가 자기 업무를 빠르게 처리하고 필요하면 직접 고치는 게 목적이면 이 도구가 낫다.

### 토큰 소비 (스킬 오버헤드 실측)

AI 에이전트로 쓸 때 요청·출력·답변은 데이터 양에 따라 양쪽 다 늘어나므로(상쇄됨), 
구조적 차이는 **매 호출에 실리는 스킬 오버헤드의 바닥값**에서 갈린다. 실측 비교(값 `≤` 실제 소비):

| | 스킬 오버헤드 (최소) | 참조 문서 |
|---|---|---|
| 이 도구 (`dooray.py`) | **0.55~0.61KB ≤** (Codex/Claude 스킬 1개, 예: `dooray-list`) | 없음 → 항상 평평 |
| `@bifos/dooray-cli` | **2.95KB ≤** (라우터 `SKILL.md` 항상 로드) | 필요 시 최대 +34KB |

일반 스킬은 초기화된 `dooray` 하위 명령 한 줄만 호출하므로 바닥이 낮고,
projectId·workflowId·memberId·tagId 해석을 도구 안에서 끝내 모델이 중간 데이터를 읽지 않는다.
서드파티는 참조 문서가 열릴수록 격차가 더 벌어진다.

주의: 위 비교는 **호출 1건에 로드되는 스킬 문서의 바이트 수**만 재 것이다. 
우리 쪽은 스킬이 기능별로 9개 나뉘어 있어 개별 파일이 작고, 서드파티는 라우터 하나가 여러 기능을 안내하는 구조라 파일이 크다. 
실제 대화 전체의 토큰 총량은 사용 패턴에 따라 달라진다.


## 문제 해결

| 증상 | 원인·조치 |
|---|---|
| `dooray` 명령을 찾을 수 없음 | 최초 설정이 필요하다. `/dooray-init`·`$dooray-init`을 호출하거나 OS에 맞게 `Dooray/dooray.py init`을 직접 실행 |
| 초기화했지만 `dooray`를 찾을 수 없음 | 터미널과 Claude Code/Codex를 다시 시작. macOS·Linux는 `~/.local/bin`이 PATH에 포함됐는지 확인 |
| `dooray-read` 같은 단축 명령을 찾을 수 없음 | AI의 `dooray-init` Skill로 셸 프로필에 단축 함수를 등록하거나 프로필을 다시 불러오기 |
| `Config.md 가 없습니다` | `Dooray/Config.md`를 만들고 `DOORAY_API_TOKEN`·`REPOSITORY` 기입 |
| `'...' 가 없습니다` (프로젝트) | `REPOSITORY=` 프로젝트 코드가 접근 가능한 프로젝트와 일치하는지 확인 |
| `Dooray API 오류 (HTTP 401)` | 토큰이 만료·오타·권한 부족. 토큰 재발급 |
| `응답이 N초 안에 오지 않았습니다` | 네트워크 지연. `Config.md`의 `RESPONSE_TIME=` 값을 늘림 |
| `link`/`이력 주소 확인 불가` | `Config.md`에 `TENANT=` 설정 필요 |

## 라이선스

MIT — [`LICENSE.md`](LICENSE.md)
