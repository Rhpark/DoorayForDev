#!/usr/bin/env python3
"""Dooray 업무 연동 코어 스크립트.

설정: Dooray/Config.md (KEY=VALUE 형식, 이 스크립트와 같은 폴더)
  DOORAY_API_TOKEN, REPOSITORY, TENANT, COMPANY(선택, @멘션 검색을 이 회사 이메일 도메인으로 한정)
  RESPONSE_TIME(선택, API 응답 대기 초. 기본 10)

최초 초기화 (저장소 루트에서 실행):
  Windows:      python Dooray/dooray.py init
  macOS/Linux:  python3 Dooray/dooray.py init

초기화 후 사용법 (저장소 루트에서 실행):
  dooray read <업무번호>              제목 + 상태 + 본문
  dooray full <업무번호> [개수]        read + 태그 + 댓글 이력 + 파일 목록 (개수 생략 시 전체, 지정 시 최신 N개)
  dooray link <업무번호>              업무 웹 주소
  dooray status <업무번호>            현재 상태
  dooray workflows                    이 프로젝트의 상태 목록
  dooray setstatus <업무번호> <상태명>  상태 변경
  dooray comment <업무번호> <내용>     댓글 등록 (--file <경로> 로 파일에서 읽기 가능 — 셸 이스케이프 없이 안전)
  dooray download <업무번호> [파일명|번호|all]  첨부·본문·댓글 이미지 저장 (생략 시 전체).
                                      Dooray/task/report/<업무번호>/download/<파일ID>_<파일명> 으로 저장
  dooray list <개수>                  완료되지 않은 업무를 최신 등록순으로 N개
  dooray wiki-list [경로]             프로젝트 위키 페이지를 전체 경로로 (경로를 주면 그 아래만)
  dooray wiki-read [경로][>]          위키 페이지 본문 + 댓글 + 파일 목록. 끝에 > 를 붙이거나 생략하면 하위 페이지 목록
  dooray wiki-download <경로> [파일명|번호|all]  위키 첨부·이미지 저장 (생략 시 전체).
                                      Dooray/wiki/<위키이름>/<제목>/.../download/<파일ID>_<파일명> 으로 저장
  dooray wiki-write <경로> <내용>      있으면 '## 날짜 시:분' 헤더로 이어쓰기, 없으면 부모 아래 생성
                                      (--file <경로> 로 파일에서 읽기, --dry-run 은 판단만 출력)
                                      내용 속 로컬 ![이미지](경로)·[파일](경로)는 올리고 Dooray 참조로 바꿈
                                      (공백 있는 경로는 (<경로>)), --move-draft 는 성공 후 초안을 페이지 폴더로 이동(로컬 경로는 새 위치 기준으로 맞춤)
  위키 경로는 '회의록 > LG ICON25 프로젝트'처럼 > 로 구분한다. 공백이 있으면 따옴표로 감싼다.
"""
import json
import mimetypes
import os
import re
import shutil
import stat
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path

BASE = "https://api.dooray.com"
CONF = Path(__file__).parent / "Config.md"
TASK_DIR = Path(__file__).parent / "task" / "report"  # <업무번호>/REPORT.md 와 download/
WIKI_DIR = Path(__file__).parent / "wiki"  # <위키이름>/<제목>/.../download/
KNOWN_CMDS = {"init", "help", "read", "full", "link", "status", "workflows", "setstatus", "comment", "download", "list",
              "wiki-list", "wiki-read", "wiki-write", "wiki-download"}
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
        raw_timeout = cfg.get("RESPONSE_TIME") or "10"
        try:
            self.timeout = int(raw_timeout)
        except ValueError:
            sys.exit(f"{CONF} 의 RESPONSE_TIME= 값이 숫자가 아닙니다: {raw_timeout}")
        self.pid = self._project_id()
        self._me_cache = None
        self._wiki_cache = None

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
        return self._raw(f"/project/v1/projects/{self.pid}/posts/{post_id}/files/{file_id}")

    def wiki_download_file(self, page_id, file_id):
        """위키 첨부·이미지 원본 바이트. attachFileId가 아니라 id로 받는다(attachFileId는 404, 실측)."""
        return self._raw(f"/wiki/v1/wikis/{self.wiki()['id']}/pages/{page_id}/files/{file_id}")

    def _raw(self, path):
        """파일 원본 바이트(?media=raw). Dooray는 307 리다이렉트로 다른 호스트에 저장하지만
        urllib이 Authorization 헤더를 유지한 채 자동으로 따라간다(실측 확인)."""
        url = f"{BASE}{path}?media=raw"
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

    def upload_wiki_file(self, page_id, path, ftype):
        """로컬 파일을 위키 페이지에 올리고 attachFileId를 돌려준다. ftype은 inline_image 또는 general.
        형식은 확장자로 추정한다 — octet-stream으로 올리면 클릭 시 숫자 이름으로 다운로드된다(실측)."""
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        res = self._upload(f"/wiki/v1/wikis/{self.wiki()['id']}/pages/{page_id}/files",
                           path.name, path.read_bytes(), ftype, mime)
        return res["result"]["attachFileId"]

    def _upload(self, path, name, data, ftype, mime):
        """파일 업로드(multipart). type 필드를 file보다 먼저 보낸다(서버가 순서에 의존, 서드파티 근거).
        API 서버가 307로 파일 서버를 가리키는데 urllib은 POST의 307을 따라가지 않으므로,
        trusted_file_host를 통과한 주소로만 같은 요청을 다시 보낸다(실측: file-api.dooray.com)."""
        boundary = uuid.uuid4().hex
        filename = name.replace('"', "_")
        body = (f'--{boundary}\r\nContent-Disposition: form-data; name="type"\r\n\r\n{ftype}\r\n'
                f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{filename}"\r\n'
                f"Content-Type: {mime}\r\n\r\n").encode("utf-8") + data + f"\r\n--{boundary}--\r\n".encode()
        headers = {"Authorization": f"dooray-api {self.token}",
                   "Content-Type": f"multipart/form-data; boundary={boundary}"}
        url = BASE + path
        for _ in range(3):
            req = urllib.request.Request(url, data=body, method="POST", headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    return json.loads(r.read().decode())
            except urllib.error.HTTPError as e:
                if e.code in (307, 308):
                    url = e.headers.get("Location")
                    if not trusted_file_host(url):
                        host = urllib.parse.urlparse(url or "").netloc or "(없음)"
                        sys.exit(f"업로드가 Dooray가 아닌 주소({host})로 리다이렉트되어 중단했습니다.")
                    continue
                sys.exit(f"파일 업로드 실패 (HTTP {e.code}): {e.read().decode(errors='replace')[:300]}")
            except urllib.error.URLError as e:
                sys.exit(f"Dooray 접속 실패: {e.reason}")
            except TimeoutError:
                sys.exit(f"파일 업로드가 {self.timeout}초 안에 끝나지 않았습니다 (Dooray/Config.md 의 RESPONSE_TIME= 로 조정 가능).")
        sys.exit("업로드 리다이렉트가 반복되어 중단했습니다.")

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
        """상태명 → workflow dict. 공백/대소문자 관대 비교."""
        norm = lambda s: s.replace(" ", "").lower()
        flows = self.workflows()
        for w in flows:
            if norm(w["name"]) == norm(name):
                return w
        names = ", ".join(w["name"] for w in flows)
        sys.exit(f"상태 '{name}' 이(가) 없습니다. 가능한 상태: {names}")

    def wiki(self):
        """REPOSITORY 프로젝트에 연결된 위키(project.id 일치). 위키 목록을 찾을 때까지 페이지네이션한다."""
        if self._wiki_cache is None:
            page, fetched = 0, 0
            while self._wiki_cache is None:
                res = self._api("/wiki/v1/wikis", page=page, size=100)
                self._wiki_cache = next((w for w in res["result"]
                                         if str((w.get("project") or {}).get("id")) == str(self.pid)), None)
                fetched += len(res["result"])
                if self._wiki_cache is None and (not res["result"] or fetched >= res.get("totalCount", fetched)):
                    sys.exit(f"'{self.repo}' 프로젝트에 연결된 위키가 없습니다.")
                page += 1
        return self._wiki_cache

    def wiki_walk(self, parts, page=None, i=0):
        """Home에서 parts를 따라간다. (마지막으로 찾은 페이지, 소비한 조각 수, 멈춘 단계의 하위 목록).

        각 단계에서 남은 조각을 가장 길게 붙인 것부터 제목과 맞춘다(제목 우선). 그래서
        'HD Map > SUMO Network'처럼 제목에 > 가 있는 페이지가 같은 글자의 중첩 경로보다 먼저 잡힌다.
        제목 쪽이 막다른 길이면 짧게 나눈 쪽을 시도하고, 끝까지 못 가면 가장 깊이 간 결과(같으면 제목 쪽)를 돌려준다.
        찾은 페이지의 "path"에는 Home 아래 실제 제목 목록이 담긴다(입력 조각이 아니라 제목 기준).
        """
        page = page or {"id": self.wiki()["home"]["pageId"], "subject": "Home", "path": []}
        if i == len(parts):
            return page, i, None
        kids = self.wiki_children(page["id"])
        where = " > ".join([self.wiki()["name"], *parts[:i]])
        best = (page, i, kids)
        for j in range(len(parts), i, -1):
            child = match_child(kids, " > ".join(parts[i:j]), where)
            if child:
                found = self.wiki_walk(parts, {**child, "path": page["path"] + [child["subject"]]}, j)
                if found[1] == len(parts):
                    return found
                if found[1] > best[1]:
                    best = found
        return best

    def wiki_find(self, parts):
        """경로의 페이지 {id, subject}. 없거나 같은 제목이 여럿이면 그 단계의 하위 목록과 함께 종료."""
        page, i, kids = self.wiki_walk(parts)
        if i < len(parts):
            sys.exit(wiki_missing(self.wiki()["name"], parts, i, kids))
        return page

    def wiki_children(self, page_id):
        """바로 아래 한 깊이의 하위 페이지(API 순서). totalCount까지 페이지네이션한다."""
        pages, page = [], 0
        while True:
            res = self._api(f"/wiki/v1/wikis/{self.wiki()['id']}/pages", parentPageId=page_id, page=page, size=100)
            pages.extend(res["result"])
            if not res["result"] or len(pages) >= res.get("totalCount", len(pages)):
                return pages
            page += 1

    def wiki_url(self, page_id):
        """위키 페이지 웹 주소. API가 주지 않아 만든다(형식은 실제 브라우저로 확인)."""
        return f"https://{self.tenant}.dooray.com/wiki/{self.wiki()['id']}/{page_id}" if self.tenant else None

    def wiki_page(self, page_id):
        return self._api(f"/wiki/v1/wikis/{self.wiki()['id']}/pages/{page_id}")["result"]

    def wiki_comments(self, page_id):
        """페이지 댓글 전체를 시간순으로. API는 최신순으로 주므로 createdAt으로 다시 정렬한다."""
        logs, page = [], 0
        while True:
            res = self._api(f"/wiki/v1/wikis/{self.wiki()['id']}/pages/{page_id}/comments", page=page, size=100)
            logs.extend(res["result"])
            if not res["result"] or len(logs) >= res.get("totalCount", len(logs)):
                return sorted(logs, key=lambda c: c.get("createdAt") or "")
            page += 1

    def create_wiki_page(self, parent_id, subject, text):
        return self._api(f"/wiki/v1/wikis/{self.wiki()['id']}/pages", "POST",
                         {"parentPageId": parent_id, "subject": subject,
                          "body": {"mimeType": "text/x-markdown", "content": text}})

    def set_wiki_content(self, page_id, text):
        return self._api(f"/wiki/v1/wikis/{self.wiki()['id']}/pages/{page_id}/content", "PUT",
                         {"body": {"mimeType": "text/x-markdown", "content": text}})

    def wiki_tree(self, page_id, path):
        """page_id 아래 모든 페이지의 경로(제목 목록)를 전위 순회 순서로. 형제 하위 트리는 병렬로 조회한다."""
        # ponytail: 깊이마다 스레드 풀을 새로 만든다. 페이지가 수백 개로 늘면 공유 풀로 바꾼다.
        kids = self.wiki_children(page_id)
        with ThreadPoolExecutor() as ex:
            subtrees = list(ex.map(lambda k: self.wiki_tree(k["id"], path + [k["subject"]]), kids))
        paths = []
        for kid, sub in zip(kids, subtrees):
            paths.append(path + [kid["subject"]])
            paths.extend(sub)
        return paths


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
        text = ((c.get("body") or {}).get("content") or "").strip()
        lines.append(f"[{when}] {names.get(mid, '?')}: {text}")
    return "\n".join(lines) or "(댓글 없음)"


INLINE_IMG_TAG = re.compile(r"<img\b[^>]*>", re.I)
INLINE_IMG_SRC = re.compile(r'src\s*=\s*"/files/(\d+)"', re.I)
INLINE_IMG_ALT = re.compile(r'alt\s*=\s*"([^"]*)"', re.I)
# ★본문 문법은 두 가지다★ mimeType은 셋 다 text/x-markdown인데도 #53·#57은 본문에 HTML
# <img> 태그가 그대로 박혀 있고 #60은 마크다운 ![alt](/files/id)였다(실측). mimeType으로는
# 구분할 수 없으니 두 형태를 모두 훑는다 — 한쪽만 알면 나머지 이력에서 조용히 0건이 된다.
INLINE_IMG_MD = re.compile(r"!\[([^\]]*)\]\(/files/(\d+)\)")
# 두 문법을 본문 등장 순서대로 한 번에 훑는 스캐너. 문법별로 따로 훑어 이어 붙이면
# 섞인 본문에서 순서가 뒤바뀐다(호출부가 번호로 파일을 고르므로 순서가 곧 계약이다).
INLINE_IMG_ANY = re.compile(f"{INLINE_IMG_TAG.pattern}|{INLINE_IMG_MD.pattern}", re.I)
UNSAFE_NAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def inline_files(body):
    """본문에 붙여넣은 인라인 이미지 목록을 첨부 목록과 같은 모양으로 돌려줍니다.

    ★Dooray는 인라인 이미지를 `/posts/{id}/files` 목록에 넣지 않는다★ 실측으로 업무 #53·#57·#60 모두
    본문에 이미지가 있는데 목록 API는 빈 배열을 반환했다. 그래서 목록만 보고
    "첨부파일 없음"으로 판단하면 실제로는 받을 수 있는 이미지를 놓친다.

    ★HTML `<img src="/files/...">`와 마크다운 `![alt](/files/...)` 둘 다 인식한다★ 이미지 표기는
    작성자 입력 방식에 따라 이력마다 다르다(#53·#57은 HTML 태그, #60은 마크다운). `mimeType`은
    셋 다 `text/x-markdown`이라 표기 형태를 알려주지 않으므로 둘 다 훑어야 한다.

    `Dooray.download_file(post_id, file_id)`는 목록을 거치지 않고 **id만으로** 동작하므로,
    본문에서 id를 뽑아 `{"id", "name"}` 항목으로 만들면 첨부파일과 동일한 경로로 내려받을 수 있다.

    :param body: 업무 본문 문자열(`post_detail(...)["body"]["content"]`). None/빈 문자열 허용.
    :returns: `[{"id": str, "name": str, "inline": True}, ...]`. 같은 id는 한 번만 담고
              본문 등장 순서를 유지한다. 같은 이미지를 두 문법으로 참조해도 한 번만 담는다.
    """
    found, seen = [], set()
    for match in INLINE_IMG_ANY.finditer(body or ""):
        chunk = match.group(0)
        md = INLINE_IMG_MD.match(chunk)
        if md:
            # 마크다운은 대괄호 안이 곧 alt(=원본 파일명)이고 괄호 안이 id다.
            name, file_id = md.group(1).strip(), md.group(2)
        else:
            src = INLINE_IMG_SRC.search(chunk)
            if not src:
                continue  # 외부 호스트 이미지 등 이 API로 받을 수 없는 <img>.
            file_id = src.group(1)
            alt = INLINE_IMG_ALT.search(chunk)
            name = alt.group(1).strip() if alt else ""
        if file_id in seen:
            continue
        seen.add(file_id)
        # alt에 원본 파일명이 들어 있다(예: Inline-image-2026-08-18 15.43.42.133.png).
        # 없으면 id로 이름을 만든다. 파일명에 쓸 수 없는 문자는 치환한다(Windows).
        name = name or f"inline-{file_id}.png"
        found.append({"id": file_id, "name": UNSAFE_NAME_CHARS.sub("_", name), "inline": True})
    return found


def collect_files(files, body, logs):
    """첨부→본문→댓글 순으로 파일 ID를 병합하고 모든 발견 출처를 보존한다.

    files는 첨부 API 목록, body는 업무 본문, logs는 조회한 댓글 목록이다.
    입력을 수정하지 않는다. 반환 항목의 sources는 본문 또는 댓글 ID·시각을 식별한다.
    """
    merged = {}

    def add(items, source):
        for item in items:
            file_id = str(item["id"])
            if file_id not in merged:
                merged[file_id] = {**item, "id": file_id, "sources": []}
            if source not in merged[file_id]["sources"]:
                merged[file_id]["sources"].append(source)

    add(files, "첨부 목록")
    add(inline_files(body), "본문")
    for index, log in enumerate(logs, 1):
        source = f"댓글 {log.get('id') or index} ({log.get('createdAt') or '시각 미상'})"
        add(inline_files((log.get("body") or {}).get("content")), source)
    return list(merged.values())


# 마크다운 이미지·링크 ![alt](대상) / [글](대상). 대상은 <공백 있는 경로> 또는 공백 없는 경로, 뒤에 "제목"이 올 수 있다.
# 괄호 없는 경로 안의 괄호는 한 단계 짝까지 허용한다(예: log(1).txt). 제목("…")은 바꿀 때도 남긴다.
MD_LINK = re.compile(r'(!?)\[([^\]]*)\]\((<[^>\n]+>|(?:[^()\s]|\([^()\s]*\))+)(\s+"[^"]*")?\)')


def local_target(target, base):
    """참조 대상이 로컬 파일 경로면 base 기준 절대 경로, URL·절대 경로(/…)·앵커(#…)면 None."""
    target = target[1:-1] if target.startswith("<") else target
    if re.match(r"[A-Za-z]:[\\/]", target):
        return Path(target).resolve()  # Windows 절대 경로(C:\…)는 URL 스킴이 아니라 로컬 파일이다.
    if not target or target.startswith(("/", "#")) or re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", target):
        return None
    return (base / urllib.parse.unquote(target)).resolve()


def local_files(text, base):
    """내용 속 로컬 참조를 등장 순서대로 {경로: 'inline_image'|'general'}. 이미지 문법이면 inline_image다.
    같은 파일은 한 번만 담는다(처음 나온 문법을 따른다)."""
    found = {}
    for m in MD_LINK.finditer(text):
        path = local_target(m.group(3), base)
        if path is not None and path not in found:
            found[path] = "inline_image" if m.group(1) else "general"
    return found


def rewrite_local_links(text, base, refs):
    """로컬 참조를 refs({경로: Dooray 주소})로 바꾼다. 그 밖의 링크와 제목 표기는 그대로 둔다."""
    def repl(m):
        path = local_target(m.group(3), base)
        return f"{m.group(1)}[{m.group(2)}]({refs[path]}{m.group(4) or ''})" if path in refs else m.group(0)
    return MD_LINK.sub(repl, text)


def kind_label(ftype):
    return "이미지" if ftype == "inline_image" else "첨부"


def wiki_folder(wiki_name, titles):
    """위키 트리 모양의 로컬 폴더: WIKI_DIR/<위키이름>/<제목>/... (폴더 이름에 못 쓰는 문자는 _)."""
    return WIKI_DIR.joinpath(*(safe_name(t) for t in [wiki_name, *titles]))


def move_into(path, folder):
    """파일을 folder로 옮기고 새 경로를 돌려준다. 같은 이름이 있으면 이름_2, 이름_3 … 으로 피한다."""
    folder.mkdir(parents=True, exist_ok=True)
    dest, n = folder / path.name, 2
    if dest.resolve() == path.resolve():
        return dest
    while dest.exists():
        dest, n = folder / f"{path.stem}_{n}{path.suffix}", n + 1
    shutil.move(str(path), str(dest))
    return dest


def archive_draft(draft, folder):
    """초안을 folder로 옮기고, 안의 로컬 이미지·파일 상대 경로를 새 위치 기준으로 다시 맞춘다.
    그대로 두면 더 깊은 폴더에서 같은 경로가 엉뚱한 곳을 가리켜 미리보기와 재업로드가 깨진다."""
    old_base = draft.resolve().parent
    dest = move_into(draft, folder)
    with open(dest, encoding="utf-8", newline="") as f:  # 줄바꿈 형식을 그대로 둔다
        text = f.read()
    refs = {}
    for path in local_files(text, old_base):
        try:
            rel = os.path.relpath(path, dest.resolve().parent).replace("\\", "/")
        except ValueError:  # 드라이브가 다르면 상대 경로를 만들 수 없어 절대 경로로 둔다.
            rel = str(path)
        refs[path] = f"<{rel}>" if re.search(r"[\s()]", rel) else rel
    if refs:
        with open(dest, "w", encoding="utf-8", newline="") as f:
            f.write(rewrite_local_links(text, old_base, refs))
    return dest


def trusted_file_host(url):
    """업로드 307의 Location으로 토큰을 다시 보내도 되는지. https이고 호스트가 dooray.com 또는 그 하위일 때만."""
    parts = urllib.parse.urlparse(url or "")
    host = (parts.hostname or "").lower()
    return parts.scheme == "https" and (host == "dooray.com" or host.endswith(".dooray.com"))


def safe_name(name, fallback="_"):
    """파일·폴더 이름으로 쓸 수 있게 Windows 금지 문자와 경로 구분자를 _ 로 바꾸고 끝의 공백·점을 뗀다."""
    return UNSAFE_NAME_CHARS.sub("_", name or "").rstrip(" .") or fallback


def download_name(file):
    """숫자 파일 ID를 접두사로 붙여 다른 ID의 동명 파일을 보존한다.

    Windows 금지 문자와 경로 구분자는 치환한다. 잘못된 ID는 저장 전에 거절한다.
    """
    file_id = str(file["id"])
    if not re.fullmatch(r"[0-9]+", file_id):
        raise ValueError("파일 ID는 숫자여야 합니다")
    return f"{file_id}_{safe_name(file['name'], 'file')}"


def fmt_file_catalog(files, numbered=True):
    """수집된 파일의 번호·ID·이름·출처를 표시한다. 다운로드는 번호 또는 파일명으로 고른다.

    번호는 download가 전체 댓글로 만든 목록의 순서다. 댓글 범위가 다른 목록이면 numbered=False로 뺀다.
    """
    lines = []
    for i, f in enumerate(files, 1):
        num = f"{i}. " if numbered else ""
        lines.append(f"  {num}ID={f['id']} {f['name']} — {'; '.join(f['sources'])}")
    return "\n".join(lines) or "(파일 없음)"


def pick_files(files, target):
    """download 대상 선택. 생략·all → 전체, 범위 안 번호 → 그 하나(1부터), 그 외 → 같은 이름 전부.

    번호는 collect_files 순서(첨부 → 본문 → 댓글)라 read 첨부 번호·full 파일 목록 번호와 같다.
    """
    if not target or target.lower() == "all":
        return files
    if target.isdigit() and 1 <= int(target) <= len(files):
        return [files[int(target) - 1]]
    # 같은 이름이 여러 개면 모두 받는다. 저장명이 <파일ID>_<이름>이라 디스크에서 구분된다.
    picks = [f for f in files if f["name"] == target]
    if not picks:
        sys.exit(f"'{target}' 파일을 찾을 수 없습니다. 받을 수 있는 파일:\n{fmt_file_catalog(files)}")
    return picks


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
            "\n\n다운로드할까요? (번호 또는 파일명 지정, 생략하면 전체)")


def text_arg(args):
    """내용 인자. '--file <경로>'면 UTF-8 파일 내용(끝 줄바꿈 제거), 아니면 공백으로 이은 문자열."""
    if args[0] == "--file":
        if len(args) < 2:
            sys.exit("--file 뒤에 파일 경로가 필요합니다.")
        try:
            return Path(args[1]).read_text(encoding="utf-8").rstrip("\n")
        except OSError as e:
            sys.exit(f"파일을 읽을 수 없습니다: {args[1]} ({e.strerror or e})")
    return " ".join(args)


def parse_wiki_path(arg, wiki_name):
    """'회의록 > LG ICON25 프로젝트 >' → (['회의록', 'LG ICON25 프로젝트'], True).

    끝의 > 나 빈 인자는 탐색 표시다. > 앞뒤 공백과 빈 조각은 무시하고, 맨 앞의 위키 이름은 뺀다
    (wiki-list 출력 줄을 그대로 받기 위해).
    """
    parts = [s.strip() for s in (arg or "").split(">")]
    browse = parts[-1] == ""
    parts = [s for s in parts if s]
    if parts and parts[0] == wiki_name:
        parts = parts[1:]
    return parts, browse


def norm_title(title):
    """제목 비교용. 제목 안의 > 앞뒤 공백 차이를 없앤다('HD Map>SUMO' == 'HD Map > SUMO')."""
    return " > ".join(s.strip() for s in (title or "").split(">") if s.strip())


def match_child(kids, name, where):
    """kids 중 제목이 name과 같은 페이지. 없으면 None, 여럿이면 종료한다(추측하지 않는다)."""
    hits = [k for k in kids if norm_title(k.get("subject")) == name]
    if len(hits) > 1:
        sys.exit(f"'{where}' 아래에 '{name}' 페이지가 {len(hits)}개입니다. 위키에서 제목을 구분한 뒤 다시 시도하세요.")
    return hits[0] if hits else None


def fmt_children(kids):
    return "\n".join(f"  {i}. {k['subject']}" for i, k in enumerate(kids, 1)) or "  (하위 페이지 없음)"


def wiki_files(detail):
    """위키 페이지 상세의 첨부 → 이미지. 이 순서가 곧 wiki-download 번호다."""
    return ([{**f, "sources": ["첨부"]} for f in detail.get("files") or []] +
            [{**f, "sources": ["이미지"]} for f in detail.get("images") or []])


def wiki_missing(wiki_name, parts, i, kids):
    where = " > ".join([wiki_name, *parts[:i]])
    return f"'{where}' 아래에 '{parts[i]}' 페이지가 없습니다. 하위 페이지:\n{fmt_children(kids)}"


def fmt_link(url, label="이력 주소"):
    return f"\n\n{label}: {url}" if url else f"\n\n({label} 확인 불가 — Dooray/Config.md 에 TENANT= 설정 없음)"


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
    elif cmd not in ("workflows", "wiki-list", "wiki-read", "wiki-write", "wiki-download") and not rest:
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
    if cmd == "wiki-list":
        w = d.wiki()
        # 따옴표 없이 띄어 쓴 제목(주간 미팅 노트)도 한 경로로 받는다.
        parts, _ = parse_wiki_path(" ".join(rest), w["name"])
        start = [w["name"], *parts]
        paths = d.wiki_tree(d.wiki_find(parts)["id"], start)
        if not paths:
            print(f"'{' > '.join(start)}' 아래에 하위 페이지가 없습니다.")
        for i, path in enumerate(paths, 1):
            print(f"{i}. {' > '.join(path)}")
        return
    if cmd == "wiki-read":
        w = d.wiki()
        parts, browse = parse_wiki_path(" ".join(rest), w["name"])
        head = " > ".join([w["name"], *parts])
        page = d.wiki_find(parts)
        # 탐색 표시(끝 > 또는 인자 없음)여도 하위가 없으면 그 페이지를 읽는다.
        kids = d.wiki_children(page["id"]) if browse else []
        if kids:
            print(f"{head}\n{fmt_children(kids)}")
            return
        with ThreadPoolExecutor() as ex:
            detail_f = ex.submit(d.wiki_page, page["id"])
            comments_f = ex.submit(d.wiki_comments, page["id"])
            detail, logs = detail_f.result(), comments_f.result()
        body = body_text(detail.get("body")).strip()
        out = f"{head}\n\n{body}" if body else head
        # 본문 없이 댓글에만 내용을 쌓는 페이지(주간 미팅 노트)가 있어 댓글은 항상 함께 보여준다.
        if logs:
            names = {}
            for c in logs:
                member = (c.get("creator") or {}).get("member") or {}
                names[member.get("organizationMemberId")] = member.get("name", "?")
            out += "\n\n--- 댓글 ---\n" + fmt_comments(logs, names)
        files = wiki_files(detail)
        if files:
            out += "\n\n--- 파일 ---\n" + fmt_file_catalog(files)
        print(out + fmt_link(d.wiki_url(page["id"]), "위키 주소"))
        return
    if cmd == "wiki-download":
        if not rest:
            sys.exit('위키 경로가 필요합니다. 예: dooray wiki-download "Visualizer > 실행 방법" [파일명|번호|all]')
        w = d.wiki()
        parts, _ = parse_wiki_path(rest[0], w["name"])
        page = d.wiki_find(parts)
        files = wiki_files(d.wiki_page(page["id"]))
        if not files:
            sys.exit(f"'{' > '.join([w['name'], *parts])}' 에 받을 수 있는 파일이 없습니다(첨부·이미지 모두 없음).")
        picks = pick_files(files, rest[1] if len(rest) > 1 else None)
        # 위키 트리와 같은 모양으로 저장한다: wiki/<위키이름>/<제목>/.../download/. 하위 페이지 폴더와 섞이지 않게 download/를 둔다.
        # ponytail: 제목 기준이라 Dooray에서 제목을 바꾸면 새 폴더가 생기고, 트리가 아주 깊으면 Windows 경로 260자에 걸릴 수 있다.
        out_dir = wiki_folder(w["name"], page["path"]) / "download"
        out_dir.mkdir(parents=True, exist_ok=True)
        with ThreadPoolExecutor() as ex:
            futures = {ex.submit(d.wiki_download_file, page["id"], f["id"]): f for f in picks}
            for fut, f in futures.items():
                out_path = out_dir / download_name(f)
                out_path.write_bytes(fut.result())
                print(f"다운로드 완료: {out_path} — {'; '.join(f['sources'])}")
        return
    if cmd == "wiki-write":
        dry_run, move_draft = "--dry-run" in rest, "--move-draft" in rest
        rest = [a for a in rest if a not in ("--dry-run", "--move-draft")]
        w = d.wiki()
        parts, browse = parse_wiki_path(rest[0] if rest else "", w["name"])
        if browse or not parts:
            sys.exit('쓰기 대상 페이지 이름이 필요합니다. 예: dooray wiki-write "Visualizer > 실행 방법" --file note.md')
        if len(rest) < 2:
            sys.exit('내용이 필요합니다. 예: dooray wiki-write "Visualizer > 실행 방법" "내용" 또는 --file <경로>')
        text = text_arg(rest[1:])
        if not text.strip():
            sys.exit("내용이 비어 있습니다. 빈 날짜 섹션이나 빈 페이지는 만들지 않습니다.")
        # 초안 속 로컬 이미지·파일 참조의 기준은 --file 이면 그 파일 폴더, 아니면 현재 폴더다.
        draft = Path(rest[2]) if rest[1] == "--file" and len(rest) > 2 else None
        base = draft.resolve().parent if draft else Path.cwd()
        files = local_files(text, base)
        missing = [str(p) for p in files if not p.is_file()]
        if missing:
            sys.exit("초안에서 참조한 로컬 파일이 없습니다(아무것도 쓰지 않음):\n" + "\n".join(f"  - {m}" for m in missing))
        full = " > ".join([w["name"], *parts])
        page, i, kids = d.wiki_walk(parts)
        # 중간 페이지는 만들지 않는다. 새로 만드는 건 마지막 페이지 하나뿐이다.
        if i < len(parts) - 1:
            sys.exit(wiki_missing(w["name"], parts, i, kids))
        target, parent = (page, None) if i == len(parts) else (None, page)
        body = dict(d.wiki_page(target["id"]).get("body") or {}) if target else {}
        if "html" in (body.get("mimeType") or ""):
            sys.exit(f"HTML 본문 페이지에는 이어쓸 수 없습니다(마크다운을 덧붙이면 본문이 깨짐): {full}")
        # 멘션 해석 실패(없는·모호한 이름)도 dry-run에서 드러나야 '예정'을 믿을 수 있다.
        text = d.apply_mentions(text)
        if dry_run:
            print(f"{'이어쓰기' if target else '생성'} 예정: {full}")
            for path, ftype in files.items():
                print(f"업로드 예정: {path.name} ({kind_label(ftype)})")
            return
        uploaded = []

        def upload_all(page_id):
            """로컬 파일을 page_id에 올리고, 참조를 Dooray 편집기와 같은 프로젝트 ID 경로로 바꾼 내용을 돌려준다."""
            refs = {}
            for path, ftype in files.items():
                refs[path] = f"/wikis/{d.pid}/files/{d.upload_wiki_file(page_id, path, ftype)}"
                uploaded.append(path.name)
                print(f"업로드 완료: {path.name} ({kind_label(ftype)})")
            return rewrite_local_links(text, base, refs)

        def leftover():
            """이어쓰기가 중간에 멈췄을 때, 본문에는 안 들어갔지만 페이지 첨부로 남은 파일 안내."""
            return (f"\n이미 올라간 파일은 본문에 쓰지 않았지만 페이지 첨부로 남아 있습니다(웹에서 정리): {', '.join(uploaded)}"
                    if uploaded else "")

        if target:
            if files:
                try:
                    text = upload_all(target["id"])
                except SystemExit as e:
                    sys.exit(f"{e.code}{leftover()}")
            old = (body.get("content") or "").rstrip("\n")
            section = f"## {datetime.now().strftime('%y-%m-%d, %H:%M')}\n\n{text}"
            content = f"{old}\n\n{section}" if old else section
            # 저장 직전에 원문과 형식을 비교한다. 재조회 실패도 PUT 전에 그대로 종료된다.
            latest_body = d.wiki_page(target["id"]).get("body") or {}
            if any(latest_body.get(key) != body.get(key) for key in ("mimeType", "content")):
                sys.exit(f"본문이 변경되어 이어쓰기를 중단했습니다: {full}\n"
                         f"최신 내용을 다시 읽고 확인한 뒤 실행하세요.{leftover()}")
            # 재조회와 PUT 사이의 변경까지 막으려면 서버의 버전 조건 검사가 필요하다.
            d.set_wiki_content(target["id"], content)
            print(f"이어쓰기 완료: {full}" + fmt_link(d.wiki_url(target["id"]), "위키 주소"))
        else:
            res = d.create_wiki_page(parent["id"], parts[-1], text)
            new_id = ((res or {}).get("result") or {}).get("id")
            if files:
                # 업로드는 페이지가 있어야 하므로 생성 → 업로드 → 참조를 바꾼 본문으로 수정 순서다.
                if not new_id:
                    sys.exit(f"페이지는 만들어졌지만 응답에 페이지 ID가 없어 파일을 올리지 못했습니다: {full}")
                try:
                    d.set_wiki_content(new_id, upload_all(new_id))
                except (SystemExit, Exception) as e:
                    # 어떤 실패든 페이지가 이미 생겼다는 사실과 주소는 알려야 사용자가 웹에서 정리할 수 있다.
                    reason = e.code if isinstance(e, SystemExit) else f"{type(e).__name__}: {e}"
                    sys.exit(f"{reason}\n페이지는 만들어졌지만 파일 업로드·본문 수정이 끝나지 않았습니다: {full}"
                             + fmt_link(d.wiki_url(new_id), "위키 주소"))
            # 응답에 새 페이지 ID가 없으면 주소를 만들 수 없으니 줄을 뺀다.
            print(f"생성 완료: {full}" + (fmt_link(d.wiki_url(new_id), "위키 주소") if new_id else ""))
        if move_draft and draft:
            # 쓰기가 모두 끝난 뒤에만 초안을 그 페이지 폴더(위키 트리 모양)로 옮겨 기록으로 남긴다.
            titles = page["path"] if target else page["path"] + [parts[-1]]
            print(f"초안 이동: {archive_draft(draft, wiki_folder(w['name'], titles))}")
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
        print("\n--- 파일 목록 (조회한 본문·댓글 기준) ---")
        # 댓글 개수를 제한하면 download(항상 전체 댓글)의 번호와 어긋나므로 번호를 뺀다.
        print(fmt_file_catalog(collect_files(files, (p.get("body") or {}).get("content"), logs),
                               numbered=limit is None))
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
        raw_text = text_arg(rest[1:])
        with ThreadPoolExecutor() as ex:
            post_id_f = ex.submit(d.find_post_id, number)
            text_f = ex.submit(d.apply_mentions, raw_text)
            post_id, text = post_id_f.result(), text_f.result()
        d.add_comment(post_id, text)
        print(f"#{number} 댓글 등록 완료")
    elif cmd == "download":
        post_id = d.find_post_id(number)
        with ThreadPoolExecutor() as ex:
            files_f = ex.submit(d.files, post_id)
            detail_f = ex.submit(d.post_detail, post_id)
            comments_f = ex.submit(d.comments, post_id)
            files, detail, logs = files_f.result(), detail_f.result(), comments_f.result()
        files = collect_files(files, (detail.get("body") or {}).get("content"), logs)
        if not files:
            sys.exit(f"업무 #{number} 에 받을 수 있는 파일이 없습니다(첨부·본문·댓글 이미지 모두 없음).")
        picks = pick_files(files, rest[1] if len(rest) > 1 else None)
        # 업무별로 나눈다. 한 폴더에 모으면 여러 이력의 같은 이름(특히 Inline-image-*.png)이 덮어써진다.
        out_dir = TASK_DIR / str(number) / "download"
        out_dir.mkdir(parents=True, exist_ok=True)
        with ThreadPoolExecutor() as ex:
            futures = {ex.submit(d.download_file, post_id, f["id"]): f for f in picks}
            for fut, f in futures.items():
                out_path = out_dir / download_name(f)
                out_path.write_bytes(fut.result())
                print(f"다운로드 완료: {out_path} — {'; '.join(f['sources'])}")


if __name__ == "__main__":
    main()
