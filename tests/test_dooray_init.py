"""Dooray launcher 생성·갱신과 현재 OS에서의 도움말 실행을 검증한다.

설치 위치는 테스트마다 임시 폴더로 지정하고 PATH 충돌 조회를 생략한다.
실제 사용자 PATH·셸 프로필·레지스트리를 변경하는 init 명령은 실행하지 않는다.
launcher 내용은 양쪽 OS 형식을 확인하고, 프로세스 실행은 현재 OS 형식만 확인한다.
"""

import contextlib
import importlib.util
import io
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "Dooray" / "dooray.py"
SPEC = importlib.util.spec_from_file_location("dooray", MODULE_PATH)
DOORAY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DOORAY)


class DoorayInitTest(unittest.TestCase):
    """launcher의 소유권과 실행 경로를 보존하면서 반복 설치할 수 있어야 한다."""

    def test_help_does_not_require_config(self):
        """설정 읽기를 금지해도 CLI의 help 분기가 도움말을 출력하고 정상 종료한다."""
        output = io.StringIO()
        # 실제 설정을 읽거나 토큰을 사용하지 못하게 막아 초기화 순서의 회귀도 검출한다.
        with mock.patch.object(DOORAY, "load_config", side_effect=AssertionError("help must not load config")) as load_config, \
                mock.patch.object(sys, "argv", [str(MODULE_PATH), "help"]), \
                contextlib.redirect_stdout(output):
            self.assertIsNone(DOORAY.main())
        load_config.assert_not_called()
        self.assertIn("dooray read", output.getvalue())

    def test_installs_posix_launcher_with_executable_permission(self):
        """POSIX launcher가 지정한 Python을 사용하고 실행 가능한 파일로 만들어진다."""
        with tempfile.TemporaryDirectory() as temp:
            launcher = DOORAY.install_launcher(
                platform="linux",
                install_dir=Path(temp) / "bin",
                python_executable="/usr/bin/python3",
                check_path=False,
            )

            content = launcher.read_text(encoding="utf-8")
            self.assertIn(DOORAY.LAUNCHER_MARKER, content)
            self.assertIn("'/usr/bin/python3'", content)
            # Windows에서는 POSIX 실행 비트를 동일하게 다룰 수 없어 내용만 검증한다.
            if os.name != "nt":
                self.assertTrue(launcher.stat().st_mode & stat.S_IXUSR)

    def test_installs_windows_launcher(self):
        """Windows launcher는 실행한 저장소 루트의 Dooray 스크립트를 찾는다."""
        with tempfile.TemporaryDirectory() as temp:
            launcher = DOORAY.install_launcher(
                platform="windows",
                install_dir=Path(temp) / "bin",
                python_executable="C:/Python/python.exe",
                check_path=False,
            )

            self.assertEqual("dooray.cmd", launcher.name)
            content = launcher.read_text(encoding="utf-8")
            self.assertIn(DOORAY.LAUNCHER_MARKER, content)
            self.assertIn("%CD%\\Dooray\\dooray.py", content)

    @unittest.skipUnless(os.name == "nt", "Windows launcher integration test")
    def test_windows_launcher_runs_help(self):
        """생성한 cmd 파일이 현재 Python으로 도움말을 실행하고 UTF-8 결과를 돌려준다."""
        with tempfile.TemporaryDirectory() as temp:
            launcher = DOORAY.install_launcher(
                platform="windows",
                install_dir=Path(temp) / "bin",
                python_executable=sys.executable,
                check_path=False,
            )

            result = subprocess.run(
                ["cmd", "/c", str(launcher), "help"],
                cwd=MODULE_PATH.parents[1],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("dooray read", result.stdout)

    @unittest.skipIf(os.name == "nt", "POSIX launcher integration test")
    def test_posix_launcher_runs_help(self):
        """생성한 POSIX launcher를 실제 실행해 명령 전달과 종료 상태를 확인한다."""
        with tempfile.TemporaryDirectory() as temp:
            launcher = DOORAY.install_launcher(
                platform="linux",
                install_dir=Path(temp) / "bin",
                python_executable=sys.executable,
                check_path=False,
            )

            result = subprocess.run(
                [str(launcher), "help"],
                cwd=MODULE_PATH.parents[1],
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("dooray read", result.stdout)

    def test_does_not_overwrite_foreign_launcher(self):
        """Dooray 소유 표시가 없는 기존 파일은 다른 프로그램일 수 있어 덮어쓰지 않는다."""
        with tempfile.TemporaryDirectory() as temp:
            install_dir = Path(temp) / "bin"
            install_dir.mkdir()
            (install_dir / "dooray").write_text("foreign", encoding="utf-8")

            with self.assertRaises(RuntimeError):
                DOORAY.install_launcher(
                    platform="linux",
                    install_dir=install_dir,
                    python_executable="/usr/bin/python3",
                    check_path=False,
                )

    def test_updates_owned_launcher_idempotently(self):
        """같은 위치에 다시 설치하면 파일을 늘리지 않고 Python 경로를 갱신한다."""
        with tempfile.TemporaryDirectory() as temp:
            install_dir = Path(temp) / "bin"
            first = DOORAY.install_launcher(
                platform="linux",
                install_dir=install_dir,
                python_executable="/usr/bin/python3",
                check_path=False,
            )
            second = DOORAY.install_launcher(
                platform="linux",
                install_dir=install_dir,
                python_executable="/opt/python3",
                check_path=False,
            )

            self.assertEqual(first, second)
            self.assertIn("'/opt/python3'", second.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
