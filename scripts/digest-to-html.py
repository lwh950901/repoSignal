#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""digest-to-html.py — 把去链接后的仓库雷达周报 md 转成微信排版 HTML（雷达屏样式，含一键复制按钮）。

用法: digest-to-html.py <input.md> [output.html]   (默认输出到 stdout)
样式规范: 见 skill 的 references/wechat-style-guide.md（方案 A 雷达屏，左对齐）
"""
import re
import sys

H1 = '<h1 style="font-size:22px;font-weight:bold;color:#0b3d66;margin:0 0 24px;">{}</h1>'
H2 = '<h2 style="font-size:18px;font-weight:bold;color:#0b3d66;border-left:4px solid #ff7a1a;padding-left:10px;margin:30px 0 6px;">{}</h2>'
P = '<p style="margin:10px 0;">{}</p>'
INTRO = '<p style="font-size:14px;color:#5c6b7a;margin:10px 0;">{}</p>'
NOTE = ('<p style="font-size:15px;color:#5c6b7a;background:#eef3f7;border-left:3px solid #c7d3de;'
        'padding:10px 12px;margin:10px 0;"><strong style="color:#999;">注意：</strong> {}</p>')
READMORE = '<p style="font-size:14px;color:#8a95a1;margin:10px 0;"><strong>阅读全文：</strong> {}</p>'
CARD_OPEN = '<section style="background:#eef3f7;border-radius:8px;padding:14px 18px;margin-top:20px;">'
CARD_CLOSE = '</section>'
CARD_TITLE = '<p style="font-weight:bold;color:#222;margin:0 0 6px;">{}</p>'
CARD_P = '<p style="font-size:15px;color:#555;margin:0;">{}</p>'
HR = '<hr style="border:none;border-top:1px solid #e3e9ef;margin:28px 0 20px;">'

BADGE = ('<span style="display:inline-block;width:26px;height:26px;line-height:26px;text-align:center;'
         'border-radius:50%;background:#ff7a1a;color:#fff;font-size:15px;font-weight:bold;'
         'margin-right:6px;">{}</span>')
NAME_SPAN = '<span style="color:#0b3d66;">{}</span>'

CODE = '<code style="font-family:Menlo,Consolas,monospace;background:#eef3f7;border-radius:3px;padding:1px 5px;font-size:15px;">{}</code>'

COPY_BUTTON = ('<button id="copyArticleBtn" style="position:fixed;right:20px;bottom:24px;z-index:9999;'
               'font-family:-apple-system,\'PingFang SC\',\'Microsoft YaHei\',sans-serif;font-size:14px;'
               'color:#fff;background:#ff7a1a;border:none;border-radius:999px;padding:10px 18px;'
               'box-shadow:0 4px 12px rgba(255,122,26,.35);cursor:pointer;">一键复制全文</button>')

COPY_SCRIPT = """<script>
(function(){
  var btn = document.getElementById('copyArticleBtn');
  if (!btn) return;
  btn.addEventListener('click', function(){
    var placeholders = document.querySelectorAll('section[style*="dashed"]');
    var hidden = [];
    placeholders.forEach(function(s){ s.style.display = 'none'; hidden.push(s); });
    var h1 = document.querySelector('body > section h1');
    if (h1) { h1.style.display = 'none'; hidden.push(h1); }
    var box = document.querySelector('body > section') || document.body;
    var r = document.createRange();
    r.selectNodeContents(box);
    var sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(r);
    var ok = false;
    try { ok = document.execCommand('copy'); } catch(e) { ok = false; }
    sel.removeAllRanges();
    hidden.forEach(function(s){ s.style.display = ''; });
    var old = btn.textContent;
    btn.textContent = ok ? '✅ 已复制，去公众号粘贴' : '❌ 复制失败，请手动框选正文';
    btn.style.background = ok ? '#0b3d66' : '#b00020';
    setTimeout(function(){ btn.textContent = old; btn.style.background = '#ff7a1a'; }, 2000);
  });
})();
</script>"""

COVER_PLACEHOLDER = ('<section style="border:2px dashed #c9d4e8;border-radius:8px;background:#f7f9fc;'
                     'color:#7a8aa5;font-size:14px;text-align:center;padding:18px 12px;margin-bottom:20px;">\n'
                     '【发布前删除】封面图占位：上传 public/covers/repository-radar-weekly-subtitle.png<br>\n'
                     '大封面 900×383，小封面另裁 1:1 方图（注意小封面会裁中间）\n</section>')
READ_PLACEHOLDER = ('<section style="border:2px dashed #c9d4e8;border-radius:8px;background:#f7f9fc;'
                    'color:#7a8aa5;font-size:14px;text-align:center;padding:14px 12px;margin-top:20px;">\n'
                    '【发布前删除】后台设置「阅读原文」→ 完整周报页面 URL（如已部署）\n</section>')

HEAD = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>开源雷达周刊 {week}（微信排版版）</title>
<!--
════════════════════════════════════════════════════════════
发布前操作清单（以下内容不进入正文）
1. 标题（三选一，≤30 字）：
   A. 每周 10 个开源项目｜从 PDF 解析到 Agent 安全，先试最小链路
   B. 开源雷达 {week}：这周值得动手的 10 个工具，两个和 Agent 直接相关
   C. PDF 先分类再 OCR、命令输出先压缩再进上下文——本周 10 个开源项目
2. 摘要（勾选原创后可填，120 字内）：
   本周开源项目精选——先验证最小链路，再决定是否进入团队基础设施。
3. 封面图：上传 public/covers/repository-radar-weekly-subtitle.png
   （大封面 900×383，小封面另裁 1:1 方图）
4. 发布时删除正文中两个【发布前删除】占位框
5. 后台「阅读原文」指向完整周报页面 URL（如已部署）
6. 勾选「原创」，添加话题标签：#开源项目 #开发者工具 #AI 编程
正文文字由脚本自动生成，与原版周报逐字一致（已通过 verify-text.sh 校验）。
════════════════════════════════════════════════════════════
-->
</head>
<body style="margin:0;padding:0;">

{button}

<section style="font-family:-apple-system,BlinkMacSystemFont,'Helvetica Neue','PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif;color:#1c2733;font-size:16px;line-height:1.9;letter-spacing:0.5px;max-width:680px;margin:0 auto;padding:24px 16px;">
"""


def inline(s):
    """行内标记：`code` -> <code>，**bold** -> <strong>"""
    s = re.sub(r'`([^`]+)`', lambda m: CODE.format(m.group(1)), s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
    return s


def make_h3(body):
    m = re.match(r'(\d+)\.\s*(.*)', body)
    if not m:
        return '<h3 style="font-size:17px;font-weight:bold;color:#1c2733;margin:22px 0 4px;">{}</h3>'.format(inline(body))
    num = m.group(1) + '.'
    rest = m.group(2)
    if '：' in rest:
        name, _, title = rest.partition('：')
    else:
        name, title = rest, ''
    parts = [BADGE.format(num), ' ']
    if name:
        parts.append(NAME_SPAN.format(inline(name)))
    if title:
        parts.append('：' + inline(title))
    return '<h3 style="font-size:17px;font-weight:bold;color:#1c2733;margin:22px 0 4px;">' + ''.join(parts) + '</h3>'


def main():
    if len(sys.argv) < 2:
        sys.stderr.write('usage: digest-to-html.py <input.md> [output.html]\n')
        sys.exit(2)
    src = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else None
    with open(src, 'r', encoding='utf-8') as f:
        md = f.read()

    week = '2026-WXX'
    m = re.search(r'(\d{4}-W\d+)', src)
    if m:
        week = m.group(1)

    out = [HEAD.format(week=week, button=COPY_BUTTON), COVER_PLACEHOLDER, '']

    in_card = False
    seen_h1 = False
    intro_left = 0

    def close_card():
        nonlocal in_card
        if in_card:
            out.append(CARD_CLOSE)
            in_card = False

    for raw in md.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith('# '):
            close_card()
            out.append(H1.format(inline(line[2:])))
            seen_h1 = True
            intro_left = 2
        elif line.startswith('### '):
            close_card()
            out.append(make_h3(line[4:]))
        elif line.startswith('## '):
            close_card()
            out.append(H2.format(inline(line[3:])))
        elif line.startswith('---'):
            close_card()
            out.append(HR)
        elif line.startswith('**关于仓库雷达**'):
            out.append(CARD_OPEN)
            out.append(CARD_TITLE.format('关于仓库雷达'))
            in_card = True
        elif line.startswith('**阅读全文：**'):
            close_card()
            out.append(READMORE.format(inline(line[len('**阅读全文：**'):].lstrip())))
        elif line.startswith('**注意：**'):
            close_card()
            out.append(NOTE.format(inline(line[len('**注意：**'):].lstrip())))
        elif line.startswith('**介绍：**'):
            close_card()
            out.append(P.format('<strong>介绍：</strong> ' + inline(line[len('**介绍：**'):].lstrip())))
        elif line.startswith('**推荐依据：**'):
            close_card()
            out.append(P.format('<strong>推荐依据：</strong> ' + inline(line[len('**推荐依据：**'):].lstrip())))
        elif line.startswith('**适合：**'):
            close_card()
            out.append(P.format('<strong>适合：</strong> ' + inline(line[len('**适合：**'):].lstrip())))
        else:
            if in_card:
                out.append(CARD_P.format(inline(line)))
            elif seen_h1 and intro_left > 0:
                out.append(INTRO.format(inline(line)))
                intro_left -= 1
            else:
                out.append(P.format(inline(line)))

    close_card()
    out.append(READ_PLACEHOLDER)
    out.append('</section>\n\n' + COPY_SCRIPT + '\n</body>\n</html>\n')

    result = '\n'.join(out)
    if out_path:
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(result)
    else:
        sys.stdout.write(result)


if __name__ == '__main__':
    main()
