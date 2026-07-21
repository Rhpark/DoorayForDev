# DoorayForDev

우리 팀 워크플로에 맞춘 **가벼운 Dooray 업무 CLI + AI 에이전트 Skill**.
터미널이나 Claude Code / Codex 안에서 Dooray 업무를 조회·관리한다.

## 왜 이 도구인가

- **Dooray 공식 CLI가 없다.** Dooray는 REST API만 제공하고, 터미널용 1차(공식) CLI는 없다.
- **잘 만들어진 서드파티 CLI(`@bifos/dooray-cli`)가 있지만, 우리에겐 과하다.** 업무뿐
  아니라 위키·이메일·메신저까지 다루는 범용 도구라 Node.js 20+와 11개의 npm 의존성
  (이메일용 `imapflow`·`nodemailer` 등 우리가 안 쓰는 것 포함)이 딸려온다.
- **우리는 "우리가 소유하고, 우리 워크플로에 맞고, 설치가 필요 없는" 도구를 원했다.**
  이 도구는 의존성 없는 단일 파이썬 파일(약 400줄)이라 파이썬만 있으면 돌고, 필요하면
  포크·PR 없이 그 자리에서 고친다. 한글 `@멘션` 자동 치환, "내 미완료 업무" 기본값처럼
  우리 방식에 맞춘 동작이 이미 들어 있다.
- **Claude Code / Codex용 Skill이 함께 온다.** `/dooray-list 5`, `/dooray-read 1234`,
  `/dooray-status-change 1234`처럼 **슬래시 명령으로 직접 호출**하면 위 CLI를 대신 실행하고
  결과를 정리해 보여준다. (모델이 자연어로 알아서 실행하는 방식이 아니라 명시적 호출이다.
  서드파티도 Claude Code용 스킬을 제공하므로 AI 연동 자체는 차별점이 아니고, 다만 우리는
  Codex까지 지원한다.)
- **AI로 써도 토큰이 적게 든다.** 원시 API의 큰 JSON 대신 정리된 최소 텍스트를 돌려주고,
  프로젝트·상태·멤버 해석을 도구 안에서 처리하므로 모델이 읽는 양이 줄어든다.

### 기본 Dooray API와 비교

이 도구는 Dooray REST API를 감싼 얇은 래퍼다. 직접 호출 대비 이점:

| 관점 | 이 도구 (`dooray.py`) | 원시 Dooray REST API 직접 호출 |
|---|---|---|
| 형태 | 명령어 9개짜리 CLI | HTTP 엔드포인트를 직접 조립 |
| 의존성 | 표준 라이브러리만 (파이썬 외 설치 없음) | 클라이언트 직접 구현 or 서드파티 |
| 출력 | 사람·AI가 읽기 쉬운 정리된 텍스트 | 장황한 원시 JSON |
| **AI 토큰** | **정리된 최소 텍스트 → 적게 소비** | 큰 JSON 파싱 → 많이 소비 |
| 프로젝트 지정 | `REPOSITORY` 코드로 프로젝트 ID 자동 탐색 | `projectId`를 직접 알아야 함 |
| 업무 목록 | "내가 담당자인 미완료 업무 최신순" 한 번에 | 담당자·워크플로·정렬 필터 직접 조합 |
| @멘션 | `@한글이름` → 실제 멘션으로 자동 치환 | memberId 직접 조회·조립 |
| 성능 | 상세·첨부·댓글을 병렬 호출 | 직접 최적화 |

즉 projectId·workflowId·memberId를 몰라도 **코드·이름·상태명만으로** 쓸 수 있게 다듬은,
에이전트 친화·토큰 효율 도구다.

### 서드파티 CLI와 비교 (개발자 관점)

가장 잘 알려진 서드파티 CLI [`@bifos/dooray-cli`](https://github.com/jon890/dooray-cli)와의
사실 기반 비교. 우열이 아니라 **성격 차이**다.

| 항목 | 이 도구 (`dooray.py`) | `@bifos/dooray-cli` |
|---|---|---|
| 언어 / 런타임 | Python 3.8+ | TypeScript / Node.js 20+ |
| 설치 | 없음 (파이썬만 있으면 됨) | `npm install -g @bifos/dooray-cli` |
| 외부 의존성 | **0개** (표준 라이브러리만) | **11개** (`commander`·`ky`·`nodemailer`·`imapflow` 등) |
| 코드 형태 | 단일 파일 ~412줄 | 멀티파일 프로젝트 |
| 기능 범위 | 업무 조회·상태·댓글·첨부 (명령 9개) | 위키·이메일·메신저까지 포함한 범용 |
| 출력 | 정리된 텍스트 | 표 / `--json` / `--quiet` |
| 커스터마이징 | 파일 직접 수정, 빌드 없음 | 포크·빌드 또는 upstream PR |
| 유지보수 주체 | 우리(사내) | 외부 오픈소스 |
| 성숙도 | 최소한 | v0.14.1, 릴리스·CI/CD·캐싱·시크릿 마스킹 |
| 라이선스 | 미정 | MIT |
| AI 연동 | Claude Code + Codex Skill | Claude 연동 지원 |

**판단:** 이 도구는 처음부터 **개발자의 업무 루프**(내 미완료 업무 확인 → 내용·댓글 읽기 →
상태 변경 → 댓글 → 첨부 다운로드)만 겨냥해 설계했다. 개발자가 자기 업무를 처리하는 데는
이 9개 명령으로 충분하며, 업무 생성·수정이나 위키·메일·메신저 같은 기획/PM성 기능은
의도적으로 뺐다. 그래서 순수 기능 폭·성숙도·유지보수 규모는 `@bifos/dooray-cli`가 앞서지만,
이 도구는 **무의존성(파이썬만) · 단일 파일이라 손대기 쉬움 · 개발자 워크플로에 정확히 맞음**
으로 승부한다. 범용 관리 기능이나 다양한 출력 포맷이 필요하면 서드파티가 낫고, 최소 설치로
개발자가 자기 업무를 빠르게 처리하고 필요하면 직접 고치는 게 목적이면 이 도구가 낫다.

#### 토큰 소비 (스킬 오버헤드 실측)

AI 에이전트로 쓸 때 요청·출력·답변은 데이터 양에 따라 양쪽 다 늘어나므로(상쇄됨), 구조적
차이는 **매 호출에 실리는 스킬 오버헤드의 바닥값**에서 갈린다. 실측 비교(값 `≤` 실제 소비):

| | 스킬 오버헤드 (최소) | 참조 문서 |
|---|---|---|
| 이 도구 (`dooray.py`) | **0.43KB ≤** (스킬 1개, 예: `/dooray-list`) | 없음 → 항상 평평 |
| `@bifos/dooray-cli` | **2.95KB ≤** (라우터 `SKILL.md` 항상 로드) | 필요 시 최대 +34KB |

우리 스킬은 "python 명령 한 줄 호출"뿐이라 에이전트에게 가르칠 문서가 없어 바닥이 낮고,
projectId·workflowId·memberId 해석을 도구 안에서 끝내 모델이 중간 데이터를 읽지 않는다.
바닥에서 이미 약 7배 차이이며(2.95 ÷ 0.43), 서드파티는 참조 문서가 열릴수록 더 벌어진다.

## 요구 사항

- **Python 3.8 이상** — 유일한 실행 요구 사항. 별도 `pip install` 없음
  (`urllib`·`json`·`concurrent.futures` 등 표준 라이브러리만 사용)
- **Dooray 개인 API 토큰** — Dooray 설정에서 발급해 `Config.md`에 기입
- (선택) **Claude Code 또는 Codex** — Skill로 에이전트에서 쓸 경우
- 네트워크: `api.dooray.com` 접근 가능해야 함

## 빠른 시작

1. Python 3.8+ 설치 확인: `python --version`
2. `Dooray/Config.md` 작성 (아래 설정 참고)
3. 실행: `python Dooray/dooray.py list 5`

## 설정

`Dooray/dooray.py`와 같은 폴더에 `Dooray/Config.md`를 `KEY=VALUE`로 작성한다.

```text
DOORAY_API_TOKEN=발급받은_토큰   # 필수: Dooray 개인 API 토큰
REPOSITORY=프로젝트명            # 필수: 프로젝트 코드
TENANT=회사테넌트                # 필수: 업무 웹 주소 생성용 (/dooray-link 등)
WORKING=DEV 진행중               # 선택: --working 별칭이 가리킬 상태
COMPLETED=DEV 완료               # 선택: --completed 별칭이 가리킬 상태
COMPANY=회사명                   # 선택: @멘션을 이 회사 이메일 도메인으로 한정
RESPONSE_TIME=10                 # 선택: API 응답 대기 초 (기본 10)
```


## 구성

| 경로 | 설명 |
|---|---|
| `Dooray/dooray.py` | Dooray API 연동 코어 CLI |
| `Dooray/Config.md` | 로컬 설정 (커밋 안 됨) |
| `Dooray/download/` | 첨부파일 다운로드 위치 |
| `.claude/skills/dooray-*` | Claude Code용 Skill |
| `.agents/skills/dooray-*` | Codex용 Skill |
| `DOORAY.md` | 에이전트가 Dooray 요청을 처리할 때 따르는 지침 |

## 사용법

저장소 루트에서 실행한다.

```text
python Dooray/dooray.py list <개수>                 미완료 담당 업무를 최신순으로 N개
python Dooray/dooray.py read <업무번호>              제목 + 상태 + 본문 + 첨부
python Dooray/dooray.py full <업무번호> [개수]        read + 댓글 이력 (생략 시 전체)
python Dooray/dooray.py status <업무번호>            현재 상태
python Dooray/dooray.py link <업무번호>              업무 웹 주소
python Dooray/dooray.py workflows                    프로젝트의 상태 목록
python Dooray/dooray.py setstatus <업무번호> <상태명>  상태 변경 (--working/--completed 별칭 가능)
python Dooray/dooray.py comment <업무번호> <내용>     댓글 등록 (--file <경로> 로 파일에서 읽기 가능)
python Dooray/dooray.py download <업무번호> [파일명|번호|all]  첨부파일을 Dooray/download/ 에 저장
```

## 에이전트에서 사용

Claude Code와 Codex는 각각 `.claude/skills/`, `.agents/skills/`의 `dooray-*` Skill로 위
CLI를 호출한다. Skill은 모델이 자연어로 알아서 실행하지 않고(`disable-model-invocation`),
아래 **슬래시 명령으로 직접 호출**해야 한다.

| 슬래시 명령 | 기능 |
|---|---|
| `/dooray-list <개수>` | 미완료 담당 업무를 최신순으로 N개 |
| `/dooray-read <업무번호>` | 제목·상태·본문 조회 |
| `/dooray-read-full <업무번호> [개수]` | 위 + 댓글 이력 |
| `/dooray-status <업무번호>` | 현재 상태만 확인 |
| `/dooray-status-change <업무번호>` | 상태 목록에서 선택해 변경 |
| `/dooray-link <업무번호>` | 업무 웹 주소 |
| `/dooray-reply <업무번호> <댓글 내용>` | 댓글 등록 |
| `/dooray-shell-setup` | PowerShell/cmd용 단축 명령을 `$PROFILE`에 등록 |

댓글 등록·상태 변경 같은 쓰기 작업은 사용자의 명시적 요청 없이 실행하지 않는다. 상세 지침은
`DOORAY.md` 참고.

## 문제 해결

| 증상 | 원인·조치 |
|---|---|
| `Config.md 가 없습니다` | `Dooray/Config.md`를 만들고 `DOORAY_API_TOKEN`·`REPOSITORY` 기입 |
| `'...' 가 없습니다` (프로젝트) | `REPOSITORY=` 프로젝트 코드가 접근 가능한 프로젝트와 일치하는지 확인 |
| `Dooray API 오류 (HTTP 401)` | 토큰이 만료·오타·권한 부족. 토큰 재발급 |
| `응답이 N초 안에 오지 않았습니다` | 네트워크 지연. `Config.md`의 `RESPONSE_TIME=` 값을 늘림 |
| `link`/`이력 주소 확인 불가` | `Config.md`에 `TENANT=` 설정 필요 |
