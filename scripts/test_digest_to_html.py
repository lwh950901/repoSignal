#!/usr/bin/env python3
"""Regression tests for the WeChat weekly digest HTML renderer."""

import subprocess
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
RENDERER = REPO / "scripts" / "digest-to-html.py"
TEMPLATE = REPO / ".codex" / "skills" / "wechat-weekly-digest" / "templates" / "wechat-template.html"


class _CellParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.td_styles = []

    def handle_starttag(self, tag, attrs):
        if tag == "td":
            self.td_styles.append(dict(attrs).get("style", ""))


def render_fixture():
    markdown = """# 开源雷达周刊

第一段导语

第二段导语

### 1. Example

**介绍：** 示例项目。

| 角色 | 项目 | 入选理由 |
|---|---|---|
| 数据入口 | owner/example | a-very-long-unbroken-reason-token |
"""
    with tempfile.TemporaryDirectory() as tmpdir:
        source = Path(tmpdir) / "2026-W38.md"
        source.write_text(markdown, encoding="utf-8")
        result = subprocess.run(
            ["python3", str(RENDERER), str(source)],
            check=True,
            capture_output=True,
            text=True,
        )
    return result.stdout


class DigestToHtmlStyleTests(unittest.TestCase):
    def test_copy_keeps_article_heading(self):
        html = render_fixture()

        self.assertNotIn("h1.style.display = 'none'", html)
        self.assertNotIn("hidden.push(h1)", html)

    def test_intro_label_uses_deep_sea_blue(self):
        html = render_fixture()

        self.assertIn(
            '<strong style="color:#0b3d66;">介绍：</strong>',
            html,
        )
        self.assertNotIn("<strong>介绍：</strong>", html)

    def test_every_table_cell_forces_long_content_to_wrap(self):
        html = render_fixture()
        parser = _CellParser()
        parser.feed(html)

        self.assertTrue(parser.td_styles)
        self.assertTrue(
            all("word-break:break-all" in style for style in parser.td_styles),
            parser.td_styles,
        )

    def test_manual_template_follows_copy_and_intro_contract(self):
        html = TEMPLATE.read_text(encoding="utf-8")

        self.assertNotIn("h1.style.display = 'none'", html)
        self.assertNotIn("<strong>介绍：</strong>", html)
        self.assertIn(
            '<strong style="color:#0b3d66;">介绍：</strong>',
            html,
        )


if __name__ == "__main__":
    unittest.main()
