---
name: dooray-init
description: 현재 OS와 셸을 확인해 Dooray launcher, PATH와 셸 단축 명령을 최초 설치하거나 복구한다. 사용법 /dooray-init. 사용자가 이 명령을 직접 호출했을 때만 사용한다.
disable-model-invocation: true
model: sonnet
effort: medium
allowed-tools:
  - PowerShell(python Dooray/dooray.py init)
  - Bash(python Dooray/dooray.py init)
  - Bash(python3 Dooray/dooray.py init)
---

# Dooray 초기화

사용자가 직접 호출하지 않았다면 PATH나 셸 프로필을 수정하지 않는다.

1. 저장소 루트에 `Dooray/dooray.py`가 있는지 확인한다.
2. 현재 환경에서 Python 3.8 이상을 확인하고 launcher를 설치하거나 갱신한다.
   - Windows PowerShell: `python Dooray/dooray.py init`
   - macOS·Linux bash/zsh: `python3 Dooray/dooray.py init`
3. launcher를 확인하고 현재 셸의 프로필을 정한다.
   - Windows: `$env:LOCALAPPDATA/DoorayForDev/bin/dooray.cmd`, PowerShell `$PROFILE`
   - macOS·Linux: `~/.local/bin/dooray`, bash `~/.bashrc` 또는 zsh `~/.zshrc`
   - cmd.exe 등 지원하지 않는 셸이면 프로필을 수정하지 않고 지원 셸을 안내한다.
4. 기존 프로필 내용은 보존한다.
5. `# === Dooray shortcuts (dooray-shell-setup) ===`와 `# === End Dooray shortcuts ===`가 모두 있으면 그 사이의 기존 Dooray 블록만 아래 내용으로 교체한다. 마커가 모두 없으면 파일 끝에 추가한다. 한쪽 마커만 있으면 수정하지 않고 손상된 상태를 알린다. 마커 이름은 이전 설치 호환용이며 별도 `dooray-shell-setup` Skill은 없다.

PowerShell:

```powershell
# === Dooray shortcuts (dooray-shell-setup) ===
$doorayBin = Join-Path $env:LOCALAPPDATA "DoorayForDev/bin"
if (($env:Path -split ';') -notcontains $doorayBin) { $env:Path = "$doorayBin;$env:Path" }
function dooray-read { dooray read @args }
function dooray-read-full { dooray full @args }
function dooray-link { dooray link @args }
function dooray-status { dooray status @args }
function dooray-workflows { dooray workflows @args }
function dooray-setstatus { dooray setstatus @args }
function dooray-reply { dooray comment @args }
function dooray-list { dooray list @args }
function dooray-download { dooray download @args }
# === End Dooray shortcuts ===
```

bash/zsh:

```bash
# === Dooray shortcuts (dooray-shell-setup) ===
case ":$PATH:" in *":$HOME/.local/bin:"*) ;; *) export PATH="$HOME/.local/bin:$PATH" ;; esac
dooray-read() { dooray read "$@"; }
dooray-read-full() { dooray full "$@"; }
dooray-link() { dooray link "$@"; }
dooray-status() { dooray status "$@"; }
dooray-workflows() { dooray workflows "$@"; }
dooray-setstatus() { dooray setstatus "$@"; }
dooray-reply() { dooray comment "$@"; }
dooray-list() { dooray list "$@"; }
dooray-download() { dooray download "$@"; }
# === End Dooray shortcuts ===
```

6. 설치된 launcher의 절대경로로 `help`를 실행해 검증한다. PATH 반영 전에는 `dooray help`를 사용하지 않는다.
7. launcher와 프로필 경로, 추가·갱신 결과를 알린다. PowerShell은 새 창 또는 `. $PROFILE`, bash는 `source ~/.bashrc`, zsh는 `source ~/.zshrc`로 적용한다. Claude Code도 다시 시작하도록 안내한다.

기존 `dooray` 명령이나 소유하지 않은 launcher·프로필 블록과 충돌하면 덮어쓰지 않는다. `dooray`와 단축 명령은 현재 디렉터리의 `Dooray/dooray.py`를 사용하므로 저장소 루트에서 실행한다.
