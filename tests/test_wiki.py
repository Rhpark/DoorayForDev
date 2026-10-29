"""위키 목록·읽기·쓰기·다운로드 명령의 사용자 동작을 검증한다.

CLI main에 인자를 전달하고 설정 읽기와 HTTP 입출력(_api·_raw·_upload)을 가짜 응답으로 교체한다.
실제 토큰·네트워크·Config.md가 필요 없으며 Dooray 서버에 페이지를 생성하지 않는다.
다운로드와 초안 이동은 임시 폴더에서 검증하고, 요청 기록으로 생성·업로드·본문 수정 순서를 확인한다.
"""
import contextlib
import importlib.util
import io
import os
import sys
import unittest
from unittest import mock
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "Dooray" / "dooray.py"
SPEC = importlib.util.spec_from_file_location("dooray", MODULE_PATH)
DOORAY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DOORAY)

PAGE_SIZE = 2  # 목록 API가 요청 size와 무관하게 2개씩 끊어 줘서 페이지네이션 경로를 반드시 탄다.
MD = "text/x-markdown"


class FakeWiki:
    """경로 충돌·페이지네이션·파일 업로드를 재현하는 메모리 위키와 요청 기록이다.

    P1은 프로젝트, W1은 위키, H는 Home, C1은 기존 마크다운 페이지다.
    F 계열 페이지는 제목 속 > 와 중첩 경로가 충돌하는 경우를, G는 댓글·첨부·이미지를 제공한다.
    writes는 create·upload·update 요청을 발생 순서대로 담아 부분 실패 때의 상태도 비교한다.
    """

    def __init__(self):
        self.pages = {}
        self.writes = []
        self.uploaded = {}
        self.add("H", None, "Home", "")
        self.add("A", "H", "주간 미팅 노트", "")
        self.add("B", "H", "회의록", "")
        self.add("B1", "B", "LG ICON25 프로젝트", "")
        self.add("B11", "B1", "260402_고객사 협의내용", "협의 본문")
        self.add("B2", "B", "ublox 한국지사 X20K 제공관련 논의", "")
        self.add("C", "H", "Visualizer", "비주얼 본문")
        self.add("C1", "C", "test", "기존 본문")
        self.add("D1", "H", "중복", "")
        self.add("D2", "H", "중복", "")
        self.add("E", "H", "HTML 페이지", "<p>위지윅</p>", mime="text/html")
        # 실제 Snoopy 위키처럼 제목 자체에 > 가 있는 페이지. 같은 글자의 중첩 경로도 있어 제목 우선을 가린다.
        self.add("F", "H", "AI BSM", "")
        self.add("F1", "F", "SUMO", "")
        self.add("F11", "F1", "HD Map > SUMO Network", "맵 본문",
                 files=[{"id": "81", "attachFileId": "a81", "name": "맵.zip", "size": 5}])
        self.add("F12", "F1", "HD Map", "")
        self.add("F121", "F12", "SUMO Network", "중첩 본문")
        self.add("F1211", "F121", "노트", "중첩 노트")  # 제목 쪽(F11) 아래에는 없고 중첩 쪽에만 있다
        # 댓글·첨부·이미지가 있는 페이지(이미지는 본문이 아니라 댓글에 있을 수도 있다). API처럼 댓글은 최신순으로 준다.
        self.add("G", "H", "측위 시험", "측위 본문",
                 files=[{"id": "91", "attachFileId": "a91", "name": "계획서.xlsx", "size": 2048}],
                 images=[{"id": "92", "attachFileId": "a92", "name": "그림.png", "size": 10}],
                 comments=[comment("2026-03-17T10:31:00+09:00", "이서진", "둘째 댓글"),
                           comment("2026-03-03T10:44:00+09:00", "정홍종", "첫 댓글"),
                           comment("2026-03-10T09:00:00+09:00", "박랑호", "가운데 댓글")])

    def add(self, pid, parent, subject, content, mime=MD, files=(), images=(), comments=()):
        """부모 관계와 본문·파일·댓글을 가진 페이지를 테스트 트리에 등록한다."""
        self.pages[pid] = {"id": pid, "parent": parent, "subject": subject,
                           "body": {"mimeType": mime, "content": content},
                           "files": list(files), "images": list(images), "comments": list(comments)}

    def children(self, parent):
        """페이지 등록 순서대로 바로 아래 자식만 돌려줘 형제 출력 순서를 고정한다."""
        return [{"id": p["id"], "subject": p["subject"]} for p in self.pages.values() if p["parent"] == parent]

    def api(self, path, method="GET", body=None, **params):
        """사용하는 조회·생성·수정 API의 응답과 저장 결과를 메모리에서 재현한다."""
        if path == "/project/v1/projects":
            return {"result": [{"id": "P1", "code": "Snoopy"}], "totalCount": 1}
        if path == "/wiki/v1/wikis":
            # 연결된 위키를 두 번째 응답에 배치해 첫 목록에서 탐색을 끝내는 회귀를 잡는다.
            wikis = [{"id": "W0", "name": "다른위키", "project": {"id": "PX"}, "home": {"pageId": "X"}},
                     {"id": "W1", "name": "Snoopy", "project": {"id": "P1"}, "home": {"pageId": "H"}}]
            page = params.get("page", 0)
            return {"result": wikis[page:page + 1], "totalCount": len(wikis)}
        if path == "/common/v1/members/me":
            return {"result": {"id": "ME", "defaultOrganization": {"id": "ORG"}}}
        if path == "/common/v1/members":
            if params["name"] == "없는사람":
                return {"result": []}
            return {"result": [{"id": "M1", "name": params["name"], "externalEmailAddress": "a@wayties.com"}]}
        # 최적화 모드에서도 잘못된 요청을 놓치지 않도록 일반 assert 대신 명시적으로 실패시킨다.
        if not path.startswith("/wiki/v1/wikis/W1/pages"):
            raise AssertionError(path)
        rest = path[len("/wiki/v1/wikis/W1/pages"):]
        if method == "POST" and rest == "":
            self.writes.append(("create", body["parentPageId"], body["subject"], body["body"]))
            self.add(f"N{len(self.writes)}", body["parentPageId"], body["subject"], body["body"]["content"])
            return {"result": {"id": f"N{len(self.writes)}"}}
        if method == "PUT" and rest.endswith("/content"):
            pid = rest[1:-len("/content")]
            self.writes.append(("update", pid, body["body"]))
            self.pages[pid]["body"] = body["body"]
            return {"result": None}
        if rest == "":
            kids = self.children(params.get("parentPageId"))
            page = params.get("page", 0)
            return {"result": kids[page * PAGE_SIZE:(page + 1) * PAGE_SIZE], "totalCount": len(kids)}
        if rest.endswith("/comments"):
            items = self.pages[rest[1:-len("/comments")]]["comments"]
            page = params.get("page", 0)
            return {"result": items[page * PAGE_SIZE:(page + 1) * PAGE_SIZE], "totalCount": len(items)}
        p = self.pages[rest[1:]]
        return {"result": {"id": p["id"], "subject": p["subject"], "body": p["body"],
                           "files": p["files"], "images": p["images"]}}

    def upload(self, path, name, data, ftype, mime):
        """multipart 업로드. 쓰기 요청과 같은 목록에 순서대로 기록하고 attachFileId를 발급한다."""
        if not (path.startswith("/wiki/v1/wikis/W1/pages/") and path.endswith("/files")):
            raise AssertionError(path)
        page_id = path[len("/wiki/v1/wikis/W1/pages/"):-len("/files")]
        self.writes.append(("upload", page_id, name, ftype, mime))
        self.uploaded[name] = data
        # 다운로드용 id와 본문 참조용 attachFileId를 다르게 만들어 두 값을 혼동하면 드러나게 한다.
        return {"result": {"id": f"F{len(self.writes)}", "attachFileId": f"A{len(self.writes)}", "name": name}}

    def raw(self, path):
        """?media=raw 다운로드. 파일 ID로 알아볼 수 있는 바이트를 돌려준다."""
        if not (path.startswith("/wiki/v1/wikis/W1/pages/") and "/files/" in path):
            raise AssertionError(path)
        return f"bytes-{path.rsplit('/', 1)[1]}".encode()


def comment(created_at, name, text):
    """작성자 표시와 시간순 정렬에 필요한 최소 댓글 응답을 만든다."""
    return {"id": f"c-{name}", "createdAt": created_at, "body": {"mimeType": MD, "content": text},
            "creator": {"type": "member", "member": {"organizationMemberId": f"u-{name}", "name": name}}}


def run(*args, wiki=None, config=None, wiki_dir=None):
    """dooray <args>를 실행해 (stdout, 종료 메시지, fake)를 돌려준다. 정상 종료면 종료 메시지는 None.

    config는 가짜 설정이며 실제 설정 파일을 읽지 않는다. HTTP 세 종류도 모두 fake로 바꾼다.
    wiki_dir는 다운로드와 초안 보관의 기준 폴더다. 파일을 만드는 테스트는 임시 경로를 전달한다.
    SystemExit는 메시지로 반환하고 그 밖의 예외는 숨기지 않아 예상 밖 오류로 테스트가 실패하게 한다.
    """
    wiki = wiki or FakeWiki()
    config = config or {"DOORAY_API_TOKEN": "t", "REPOSITORY": "Snoopy", "TENANT": "acme"}
    out, exit_msg = io.StringIO(), None
    with mock.patch.object(DOORAY, "load_config", return_value=config), \
            mock.patch.object(DOORAY.Dooray, "_api", lambda self, *a, **k: wiki.api(*a, **k)), \
            mock.patch.object(DOORAY.Dooray, "_raw", lambda self, path: wiki.raw(path)), \
            mock.patch.object(DOORAY.Dooray, "_upload", lambda self, *a: wiki.upload(*a)), \
            mock.patch.object(DOORAY, "WIKI_DIR", Path(wiki_dir) if wiki_dir else DOORAY.WIKI_DIR), \
            mock.patch.object(sys, "argv", ["dooray.py", *args]), \
            contextlib.redirect_stdout(out):
        try:
            DOORAY.main()
        except SystemExit as e:
            exit_msg = str(e.code)
    return out.getvalue(), exit_msg, wiki


class WikiListTest(unittest.TestCase):
    """위키 구조를 빠짐없이 조회하고 복사해 사용할 수 있는 전체 경로로 표시한다."""

    def test_lists_every_page_as_full_path_in_tree_order(self):
        """여러 API 페이지에 걸친 트리를 부모 다음에 자식이 오는 순서로 펼친다."""
        out, err, _ = run("wiki-list")
        self.assertIsNone(err)
        self.assertEqual([
            "1. Snoopy > 주간 미팅 노트",
            "2. Snoopy > 회의록",
            "3. Snoopy > 회의록 > LG ICON25 프로젝트",
            "4. Snoopy > 회의록 > LG ICON25 프로젝트 > 260402_고객사 협의내용",
            "5. Snoopy > 회의록 > ublox 한국지사 X20K 제공관련 논의",
            "6. Snoopy > Visualizer",
            "7. Snoopy > Visualizer > test",
            "8. Snoopy > 중복",
            "9. Snoopy > 중복",
            "10. Snoopy > HTML 페이지",
            "11. Snoopy > AI BSM",
            "12. Snoopy > AI BSM > SUMO",
            "13. Snoopy > AI BSM > SUMO > HD Map > SUMO Network",
            "14. Snoopy > AI BSM > SUMO > HD Map",
            "15. Snoopy > AI BSM > SUMO > HD Map > SUMO Network",
            "16. Snoopy > AI BSM > SUMO > HD Map > SUMO Network > 노트",
            "17. Snoopy > 측위 시험",
        ], out.splitlines())

    def test_start_path_lists_only_its_subtree(self):
        """위키 이름 접두어와 구분자 공백이 달라도 지정한 하위 트리만 조회한다."""
        expected = [
            "1. Snoopy > 회의록 > LG ICON25 프로젝트",
            "2. Snoopy > 회의록 > LG ICON25 프로젝트 > 260402_고객사 협의내용",
            "3. Snoopy > 회의록 > ublox 한국지사 X20K 제공관련 논의",
        ]
        # 위키 이름 접두어, > 앞뒤 공백, 끝 > 는 같은 경로로 본다(list 줄을 복사해 넣어도 동작).
        for arg in ("회의록", "Snoopy > 회의록", "Snoopy>회의록 >"):
            out, err, _ = run("wiki-list", arg)
            self.assertIsNone(err, arg)
            self.assertEqual(expected, out.splitlines(), arg)

    def test_unknown_step_exits_with_that_level_candidates(self):
        """경로를 찾지 못한 위치의 자식 목록을 알려 사용자가 다음 입력을 고칠 수 있다."""
        out, err, _ = run("wiki-list", "회의록 > 없는페이지")
        self.assertEqual("", out)
        self.assertIn("'Snoopy > 회의록' 아래에 '없는페이지' 페이지가 없습니다", err)
        self.assertIn("1. LG ICON25 프로젝트", err)
        self.assertIn("2. ublox 한국지사 X20K 제공관련 논의", err)

    def test_same_title_siblings_exit_instead_of_guessing(self):
        """같은 부모 아래 제목이 중복되면 임의의 페이지를 선택하지 않는다."""
        _, err, _ = run("wiki-list", "중복")
        self.assertIn("'중복' 페이지가 2개입니다", err)

    def test_page_without_children_says_so(self):
        """하위가 없는 페이지는 조회 실패와 구분되는 안내를 출력한다."""
        out, err, _ = run("wiki-list", "Visualizer > test")
        self.assertIsNone(err)
        self.assertEqual("'Snoopy > Visualizer > test' 아래에 하위 페이지가 없습니다.\n", out)


LINK = "\n\n위키 주소: https://acme.dooray.com/wiki/W1/"


class WikiReadTest(unittest.TestCase):
    """본문 읽기와 하위 탐색을 구분하고 댓글·파일·웹 주소를 함께 제공한다."""

    def test_path_prints_header_body_and_page_link(self):
        """명시한 페이지를 읽으면 현재 경로·본문·웹 주소가 함께 출력된다."""
        out, err, _ = run("wiki-read", "Visualizer")
        self.assertIsNone(err)
        self.assertEqual(f"Snoopy > Visualizer\n\n비주얼 본문{LINK}C\n", out)

    def test_empty_body_prints_only_header_and_link(self):
        """본문이 비어 있어도 페이지 경로와 주소를 제공하고 공백 있는 인자를 처리한다."""
        # 따옴표 없이 띄어 쓴 제목도 한 경로로 받는다.
        out, err, _ = run("wiki-read", "주간", "미팅", "노트")
        self.assertIsNone(err)
        self.assertEqual(f"Snoopy > 주간 미팅 노트{LINK}A\n", out)

    def test_comments_in_time_order_and_numbered_files_before_link(self):
        """댓글을 시간순으로 정렬하고 다운로드에 사용할 첨부·이미지 번호를 표시한다."""
        out, err, _ = run("wiki-read", "측위 시험")
        self.assertIsNone(err)
        self.assertEqual(
            "Snoopy > 측위 시험\n\n측위 본문\n\n"
            "--- 댓글 ---\n"
            "[2026-03-03 10:44] 정홍종: 첫 댓글\n"
            "[2026-03-10 09:00] 박랑호: 가운데 댓글\n"
            "[2026-03-17 10:31] 이서진: 둘째 댓글\n\n"
            "--- 파일 ---\n"
            "  1. ID=91 계획서.xlsx — 첨부\n"
            "  2. ID=92 그림.png — 이미지"
            f"{LINK}G\n", out)

    def test_without_tenant_link_line_says_why(self):
        """테넌트 설정이 없으면 잘못된 주소 대신 주소를 만들 수 없는 이유를 알린다."""
        out, _, _ = run("wiki-read", "Visualizer", config={"DOORAY_API_TOKEN": "t", "REPOSITORY": "Snoopy"})
        self.assertTrue(out.endswith("\n\n(위키 주소 확인 불가 — Dooray/Config.md 에 TENANT= 설정 없음)\n"), out)

    def test_trailing_marker_lists_children_with_numbers(self):
        """끝의 > 는 본문 읽기 대신 하위 페이지를 번호로 고르는 탐색 요청이다."""
        for arg in ("Visualizer>", "Visualizer >"):
            out, err, _ = run("wiki-read", arg)
            self.assertIsNone(err, arg)
            self.assertEqual("Snoopy > Visualizer\n  1. test\n", out, arg)

    def test_no_argument_starts_browsing_under_home(self):
        """경로를 모르는 사용자는 인자 없이 Home 아래부터 탐색을 시작할 수 있다."""
        out, err, _ = run("wiki-read")
        self.assertIsNone(err)
        self.assertEqual("Snoopy", out.splitlines()[0])
        self.assertEqual(["  1. 주간 미팅 노트", "  2. 회의록", "  3. Visualizer"], out.splitlines()[1:4])

    def test_trailing_marker_on_leaf_reads_it(self):
        """탐색한 페이지에 하위가 없으면 추가 선택 없이 해당 본문을 보여준다."""
        out, err, _ = run("wiki-read", "Visualizer > test >")
        self.assertIsNone(err)
        self.assertEqual(f"Snoopy > Visualizer > test\n\n기존 본문{LINK}C1\n", out)

    def test_html_body_becomes_plain_text(self):
        """위지윅으로 작성된 페이지도 HTML 태그 대신 읽을 수 있는 본문을 출력한다."""
        out, _, _ = run("wiki-read", "HTML 페이지")
        self.assertEqual(f"Snoopy > HTML 페이지\n\n위지윅{LINK}E\n", out)

    def test_title_containing_marker_wins_over_nested_path(self):
        """제목 자체에 포함된 > 를 지원하기 위해 가장 긴 제목 일치를 우선한다."""
        # 제목 우선: 'HD Map > SUMO Network' 제목이 'HD Map' 아래 'SUMO Network'보다 먼저다. > 앞뒤 공백은 무관하다.
        for arg in ("AI BSM > SUMO > HD Map > SUMO Network", "AI BSM>SUMO>HD Map>SUMO Network"):
            out, err, _ = run("wiki-read", arg)
            self.assertIsNone(err, arg)
            self.assertEqual("Snoopy > AI BSM > SUMO > HD Map > SUMO Network\n\n맵 본문\n\n"
                             f"--- 파일 ---\n  1. ID=81 맵.zip — 첨부{LINK}F11\n", out, arg)


class FixedNow(__import__("datetime").datetime):
    """이어쓰기 날짜가 실행 시각에 따라 바뀌지 않도록 고정된 로컬 시각을 제공한다."""

    @classmethod
    def now(cls, tz=None):
        """테스트가 기대하는 날짜 헤더를 만들 시각을 반환한다."""
        return cls(2026, 10, 27, 9, 5)


class WikiWriteTest(unittest.TestCase):
    """새 페이지 생성과 날짜별 이어쓰기를 구분하고 잘못된 입력·동시 편집을 보호한다."""

    def test_existing_page_gets_dated_section_appended(self):
        """기존 본문을 보존한 뒤 날짜 헤더와 새 내용을 붙이고 완료 주소를 알린다."""
        with mock.patch.object(DOORAY, "datetime", FixedNow):
            out, err, wiki = run("wiki-write", "Visualizer > test", "새 내용")
        self.assertIsNone(err)
        self.assertEqual([("update", "C1", {"mimeType": MD, "content": "기존 본문\n\n## 26-10-27, 09:05\n\n새 내용"})],
                         wiki.writes)
        self.assertEqual(f"이어쓰기 완료: Snoopy > Visualizer > test{LINK}C1\n", out)

    def test_concurrent_body_change_refuses_without_overwriting(self):
        """저장 전 재조회에서 내용·형식 변경을 감지하면 다른 편집을 덮어쓰지 않는다."""
        # 끝 줄바꿈만 달라진 편집도 변경이다. 본문을 정규화한 뒤 비교하면 놓칠 수 있다.
        for change in ({"content": "다른 사람이 수정한 본문"},
                       {"content": "기존 본문\n"},
                       {"mimeType": "text/html"}):
            with self.subTest(change=change):
                wiki = FakeWiki()
                original_api = wiki.api
                reads = 0

                def api(path, method="GET", body=None, **params):
                    nonlocal reads
                    if method == "GET" and path == "/wiki/v1/wikis/W1/pages/C1":
                        reads += 1
                        if reads == 2:
                            # 첫 조회 뒤 다른 사용자가 내용을 편집한 상황을 두 번째 응답 직전에 재현한다.
                            wiki.pages["C1"]["body"].update(change)
                    return original_api(path, method, body, **params)

                with mock.patch.object(wiki, "api", side_effect=api):
                    out, err, _ = run("wiki-write", "Visualizer > test", "새 내용", wiki=wiki)

                self.assertIn("본문이 변경되어 이어쓰기를 중단했습니다", err or "")
                self.assertEqual("", out)
                self.assertEqual([], wiki.writes)
                for key, value in change.items():
                    self.assertEqual(value, wiki.pages["C1"]["body"][key])

    def test_recheck_failure_refuses_without_writing(self):
        """최신 본문을 확인하지 못하면 저장을 중단하고 기존 본문을 보존한다."""
        wiki = FakeWiki()
        original_api = wiki.api
        reads = 0

        def api(path, method="GET", body=None, **params):
            nonlocal reads
            if method == "GET" and path == "/wiki/v1/wikis/W1/pages/C1":
                reads += 1
                if reads == 2:
                    # 최초 본문은 읽었지만 저장 직전 확인 요청만 실패하는 상황이다.
                    raise SystemExit("본문 재조회 실패")
            return original_api(path, method, body, **params)

        with mock.patch.object(wiki, "api", side_effect=api):
            out, err, _ = run("wiki-write", "Visualizer > test", "새 내용", wiki=wiki)

        self.assertEqual("본문 재조회 실패", err)
        self.assertEqual("", out)
        self.assertEqual([], wiki.writes)
        self.assertEqual("기존 본문", wiki.pages["C1"]["body"]["content"])

    def test_missing_page_is_created_under_parent_without_header(self):
        """부모가 있는 새 페이지에는 이어쓰기 날짜 없이 최초 내용을 저장한다."""
        out, err, wiki = run("wiki-write", "Snoopy > Visualizer > 새 페이지", "첫", "내용")
        self.assertIsNone(err)
        self.assertEqual([("create", "C", "새 페이지", {"mimeType": MD, "content": "첫 내용"})], wiki.writes)
        self.assertEqual(f"생성 완료: Snoopy > Visualizer > 새 페이지{LINK}N1\n", out)

    def test_title_containing_marker_is_append_target_and_parent(self):
        """> 가 들어 있는 실제 제목을 이어쓰기 대상과 새 페이지의 부모로 사용할 수 있다."""
        _, err, wiki = run("wiki-write", "AI BSM > SUMO > HD Map > SUMO Network", "추가")
        self.assertIsNone(err)
        self.assertEqual("F11", wiki.writes[0][1])
        _, err, wiki = run("wiki-write", "AI BSM > SUMO > HD Map > SUMO Network > 하위", "첫 내용")
        self.assertIsNone(err)
        self.assertEqual([("create", "F11", "하위", {"mimeType": MD, "content": "첫 내용"})], wiki.writes)

    def test_dead_end_on_title_side_falls_back_to_existing_nested_page(self):
        """긴 제목 쪽에서 경로가 끊기면 중첩 경로의 기존 페이지까지 탐색한다."""
        # 제목 쪽(F11) 아래에 '노트'가 없다고 거기 새로 만들면 안 된다. 중첩 쪽에 있는 페이지에 이어쓴다.
        _, err, wiki = run("wiki-write", "AI BSM > SUMO > HD Map > SUMO Network > 노트", "추가")
        self.assertIsNone(err)
        self.assertEqual("F1211", wiki.writes[0][1])

    def test_content_from_file_is_sent_unchanged(self):
        """파일 입력은 문장부호·셸 특수문자를 보존하고 계약대로 끝 줄바꿈만 제거한다."""
        import tempfile
        text = '# 실행 방법\n\n"따옴표"와 $변수, `백틱`\n'
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "note.md"
            path.write_text(text, encoding="utf-8")
            _, err, wiki = run("wiki-write", "Visualizer > 실행 방법", "--file", str(path))
        self.assertIsNone(err)
        self.assertEqual(text.rstrip("\n"), wiki.writes[0][3]["content"])

    def test_dry_run_reports_plan_without_writing(self):
        """실제 실행과 같은 대상 판단을 보여주되 생성·수정 요청은 보내지 않는다."""
        out, err, wiki = run("wiki-write", "Visualizer > test", "x", "--dry-run")
        self.assertEqual(("이어쓰기 예정: Snoopy > Visualizer > test\n", None, []), (out, err, wiki.writes))
        out, err, wiki = run("wiki-write", "--dry-run", "Visualizer > 새 페이지", "x")
        self.assertEqual(("생성 예정: Snoopy > Visualizer > 새 페이지\n", None, []), (out, err, wiki.writes))

    def test_mentions_become_member_links(self):
        """한글 사용자 멘션을 조직·구성원 ID가 포함된 Dooray 링크로 변환한다."""
        _, err, wiki = run("wiki-write", "Visualizer > test", "@홍길동 확인 부탁")
        self.assertIsNone(err)
        self.assertIn('[@홍길동](dooray://ORG/members/M1 "member") 확인 부탁', wiki.writes[0][2]["content"])

    def test_refuses_without_writing(self):
        """없는 중간 경로·중복 제목·빈 내용 등은 저장 요청 전에 설명과 함께 거부한다."""
        cases = {
            ("없는 > x", "내용"): "'Snoopy' 아래에 '없는' 페이지가 없습니다",  # 중간 페이지는 만들지 않는다
            ("중복", "내용"): "'중복' 페이지가 2개입니다",
            ("Visualizer >", "내용"): "쓰기 대상 페이지 이름이 필요합니다",
            ("Snoopy", "내용"): "쓰기 대상 페이지 이름이 필요합니다",
            ("Visualizer > test",): "내용이 필요합니다",
            ("HTML 페이지", "내용"): "HTML 본문 페이지에는 이어쓸 수 없습니다",
            ("Visualizer > test", "  "): "내용이 비어 있습니다",  # 빈 날짜 섹션을 만들지 않는다
            # dry-run도 실제 실행과 같은 검사(멘션 해석)를 거쳐야 '예정'을 믿을 수 있다.
            ("Visualizer > test", "@없는사람 확인", "--dry-run"): "'없는사람' 을(를) 찾을 수 없습니다",
        }
        for args, message in cases.items():
            _, err, wiki = run("wiki-write", *args)
            self.assertIn(message, err or "", args)
            self.assertEqual([], wiki.writes, args)


class WikiDownloadTest(unittest.TestCase):
    """읽기 결과의 파일 선택 번호와 위키 트리 모양의 저장 경로를 함께 검증한다."""

    def setUp(self):
        """실제 위키 폴더에 쓰지 않도록 테스트마다 비어 있는 임시 저장소를 만든다."""
        import tempfile
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        # 위키 제목 경로로 폴더를 만든다: Dooray/wiki/<위키이름>/<제목>/.../download/
        self.folder = Path(self.temp.name) / "Snoopy" / "측위 시험" / "download"

    def saved(self):
        """이번 테스트의 다운로드 파일명과 바이트를 모아 누락·덮어쓰기를 비교한다."""
        return {p.name: p.read_bytes() for p in self.folder.iterdir()} if self.folder.exists() else {}

    def test_omitted_target_saves_every_file_with_id_prefix(self):
        """대상을 생략하면 첨부와 이미지를 모두 ID가 포함된 파일명으로 저장한다."""
        out, err, _ = run("wiki-download", "측위 시험", wiki_dir=self.temp.name)
        self.assertIsNone(err)
        self.assertEqual({"91_계획서.xlsx": b"bytes-91", "92_그림.png": b"bytes-92"}, self.saved())
        self.assertIn("다운로드 완료: ", out)
        self.assertIn("— 이미지", out)

    def test_number_follows_wiki_read_file_list(self):
        """위키 읽기에 표시한 번호와 다운로드할 파일이 일치해야 한다."""
        _, err, _ = run("wiki-download", "측위 시험", "2", wiki_dir=self.temp.name)
        self.assertIsNone(err)
        self.assertEqual({"92_그림.png": b"bytes-92"}, self.saved())

    def test_name_picks_that_file(self):
        """전체 위키 경로와 파일명을 함께 지정해 해당 파일을 받을 수 있다."""
        _, err, _ = run("wiki-download", "Snoopy > 측위 시험", "계획서.xlsx", wiki_dir=self.temp.name)
        self.assertIsNone(err)
        self.assertEqual({"91_계획서.xlsx": b"bytes-91"}, self.saved())

    def test_refuses_without_saving(self):
        """대상이 없거나 잘못되면 오류를 알리고 다운로드 파일을 남기지 않는다."""
        cases = {
            ("측위 시험", "없음.txt"): "'없음.txt' 파일을 찾을 수 없습니다",
            ("Visualizer",): "받을 수 있는 파일이 없습니다",
            (): "위키 경로가 필요합니다",
        }
        for args, message in cases.items():
            _, err, _ = run("wiki-download", *args, wiki_dir=self.temp.name)
            self.assertIn(message, err or "", args)
            self.assertEqual({}, self.saved(), args)

    def test_folder_follows_real_titles_with_unsafe_characters_replaced(self):
        """제목 속 > 를 경로 계층으로 오인하지 않고 실제 제목 단위로 저장한다."""
        # 경로 조각(HD Map / SUMO Network)이 아니라 실제 제목 'HD Map > SUMO Network'로 폴더를 만들고,
        # Windows 폴더 이름에 못 쓰는 > 는 _ 로 바꾼다.
        out, err, _ = run("wiki-download", "AI BSM > SUMO > HD Map > SUMO Network", wiki_dir=self.temp.name)
        self.assertIsNone(err)
        folder = Path(self.temp.name) / "Snoopy" / "AI BSM" / "SUMO" / "HD Map _ SUMO Network" / "download"
        self.assertEqual(b"bytes-81", (folder / "81_맵.zip").read_bytes())


class WikiWriteLocalFilesTest(unittest.TestCase):
    """task-to-wiki 초안의 로컬 자료 업로드·링크 변환·보관을 검증한다.

    파일 바이트는 전달 여부를 확인하는 더미다. 서버의 실제 이미지 표시나 업로드 API는 호출하지 않는다.
    """

    # 같은 이미지의 반복 참조와 외부·기존 위키·앵커 링크를 섞어 변환할 대상만 고르는지 확인한다.
    DRAFT = ("설명\n![화면](<../files/화면 캡처.png>)\n[자료](../files/자료.txt)\n"
             "![화면 다시](<../files/화면 캡처.png>)\n[외부](https://example.com/a.png)\n"
             "![기존](/wikis/P1/files/999)\n[앵커](#설정)")
    REWRITTEN = ("설명\n![화면](/wikis/P1/files/A1)\n[자료](/wikis/P1/files/A2)\n"
                 "![화면 다시](/wikis/P1/files/A1)\n[외부](https://example.com/a.png)\n"
                 "![기존](/wikis/P1/files/999)\n[앵커](#설정)")

    def setUp(self):
        """초안 폴더와 자료 폴더를 분리해 파일명·상대 경로 처리 조건을 만든다."""
        import tempfile
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        (self.root / "files").mkdir()
        (self.root / "files" / "화면 캡처.png").write_bytes(b"png-bytes")
        (self.root / "files" / "자료.txt").write_bytes(b"txt-bytes")
        self.drafts = self.root / "wiki"
        self.drafts.mkdir()

    def draft(self, text, name="242_정리.md"):
        """지정한 본문을 UTF-8 초안으로 저장하고 CLI에 넘길 실제 파일 경로를 돌려준다."""
        path = self.drafts / name
        path.write_text(text, encoding="utf-8")
        return path

    def write(self, *args, wiki=None):
        """이어쓰기 시각과 위키 보관 위치를 고정해 파일 처리 결과를 비교한다."""
        with mock.patch.object(DOORAY, "datetime", FixedNow):
            return run("wiki-write", *args, wiki=wiki, wiki_dir=self.drafts)

    def test_append_uploads_each_local_file_once_and_rewrites_only_local_refs(self):
        """같은 자료는 한 번만 올리고 로컬 링크만 바꾼 뒤 기존 본문에 이어쓴다."""
        out, err, wiki = self.write("Visualizer > test", "--file", str(self.draft(self.DRAFT)))
        self.assertIsNone(err)
        self.assertEqual([
            ("upload", "C1", "화면 캡처.png", "inline_image", "image/png"),
            ("upload", "C1", "자료.txt", "general", "text/plain"),
            ("update", "C1", {"mimeType": MD, "content": f"기존 본문\n\n## 26-10-27, 09:05\n\n{self.REWRITTEN}"}),
        ], wiki.writes)
        self.assertEqual(b"png-bytes", wiki.uploaded["화면 캡처.png"])
        self.assertIn("이어쓰기 완료: Snoopy > Visualizer > test", out)

    def test_create_makes_page_then_uploads_then_rewrites_body(self):
        """업로드 대상 페이지가 먼저 필요하므로 생성→업로드→참조를 바꾼 본문 수정 순서다."""
        _, err, wiki = self.write("Visualizer > 새 문서", "--file", str(self.draft("![화면](<../files/화면 캡처.png>)")))
        self.assertIsNone(err)
        self.assertEqual([
            ("create", "C", "새 문서", {"mimeType": MD, "content": "![화면](<../files/화면 캡처.png>)"}),
            ("upload", "N1", "화면 캡처.png", "inline_image", "image/png"),
            ("update", "N1", {"mimeType": MD, "content": "![화면](/wikis/P1/files/A2)"}),
        ], wiki.writes)

    def test_dry_run_lists_planned_uploads_without_uploading(self):
        """이미지와 첨부의 예정 목록을 보여주되 파일 업로드와 본문 저장은 수행하지 않는다."""
        out, err, wiki = self.write("Visualizer > test", "--file", str(self.draft(self.DRAFT)), "--dry-run")
        self.assertIsNone(err)
        self.assertEqual("이어쓰기 예정: Snoopy > Visualizer > test\n"
                         "업로드 예정: 화면 캡처.png (이미지)\n업로드 예정: 자료.txt (첨부)\n", out)
        self.assertEqual([], wiki.writes)

    def test_missing_local_file_stops_before_any_write(self):
        """자료가 하나라도 없으면 일부만 올리는 대신 실제 실행·dry-run 모두 거부한다."""
        draft = self.draft("![없음](../files/없는그림.png)\n![화면](<../files/화면 캡처.png>)")
        for extra in ((), ("--dry-run",)):
            _, err, wiki = self.write("Visualizer > test", "--file", str(draft), *extra)
            self.assertIn("로컬 파일이 없습니다", err or "", extra)
            self.assertIn("없는그림.png", err or "", extra)
            self.assertEqual([], wiki.writes, extra)

    def test_upload_failure_after_create_reports_created_page(self):
        """페이지 생성 뒤 업로드가 실패해도 이미 만들어진 페이지 주소를 사용자에게 알린다."""
        wiki = FakeWiki()

        def failing_upload(*a):
            raise SystemExit("파일 업로드 실패 (HTTP 500)")
        wiki.upload = failing_upload
        _, err, wiki = self.write("Visualizer > 새 문서", "--file",
                                  str(self.draft("![화면](<../files/화면 캡처.png>)")), wiki=wiki)
        self.assertIn("파일 업로드 실패 (HTTP 500)", err)
        self.assertIn("페이지는 만들어졌지만", err)
        self.assertIn("https://acme.dooray.com/wiki/W1/N1", err)
        self.assertEqual(["create"], [w[0] for w in wiki.writes])

    @unittest.skipUnless(os.name == "nt", "Windows drive-letter path test")
    def test_windows_absolute_path_is_uploaded_not_published(self):
        """Windows 드라이브 경로를 외부 URL로 오인해 본문에 그대로 남기지 않는다."""
        # 'C:' 를 URL 스킴으로 오인하면 죽은 로컬 경로가 그대로 위키에 실린다.
        image = (self.root / "files" / "화면 캡처.png").resolve()
        _, err, wiki = self.write("Visualizer > test", "--file", str(self.draft(f"![화면](<{image}>)")))
        self.assertIsNone(err)
        self.assertEqual(("upload", "C1", "화면 캡처.png", "inline_image", "image/png"), wiki.writes[0])
        self.assertTrue(wiki.writes[-1][2]["content"].endswith("![화면](/wikis/P1/files/A1)"))

    def test_parentheses_in_plain_path_and_title_are_kept(self):
        """경로의 괄호와 링크의 제목 속성을 손상시키지 않고 참조 대상만 바꾼다."""
        (self.root / "files" / "log(1).txt").write_bytes(b"log")
        draft = self.draft('[로그](../files/log(1).txt)\n![화면](<../files/화면 캡처.png> "캡처")')
        _, err, wiki = self.write("Visualizer > test", "--file", str(draft))
        self.assertIsNone(err)
        self.assertEqual(["log(1).txt", "화면 캡처.png"], [w[2] for w in wiki.writes if w[0] == "upload"])
        self.assertTrue(wiki.writes[-1][2]["content"].endswith(
            '[로그](/wikis/P1/files/A1)\n![화면](/wikis/P1/files/A2 "캡처")'))

    def test_append_abort_after_upload_says_which_files_remain(self):
        """업로드 후 동시 편집을 감지하면 본문 저장을 중단하고 남은 첨부를 안내한다."""
        # 업로드 뒤 본문이 바뀌어 중단되면, 이미 올라간 파일이 페이지 첨부로 남는다는 걸 알려야 한다.
        wiki = FakeWiki()
        original_api, reads = wiki.api, [0]

        def api(path, method="GET", body=None, **params):
            if method == "GET" and path == "/wiki/v1/wikis/W1/pages/C1":
                reads[0] += 1
                if reads[0] == 2:
                    wiki.pages["C1"]["body"]["content"] = "다른 사람이 수정한 본문"
            return original_api(path, method, body, **params)
        wiki.api = api
        _, err, wiki = self.write("Visualizer > test", "--file",
                                  str(self.draft("![화면](<../files/화면 캡처.png>)")), wiki=wiki)
        self.assertIn("본문이 변경되어 이어쓰기를 중단했습니다", err)
        self.assertIn("이미 올라간 파일", err)
        self.assertIn("화면 캡처.png", err)
        self.assertEqual(["upload"], [w[0] for w in wiki.writes])

    def test_unexpected_error_after_create_still_reports_created_page(self):
        """응답 형식 오류처럼 예상 밖 예외여도 생성된 페이지의 존재와 주소를 숨기지 않는다."""
        wiki = FakeWiki()

        def broken_upload(*a):
            raise KeyError("attachFileId")
        wiki.upload = broken_upload
        _, err, wiki = self.write("Visualizer > 새 문서", "--file",
                                  str(self.draft("![화면](<../files/화면 캡처.png>)")), wiki=wiki)
        self.assertIn("페이지는 만들어졌지만", err)
        self.assertIn("https://acme.dooray.com/wiki/W1/N1", err)

    def test_move_draft_puts_draft_in_page_folder_and_numbers_duplicates(self):
        """게시한 초안을 페이지 폴더에 보관하고 같은 이름의 이전 초안은 덮어쓰지 않는다."""
        folder = self.drafts / "Snoopy" / "Visualizer" / "test"
        out, err, _ = self.write("Visualizer > test", "--file", str(self.draft("첫 정리")), "--move-draft")
        self.assertIsNone(err)
        self.assertEqual("첫 정리", (folder / "242_정리.md").read_text(encoding="utf-8"))
        self.assertFalse((self.drafts / "242_정리.md").exists())
        self.assertIn("초안 이동: ", out)
        _, err, _ = self.write("Visualizer > test", "--file", str(self.draft("둘째 정리")), "--move-draft")
        self.assertIsNone(err)
        self.assertEqual("둘째 정리", (folder / "242_정리_2.md").read_text(encoding="utf-8"))

    def test_moved_draft_keeps_pointing_at_the_same_local_files(self):
        """초안을 깊은 폴더로 옮겨도 이미지·첨부가 같은 원본을 가리키도록 경로를 조정한다."""
        # 더 깊은 페이지 폴더로 옮겨도 초안 속 상대 경로가 같은 파일을 가리켜야 미리보기·재업로드가 된다.
        draft = self.draft('앞\n![화면](<../files/화면 캡처.png>)\n[자료](../files/자료.txt "원본")\n[외부](https://example.com)')
        _, err, _ = self.write("Visualizer > test", "--file", str(draft), "--move-draft")
        self.assertIsNone(err)
        moved = self.drafts / "Snoopy" / "Visualizer" / "test" / "242_정리.md"
        self.assertEqual('앞\n![화면](<../../../../files/화면 캡처.png>)\n'
                         '[자료](../../../../files/자료.txt "원본")\n[외부](https://example.com)',
                         moved.read_text(encoding="utf-8"))
        self.assertEqual({(self.root / "files" / "화면 캡처.png").resolve(), (self.root / "files" / "자료.txt").resolve()},
                         set(DOORAY.local_files(moved.read_text(encoding="utf-8"), moved.parent)))

    def test_move_draft_follows_new_page_title(self):
        """새 페이지 생성 성공 시 실제 위키 제목 계층에 맞춰 초안 폴더를 만든다."""
        _, err, _ = self.write("Visualizer > 새 문서", "--file", str(self.draft("새 정리")), "--move-draft")
        self.assertIsNone(err)
        self.assertTrue((self.drafts / "Snoopy" / "Visualizer" / "새 문서" / "242_정리.md").exists())

    def test_draft_stays_when_dry_run_or_failure(self):
        """실패하거나 판단만 실행한 경우 검토 중인 원본 초안을 이동하지 않는다."""
        draft = self.draft("![없음](../files/없는그림.png)")
        self.write("Visualizer > test", "--file", str(draft), "--move-draft")
        self.assertTrue(draft.exists())
        ok = self.draft("정상", name="243_정리.md")
        self.write("Visualizer > test", "--file", str(ok), "--move-draft", "--dry-run")
        self.assertTrue(ok.exists())


class RedirectHostTest(unittest.TestCase):
    """업로드 리다이렉트에서 인증 토큰을 전달할 수 있는 호스트 범위를 제한한다."""

    # 업로드 307의 Location으로 토큰을 다시 보내므로, Dooray 호스트(https)만 허용해야 한다.
    def test_only_https_dooray_hosts_are_trusted(self):
        """Dooray HTTPS 호스트만 신뢰하고 유사 도메인·다른 스킴·빈 주소는 거부한다."""
        self.assertTrue(DOORAY.trusted_file_host("https://file-api.dooray.com/upload?x=1"))
        for url in ("https://evil.example.com/x", "https://dooray.com.evil.com/x",
                    "http://file-api.dooray.com/x", "https://evildooray.com/x", None, ""):
            self.assertFalse(DOORAY.trusted_file_host(url), url)


if __name__ == "__main__":
    unittest.main()
