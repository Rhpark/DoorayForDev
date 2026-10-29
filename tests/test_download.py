"""다운로드 대상 선택과 저장 파일명 규칙을 검증한다.

파일 목록을 메모리에서 만들어 번호·파일명 선택 결과만 확인한다.
실제 API 호출이나 파일 다운로드는 하지 않는다.
"""

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "Dooray" / "dooray.py"
SPEC = importlib.util.spec_from_file_location("dooray", MODULE_PATH)
DOORAY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DOORAY)

# 같은 이름에 서로 다른 ID와 출처를 부여해 이름 선택과 덮어쓰기 방지를 함께 확인한다.
FILES = [
    {"id": "1", "name": "로그.txt", "sources": ["첨부 목록"]},
    {"id": "2", "name": "a.png", "sources": ["본문"]},
    {"id": "3", "name": "a.png", "sources": ["댓글 9 (2026-10-27)"]},
]


class PickFilesTest(unittest.TestCase):
    """화면에 표시한 목록 순서와 사용자가 지정한 다운로드 대상이 일치해야 한다."""

    def test_omitted_or_all_picks_everything(self):
        """대상을 생략하거나 all을 대소문자와 무관하게 입력하면 전체를 선택한다."""
        self.assertEqual(FILES, DOORAY.pick_files(FILES, None))
        self.assertEqual(FILES, DOORAY.pick_files(FILES, "ALL"))

    def test_number_picks_one_in_collected_order(self):
        """사용자에게 보이는 1부터 시작하는 번호로 해당 파일 하나를 선택한다."""
        self.assertEqual([FILES[1]], DOORAY.pick_files(FILES, "2"))

    def test_name_picks_every_same_name(self):
        """동일 이름의 파일이 여러 출처에 있으면 누락하지 않고 모두 선택한다."""
        self.assertEqual(FILES[1:], DOORAY.pick_files(FILES, "a.png"))

    def test_unknown_name_or_out_of_range_number_exits_with_catalog(self):
        """잘못된 입력에는 받을 수 있는 목록을 제공하고 임의의 파일을 선택하지 않는다."""
        for target in ("없음.txt", "4", "0"):
            with self.assertRaises(SystemExit) as ctx:
                DOORAY.pick_files(FILES, target)
            self.assertIn("1. ID=1 로그.txt", str(ctx.exception.code))


class DownloadNameTest(unittest.TestCase):
    """파일명이 같아도 ID가 다른 원본은 서로 다른 저장 이름을 가져야 한다."""

    def test_id_prefix_keeps_same_names_apart(self):
        """파일 ID 접두사가 동일 이름의 본문·댓글 이미지를 구분한다."""
        self.assertEqual("2_a.png", DOORAY.download_name(FILES[1]))
        self.assertEqual("3_a.png", DOORAY.download_name(FILES[2]))


if __name__ == "__main__":
    unittest.main()
