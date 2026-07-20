## ADDED Requirements

### Requirement: Generator aggregates repository-local monthly evidence
生成器 SHALL 读取指定自然月的候选 JSONL、日报 Markdown 和与该月相交的 ISO 周报，按小写 `owner/repo` 去重并合并发现日期与来源。

#### Scenario: Same repository appears in all sources
- **WHEN** 同一仓库以不同大小写出现在候选账本、日报和周报
- **THEN** 初稿只包含一个小写仓库条目，并列出三个来源与全部发现日期

### Requirement: Generator output is deterministic and non-published
生成器 MUST 对相同输入产生稳定排序和相同 Markdown，默认只写入被忽略的 `monthly-drafts/YYYY-MM.md`，网站构建 MUST NOT 读取该目录。

#### Scenario: Generator runs twice with unchanged input
- **WHEN** 编辑连续两次为同一月份运行生成器且数据未变化
- **THEN** 两份输出内容完全相同且已发布月报目录不被修改

### Requirement: Generator provides an offline self-check
生成器 SHALL 提供只使用 Python 3 标准库的 `--check` 模式，验证去重、来源合并、日期合并和渲染结果。

#### Scenario: Self-check runs in a clean environment
- **WHEN** 执行 `python3 scripts/generate_monthly_digest.py --check`
- **THEN** 命令无需网络和第三方 Python 依赖并以退出码 0 报告 PASS
