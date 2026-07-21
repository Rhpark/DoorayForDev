---
name: dooray-shell-setup
description: 일반 PowerShell/cmd 창에서도 Dooray 명령을 slash command와 같은 이름으로 쓸 수 있도록 $PROFILE에 함수를 등록한다. 사용법 /dooray-shell-setup. 사용자가 이 명령을 직접 호출했을 때 사용.
disable-model-invocation: true
model: sonnet
effort: medium
---

목적: `python Dooray/dooray.py read ...`처럼 매번 치는 대신, 일반 터미널에서도 `dooray-read 3`처럼 Claude Code의 slash command와 같은 이름으로 부를 수 있게 PowerShell 프로필에 함수를 등록한다. 프로젝트마다 다른 `Dooray/` 폴더를 가리켜야 하므로 **상대경로**(`Dooray\dooray.py`, 현재 디렉터리 기준)로 등록한다 — 실행 시점의 현재 폴더에 있는 `Dooray/`를 자동으로 찾는다.

PowerShell 도구로 다음을 수행한다:

1. `$PROFILE` 경로를 확인한다 (`Write-Output $PROFILE`). 파일이 없으면 부모 폴더까지 포함해 새로 만든다(`New-Item -ItemType File -Force`로 덮어쓰지 않도록 존재 여부를 먼저 확인).
2. 파일 내용에 `# === Dooray shortcuts (dooray-shell-setup) ===` 마커가 이미 있으면 아무것도 하지 않고 "이미 등록되어 있습니다"라고 안내한다.
3. 마커가 없으면 아래 블록을 파일 **끝에 추가**한다(기존 내용은 절대 덮어쓰지 않음):

```powershell
# === Dooray shortcuts (dooray-shell-setup) ===
function dooray-read { python "Dooray\dooray.py" read @args }
function dooray-read-full { python "Dooray\dooray.py" full @args }
function dooray-link { python "Dooray\dooray.py" link @args }
function dooray-status { python "Dooray\dooray.py" status @args }
function dooray-workflows { python "Dooray\dooray.py" workflows @args }
function dooray-setstatus { python "Dooray\dooray.py" setstatus @args }
function dooray-reply { python "Dooray\dooray.py" comment @args }
function dooray-list { python "Dooray\dooray.py" list @args }
function dooray-download { python "Dooray\dooray.py" download @args }
# === End Dooray shortcuts ===
```

`dooray-status-change`는 목록 제시 후 선택을 기다리는 대화형 흐름이라 단순 함수로 옮길 수 없다 — 터미널에서는 `dooray-status`로 현재 상태를, `dooray-workflows`로 가능한 상태 목록을 확인한 뒤 `dooray-setstatus <번호> "<상태명>"`을 직접 실행하는 것으로 대체한다는 점을 사용자에게 알려준다.

4. 완료 후 무엇을 추가했는지(또는 이미 있어서 건너뛰었는지) 알려주고, 새 PowerShell 창을 열거나 `. $PROFILE`로 다시 불러와야 적용된다고 안내한다.
