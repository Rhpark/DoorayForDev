"""위지윅 HTML 본문을 터미널에서 읽을 수 있는 텍스트로 바꾸는 규칙을 검증한다.

태그 제거뿐 아니라 문단·목록·표의 구분, 링크 주소와 이미지 존재 표시를 확인한다.
HTML이 아닌 마크다운은 원문을 유지하며 네트워크나 파일 저장을 사용하지 않는다.
"""

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "Dooray" / "dooray.py"
SPEC = importlib.util.spec_from_file_location("dooray", MODULE_PATH)
DOORAY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DOORAY)


class HtmlBodyTest(unittest.TestCase):
    """본문 형식에 맞춰 읽기용 표시를 만들고 문서의 주요 정보를 보존한다."""

    def test_markdown_body_is_untouched(self):
        """마크다운 안의 HTML 문법을 위지윅 본문으로 오인해 변환하지 않는다."""
        body = {"mimeType": "text/x-markdown", "content": "# 제목\n\n- 항목 <b>주의</b>"}
        self.assertEqual("# 제목\n\n- 항목 <b>주의</b>", DOORAY.body_text(body))

    def test_html_body_becomes_plain_text(self):
        """문단·목록의 줄 구분과 HTML 공백 문자를 읽을 수 있는 텍스트로 바꾼다."""
        body = {
            "mimeType": "text/html",
            "content": '<div>첫 줄</div><p>둘째&nbsp;줄</p><ul><li>가</li><li>나</li></ul>',
        }
        self.assertEqual("첫 줄\n둘째 줄\n- 가\n- 나", DOORAY.body_text(body))

    def test_link_keeps_url_and_image_leaves_marker(self):
        """링크의 목적지와 이미지 존재를 남기되 주소를 표시한 링크는 중복하지 않는다."""
        text = DOORAY.html_to_text(
            '<p><a href="https://x.test/a">문서</a> 참고</p>'
            '<p><a href="https://x.test/b">https://x.test/b</a></p>'
            '<p><img src="a.png" alt="설계도"></p>'
        )
        self.assertEqual("문서 (https://x.test/a) 참고\nhttps://x.test/b\n[이미지: 설계도]", text)

    def test_script_and_style_are_dropped(self):
        """스크립트와 스타일 정의를 사용자에게 보여주는 본문에 섞지 않는다."""
        text = DOORAY.html_to_text('<style>p{color:red}</style><p>본문</p><script>alert(1)</script>')
        self.assertEqual("본문", text)

    def test_table_cells_are_separated(self):
        """셀은 탭, 행은 줄바꿈으로 구분해 표의 열과 행을 읽을 수 있게 한다."""
        text = DOORAY.html_to_text('<table><tr><td>이름</td><td>값</td></tr><tr><td>a</td><td>1</td></tr></table>')
        self.assertEqual("이름\t값\na\t1", text)

    def test_missing_body_is_empty(self):
        """본문이 없는 응답도 예외 없이 빈 표시 문자열로 처리한다."""
        self.assertEqual("", DOORAY.body_text(None))


if __name__ == "__main__":
    unittest.main()
