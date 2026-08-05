import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "Dooray" / "dooray.py"
SPEC = importlib.util.spec_from_file_location("dooray", MODULE_PATH)
DOORAY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DOORAY)


class HtmlBodyTest(unittest.TestCase):
    def test_markdown_body_is_untouched(self):
        body = {"mimeType": "text/x-markdown", "content": "# 제목\n\n- 항목 <b>주의</b>"}
        self.assertEqual("# 제목\n\n- 항목 <b>주의</b>", DOORAY.body_text(body))

    def test_html_body_becomes_plain_text(self):
        body = {
            "mimeType": "text/html",
            "content": '<div>첫 줄</div><p>둘째&nbsp;줄</p><ul><li>가</li><li>나</li></ul>',
        }
        self.assertEqual("첫 줄\n둘째 줄\n- 가\n- 나", DOORAY.body_text(body))

    def test_link_keeps_url_and_image_leaves_marker(self):
        text = DOORAY.html_to_text(
            '<p><a href="https://x.test/a">문서</a> 참고</p>'
            '<p><a href="https://x.test/b">https://x.test/b</a></p>'
            '<p><img src="a.png" alt="설계도"></p>'
        )
        self.assertEqual("문서 (https://x.test/a) 참고\nhttps://x.test/b\n[이미지: 설계도]", text)

    def test_script_and_style_are_dropped(self):
        text = DOORAY.html_to_text('<style>p{color:red}</style><p>본문</p><script>alert(1)</script>')
        self.assertEqual("본문", text)

    def test_table_cells_are_separated(self):
        text = DOORAY.html_to_text('<table><tr><td>이름</td><td>값</td></tr><tr><td>a</td><td>1</td></tr></table>')
        self.assertEqual("이름\t값\na\t1", text)

    def test_missing_body_is_empty(self):
        self.assertEqual("", DOORAY.body_text(None))


if __name__ == "__main__":
    unittest.main()
