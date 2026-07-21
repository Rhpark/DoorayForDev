# Dooray 연동 지침

이 문서는 Dooray 관련 요청을 처리할 때만 읽는다. 일반 개발 작업에는 적용하지 않는다.

## 구성

- 공용 CLI: `Dooray/dooray.py`
- 로컬 설정: `Dooray/Config.md`
- 다운로드 위치: `Dooray/download/`
- Claude Code Skill: `.claude/skills/dooray-*`
- Codex Skill: `.agents/skills/dooray-*`

`Dooray/Config.md`의 API 토큰과 인증 정보는 출력하거나 커밋하지 않는다.

## Skill 선택

| 요청 | Skill | 기능 |
|---|---|---|
| 미완료 담당 업무 목록 | `dooray-list` | 최신 등록순으로 지정 개수 조회 |
| 업무 내용 | `dooray-read` | 제목, 상태, 본문, 첨부파일 조회 |
| 전체 맥락 또는 댓글 이력 | `dooray-read-full` | 업무 내용과 댓글 조회 |
| 업무 주소 | `dooray-link` | 웹 주소 조회 |
| 현재 상태 | `dooray-status` | 제목과 상태만 조회 |
| 상태 변경 | `dooray-status-change` | 현재 상태와 상태 목록 확인 후 변경 |
| 댓글 등록 | `dooray-reply` | 사용자가 지정한 댓글 등록 |
| PowerShell 단축 명령 설치 | `dooray-shell-setup` | PowerShell 프로필에 함수 등록 |

현재 실행 환경에 맞는 Skill의 `SKILL.md`를 읽고 그 절차를 우선 적용한다. Claude Code에서는 `.claude/skills/`, Codex에서는 `.agents/skills/`를 사용한다.

## 공통 실행 규칙

- CLI 명령은 저장소 루트에서 실행한다. 상대경로가 `Dooray/dooray.py`를 기준으로 한다.
- 조회 결과는 Skill 지시에 따라 원본 그대로 즉시 보여주고 임의로 요약하거나 재작성하지 않는다.
- 댓글 내용은 사용자가 준 문구를 임의로 다듬지 않는다.
- 상태 변경은 현재 상태와 워크플로 목록을 먼저 보여주고 사용자가 선택한 뒤 실행한다.
- 댓글 등록과 상태 변경 같은 쓰기 작업은 사용자의 명시적인 요청 없이 실행하지 않는다.
- CLI 오류를 성공으로 해석하지 말고 오류 내용을 그대로 알린다.

## CLI 대응표

```text
python Dooray/dooray.py list 개수
python Dooray/dooray.py read 업무번호
python Dooray/dooray.py full 업무번호 선택적-댓글-개수
python Dooray/dooray.py link 업무번호
python Dooray/dooray.py status 업무번호
python Dooray/dooray.py workflows
python Dooray/dooray.py setstatus 업무번호 "상태명"
python Dooray/dooray.py comment 업무번호 --file 임시파일경로
python Dooray/dooray.py download 업무번호 파일명-또는-번호-또는-all
```

댓글을 등록할 때는 셸 인젝션과 인코딩 문제를 피하도록 댓글을 임시 파일에 기록하고 `--file`로 전달한 뒤 임시 파일을 제거한다.

## PowerShell 단축 명령

`dooray-shell-setup`이 등록한 명령은 현재 디렉터리를 기준으로 `Dooray\dooray.py`를 찾는다. 따라서 현재 구현에서는 저장소 루트에서 실행한다. `Dooray` 폴더 안에서 실행하면 `Dooray\Dooray\dooray.py`를 찾게 되어 실패한다.

`dooray-status-change`는 대화형 Skill이므로 단일 셸 함수가 없다. 터미널에서는 다음 순서로 실행한다.

```text
dooray-status 업무번호
dooray-workflows
dooray-setstatus 업무번호 "상태명"
```
