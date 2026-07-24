---
name: dooray-shell-setup
description: PowerShell 프로필에 Dooray CLI 단축 함수를 등록한다. 사용자가 일반 PowerShell이나 cmd에서 dooray-read, dooray-reply 등의 명령을 사용하도록 설정해 달라고 하거나 $dooray-shell-setup을 직접 호출했을 때 사용한다.
---

# Dooray 셸 명령 설정

일반 PowerShell에서도 `dooray-read 3`처럼 Dooray 명령을 사용할 수 있도록 현재 사용자의 PowerShell 프로필에 함수를 등록한다. 프로젝트마다 다른 `Dooray/` 폴더를 사용하므로 현재 디렉터리 기준 상대경로를 등록한다.

## 설정 절차

1. 현재 디렉터리에 `Dooray\dooray.py`가 있는지 확인한다. 없으면 프로필을 수정하지 말고 프로젝트 루트에서 다시 실행하도록 안내한다.
2. `Write-Output $PROFILE`로 프로필 경로를 확인한다. 프로필이 작업공간 밖에 있어 승인이 필요하면 해당 경로 수정에 필요한 범위로 승인을 요청한다.
3. 프로필 파일이 없으면 부모 디렉터리와 파일을 생성한다. 기존 파일이 있으면 보존한다.
4. 프로필 전체에서 `# === Dooray shortcuts (dooray-shell-setup) ===` 마커를 찾는다.
5. 마커가 있으면 수정하지 않고 `이미 등록되어 있습니다`라고 알린다.
6. 마커가 없으면 다음 블록을 프로필 끝에 추가한다. 기존 내용을 덮어쓰지 않는다.

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

7. 추가 또는 건너뛴 결과와 프로필 경로를 알려준다.
8. 새 PowerShell 창을 열거나 `. $PROFILE`을 실행해야 적용된다고 안내한다.

상대경로를 사용하므로 명령 실행 시 `Dooray\dooray.py`가 있는 프로젝트 루트가 현재 디렉터리여야 한다.

`dooray-status-change`는 대화형 Skill이므로 함수로 등록하지 않는다. 터미널에서는 `dooray-status`와 `dooray-workflows`로 확인한 뒤 `dooray-setstatus <업무번호> "<상태명>"`을 실행하도록 안내한다.
