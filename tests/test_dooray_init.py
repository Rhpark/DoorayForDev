import importlib.util
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "Dooray" / "dooray.py"
SPEC = importlib.util.spec_from_file_location("dooray", MODULE_PATH)
DOORAY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DOORAY)


class DoorayInitTest(unittest.TestCase):
    def test_help_does_not_require_config(self):
        self.assertIn("dooray read", DOORAY.__doc__)

    def test_installs_posix_launcher_with_executable_permission(self):
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
            if os.name != "nt":
                self.assertTrue(launcher.stat().st_mode & stat.S_IXUSR)

    def test_installs_windows_launcher(self):
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
