#!/usr/bin/env python3
"""Dooray 업무 연동 코어 스크립트.

설정: Dooray/Config.md (KEY=VALUE 형식, 이 스크립트와 같은 폴더)
  DOORAY_API_TOKEN, REPOSITORY, TENANT, WORKING, COMPLETED, COMPANY(선택, @멘션 검색을 이 회사 이메일 도메인으로 한정)
  RESPONSE_TIME(선택, API 응답 대기 초. 기본 10)

최초 초기화 (저장소 루트에서 실행):
  Windows:      python Dooray/dooray.py init
  macOS/Linux:  python3 Dooray/dooray.py init

초기화 후 사용법 (저장소 루트에서 실행):
  dooray read <업무번호>              제목 + 상태 + 본문
  dooray full <업무번호> [개수]        read + 태그 + 댓글 이력 (개수 생략 시 전체, 지정 시 최신 N개)
  dooray link <업무번호>              업무 웹 주소
  dooray status <업무번호>            현재 상태
  dooray workflows                    이 프로젝트의 상태 목록
  dooray setstatus <업무번호> <상태명>  상태 변경 (--working / --completed 별칭 가능)
  dooray comment <업무번호> <내용>     댓글 등록 (--file <경로> 로 파일에서 읽기 가능 — 셸 이스케이프 없이 안전)
  dooray download <업무번호> [파일명|번호]  첨부파일을 Dooray/report/<업무번호>/download/ 에 저장
  dooray list <개수>                  완료되지 않은 업무를 최신 등록순으로 N개
"""
import json
import os
import re
import shutil
import stat
import sys
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path

BASE = "https://api.dooray.com"
CONF = Path(__file__).parent / "Config.md"
KNOWN_CMDS = {"init", "help", "read", "full", "link", "status", "workflows", "setstatus", "comment", "download", "list"}
CLOSED_EXCLUDED_CLASSES = "backlog,registered,working"
PYTHON_CMD = "python" if sys.platform == "win32" else "python3"
LAUNCHER_MARKER = "DoorayForDev launcher"


def current_platform():
    if sys.platform == "win32":
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    if sys.platform.startswith("linux"):
        return "linux"
    raise RuntimeError(f"지원하지 않는 플랫폼입니다: {sys.platform}")


def default_launcher_dir(platform):
    if platform == "windows":
        base = os.environ.get("LOCALAPPDATA")
        if base:
            return Path(base) / "DoorayForDev" / "bin"
        return Path.home() / "AppData" / "Local" / "DoorayForDev" / "bin"
    return Path.home() / ".local" / "bin"


def launcher_text(platform, python_executable):
    if platform == "windows":
        python_path = str(Path(python_executable).resolve())
        return (
            "@echo off\n"
            f"rem {LAUNCHER_MARKER}\n"
            "if not exist \"%CD%\\Dooray\\dooray.py\" (\n"
            "  >&2 echo Dooray/dooray.py를 찾을 수 없습니다. 저장소 루트에서 실행하세요.\n"
            "  exit /b 1\n"
            ")\n"
            f'"{python_path}" "%CD%\\Dooray\\dooray.py" %*\n'
        )
    if platform in {"macos", "linux"}:
        python_path = str(python_executable)
        if not python_path.startswith("/"):
            python_path = Path(python_path).resolve().as_posix()
        escaped_python = "'" + python_path.replace("'", "'\"'\"'") + "'"
        return (
            "#!/bin/sh\n"
            f"# {LAUNCHER_MARKER}\n"
            'script="$PWD/Dooray/dooray.py"\n'
            'if [ ! -f "$script" ]; then\n'
            "  echo 'Dooray/dooray.py를 찾을 수 없습니다. 저장소 루트에서 실행하세요.' >&2\n"
            "  exit 1\n"
            "fi\n"
            f'exec {escaped_python} "$script" "$@"\n'
        )
    raise RuntimeError(f"지원하지 않는 플랫폼입니다: {platform}")


def install_launcher(platform=None, install_dir=None, python_executable=None, check_path=True):
    platform = platform or current_platform()
    install_dir = Path(install_dir) if install_dir else default_launcher_dir(platform)
    python_executable = python_executable or sys.executable
    launcher = install_dir / ("dooray.cmd" if platform == "windows" else "dooray")

    if check_path:
        existing = shutil.which("dooray")
        if existing and Path(existing).resolve() != launcher.resolve():
            raise RuntimeError(f"다른 dooray 명령이 이미 PATH에 있습니다: {existing}")

    if launcher.exists():
        existing_text = launcher.read_text(encoding="utf-8", errors="replace")
        if LAUNCHER_MARKER not in existing_text:
            raise RuntimeError(f"기존 파일을 덮어쓸 수 없습니다: {launcher}")

    install_dir.mkdir(parents=True, exist_ok=True)
    launcher.write_text(launcher_text(platform, python_executable), encoding="utf-8")
    if platform != "windows":
        launcher.chmod(launcher.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return launcher


def add_windows_user_path(directory):
    import ctypes
    import winreg

    directory = str(Path(directory).resolve())
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
        try:
            current, value_type = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            current, value_type = "", winreg.REG_EXPAND_SZ
        entries = [item for item in current.split(";") if item]
        if any(os.path.normcase(os.path.expandvars(item).rstrip("\\/")) == os.path.normcase(directory.rstrip("\\/")) for item in entries):
            return False
        updated = ";".join(entries + [directory])
        winreg.SetValueEx(key, "Path", 0, value_type, updated)
    try:
        result = ctypes.c_size_t()
        ctypes.windll.user32.SendMessageTimeoutW(
            0xFFFF, 0x001A, 0, "Environment", 0x0002, 5000, ctypes.byref(result)
        )
    except (AttributeError, OSError):
        pass
    return True


def init_command():
    platform = current_platform()
    try:
        launcher = install_launcher(platform=platform)
        path_changed = add_windows_user_path(launcher.parent) if platform == "windows" else None
    except (OSError, RuntimeError) as exc:
        sys.exit(f"Dooray 초기화 실패: {exc}")

    print(f"플랫폼: {platform}")
    print(f"Python: {Path(sys.executable).resolve()}")
    print(f"launcher 설치 완료: {launcher}")
    if path_changed is True:
        print("Windows 사용자 PATH에 launcher 폴더를 추가했습니다.")
    elif path_changed is False:
        print("Windows 사용자 PATH에 launcher 폴더가 이미 등록되어 있습니다.")
    else:
        print("셸 프로필에 launcher 폴더를 PATH로 등록해야 합니다.")
    print("셸 단축 명령 설정 후 터미널과 AI 에이전트를 다시 시작하세요.")


def load_config():
    if not CONF.exists():
        sys.exit(f"{CONF} 가 없습니다. DOORAY_API_TOKEN=, REPOSITORY= 등을 담은 설정 파일을 먼저 만드세요.")
    cfg = {}
    for line in CONF.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0]  # 인라인 주석 제거
        if "=" in line:
            k, v = line.split("=", 1)
            k = k.strip()
            if k in cfg:
                sys.exit(f"{CONF} 에 {k}= 이(가) 중복으로 설정되어 있습니다. 하나만 남기세요.")
            cfg[k] = v.strip()
    for key in ("DOORAY_API_TOKEN", "REPOSITORY"):
        if not cfg.get(key):
            sys.exit(f"{CONF} 에 {key}= 설정이 필요합니다.")
    return cfg


class Dooray:
    def __init__(self):
        cfg = load_config()
        self.token = cfg["DOORAY_API_TOKEN"]
        self.repo = cfg["REPOSITORY"]
        self.tenant = cfg.get("TENANT", "")
        self.company = cfg.get("COMPANY", "")
        self.alias = {"--working": cfg.get("WORKING"), "--completed": cfg.get("COMPLETED")}
        raw_timeout = cfg.get("RESPONSE_TIME") or "10"
        try:
            self.timeout = int(raw_timeout)
        except ValueError:
            sys.exit(f"{CONF} 의 RESPONSE_TIME= 값이 숫자가 아닙니다: {raw_timeout}")
        self.pid = self._project_id()
        self._me_cache = None

    def _api(self, path, method="GET", body=None, **params):
        url = BASE + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers={
            "Authorization": f"dooray-api {self.token}",
            "Content-Type": "application/json",
        })
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            sys.exit(f"Dooray API 오류 (HTTP {e.code}): {e.read().decode(errors='replace')[:300]}")
        except urllib.error.URLError as e:
            sys.exit(f"Dooray 접속 실패: {e.reason}")
        except TimeoutError:
            sys.exit(f"Dooray 응답이 {self.timeout}초 안에 오지 않았습니다 (Dooray/Config.md 의 RESPONSE_TIME= 로 조정 가능).")

    def _project_id(self):
        """REPOSITORY 코드와 일치하는 프로젝트를 찾을 때까지(또는 전체 소진할 때까지) 페이지네이션한다."""
        page, fetched = 0, 0
        while True:
            res = self._api("/project/v1/projects", member="me", page=page, size=100)
            for p in res["result"]:
                if p.get("code") == self.repo:
                    return p["id"]
            fetched += len(res["result"])
            if not res["result"] or fetched >= res.get("totalCount", fetched):
                break
            page += 1
        sys.exit(f"접근 가능한 프로젝트 중 '{self.repo}' 가 없습니다. Dooray/Config.md 의 REPOSITORY= 를 확인하세요.")

    def find_post_id(self, number):
        """업무번호 → postId만. 상세(제목/본문 등)가 필요 없는 호출자는 이걸로 끝낸다."""
        found = self._api(f"/project/v1/projects/{self.pid}/posts", postNumber=number)["result"]
        if not found:
            sys.exit(f"업무 #{number} 이(가) '{self.repo}' 프로젝트에 없습니다.")
        return found[0]["id"]

    def post_detail(self, post_id):
        return self._api(f"/project/v1/projects/{self.pid}/posts/{post_id}")["result"]

    def workflows(self):
        return self._api(f"/project/v1/projects/{self.pid}/workflows")["result"]

    def tag_names(self):
        """프로젝트 태그 목록 → {tagId: 이름}. API 1번으로 전체 매핑을 얻는다."""
        return {t["id"]: t["name"]
                for t in self._api(f"/project/v1/projects/{self.pid}/tags")["result"]}

    def list_open_posts(self, limit):
        """내가 담당자인, 완료(closed)되지 않은 업무를 최신 등록순으로 최대 limit개.
        서버에서 담당자 필터·워크플로우 클래스 필터·정렬을 다 해주므로 API 호출 1번으로 끝난다."""
        return self._api(f"/project/v1/projects/{self.pid}/posts",
                          toMemberIds=self.my_member_id(),
                          postWorkflowClasses=CLOSED_EXCLUDED_CLASSES,
                          order="-createdAt", size=limit)["result"]

    def comments(self, post_id, limit=None):
        """댓글 목록. limit 없으면 전체를 페이지네이션으로 다 가져온다(시간순).
        limit 있으면 최신순으로 필요한 페이지까지 가져온 뒤 지정 개수만 시간순으로 뒤집는다."""
        if limit:
            logs, page = [], 0
            while len(logs) < limit:
                res = self._api(f"/project/v1/projects/{self.pid}/posts/{post_id}/logs",
                                order="-createdAt", page=page, size=100)
                logs.extend(res["result"])
                if not res["result"] or len(logs) >= res.get("totalCount", len(logs)):
                    break
                page += 1
            return list(reversed(logs[:limit]))
        logs, page = [], 0
        while True:
            res = self._api(f"/project/v1/projects/{self.pid}/posts/{post_id}/logs", page=page, size=100)
            logs.extend(res["result"])
            if not res["result"] or len(logs) >= res.get("totalCount", len(logs)):
                break
            page += 1
        return logs

    def files(self, post_id):
        return self._api(f"/project/v1/projects/{self.pid}/posts/{post_id}/files")["result"]

    def download_file(self, post_id, file_id):
        """첨부파일 원본 바이트. Dooray는 307 리다이렉트로 다른 호스트에 저장하지만
        urllib이 Authorization 헤더를 유지한 채 자동으로 따라간다(실측 확인)."""
        url = f"{BASE}/project/v1/projects/{self.pid}/posts/{post_id}/files/{file_id}?media=raw"
        req = urllib.request.Request(url, headers={"Authorization": f"dooray-api {self.token}"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            sys.exit(f"파일 다운로드 실패 (HTTP {e.code})")
        except urllib.error.URLError as e:
            sys.exit(f"Dooray 접속 실패: {e.reason}")
        except TimeoutError:
            sys.exit(f"파일 다운로드가 {self.timeout}초 안에 끝나지 않았습니다 (Dooray/Config.md 의 RESPONSE_TIME= 로 조정 가능).")

    def add_comment(self, post_id, text):
        return self._api(f"/project/v1/projects/{self.pid}/posts/{post_id}/logs", "POST",
                         {"body": {"mimeType": "text/x-markdown", "content": text}})

    def me(self):
        if self._me_cache is None:
            self._me_cache = self._api("/common/v1/members/me")["result"]
        return self._me_cache

    def org_id(self):
        return self.me()["defaultOrganization"]["id"]

    def my_member_id(self):
        return self.me()["id"]

    def search_members(self, name):
        return self._api("/common/v1/members", name=name)["result"]

    def resolve_mention(self, name):
        """이름 → (memberId, 표시이름). COMPANY 설정 시 이메일 도메인으로 한정. 모호하면 목록과 함께 종료."""
        hits = self.search_members(name)
        if self.company:
            hits = [m for m in hits
                    if (m.get("externalEmailAddress") or "").split("@")[-1].split(".")[0].lower() == self.company.lower()]
        if not hits:
            sys.exit(f"멘션할 사람 '{name}' 을(를) 찾을 수 없습니다" +
                     (f" (COMPANY={self.company} 한정)" if self.company else "") + ".")
        if len(hits) > 1:
            lines = "\n".join(f"  {i}. {m['name']} ({m.get('externalEmailAddress', '?')})"
                              for i, m in enumerate(hits, 1))
            sys.exit(f"'{name}' 으로 {len(hits)}명이 검색됩니다:\n{lines}\n"
                     f"Dooray/Config.md 의 COMPANY= 로 회사를 한정하거나, 다른 이름으로 다시 시도하세요.")
        return hits[0]["id"], hits[0]["name"]

    def apply_mentions(self, text):
        """본문 안의 @이름(한글) 토큰을 실제 알림이 가는 멘션 markdown으로 치환.
        서로 다른 이름은 중복 제거 후 병렬로 검색한다."""
        names = set(re.findall(r"@([가-힣]+)", text))
        if not names:
            return text
        org_id = self.org_id()
        with ThreadPoolExecutor() as ex:
            futures = {name: ex.submit(self.resolve_mention, name) for name in names}
            resolved = {name: fut.result() for name, fut in futures.items()}

        def repl(m):
            member_id, display = resolved[m.group(1)]
            return f'[@{display}](dooray://{org_id}/members/{member_id} "member")'

        return re.sub(r"@([가-힣]+)", repl, text)

    def member_names(self, ids):
        """organizationMemberId 목록 → {id: 이름}. 서로 독립적인 조회라 병렬로 부른다.
        실패한 개별 조회는 ID 그대로 표시."""
        ids = set(ids)
        names = {}
        if not ids:
            return names
        with ThreadPoolExecutor() as ex:
            futures = {ex.submit(self._api, f"/common/v1/members/{mid}"): mid for mid in ids}
            for fut, mid in futures.items():
                try:
                    names[mid] = fut.result()["result"]["name"]
                except SystemExit:
                    names[mid] = mid
        return names

    def task_url(self, post_id):
        return f"https://{self.tenant}.dooray.com/task/to/{post_id}" if self.tenant else None

    def set_workflow(self, post_id, workflow_id):
        return self._api(f"/project/v1/projects/{self.pid}/posts/{post_id}/set-workflow", "POST",
                         {"workflowId": workflow_id})

    def resolve_workflow(self, name):
        """상태명(또는 --working/--completed 별칭) → workflow dict. 공백/대소문자 관대 비교."""
        if name in self.alias:
            if not self.alias[name]:
                sys.exit(f"Dooray/Config.md 에 {'WORKING' if name == '--working' else 'COMPLETED'}= 설정이 없습니다.")
            name = self.alias[name]
        norm = lambda s: s.replace(" ", "").lower()
        flows = self.workflows()
        for w in flows:
            if norm(w["name"]) == norm(name):
                return w
        names = ", ".join(w["name"] for w in flows)
        sys.exit(f"상태 '{name}' 이(가) 없습니다. 가능한 상태: {names}")


# ul/ol/table은 넣지 않는다. 자식인 li/tr이 이미 줄을 바꾸므로 빈 줄만 늘어난다.
BLOCK_TAGS = {"p", "div", "br", "li", "tr", "hr", "blockquote", "pre",
              "h1", "h2", "h3", "h4", "h5", "h6", "section", "article"}


class _HtmlToText(HTMLParser):
    """Dooray 위지윅 본문(text/html)을 터미널에서 읽을 수 있는 평문으로 바꾼다."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.skip = 0
        self.href = None
        self.href_at = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        elif tag in BLOCK_TAGS:
            self.out.append("\n")
            if tag == "li":
                self.out.append("- ")
        elif tag in ("td", "th"):
            self.out.append("\t")
        elif tag == "a":
            self.href = dict(attrs).get("href")
            self.href_at = len(self.out)
        elif tag == "img":
            alt = (dict(attrs).get("alt") or "").strip()
            self.out.append(f"[이미지: {alt}]" if alt else "[이미지]")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip = max(0, self.skip - 1)
        elif tag == "a":
            if self.href and self.href != "".join(self.out[self.href_at:]).strip():
                self.out.append(f" ({self.href})")
            self.href = None

    def handle_data(self, data):
        if not self.skip:
            self.out.append(data)


def html_to_text(src):
    parser = _HtmlToText()
    parser.feed(src)
    parser.close()
    text = re.sub(r"[ \xa0]+", " ", "".join(parser.out))
    text = "\n".join(line.strip() for line in text.splitlines())
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def body_text(body):
    body = body or {}
    content = body.get("content") or ""
    if "html" in (body.get("mimeType") or ""):
        return html_to_text(content)
    return content


def fmt_post(p, tags_line=""):
    wf = (p.get("workflow") or {}).get("name", "?")
    body = body_text(p.get("body")).strip()
    head = f"#{p['number']} {p['subject']}\n상태: {wf}"
    if tags_line:
        head += f"\n{tags_line}"
    return f"{head}\n\n{body or '(본문 없음)'}"


def fmt_tags(p, tag_map):
    ids = [t.get("id") for t in (p.get("tags") or [])]
    if not ids:
        return ""
    names = [tag_map.get(i, i) for i in ids]
    return "태그: " + ", ".join(names)


def fmt_list(posts):
    if not posts:
        return "담당자로 지정된, 완료되지 않은 업무가 없습니다."
    lines = []
    for p in posts:
        wf = (p.get("workflow") or {}).get("name", "?")
        writer = (((p.get("users") or {}).get("from") or {}).get("member") or {}).get("name", "?")
        lines.append(f"{p['project']['code']} / {p['number']} - {wf} - {p['subject']} (작성자: {writer})")
    return "\n".join(lines)


def fmt_comments(logs, names):
    lines = []
    for c in logs:
        mid = ((c.get("creator") or {}).get("member") or {}).get("organizationMemberId")
        when = (c.get("createdAt") or "")[:16].replace("T", " ")
        text = body_text(c.get("body")).strip()
        lines.append(f"[{when}] {names.get(mid, '?')}: {text}")
    return "\n".join(lines) or "(댓글 없음)"


def fmt_files(files):
    if not files:
        return ""
    def size(n):
        return f"{n/1024:.1f}KB" if n >= 1024 else f"{n}B"
    if len(files) == 1:
        f = files[0]
        return f"\n\n첨부파일: {f['name']} ({size(f['size'])}) — 다운로드할까요?"
    lines = [f"  {i}. {f['name']} ({size(f['size'])})" for i, f in enumerate(files, 1)]
    return (f"\n\n첨부파일 ({len(files)}개):\n" + "\n".join(lines) +
            "\n\n다운로드할까요? (번호 또는 all)")


def fmt_link(url):
    return f"\n\n이력 주소: {url}" if url else "\n\n(이력 주소 확인 불가 — Dooray/Config.md 에 TENANT= 설정 없음)"


def creator_ids(logs):
    return [mid for c in logs
            if (mid := ((c.get("creator") or {}).get("member") or {}).get("organizationMemberId"))]


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    cmd, rest = args[0], args[1:]
    if cmd not in KNOWN_CMDS:
        sys.exit(f"알 수 없는 명령: {cmd}\n{__doc__}")
    if cmd == "help":
        print(__doc__)
        return
    if cmd == "init":
        if rest:
            sys.exit(f"init 명령에는 인자가 없습니다. 예: {PYTHON_CMD} Dooray/dooray.py init")
        init_command()
        return
    if cmd == "list":
        if not rest or not rest[0].isdigit():
            sys.exit("조회할 개수가 필요합니다. 예: dooray list 5")
    elif cmd != "workflows" and not rest:
        sys.exit("업무번호가 필요합니다. 예: dooray read 1")
    if cmd == "full" and len(rest) > 1:
        if len(rest) > 2 or not rest[1].isdigit() or int(rest[1]) <= 0:
            sys.exit("댓글 개수는 양의 정수여야 합니다. 예: dooray full 1 10")
    d = Dooray()

    if cmd == "workflows":
        for i, w in enumerate(d.workflows(), 1):
            print(f"{i}. {w['name']} ({w['class']})")
        return
    if cmd == "list":
        print(fmt_list(d.list_open_posts(int(rest[0]))))
        return
    number = rest[0]

    if cmd == "read":
        post_id = d.find_post_id(number)
        with ThreadPoolExecutor() as ex:
            detail_f = ex.submit(d.post_detail, post_id)
            files_f = ex.submit(d.files, post_id)
            p, files = detail_f.result(), files_f.result()
        print(fmt_post(p) + fmt_files(files) + fmt_link(d.task_url(post_id)))
    elif cmd == "full":
        limit = int(rest[1]) if len(rest) > 1 else None
        post_id = d.find_post_id(number)
        with ThreadPoolExecutor() as ex:
            detail_f = ex.submit(d.post_detail, post_id)
            files_f = ex.submit(d.files, post_id)
            comments_f = ex.submit(d.comments, post_id, limit)
            tags_f = ex.submit(d.tag_names)
            p, files, logs, tag_map = (detail_f.result(), files_f.result(),
                                       comments_f.result(), tags_f.result())
        print(fmt_post(p, fmt_tags(p, tag_map)) + fmt_files(files) + fmt_link(d.task_url(post_id)))
        print("\n--- 댓글 ---")
        print(fmt_comments(logs, d.member_names(creator_ids(logs))))
    elif cmd == "link":
        if not d.tenant:
            sys.exit("Dooray/Config.md 에 TENANT= 설정이 필요합니다.")
        print(d.task_url(d.find_post_id(number)))
    elif cmd == "status":
        p = d.post_detail(d.find_post_id(number))
        print(f"#{p['number']} {p['subject']}\n상태: {(p.get('workflow') or {}).get('name', '?')}")
    elif cmd == "setstatus":
        if len(rest) < 2:
            sys.exit("상태명이 필요합니다. 예: dooray setstatus 1 \"DEV 진행중\"")
        with ThreadPoolExecutor() as ex:
            post_id_f = ex.submit(d.find_post_id, number)
            workflow_f = ex.submit(d.resolve_workflow, " ".join(rest[1:]))
            post_id, w = post_id_f.result(), workflow_f.result()
        d.set_workflow(post_id, w["id"])
        print(f"#{number} 상태 변경 완료: {w['name']}")
    elif cmd == "comment":
        if len(rest) < 2:
            sys.exit("댓글 내용이 필요합니다. 예: dooray comment 1 \"내용\" 또는 --file <경로>")
        if rest[1] == "--file":
            if len(rest) < 3:
                sys.exit("--file 뒤에 파일 경로가 필요합니다.")
            try:
                raw_text = Path(rest[2]).read_text(encoding="utf-8").rstrip("\n")
            except OSError as e:
                sys.exit(f"파일을 읽을 수 없습니다: {rest[2]} ({e.strerror or e})")
        else:
            raw_text = " ".join(rest[1:])
        with ThreadPoolExecutor() as ex:
            post_id_f = ex.submit(d.find_post_id, number)
            text_f = ex.submit(d.apply_mentions, raw_text)
            post_id, text = post_id_f.result(), text_f.result()
        d.add_comment(post_id, text)
        print(f"#{number} 댓글 등록 완료")
    elif cmd == "download":
        post_id = d.find_post_id(number)
        files = d.files(post_id)
        if not files:
            sys.exit(f"업무 #{number} 에 첨부파일이 없습니다.")
        target = rest[1] if len(rest) > 1 else None
        if target and target.lower() == "all":
            picks = files
        elif target:
            if target.isdigit() and 1 <= int(target) <= len(files):
                picks = [files[int(target) - 1]]
            else:
                matched = [f for f in files if f["name"] == target]
                if not matched:
                    names = ", ".join(f["name"] for f in files)
                    sys.exit(f"'{target}' 파일을 찾을 수 없습니다. 첨부파일: {names}")
                picks = matched
        elif len(files) == 1:
            picks = files
        else:
            lines = "\n".join(f"  {i}. {f['name']}" for i, f in enumerate(files, 1))
            sys.exit(f"첨부파일이 여러 개입니다. 파일명·번호 또는 all 을 지정하세요:\n{lines}")
        out_dir = Path(__file__).parent / "report" / str(number) / "download"
        out_dir.mkdir(parents=True, exist_ok=True)
        with ThreadPoolExecutor() as ex:
            futures = {ex.submit(d.download_file, post_id, f["id"]): f for f in picks}
            for fut, f in futures.items():
                out_path = out_dir / Path(f["name"]).name
                out_path.write_bytes(fut.result())
                print(f"다운로드 완료: {out_path}")


if __name__ == "__main__":
    main()
