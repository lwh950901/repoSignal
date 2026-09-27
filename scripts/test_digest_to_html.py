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


def render(markdown, week="2026-W38"):
    with tempfile.TemporaryDirectory() as tmpdir:
        source = Path(tmpdir) / f"{week}.md"
        source.write_text(markdown, encoding="utf-8")
        result = subprocess.run(
            ["python3", str(RENDERER), str(source)],
            check=True,
            capture_output=True,
            text=True,
        )
    return result.stdout


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
    return render(markdown)


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

    def test_role_header_variant_keeps_role_styling_and_reason_width(self):
        html = render(
            "# 开源雷达周刊\n\n## 本周可行性精选\n### 可行性方案 1：示例\n\n"
            "**组合方案**：\n\n| 试验角色 | 项目 | 首先验证什么 |\n|---|---|---|\n"
            "| 受控移动端任务样本 | ARTEMIS | 在隔离模拟器中运行固定任务。 |\n"
        )
        parser = _CellParser()
        parser.feed(html)

        self.assertIn("color:#ff7a1a", parser.td_styles[0])
        self.assertIn("width:13%", parser.td_styles[0])
        self.assertIn("width:67%", parser.td_styles[-1])

    def test_plan_verdict_line_renders_pill_verbatim(self):
        html = render(
            "# 开源雷达周刊\n\n## 本周可行性精选\n### 可行性方案 1：示例\n\n"
            "**方案判断**：值得技术试验。技术组合成熟度 93/100，需求证据强度 44/100。\n"
        )

        self.assertIn(
            '<strong style="color:#fff;background:#0b3d66;border-radius:999px;'
            'padding:2px 12px;font-size:15px;">值得技术试验</strong>'
            "。技术组合成熟度 93/100，需求证据强度 44/100。",
            html,
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
