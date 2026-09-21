# 雷达屏样式规范（方案 A，已定稿）

默认样式方案。所有值均为微信编辑器可保留的内联样式。

## 色板

| 角色 | 值 | 用途 |
| --- | --- | --- |
| 底色 | `#ffffff` | 页面背景 |
| 正文 | `#1c2733` | 段落文字 |
| 主色 | `#0b3d66` 深海蓝 | h1、h2、介绍标签、项目名 |
| 强调 | `#ff7a1a` 信号橙 | 编号徽章、h2 左竖条、复制按钮 |
| 导语 | `#5c6b7a` 石板灰 | 标题下两段引言（14px） |
| 注意文字 | `#5c6b7a` | 注意段 |
| 卡片/代码底 | `#eef3f7` | 注意段、关于仓库雷达、代码 |
| 弱化 | `#8a95a1` | 阅读全文行 |
| 表格边框 | `#e9eef4` | 组合方案表格单元格边框 |
| 徽章底 | `#0b3d66` 深海蓝 | 方案评分胶囊（白字）、表格表头 |

## 元素规范

- 外层容器：16px、line-height 1.9、letter-spacing 0.5px、max-width 680px、padding 24px 16px（微信会忽略 max-width，无需处理）
- h1：22px、`#0b3d66`、**左对齐**、margin 0 0 24px
- **导语（h1 下两段）**：14px、`#5c6b7a`、margin 10px 0——比正文小一档、颜色轻一档，作为引言层次
- h2：18px、`#0b3d66`、`border-left:4px solid #ff7a1a`、padding-left 10px、margin 30px 0 6px
- h3 编号徽章（10 个项目）：

  ```html
  <h3 style="font-size:17px;font-weight:bold;color:#1c2733;margin:22px 0 4px;">
    <span style="display:inline-block;width:26px;height:26px;line-height:26px;text-align:center;border-radius:50%;background:#ff7a1a;color:#fff;font-size:15px;font-weight:bold;margin-right:6px;">1.</span>
    <span style="color:#0b3d66;">pdf-inspector</span>：先判断 PDF，再决定是否调用 OCR
  </h3>
  ```

  徽章内文字保留原文编号格式（`1.` 带句点）；徽章与项目名之间有一个空格字符（保证文字流一致）。
- 段落：margin 10px 0
- 标签强度：介绍 `#0b3d66` 加粗（信息入口）；推荐依据/适合 黑色加粗；注意 灰色 `#999`
- 注意段：15px、`#5c6b7a`、background `#eef3f7`、`border-left:3px solid #c7d3de`、padding 10px 12px、margin 10px 0
- 行内代码：`font-family:Menlo,Consolas,monospace`、background `#eef3f7`、15px
- 阅读全文行：14px、`#8a95a1`、左对齐、margin 10px 0
- 关于仓库雷达：background `#eef3f7`、border-radius 8px、padding 14px 18px
- 分隔线：1px `#e3e9ef`
- 占位框（发布前删除）：2px dashed `#c9d4e8`、background `#f7f9fc`、文字 `#7a8aa5`

## 本周可行性精选（组合方案与风险）

有可行性章节时，它位于 10 个项目之后、"本周优先试用"之前。正文文字仍与 md 逐字一致；`|`、表格分隔行、行首 `- ` 属于 md 语法，不视为正文。

- **节引言**：`## 本周可行性精选` 后的第一段用导语样式（14px、`#5c6b7a`、margin 10px 0）
- **方案标题**（`### 可行性方案 N：…`）：17px、`#0b3d66`、`border-left:4px solid #ff7a1a`、padding-left 10px、margin 26px 0 10px（与 h2 同族、字号小一档）
- **方案评分**：标签黑色加粗；值做成深蓝胶囊（白字、background `#0b3d66`、border-radius 999px、padding 2px 12px、15px）；所在段 margin 10px 0 6px
- **组合方案表 → 真表格**（不再用卡片；`<table width:100% border-collapse:collapse cellpadding=0 cellspacing=0`、13px、margin 10px 0）：
  - 表头行 `<th>`：深海蓝底 `#0b3d66`、白字 13px 加粗、左对齐、`border 1px solid #0b3d66`、padding 5px 6px
  - 列宽：按表头语义推断——角色 13% / 项目 20% / 来源 15% / 许可证 10%（写在每行同名单元格内联 `width`），**入选理由列自动拿剩余宽度**（5 列时 42%，3 列精简表 67%）；「今日锚点组合」把项目定位整句写进角色列（最长约 60 字），此时角色列自动改用 35%（超过 20 字即触发，见 `ROLE_WIDE`/`ROLE_LABEL_MAX`），避免被压成竖排窄条并撑高整行。所以 3/4/5 列表都能紧凑显示；微信若过滤 width 则退回内容自适应
  - 数据行 `<td>`：`border 1px solid #e9eef4`、padding 5px 6px、`vertical-align:top`、`word-break:break-all`（防长仓库名/日期撑破窄屏，表格不横向溢出）
  - 列内语义：角色 13px 信号橙加粗；项目等宽字体 13px 深海蓝；来源 12px `#8a95a1`；许可证单元格内为细边框小标签（`border 1px solid #d9e1ea`、12px、radius 4px、padding 2px 6px）；理由 13px 正文色
  - 表头文字（角色 项目 来源 许可证 入选理由）即 md 表头行；全部单元格文本顺序与 md 逐行一致
- **风险条目**（行首 `- `）：保留 `-` 字形，包成橙色加粗 span（`color:#ff7a1a;font-weight:bold;margin-right:8px`），其余 15px `#1c2733`、margin 8px 0；行首空格由 margin 承担，不新增圆点等符号
- 可行性区内的行内代码与正文一致（Menlo/Consolas、background `#eef3f7`、15px）

## 一键复制按钮

- 位置：`position:fixed; right:20px; bottom:24px`，悬浮在页面角落，**在正文容器之外**（不会被复制进文章）
- 样式：橙色 `#ff7a1a` 圆角胶囊、白字 14px、阴影
- 行为（`<script>` 在 `</body>` 前）：
  - 点击 → 临时隐藏两个 dashed 占位框 → Range 选中正文容器 → `document.execCommand('copy')` → 恢复占位框
  - 成功：按钮变「✅ 已复制，去公众号粘贴」（深海蓝），2 秒后复原；失败：红色提示
  - 本地 `file://` 打开即可用，无需服务器
- 粘贴到微信编辑器后保留全部内联样式；`max-width`/`margin:0 auto` 会被微信过滤（宽度自动适配）

## 备选方案（不默认使用）

- **B 终端日志**：浅灰底 `#f6f7f8`、墨绿 `#0f6b4f`、琥珀 `#b45309`、编号用等宽字体渲染
- **C 规格书**：宋体标题（`"Songti SC",STSong,serif`）、靛蓝灰 `#37475a`、直角细线卡片（无圆角）、h2 用下边框线

## 微信兼容提醒

- 微信编辑器过滤 `max-width`、`margin:0 auto`（宽度自动适配）
- 会保留：行高、字距、背景色、边框、圆角
- 粘贴后用格式刷统一一遍，再手机预览检查字号与卡片效果
- 深色模式可能让浅底卡片发暗，重点检查注意段、"关于仓库雷达"卡片与组合方案表格
