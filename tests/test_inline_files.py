"""dooray.inline_files 검증.

Dooray API를 호출하지 않으므로 토큰·네트워크가 필요 없다. 정규식 파서라 조용히 깨지기 쉬워
(예: 속성 순서가 바뀌거나 대문자 태그가 오면 못 잡는 식) 경계 입력을 고정해 둔다.
"""
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "Dooray" / "dooray.py"
SPEC = importlib.util.spec_from_file_location("dooray", MODULE_PATH)
DOORAY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DOORAY)
inline_files = DOORAY.inline_files


def ids(body):
    """파싱 결과에서 ID만 추려 발견 순서와 중복 제거 여부를 비교한다."""
    return [f["id"] for f in inline_files(body)]


def names(body):
    """파싱 결과의 파일명만 추려 alt 처리와 이름 보정 규칙을 확인한다."""
    return [f["name"] for f in inline_files(body)]


class InlineFilesTest(unittest.TestCase):
    """Dooray 본문에 실제 사용되는 HTML·마크다운 이미지 표기를 모두 인식한다."""

    def test_html_img(self):
        """HTML 이미지에서 로컬 파일만 추출하고 순서·중복·저장 이름 규칙을 보존한다."""
        # 입력이 없거나 태그가 없으면 빈 목록. None도 허용해야 한다
        # (post_detail의 body.content가 없을 수 있다).
        self.assertEqual([], inline_files(None))
        self.assertEqual([], inline_files(""))
        self.assertEqual([], inline_files("본문에 /files/123 문자열만 있고 img 태그는 없다"))

        # 실제 업무 #57 본문 형태
        real = '<img src="/files/4401766189020297179" alt="Inline-image-2026-08-18 15.43.42.133.png" width="982" />'
        self.assertEqual(["4401766189020297179"], ids(real))
        self.assertEqual(["Inline-image-2026-08-18 15.43.42.133.png"], names(real))

        # 같은 이미지를 두 번 참조해도 한 번만 내려받아야 한다
        self.assertEqual(["11"], ids('<img src="/files/11" alt="a.png"/><img src="/files/11" alt="a.png"/>'))

        # 서로 다른 이미지는 본문 순서를 유지한다
        self.assertEqual(["11", "22"], ids('<img src="/files/11" alt="a.png"/><img src="/files/22" alt="b.png"/>'))

        # Dooray 외부 호스트 이미지는 이 API로 받을 수 없으므로 후보에 넣지 않는다
        self.assertEqual([], inline_files('<img src="https://example.com/y.png" alt="z.png"/>'))

        # alt가 없거나 비면 id로 이름을 만든다(파일명이 비면 저장할 수 없다)
        self.assertEqual(["inline-33.png"], names('<img src="/files/33" width="10"/>'))
        self.assertEqual(["inline-44.png"], names('<img src="/files/44" alt=""/>'))

        # 파일명에 쓸 수 없는 문자는 치환한다(Windows: : / \ * ? " < > |)
        self.assertEqual(["a_b_c_d.png"], names('<img src="/files/55" alt="a:b/c*d.png"/>'))

        # 속성 순서와 대소문자에 의존하지 않는다
        self.assertEqual(["66"], ids('<img alt="e.png" src="/files/66"/>'))
        self.assertEqual(["77"], ids('<IMG SRC="/files/77" ALT="f.png">'))

    def test_markdown_img(self):
        """마크다운과 HTML이 섞여도 이미지 누락 없이 본문의 등장 순서를 유지한다."""
        # 실제 업무 #60 본문 형태. HTML <img>만 알던 시절 여기서 0건이 나와
        # "받을 수 있는 파일이 없습니다"로 오판했다. mimeType은 #53·#57·#60 모두
        # text/x-markdown이라 표기 형태를 알려주지 않는다 — 둘 다 훑어야 한다.
        md = "![Inline-image-2026-08-18 16.32.56.350.png](/files/4401790971210844557)"
        self.assertEqual(["4401790971210844557"], ids(md))
        self.assertEqual(["Inline-image-2026-08-18 16.32.56.350.png"], names(md))

        # 마크다운도 alt가 비면 id로 이름을 만들고, 못 쓰는 문자는 치환한다
        self.assertEqual(["inline-88.png"], names("![](/files/88)"))
        self.assertEqual(["a_b_c_d.png"], names("![a:b/c*d.png](/files/99)"))

        # 외부 호스트는 마크다운에서도 후보가 아니다
        self.assertEqual([], inline_files("![z.png](https://example.com/y.png)"))

        # 이미지가 아닌 마크다운 링크는 이미지가 아니다(느낌표가 없으면 첨부가 아니라 본문 링크)
        self.assertEqual([], inline_files("[첨부 보기](/files/123)"))

        # 두 문법이 섞여도 본문 등장 순서를 유지한다
        mixed = '![a.png](/files/11)<img src="/files/22" alt="b.png"/>![c.png](/files/33)'
        self.assertEqual(["11", "22", "33"], ids(mixed))

        # 같은 이미지를 두 문법으로 참조해도 한 번만 담는다
        self.assertEqual(["11"], ids('<img src="/files/11" alt="a.png"/>![a.png](/files/11)'))


if __name__ == "__main__":
    unittest.main()
