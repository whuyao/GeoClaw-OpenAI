from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from geoclaw_qgis.web.app import (
    _page_html,
    create_session,
    delete_session,
    extract_output_links,
    list_sessions,
    load_session_detail,
)


class TestWebApp(unittest.TestCase):
    def test_page_template_has_responsive_layout_and_bottom_scroll_logic(self) -> None:
        html = _page_html()
        self.assertIn("height: 100dvh;", html)
        self.assertIn("overflow: hidden;", html)
        self.assertIn("function scrollChatToBottom", html)
        self.assertIn("window.addEventListener(\"resize\"", html)
        self.assertIn("UrbanComp Lab @ China University of Geosciences (Wuhan)", html)
        self.assertIn("https://github.com/whuyao/GeoClaw-OpenAI", html)
        self.assertIn("License: MIT", html)
        self.assertIn("TrackIntel-based mobility/network analysis algorithms", html)

    def test_session_crud(self) -> None:
        old = dict(os.environ)
        try:
            with tempfile.TemporaryDirectory() as tmp:
                os.environ["GEOCLAW_OPENAI_HOME"] = str(Path(tmp) / "home")
                created = create_session("demo_web_session")
                self.assertEqual(created["session_id"], "demo_web_session")

                sessions = list_sessions()
                self.assertTrue(any(x.get("session_id") == "demo_web_session" for x in sessions))

                detail = load_session_detail("demo_web_session")
                self.assertEqual(detail["session_id"], "demo_web_session")
                self.assertEqual(detail["turn_count"], 0)

                deleted = delete_session("demo_web_session")
                self.assertTrue(deleted["deleted"])
        finally:
            os.environ.clear()
            os.environ.update(old)

    def test_extract_output_links_filters_to_allowed_roots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "data" / "outputs"
            out.mkdir(parents=True, exist_ok=True)
            report = out / "demo_report.md"
            report.write_text("ok", encoding="utf-8")

            other = root / "tmp" / "secret.txt"
            other.parent.mkdir(parents=True, exist_ok=True)
            other.write_text("x", encoding="utf-8")

            payload = {
                "chat": {"reply": "see data/outputs/demo_report.md and tmp/secret.txt"},
                "execution": {"stdout": str(report)},
            }
            links = extract_output_links(payload, workspace_root=root)
            paths = {x["path"] for x in links}
            self.assertIn(str(report.resolve()), paths)
            self.assertNotIn(str(other.resolve()), paths)

    def test_session_detail_with_turns(self) -> None:
        old = dict(os.environ)
        try:
            with tempfile.TemporaryDirectory() as tmp:
                os.environ["GEOCLAW_OPENAI_HOME"] = str(Path(tmp) / "home")
                created = create_session("detail_case")
                path = Path(created["path"])
                payload = json.loads(path.read_text(encoding="utf-8"))
                payload["turns"] = [{"user": "u1", "assistant": "a1", "time": "2026-03-11T00:00:00Z"}]
                path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

                detail = load_session_detail("detail_case")
                self.assertEqual(detail["turn_count"], 1)
                self.assertEqual(detail["turns"][0]["assistant"], "a1")
        finally:
            os.environ.clear()
            os.environ.update(old)


if __name__ == "__main__":
    unittest.main()
