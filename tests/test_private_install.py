import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest


spec = importlib.util.spec_from_file_location(
    "private_install", Path(__file__).resolve().parents[1] / "install/private-config.py"
)
private_install = importlib.util.module_from_spec(spec)
spec.loader.exec_module(private_install)


class PrivateInstallationTests(unittest.TestCase):
    def test_preview_does_not_create_files(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            home = Path(temporary_directory) / "new-home"
            private_install.install_config(home)
            self.assertFalse(home.exists())

    def test_backup_preserves_files_directories_and_symlink_targets_on_repeated_install(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            home = Path(temporary_directory)
            original_config = home / "original-i3"
            original_config.mkdir()
            (original_config / "config").write_text("keep original")
            (home / ".config").mkdir()
            (home / ".config/i3").symlink_to(original_config, target_is_directory=True)
            (home / ".bashrc").write_text("keep bashrc")
            (home / ".bash_secrets").write_text("keep secrets")

            backup = private_install.install_config(home, apply=True)
            self.assertEqual((backup / ".bashrc").read_text(), "keep bashrc")
            self.assertTrue((backup / ".config/i3").is_symlink())
            self.assertEqual((original_config / "config").read_text(), "keep original")
            self.assertEqual((home / ".bash_secrets").read_text(), "keep secrets")
            self.assertFalse((home / ".config/i3").is_symlink())

            (home / ".config/i3/config").write_text("private customization")
            second_backup = private_install.install_config(home, apply=True)
            self.assertNotEqual(backup, second_backup)
            self.assertEqual((second_backup / ".config/i3/config").read_text(), "private customization")

    def test_installed_profile_has_no_work_rules_and_has_valid_shell_scripts(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            home = Path(temporary_directory)
            private_install.install_config(home, apply=True)
            i3_config = (home / ".config/i3/config").read_text()
            aliases = (home / ".bash_aliases").read_text()
            menu = (home / ".config/scripts/system-menu.sh").read_text()
            blocks = (home / ".config/i3/i3blocks.conf").read_text()
            self.assertNotIn("xinput set-prop", i3_config)
            self.assertNotIn("crx_", i3_config)
            self.assertNotIn("Slack", i3_config)
            self.assertNotIn("jira-", aliases)
            self.assertNotIn("stand-up-timer", blocks)
            self.assertIn("command=$HOME/.config/i3/hydration-reminder", blocks)
            self.assertNotIn("/home/johan", (home / ".bashrc").read_text())
            self.assertNotIn("savePath", (home / ".config/flameshot/flameshot.ini").read_text())
            for relative_path in private_install.EXCLUDED_FILES:
                self.assertFalse((home / ".config" / relative_path).exists())
            for path in home.rglob("*"):
                if path.is_file():
                    with self.subTest(path=path.relative_to(home)):
                        content = path.read_text().lower()
                        self.assertNotIn("chatgpt", content)
                        self.assertNotIn("codex", content)
            for path in [home / ".bashrc", home / ".bash_aliases", *home.glob(".config/scripts/*.sh")]:
                subprocess.run(["bash", "-n", str(path)], check=True)


if __name__ == "__main__":
    unittest.main()
