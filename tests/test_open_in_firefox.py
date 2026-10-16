import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location(
    "open_in_firefox", Path(__file__).resolve().parents[1] / "scripts/open-in-firefox.py"
)
opener = importlib.util.module_from_spec(spec)
spec.loader.exec_module(opener)


class FirefoxLinkTests(unittest.TestCase):
    def test_local_mockup_link_opens_as_one_argument(self):
        url = "file:///tmp/My%20mockup.html?role=operator&touch=true#controls"
        copied = subprocess.CompletedProcess([], 0, f" {url}\n")
        with patch.object(opener.subprocess, "run", return_value=copied) as read, \
                patch.object(opener.subprocess, "Popen") as launch:
            self.assertEqual(opener.open_url("clipboard"), 0)

        self.assertEqual(read.call_args.args[0], ["xclip", "-selection", "clipboard", "-o"])
        launch.assert_called_once_with(["firefox", "--new-tab", url], start_new_session=True)

    def test_accepts_web_and_local_file_urls(self):
        for url in ("https://example.com", "http://localhost:3000", "file:///tmp/mockup.html",
                    "file://localhost/tmp/mockup.html"):
            with self.subTest(url=url):
                self.assertEqual(opener.web_url(url), url)

    def test_rejects_non_urls_and_unsupported_schemes(self):
        for value in ("", "some text", "https://", "file:relative.html", "file://remote/tmp/test.html",
                      "javascript:alert(1)", "--private-window", "http://localhost:99999",
                      "https://example.com\nhttps://other.example"):
            with self.subTest(value=value):
                self.assertIsNone(opener.web_url(value))


if __name__ == "__main__":
    unittest.main()
