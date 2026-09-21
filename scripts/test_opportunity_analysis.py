import re
import tempfile
import unittest
from pathlib import Path

from scripts import opportunity_analysis as analysis


def plan_project(repo, tag, score=88, stars=100, tagline="", value="", risks="",
                 source_date="2026-09-14"):
    """构造一个带接口依据的组件项目（闭环门槛要求有输入输出描述）。"""
    return {
        "id": repo, "repo": repo, "url": "https://github.com/{}".format(repo),
        "score": score, "stars": stars, "tags": {tag: 5}, "source_date": source_date,
        "fields": {
            "tagline": tagline or "{} 提供可试用的接口与导出格式。".format(repo),
            "value": value or "可先小范围试用并记录产出。",
            "risks": risks, "quality": "", "activity": "", "metrics": "MIT",
        },
    }


def plan_steps(slots):
    return [(tag, role, plan_project("owner/{}".format(tag), tag))
            for tag, role in slots]


def make_combo(steps, business=None, track=analysis.TRACK_MATURE, run_date="2026-09-14",
               feedback=None):
    business = business or dict(analysis.TEMPLATE_BUSINESS[
        analysis.TEMPLATES[0]["name"]])
    combo = {
        "name": "测试方案", "origin": "template", "track": track,
        "business": business, "pitch": "测试定位", "target": business["customer"],
        "market": "【待验证假设】测试市场", "differentiation": "测试差异",
        "rationale": "测试依据", "mvp": "测试范围",
        "picks": {role: p for _, role, p in steps},
        "slot_supply": {tag: 30 for tag, _, _ in steps},
        "min_supply": 30, "total": len(steps), "today_count": len(steps),
        "stars": sum(p["stars"] for _, _, p in steps),
        "plan_family": "test-family", "variant": "test-variant",
    }
    return analysis.finalize_combo(combo, steps, feedback or [], run_date)


class DailyParsingTests(unittest.TestCase):
    def test_reusable_section_starts_a_new_project(self):
        markdown = """# GitHub 项目日报｜2026-09-21

### 学习型：owner/learner
- 一句话定位：提供带接口的学习工具。
- 实时指标：100 Stars · MIT

### 可复用型：owner/reusable
- 一句话定位：提供可复用的数据处理接口。
- 实时指标：200 Stars · Apache-2.0
"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "2026-09-21.md"
            path.write_text(markdown, encoding="utf-8")

            projects = analysis.parse_daily(path)

        self.assertEqual([p["repo_raw"] for p in projects],
                         ["owner/learner", "owner/reusable"])
        self.assertEqual([p["kind"] for p in projects], ["学习型", "可复用型"])
        self.assertEqual(projects[0]["fields"]["tagline"], "提供带接口的学习工具。")
        self.assertEqual(projects[1]["fields"]["tagline"],
                         "提供可复用的数据处理接口。")


class PlanIdentityTests(unittest.TestCase):
    def test_fixed_template_keeps_family_when_components_change(self):
        name = "本地优先个人 AI 工作台（组合 5 个项目，今日锚点 2 个）"

        self.assertEqual(analysis.plan_family(name), "local-first-personal-ai-workbench")
        self.assertEqual(
            analysis.plan_family(name),
            analysis.plan_family("本地优先个人 AI 工作台"),
        )
        self.assertNotEqual(
            analysis.plan_variant(["owner/one", "owner/two"]),
            analysis.plan_variant(["owner/one", "owner/three"]),
        )

    def test_variant_is_independent_of_component_order_and_case(self):
        expected = analysis.plan_variant(["Owner/One", "owner/two"])

        self.assertEqual(
            analysis.plan_variant(["OWNER/TWO", "owner/one", "owner/one"]),
            expected,
        )

    def test_legacy_markdown_derives_identity_from_heading_and_links(self):
        markdown = """# GitHub 项目组合可行性方案｜2026-08-29

## 可行性方案

### 1. 本地优先个人 AI 工作台（组合 2 个项目，今日锚点 1 个）

| 角色 | 项目 |
|---|---|
| 编排 | [`owner/one`](https://github.com/Owner/One) |
| 记忆 | [`owner/two`](https://github.com/owner/two) |

## 单点项目机会（供参考）
"""

        identities = analysis.parse_plan_identities(markdown)

        self.assertEqual(len(identities), 1)
        self.assertEqual(identities[0]["family"], "local-first-personal-ai-workbench")
        self.assertEqual(
            identities[0]["variant"],
            analysis.plan_variant(["owner/one", "owner/two"]),
        )
        self.assertEqual(identities[0]["repositories"], ["owner/one", "owner/two"])

    def test_explicit_identity_is_preserved_for_new_reports(self):
        markdown = """## 可行性方案

### 1. 自定义方案（组合 1 个项目）

**方案身份**：`plan_family=manual-family` · `variant=manual-variant`

| 角色 | 项目 |
|---|---|
| test | [`owner/one`](https://github.com/owner/one) |
"""

        identities = analysis.parse_plan_identities(markdown)

        self.assertEqual(identities[0]["family"], "manual-family")
        self.assertEqual(identities[0]["variant"], "manual-variant")


class ReuseAwareSelectionTests(unittest.TestCase):
    @staticmethod
    def project(repo, tag_score=5, stars=0):
        return {
            "id": repo,
            "repo": repo,
            "score": 85,
            "stars": stars,
            "tags": {"agent": tag_score},
            "fields": {"risks": "", "quality": "", "activity": ""},
        }

    def test_pick_best_penalizes_recent_component_reuse(self):
        frequent = self.project("owner/frequent", stars=1000)
        fresh = self.project("owner/fresh", stars=10)

        selected = analysis.pick_best(
            [frequent, fresh],
            "agent",
            set(),
            set(),
            reuse_counts={"owner/frequent": 3},
        )

        self.assertEqual(selected["id"], "owner/fresh")

    def test_portfolio_may_return_fewer_than_three_plans(self):
        a = self.project("owner/shared")
        b = self.project("owner/other")
        c = self.project("owner/third")
        combos = [
            {"name": "first", "score": 80, "today_count": 2, "total": 2,
             "stars": 100, "picks": {"agent": a, "memory": c}},
            # 与已选方案共享两个组件：超出容忍度，扣分后低于合格线
            {"name": "overlapping", "score": 74, "today_count": 2, "total": 2,
             "stars": 90, "picks": {"agent": a, "memory": c}},
            {"name": "below-threshold", "score": 69, "today_count": 3, "total": 1,
             "stars": 200, "picks": {"agent": b}},
        ]

        selected = analysis.select_combo_portfolio(combos, max_count=3)

        self.assertEqual([combo["name"] for combo in selected], ["first"])

    def test_portfolio_does_not_restore_rejected_candidates(self):
        combo = {
            "name": "blocked-quality",
            "score": 69,
            "today_count": 3,
            "total": 1,
            "stars": 100,
            "picks": {"agent": self.project("owner/only")},
        }

        self.assertEqual(analysis.select_combo_portfolio([combo]), [])


class FeasibilityRenderingTests(unittest.TestCase):
    def test_combo_table_only_exposes_role_project_and_reason(self):
        steps = plan_steps([("document", "文档解析"), ("rag", "检索/知识库"),
                            ("agent", "Agent 编排"), ("observability", "观测/评测")])
        combo = make_combo(steps)
        project = steps[0][2]

        report = analysis.render(
            [project], [project], [combo], "2026-09-07", "2026-06-09",
            "2026-09-07", 1, 0, None,
        )

        self.assertIn("| 角色 | 项目 | 入选理由 |", report)
        self.assertNotIn("| 角色 | 项目 | 来源 | 许可证 | 入选理由 |", report)
        self.assertIn(
            "| 文档解析 | [`owner/document`](https://github.com/owner/document) | "
            "可先小范围试用并记录产出。 |",
            report,
        )
        self.assertNotIn("**组件数据流**", report)
        self.assertNotIn("**接入方式**", report)


class AnchorBusinessNamingTests(unittest.TestCase):
    @staticmethod
    def project(repo, tags, tagline, stars=0):
        return {
            "id": repo,
            "repo": repo,
            "url": f"https://github.com/{repo}",
            "score": 85,
            "stars": stars,
            "tags": tags,
            "source_date": "2026-09-07",
            "fields": {
                "tagline": tagline,
                "risks": "",
                "quality": "",
                "activity": "",
                "metrics": "MIT",
            },
        }

    def test_plan_name_uses_scene_and_rarest_capability(self):
        supply = {"agent": 296, "local": 176, "rag": 91, "observability": 127}

        self.assertEqual(
            analysis.anchor_plan_name({"agent", "local", "rag", "observability"}, supply),
            "本地优先 · 知识增强 · Agent 工作台",
        )
        self.assertEqual(
            analysis.anchor_plan_name({"agent", "comm", "rag"}),
            "团队协作 · 知识增强 · Agent 工作台",
        )

    def test_plan_name_drops_missing_segments(self):
        self.assertEqual(
            analysis.anchor_plan_name({"agent", "local"}), "本地优先 · Agent 工作台")

    def test_plan_name_follows_pool_rarity(self):
        faces = {"agent", "local", "rag", "gateway"}

        self.assertEqual(
            analysis.anchor_plan_name(faces, {"rag": 91, "gateway": 169}),
            "本地优先 · 知识增强 · Agent 工作台",
        )
        self.assertEqual(
            analysis.anchor_plan_name(faces, {"rag": 500, "gateway": 10}),
            "本地优先 · 多模型 · Agent 工作台",
        )

    def test_every_capability_face_has_naming_words(self):
        for tag in analysis.TAG_RULES:
            self.assertIn(tag, analysis.ANCHOR_CORE_NOUN)
            self.assertTrue(tag in analysis.ANCHOR_SCENE
                            or tag in analysis.ANCHOR_CAPABILITY)

    def test_template_registry_is_unique_and_fully_mapped(self):
        self.assertGreaterEqual(len(analysis.TEMPLATES), 10)
        face_sets = [frozenset(tag for tag, _ in tpl["slots"])
                     for tpl in analysis.TEMPLATES]
        self.assertEqual(len(set(face_sets)), len(face_sets))
        self.assertEqual(len(set(analysis.PLAN_FAMILIES.values())),
                         len(analysis.PLAN_FAMILIES))
        for tpl in analysis.TEMPLATES:
            self.assertIn(tpl["name"], analysis.PLAN_FAMILIES)
            self.assertIn(tpl["name"], analysis.TEMPLATE_BUSINESS)
            self.assertGreaterEqual(len(tpl["slots"]), 2)

    def test_cooldown_blocks_within_the_first_seven_days(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "feasibility").mkdir()
            (root / "feasibility" / "2026-09-10.md").write_text(
                "## 可行性方案\n\n"
                "### 1. 本地优先 · 知识增强 · Agent 工作台\n\n"
                "**方案身份**：`plan_family=biz-1a2b3c4d5e6f` · `variant=v1`\n",
                encoding="utf-8",
            )
            history = analysis.load_family_history(root, "2026-09-12")

        blocked, note = analysis.cooldown_decision(
            "biz-1a2b3c4d5e6f", history, {"picks": {"角色": {"id": "owner/new"}},
                                          "business": {}})

        self.assertTrue(blocked)
        self.assertIn("冷却期内", note)

    def test_cooldown_mid_window_requires_new_components_or_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "feasibility").mkdir()
            (root / "feasibility" / "2026-09-10.md").write_text(
                "## 可行性方案\n\n"
                "### 1. 本地优先 · 知识增强 · Agent 工作台\n\n"
                "**方案身份**：`plan_family=biz-1a2b3c4d5e6f` · `variant=v1`\n\n"
                "**业务语义**：`evidence_status=to-validate`\n\n"
                "| 角色 | 项目 |\n|---|---|\n"
                "| 编排 | [`owner/old`](https://github.com/owner/old) |\n",
                encoding="utf-8",
            )
            history = analysis.load_family_history(root, "2026-09-19")

        unchanged = {"picks": {"编排": {"id": "owner/old"}}, "business": {}}
        upgraded = {"picks": {"编排": {"id": "owner/new"}}, "business": {}}

        blocked, note = analysis.cooldown_decision("biz-1a2b3c4d5e6f", history, unchanged)
        allowed, allow_note = analysis.cooldown_decision(
            "biz-1a2b3c4d5e6f", history, upgraded)

        self.assertTrue(blocked)
        self.assertIn("冷却中", note)
        self.assertFalse(allowed)
        self.assertIn("新增关键组件", allow_note)

    def test_cooldown_expires_after_the_full_window(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "feasibility").mkdir()
            (root / "feasibility" / "2026-09-01.md").write_text(
                "## 可行性方案\n\n### 1. 本地优先 · 知识增强 · Agent 工作台\n\n"
                "**方案身份**：`plan_family=biz-1a2b3c4d5e6f` · `variant=v1`\n",
                encoding="utf-8",
            )
            history = analysis.load_family_history(root, "2026-09-20")

        blocked, note = analysis.cooldown_decision(
            "biz-1a2b3c4d5e6f", history, {"picks": {}, "business": {}})

        self.assertFalse(blocked)
        self.assertEqual(note, "")

    def test_history_ignores_reports_outside_the_cooldown_window(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "feasibility").mkdir()
            (root / "feasibility" / "2026-06-01.md").write_text(
                "## 可行性方案\n\n### 1. 旧方案\n\n"
                "**方案身份**：`plan_family=old-family` · `variant=v1`\n",
                encoding="utf-8",
            )

            history = analysis.load_family_history(root, "2026-09-20")

        self.assertEqual(history, {})


class DualTrackSelectionTests(unittest.TestCase):
    """双轨配额：最多 1 个成熟方向 + 最多 2 个探索方向，未达合格线不补齐。"""

    @staticmethod
    def combo(name, score, track, repos=None, today_count=1, business=None):
        repositories = repos or (name,)
        picks = {
            f"角色{i}": {"id": repo, "repo": repo, "url": f"https://github.com/{repo}",
                          "stars": 10, "tags": {"agent": 1}, "fields": {}}
            for i, repo in enumerate(repositories)
        }
        return {
            "name": name, "score": score, "track": track,
            "today_count": today_count, "total": len(picks), "stars": 10,
            "picks": picks, "plan_family": f"fam-{name}", "variant": f"var-{name}",
            "business": business,
        }

    def test_keeps_one_mature_and_up_to_two_exploratory(self):
        combos = [
            self.combo("m1", 90, "mature"), self.combo("m2", 88, "mature"),
            self.combo("e1", 86, "exploratory"), self.combo("e2", 84, "exploratory"),
            self.combo("e3", 82, "exploratory"),
        ]

        selected = analysis.select_tracked_portfolio(combos)

        self.assertEqual([c["name"] for c in selected], ["m1", "e1", "e2"])
        self.assertEqual([c["track"] for c in selected],
                         ["mature", "exploratory", "exploratory"])

    def test_returns_mature_only_when_no_exploratory_qualifies(self):
        combos = [self.combo("m1", 90, "mature"), self.combo("e1", 69, "exploratory")]

        selected = analysis.select_tracked_portfolio(combos)

        self.assertEqual([c["name"] for c in selected], ["m1"])

    def test_returns_nothing_when_no_candidate_qualifies(self):
        combos = [self.combo("m1", 69, "mature"), self.combo("e1", 69, "exploratory")]

        self.assertEqual(analysis.select_tracked_portfolio(combos), [])

    def test_exploratory_direction_already_covered_by_mature_is_dropped(self):
        business = {"customer_id": "c1", "problem_id": "p1", "outcome_id": "o1"}
        mature = self.combo("m1", 90, "mature", business=business)
        exploratory = self.combo("e1", 88, "exploratory", business=dict(business))

        selected = analysis.select_tracked_portfolio([mature, exploratory])

        self.assertEqual([c["name"] for c in selected], ["m1"])

    def test_one_shared_component_does_not_remove_a_different_direction(self):
        mature = self.combo("m1", 82, "mature", repos=("owner/shared", "owner/a"))
        exploratory = self.combo("e1", 80, "exploratory",
                                 repos=("owner/shared", "owner/b"))

        selected = analysis.select_combo_portfolio([mature, exploratory], max_count=2)

        self.assertEqual([c["name"] for c in selected], ["m1", "e1"])


class BusinessSemanticsTests(unittest.TestCase):
    def test_every_template_declares_business_semantics(self):
        for tpl in analysis.TEMPLATES:
            business = analysis.TEMPLATE_BUSINESS[tpl["name"]]
            for key in ("customer_id", "customer", "problem_id", "problem",
                        "outcome_id", "expected_outcome", "workflow", "delivery"):
                self.assertTrue(business.get(key), f"{tpl['name']} 缺少 {key}")
            self.assertEqual(business["evidence_status"], analysis.EVIDENCE_VERIFIED)

    def test_template_business_directions_are_distinct(self):
        keys = [analysis.business_key(analysis.TEMPLATE_BUSINESS[tpl["name"]])
                for tpl in analysis.TEMPLATES]

        self.assertEqual(len(set(keys)), len(keys))

    def test_business_family_depends_only_on_business_triple(self):
        triple = ("privacy-first-individuals", "untraceable-answers", "traceable-answers")

        family = analysis.business_family(*triple)

        self.assertTrue(family.startswith("biz-"))
        self.assertEqual(family, analysis.business_family(*triple))
        self.assertNotEqual(
            family,
            analysis.business_family("privacy-first-individuals", "untraceable-answers",
                                     "other-outcome"),
        )

    def test_business_tables_cover_every_capability_face(self):
        for tag in analysis.TAG_RULES:
            self.assertIn(tag, analysis.BUSINESS_CUSTOMERS)
            self.assertIn(tag, analysis.BUSINESS_PROBLEMS)
            self.assertTrue(analysis.BUSINESS_PROBLEMS[tag]["workflow"])
            self.assertTrue(analysis.BUSINESS_PROBLEMS[tag]["expected_outcome"])


class ExploratoryTrackTests(unittest.TestCase):
    @staticmethod
    def project(repo, tags, tagline, stars=0):
        return {
            "id": repo, "repo": repo, "url": f"https://github.com/{repo}",
            "score": 85, "stars": stars, "tags": tags,
            "source_date": "2026-09-07",
            "fields": {"tagline": tagline, "risks": "", "quality": "",
                       "activity": "", "metrics": "MIT"},
        }

    def anchors(self):
        return [
            self.project("owner/agent", {"agent": 6}, "Agent 编排框架。", stars=500),
            self.project("owner/rag", {"rag": 5}, "知识库检索。", stars=300),
            self.project("owner/local", {"local": 4}, "本地优先桌面助手。", stars=100),
        ]

    def test_one_today_anchor_can_use_pool_complements(self):
        today = self.project("owner/today-agent", {"agent": 6},
                             "Agent 编排框架。", stars=500)
        history = [
            self.project("owner/history-document", {"document": 5},
                         "文档解析接口。", stars=300),
            self.project("owner/history-rag", {"rag": 5},
                         "知识检索接口。", stars=100),
        ]

        combos = analysis.build_exploratory_combos(
            [today] + history, [today], {today["id"]}, reuse_counts={})

        self.assertEqual(len(combos), 1)
        combo = combos[0]
        self.assertEqual(combo["today_count"], 1)
        self.assertEqual(combo["anchor_id"], today["id"])
        self.assertEqual(combo["business"]["problem_id"],
                         analysis.BUSINESS_PROBLEMS["agent"]["problem_id"])
        self.assertEqual(
            {p["id"] for p in combo["picks"].values()},
            {today["id"], "owner/history-document", "owner/history-rag"},
        )

    def test_exploratory_combo_is_business_identified_and_to_validate(self):
        projects = self.anchors()

        combos = analysis.build_exploratory_combos(projects, projects,
                                                  {p["id"] for p in projects})

        self.assertGreaterEqual(len(combos), 1)
        combo = next(c for c in combos if c["anchor_face"] == "agent")
        self.assertEqual(combo["track"], analysis.TRACK_EXPLORATORY)
        self.assertEqual(combo["total"], 3)
        self.assertEqual(combo["today_count"], 3)
        self.assertTrue(combo["plan_family"].startswith("biz-"))
        self.assertEqual(combo["business"]["evidence_status"],
                         analysis.EVIDENCE_TO_VALIDATE)
        for key in ("customer", "problem", "workflow", "delivery", "expected_outcome"):
            self.assertTrue(combo["business"][key], key)
        self.assertIn("待验证", combo["market"])
        self.assertIn("不代表市场需求成立", combo["market"])
        self.assertEqual(combo["business"]["problem_id"],
                         analysis.BUSINESS_PROBLEMS["agent"]["problem_id"])

    def test_family_follows_business_direction_not_components(self):
        first = self.anchors()
        second = [
            self.project("owner/other-agent", {"agent": 6}, "Agent 工作流平台。", stars=900),
            self.project("owner/other-rag", {"rag": 5}, "向量检索库。", stars=800),
            self.project("owner/other-local", {"local": 4}, "本地优先笔记。", stars=700),
        ]

        one = analysis.build_exploratory_combos(first, first, {p["id"] for p in first})[0]
        two = analysis.build_exploratory_combos(second, second, {p["id"] for p in second})[0]

        self.assertEqual(one["plan_family"], two["plan_family"])
        self.assertNotEqual(one["variant"], two["variant"])

    def test_blocked_family_suppresses_the_direction(self):
        projects = self.anchors()
        initial = analysis.build_exploratory_combos(
            projects, projects, {p["id"] for p in projects})
        blocked = {combo["plan_family"]: {} for combo in initial}

        combos = analysis.build_exploratory_combos(
            projects, projects, {p["id"] for p in projects},
            blocked_families=blocked)

        self.assertEqual(combos, [])

    def test_prefers_today_complement_then_low_reuse_history(self):
        today_agent = self.project("owner/today-agent", {"agent": 6},
                                   "Agent 编排框架。", stars=500)
        today_rag = self.project("owner/today-rag", {"rag": 1},
                                 "今日知识检索接口。", stars=1)
        history_rag = self.project("owner/history-rag", {"rag": 9},
                                   "历史知识检索接口。", stars=5000)
        frequent_document = self.project("owner/frequent-document", {"document": 6},
                                         "常用文档解析接口。", stars=5000)
        fresh_document = self.project("owner/fresh-document", {"document": 5},
                                      "新鲜文档解析接口。", stars=10)
        projects = [today_agent, today_rag, history_rag,
                    frequent_document, fresh_document]

        combos = analysis.build_exploratory_combos(
            projects, [today_agent, today_rag],
            {today_agent["id"], today_rag["id"]},
            reuse_counts={frequent_document["id"]: 3},
        )

        combo = next(c for c in combos if c["anchor_id"] == today_agent["id"])
        selected_ids = {p["id"] for p in combo["picks"].values()}
        self.assertIn(today_rag["id"], selected_ids)
        self.assertIn(fresh_document["id"], selected_ids)
        self.assertNotIn(history_rag["id"], selected_ids)
        self.assertNotIn(frequent_document["id"], selected_ids)

    def test_no_connected_pool_components_returns_empty(self):
        today = self.project("owner/today-gateway", {"gateway": 6},
                             "模型网关接口。", stars=500)
        history = [
            self.project("owner/history-memory", {"memory": 5},
                         "长期记忆接口。", stars=300),
            self.project("owner/history-sandbox", {"sandbox": 5},
                         "隔离执行接口。", stars=100),
        ]

        combos = analysis.build_exploratory_combos(
            [today] + history, [today], {today["id"]}, reuse_counts={})

        self.assertEqual(combos, [])

    def test_deploy_only_anchor_cannot_start_a_direction(self):
        """只有部署形态定位的今日项目不在主数据流里，不能作为探索锚点。"""
        today_local = self.project("owner/today-local", {"local": 6},
                                   "本地优先桌面助手。", stars=900)
        history = [
            self.project("owner/history-agent", {"agent": 6},
                         "Agent 编排框架。", stars=500),
            self.project("owner/history-rag", {"rag": 5},
                         "知识库检索。", stars=300),
        ]

        combos = analysis.build_exploratory_combos(
            [today_local] + history, [today_local], {today_local["id"]}, reuse_counts={})

        self.assertEqual(combos, [])


class DualTrackRenderingTests(unittest.TestCase):
    @staticmethod
    def project(repo, tags, tagline):
        return {"id": repo, "repo": repo, "url": f"https://github.com/{repo}",
                "score": 85, "stars": 100, "tags": tags, "source_date": "2026-09-14",
                "fields": {"value": "完成最小任务闭环。", "risks": "", "quality": "",
                           "activity": "", "metrics": "MIT", "tagline": tagline}}

    @staticmethod
    def combo(track, project):
        return {
            "name": "本地优先 · 知识增强 · Agent 工作台", "origin": "anchor",
            "track": track, "score": 80, "score_parts": [("组件可靠度", 30, 40)],
            "tech_score": 80, "tech_parts": [("组件可靠度", 30, 40)],
            "demand_score": 24, "demand_parts": [("证据等级", 24, 40)],
            "judgment": analysis.JUDGMENT_WATCH, "judgment_reason": "测试依据",
            "plan_family": "biz-1a2b3c4d5e6f", "variant": "test-variant",
            "pitch": "按'本地优先 · 知识增强 · Agent 工作台'方向组合今日项目。",
            "target": "重视数据留在本机的个人与小型团队", "market": "测试市场（待验证假设）",
            "rationale": "test rationale",
            "picks": {"编排": project},
            "flow": [{"tag": "agent", "role": "编排", "project": project,
                      "input": "任务指令与上游片段", "output": "可审批的步骤执行结果",
                      "upstream": [], "downstream": [], "deploy": False}],
            "experiment": {"scenario": "测试场景", "data": "测试数据", "days": 14,
                           "success": ["成功指标"], "failure": ["失败指标"], "stop": ["停止条件"]},
            "uncertainty": ["需求侧：测试", "组件侧：测试"],
            "actions": ["先补证据", "核验组件"],
            "slot_supply": {"agent": 1}, "min_supply": 1, "total": 1,
            "today_count": 1, "stars": 100, "differentiation": "test differentiation",
            "mvp": "test mvp",
            "business": {
                "customer_id": "privacy-first-individuals",
                "customer": "重视数据留在本机的个人与小型团队",
                "problem_id": "untraceable-answers",
                "problem": "资料散落各处，答案没有出处可查",
                "outcome_id": "traceable-answers",
                "expected_outcome": "每条结论都能指回来源",
                "workflow": "自有语料入库 → 带引用检索",
                "delivery": "本地/自托管交付",
                "evidence_status": "to-validate",
            },
        }

    def render(self, combo, project):
        return analysis.render([project], [project], [combo], "2026-09-14",
                               "2026-06-16", "2026-09-14", 1, 0, None)

    def test_render_exposes_track_and_machine_readable_business_semantics(self):
        project = self.project("owner/tool", {"agent": 5}, "任务闭环工具。")
        history = self.project("owner/history", {"rag": 5}, "历史检索工具。")
        combo = self.combo("exploratory", project)
        combo["anchor_id"] = project["id"]
        combo["picks"]["历史检索"] = history

        report = self.render(combo, project)

        self.assertIn("**业务轨道**：探索方向（待验证）", report)
        self.assertIn("`track=exploratory`", report)
        self.assertIn("`problem=资料散落各处，答案没有出处可查`", report)
        self.assertIn("**方案判断**：", report)
        self.assertIn("（探索方向待验证）", report)
        self.assertIn("另有 1 个互补组件来自最近 90 天项目池", report)
        self.assertNotIn("组件全部来自今日日报", report)

    def test_render_marks_mature_track_without_validation_notice(self):
        project = self.project("owner/tool", {"agent": 5}, "任务闭环工具。")
        combo = self.combo("mature", project)
        combo["business"]["evidence_status"] = analysis.EVIDENCE_VERIFIED

        report = self.render(combo, project)

        self.assertIn("**业务轨道**：成熟方向（组件供给已核对）", report)
        self.assertNotIn("探索方向待验证", report)

    def test_render_states_when_no_plan_qualified(self):
        report = analysis.render([], [], [], "2026-09-14", "2026-06-16",
                                 "2026-09-14", 0, 0, None)

        self.assertIn("本轮无合格方案", report)


class ClosureGateTests(unittest.TestCase):
    """闭环门槛：仅标签相关、能力面重复、数据流不连通、组件不足都不成方案。"""

    def test_requires_at_least_three_components(self):
        steps = plan_steps([("document", "文档解析"), ("rag", "检索")])

        flow = analysis.combo_flow(steps)

        self.assertFalse(flow["ok"])
        self.assertIn("构不成完整数据流", flow["reason"])

    def test_rejects_components_without_interface_evidence(self):
        steps = plan_steps([("document", "文档解析"), ("rag", "检索"),
                            ("agent", "编排")])
        blank = steps[1][2]
        blank["fields"] = {"tagline": "", "value": "", "quality": "", "reason": ""}

        flow = analysis.combo_flow(steps)

        self.assertFalse(flow["ok"])
        self.assertIn("仅标签相关", flow["reason"])
        self.assertIn(blank["repo"], flow["reason"])

    def test_rejects_indexes_and_other_non_executable_content(self):
        steps = plan_steps([("document", "文档解析"), ("rag", "检索"),
                            ("agent", "编排")])
        index = steps[0][2]
        index["repo"] = index["id"] = "owner/awesome-tools"
        index["fields"]["tagline"] = "开源工具资源索引。"

        flow = analysis.combo_flow(steps)

        self.assertFalse(flow["ok"])
        self.assertIn("非执行组件", flow["reason"])

    def test_rejects_duplicate_capability_faces(self):
        steps = plan_steps([("agent", "编排 A"), ("agent", "编排 B"),
                            ("observability", "观测")])

        flow = analysis.combo_flow(steps)

        self.assertFalse(flow["ok"])
        self.assertIn("能力面重复", flow["reason"])

    def test_rejects_unconnected_data_flow(self):
        steps = plan_steps([("comm", "消息入口"), ("memory", "长期记忆"),
                            ("design", "设计"), ("codeintel", "代码理解")])

        flow = analysis.combo_flow(steps)

        self.assertFalse(flow["ok"])
        self.assertIn("数据流不连通", flow["reason"])

    def test_every_declared_handoff_goes_downstream(self):
        for upstream, downstream in analysis.CAPABILITY_HANDOFFS:
            self.assertLess(analysis.CAPABILITY_RANK[upstream],
                            analysis.CAPABILITY_RANK[downstream],
                            "{} → {} 的排序与交接方向不一致".format(upstream, downstream))

    def test_every_template_forms_a_connected_flow(self):
        for tpl in analysis.TEMPLATES:
            steps = plan_steps(tpl["slots"])
            flow = analysis.combo_flow(steps)
            self.assertTrue(flow["ok"], "{}：{}".format(tpl["name"], flow["reason"]))
            self.assertGreaterEqual(len(flow["steps"]), analysis.MIN_PLAN_COMPONENTS)
            for step in flow["steps"]:
                self.assertTrue(step["input"])
                self.assertTrue(step["output"])


class DualScoreTests(unittest.TestCase):
    """双评分：技术组合成熟度与需求证据强度互不合并。"""

    def test_tech_score_parts_add_up_and_exclude_demand(self):
        combo = make_combo(plan_steps([("document", "文档解析"), ("rag", "检索"),
                                       ("agent", "编排"), ("observability", "评测")]))

        self.assertEqual(combo["tech_score"], sum(v for _, v, _ in combo["tech_parts"]))
        self.assertEqual([name for name, _, _ in combo["tech_parts"]],
                         [name for name, _ in analysis.TECH_SCORE_PARTS])
        self.assertNotIn("证据等级", [name for name, _, _ in combo["tech_parts"]])

    def test_demand_score_parts_add_up(self):
        combo = make_combo(plan_steps([("document", "文档解析"), ("rag", "检索"),
                                       ("agent", "编排")]))

        self.assertEqual(combo["demand_score"],
                         sum(v for _, v, _ in combo["demand_parts"]))
        self.assertEqual([name for name, _, _ in combo["demand_parts"]],
                         [name for name, _ in analysis.DEMAND_SCORE_PARTS])

    def test_component_maturity_never_upgrades_demand_evidence(self):
        combo = make_combo(plan_steps([("document", "文档解析"), ("rag", "检索"),
                                       ("agent", "编排"), ("observability", "评测")]),
                           run_date="2026-09-14")

        self.assertGreaterEqual(combo["tech_score"], 80)
        self.assertEqual(combo["demand"]["level"], analysis.EVIDENCE_SELF_REPORTED)
        self.assertNotEqual(combo["judgment"], analysis.JUDGMENT_INTERVIEW)

    def test_user_feedback_raises_demand_level_and_judgment(self):
        steps = plan_steps([("document", "文档解析"), ("rag", "检索"), ("agent", "编排")])
        feedback = [{"source": "user", "date": "2026-09-13", "repo": "owner/rag",
                     "detail": "希望先把引用溯源跑通"},
                    {"source": "user", "date": "2026-09-12", "repo": "owner/agent",
                     "detail": "需要能中断和回滚的编排"}]

        combo = make_combo(steps, run_date="2026-09-14", feedback=feedback)

        self.assertEqual(combo["demand"]["level"], analysis.EVIDENCE_CONFIRMED)
        self.assertGreaterEqual(combo["demand_score"], 90)
        self.assertEqual(combo["judgment"], analysis.JUDGMENT_INTERVIEW)

    def test_components_without_interface_evidence_are_rejected(self):
        steps = plan_steps([("document", "文档解析"), ("rag", "检索"), ("agent", "编排")])
        steps[2][2]["fields"] = {"tagline": "", "value": "", "quality": "", "reason": "",
                                 "risks": "", "howto": "安装说明", "kind": ""}

        combo = make_combo(steps, run_date="2026-09-14")

        self.assertIsNone(combo)

    def test_no_source_components_report_none_evidence(self):
        picks = {role: {"id": "x/{}".format(i), "repo": "x/{}".format(i),
                        "source_date": "2026-01-01", "fields": {}}
                 for i, role in enumerate(("文档解析", "检索", "编排"))}

        silent = analysis.plan_evidence({"picks": picks, "business": {}}, [], "2026-09-14")

        self.assertEqual(silent["level"], analysis.EVIDENCE_NONE)
        self.assertEqual(silent["score"], 0)

    def test_plans_without_demand_evidence_are_dropped(self):
        judgment, reason = analysis.plan_judgment(
            90, {"level": analysis.EVIDENCE_NONE, "score": 0}, 20)

        self.assertEqual(judgment, analysis.JUDGMENT_DROP)
        self.assertIn("无任何可引用证据", reason)

    def test_high_risk_share_is_dropped(self):
        judgment, _ = analysis.plan_judgment(
            90, {"level": analysis.EVIDENCE_SELF_REPORTED, "score": 59}, 5)

        self.assertEqual(judgment, analysis.JUDGMENT_DROP)

    def test_judgment_ladder_covers_all_four_labels(self):
        self.assertEqual(
            analysis.plan_judgment(90, {"level": analysis.EVIDENCE_CONFIRMED,
                                        "score": 80}, 20)[0],
            analysis.JUDGMENT_INTERVIEW)
        self.assertEqual(
            analysis.plan_judgment(85, {"level": analysis.EVIDENCE_SELF_REPORTED,
                                        "score": 40}, 20)[0],
            analysis.JUDGMENT_TECH_TRIAL)
        self.assertEqual(
            analysis.plan_judgment(75, {"level": analysis.EVIDENCE_SELF_REPORTED,
                                        "score": 40}, 20)[0],
            analysis.JUDGMENT_WATCH)


class ExperimentAndEvidenceTests(unittest.TestCase):
    """MVP 要可证伪：场景/数据/周期/成功/失败/停止条件，需求表述要带证据等级。"""

    @staticmethod
    def combo():
        return make_combo(plan_steps([("document", "文档解析"), ("rag", "检索"),
                                      ("agent", "编排"), ("observability", "评测")]))

    def test_mvp_experiment_is_falsifiable(self):
        combo = self.combo()
        experiment = combo["experiment"]

        self.assertTrue(experiment["scenario"])
        self.assertTrue(experiment["data"])
        self.assertEqual(experiment["days"], analysis.EXPERIMENT_DAYS)
        self.assertTrue(experiment["success"])
        self.assertTrue(experiment["failure"])
        self.assertTrue(experiment["stop"])
        self.assertTrue(any("停止" in item for item in experiment["stop"]))

    def test_report_prints_the_experiment_block_and_next_actions(self):
        combo = self.combo()
        report = analysis.render([combo["picks"]["文档解析"]], [], [combo],
                                 "2026-09-14", "2026-06-16", "2026-09-14", 1, 0, None)

        for label in ("- 测试场景：", "- 测试数据：", "- 周期：", "- 成功指标：",
                      "- 失败指标：", "- 停止条件："):
            self.assertIn(label, report)
        self.assertIn("**下一步动作**：", report)
        self.assertNotIn("核验 2-3 个核心组件", report)
        self.assertNotIn("**最大不确定性**：", report)
        self.assertNotIn("**客户问题**：", report)

    def test_demand_statements_carry_evidence_levels(self):
        combo = self.combo()
        report = analysis.render([], [], [combo], "2026-09-14", "2026-06-16",
                                 "2026-09-14", 1, 0, None)

        self.assertIn("**需求证据**：", report)
        self.assertIn("（最高等级：项目方自述）", report)
        self.assertIn("【待验证假设】", report)
        self.assertNotIn("- 【项目方自述】", report)

    def test_templates_and_report_avoid_unfounded_claims(self):
        for tpl in analysis.TEMPLATES:
            for field in ("market", "pitch", "rationale", "differentiation", "mvp"):
                text = tpl[field]
                for word in analysis.FORBIDDEN_CLAIMS:
                    self.assertNotIn(word, text,
                                     "{} 的 {} 含无来源断言 {}".format(tpl["name"], field, word))

        combo = self.combo()
        combo["market"] = "企业愿意付费，这是刚需。"
        report = analysis.render([], [], [combo], "2026-09-14", "2026-06-16",
                                 "2026-09-14", 1, 0, None)
        body = report.split("## 可行性方案", 1)[1]

        self.assertNotIn("愿意付费", body)
        self.assertNotIn("刚需", body)
        self.assertIn("（无来源断言，已删除）", body)


class ReportStructureTests(unittest.TestCase):
    """阅读顺序与新报告结构：允许没有方案，不生成单点机会与笼统行动建议。"""

    @staticmethod
    def combo():
        return make_combo(plan_steps([("document", "文档解析"), ("rag", "检索"),
                                      ("agent", "编排"), ("observability", "评测")]))

    def test_summary_lists_cooldown_dropped_and_rejected_candidates(self):
        combo = make_combo(plan_steps([("document", "文档解析"), ("rag", "检索"),
                                       ("agent", "编排")]))

        report = analysis.render(
            [], [], [combo], "2026-09-14", "2026-06-16", "2026-09-14", 1, 0, None,
            ["企业内部知识助手：冷却期内（最近一次出现 1 天前，起点 7 天）"],
            [("旧方向", "缺需求证据（无证据）")],
            [("旧组合", "仅标签相关（缺接口依据）：owner/x")],
        )

        self.assertIn("冷却与重现：企业内部知识助手：冷却期内", report)
        self.assertIn("暂不建议（未列入）：旧方向（缺需求证据（无证据））", report)
        self.assertIn("闭环门槛未过（未列入）：旧组合（仅标签相关（缺接口依据）：owner/x）", report)

    def test_report_follows_the_agreed_reading_order(self):
        combo = self.combo()
        report = analysis.render([], [], [combo], "2026-09-14", "2026-06-16",
                                 "2026-09-14", 1, 0, None)
        order = ["## 今日结论", "**方案判断**：", "**业务定位**：", "**目标客户**：",
                 "**市场机会**：", "**需求证据**：", "**组合依据**：", "**组合方案**：",
                 "**双评分**：", "**MVP 实验**：", "**下一步动作**："]
        positions = [report.index(marker) for marker in order]

        self.assertEqual(positions, sorted(positions))

    def test_report_drops_low_value_sections(self):
        report = analysis.render([], [], [self.combo()], "2026-09-14", "2026-06-16",
                                 "2026-09-14", 1, 0, None)

        self.assertNotIn("## 单点项目机会", report)
        self.assertNotIn("## 行动建议", report)
        self.assertNotIn("优先推进评分最高的组合", report)

    def test_machine_metadata_is_visible_in_rendered_markdown(self):
        report = analysis.render([], [], [self.combo()], "2026-09-14", "2026-06-16",
                                 "2026-09-14", 1, 0, None)

        self.assertIn("**方案身份**：", report)
        self.assertIn("**业务语义**：", report)
        self.assertNotIn("<!-- **", report)

    def test_zero_plan_report_lists_skipped_and_dropped_candidates(self):
        report = analysis.render([], [], [], "2026-09-14", "2026-06-16", "2026-09-14",
                                 1, 0, None,
                                 cooldown_notes=["方案 A：冷却期内（最近一次出现 2 天前，起点 7 天）"],
                                 dropped=[("方案 B", "需求侧无任何可引用证据")],
                                 rejected=[("方案 C", "仅标签相关（缺接口依据）：owner/x")])

        self.assertIn("本轮无合格方案", report)
        self.assertIn("暂不建议（未列入）：方案 B", report)
        self.assertIn("闭环门槛未过（未列入）：方案 C", report)
        self.assertIn("冷却与重现：方案 A", report)
        self.assertIn("不为每日产出凑数", report)


class ReportCompatibilityTests(unittest.TestCase):
    def test_legacy_report_without_business_fields_falls_back(self):
        markdown = (
            "## 可行性方案\n\n"
            "### 1. 本地优先个人 AI 工作台（组合 2 个项目，今日锚点 1 个）\n\n"
            "**方案评分**：**83/100（中）**（组件可靠度 32/35）\n\n"
            "| 角色 | 项目 |\n|---|---|\n"
            "| 编排 | [`owner/one`](https://github.com/owner/one) |\n"
        )

        identity = analysis.parse_plan_identities(markdown)[0]

        self.assertEqual(identity["family"], "local-first-personal-ai-workbench")
        self.assertIsNone(identity["track"])
        self.assertIsNone(identity["business"])

    def test_report_with_business_semantics_is_parsed(self):
        markdown = (
            "## 可行性方案\n\n"
            "### 1. 本地优先 · 知识增强 · Agent 工作台（组合 3 个项目，今日锚点 3 个）\n\n"
            "**方案身份**：`plan_family=biz-1a2b3c4d5e6f` · `variant=v1`\n\n"
            "**业务语义**：`track=exploratory` · `customer=重视数据留在本机的个人与小型团队`"
            " · `problem=资料散落各处，答案没有出处可查` · `workflow=自有语料入库`"
            " · `delivery=本地/自托管交付` · `expected_outcome=每条结论都能指回来源`"
            " · `evidence_status=to-validate`\n\n"
            "| 角色 | 项目 |\n|---|---|\n"
            "| 编排 | [`owner/one`](https://github.com/owner/one) |\n"
        )

        identity = analysis.parse_plan_identities(markdown)[0]

        self.assertEqual(identity["track"], "exploratory")
        self.assertEqual(identity["business"]["problem"], "资料散落各处，答案没有出处可查")
        self.assertEqual(identity["business"]["evidence_status"], "to-validate")


class KunTaskContractTests(unittest.TestCase):
    """KUN-TASK.md 的契约必须与生成器一致（0–3 个、双评分、四档判断、冷却）。"""

    @classmethod
    def setUpClass(cls):
        cls.path = (Path(__file__).resolve().parent.parent
                    / "data" / "github-project-digest" / "feasibility" / "KUN-TASK.md")
        cls.text = cls.path.read_text(encoding="utf-8") if cls.path.is_file() else ""

    def test_contract_uses_the_dual_track_range(self):
        self.assertTrue(self.text, "KUN-TASK.md 缺失")
        self.assertIn("0–3", self.text)
        self.assertIn("成熟方向", self.text)
        self.assertIn("探索方向", self.text)

    def test_contract_defines_zero_qualified_plan_behaviour(self):
        self.assertIn("无合格方案", self.text)

    def test_contract_drops_the_fixed_three_plan_claim(self):
        self.assertNotIn("每天输出 3 个", self.text)
        self.assertNotIn("报告含 3 个方案", self.text)
        self.assertNotIn("优先推进评分最高", self.text)

    def test_contract_requires_post_generation_naming_step(self):
        self.assertIn("命名标准", self.text)
        self.assertIn("生成后", self.text)
        self.assertIn("plan_family", self.text)
        self.assertIn("8–20", self.text)

    def test_contract_splits_the_two_scores(self):
        for token in ("双评分", "技术组合成熟度", "需求证据强度", "组件成熟不等于商业可行"):
            self.assertIn(token, self.text)

    def test_contract_defines_the_four_judgments(self):
        for label in analysis.JUDGMENT_ORDER:
            self.assertIn(label, self.text)
        self.assertIn("不列入方案列表", self.text)

    def test_contract_defines_closure_gate_and_evidence_levels(self):
        for token in ("闭环门槛", "组件数据流", "接入方式", "仅标签相关"):
            self.assertIn(token, self.text)
        for level in analysis.EVIDENCE_LEVELS:
            self.assertIn(level, self.text)

    def test_contract_defines_cooldown_window_and_falsifiable_mvp(self):
        self.assertIn("7–14", self.text)
        for token in ("新增关键组件", "证据等级提升", "测试场景", "成功指标",
                      "失败指标", "停止条件"):
            self.assertIn(token, self.text)

    def test_contract_retires_low_value_sections(self):
        self.assertNotIn("单点项目机会", self.text)
        self.assertIn("刚需", self.text)   # 仅出现在禁用措辞说明里


class DailyAnchorRequirementTests(unittest.TestCase):
    """当天日报缺失时必须跳过：不回退到更早的日报，也不产出报告。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "daily").mkdir()
        (self.root / "weekly").mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def write_daily(self, day, repo):
        (self.root / "daily" / f"{day}.md").write_text(
            f"### 1. 爆发型：{repo} — 90/100\n\n"
            f"- 仓库：[{repo}](https://github.com/{repo})\n"
            "- 一句话定位：测试项目。\n",
            encoding="utf-8",
        )

    def test_missing_today_daily_skips_without_report(self):
        self.write_daily("2026-09-12", "owner/old")

        today_projects, projects, _, _, anchor = analysis.load_project_pool(
            self.root, "2026-09-14")

        self.assertEqual(anchor, "")
        self.assertIsNone(today_projects)
        self.assertIsNone(projects)
        self.assertEqual(
            analysis.main(["--date", "2026-09-14", "--data-root", str(self.root)]),
            2,
        )
        self.assertFalse((self.root / "feasibility").exists())

    def test_today_daily_is_the_only_anchor_and_generates_report(self):
        self.write_daily("2026-09-12", "owner/old")
        self.write_daily("2026-09-14", "owner/new")

        today_projects, _, _, _, anchor = analysis.load_project_pool(
            self.root, "2026-09-14")

        self.assertEqual(anchor, "2026-09-14")
        self.assertEqual([p["id"] for p in today_projects], ["owner/new"])

        exit_code = analysis.main(["--date", "2026-09-14", "--data-root",
                                   str(self.root), "--no-llm"])

        self.assertEqual(exit_code, 0)
        report = (self.root / "feasibility" / "2026-09-14.md").read_text(
            encoding="utf-8")
        self.assertIn("# GitHub 项目组合可行性方案｜2026-09-14", report)
        self.assertIn("daily/2026-09-14.md", report)
        runs_log = (self.root / "feasibility" / "runs.log").read_text(
            encoding="utf-8")
        self.assertIn("anchor=2026-09-14", runs_log)

    def test_generated_report_carries_the_new_contract_sections(self):
        self.write_daily("2026-09-12", "owner/old")
        self.write_daily("2026-09-14", "owner/new")

        code = analysis.main(["--date", "2026-09-14", "--data-root", str(self.root),
                              "--no-llm"])
        report = (self.root / "feasibility" / "2026-09-14.md").read_text(encoding="utf-8")

        self.assertEqual(code, 0)
        self.assertIn("## 今日结论", report)
        self.assertNotIn("## 单点项目机会", report)
        self.assertNotIn("## 行动建议", report)
        for word in analysis.FORBIDDEN_CLAIMS:
            self.assertNotIn(word, report.replace("不使用刚需、愿意付费等无来源结论", ""))

    def test_second_run_of_the_same_family_is_skipped_by_cooldown(self):
        self.write_daily("2026-09-12", "owner/old")
        self.write_daily("2026-09-14", "owner/new")
        analysis.main(["--date", "2026-09-14", "--data-root", str(self.root),
                       "--no-llm"])
        first = (self.root / "feasibility" / "2026-09-14.md").read_text(encoding="utf-8")

        self.write_daily("2026-09-15", "owner/newer")
        analysis.main(["--date", "2026-09-15", "--data-root", str(self.root),
                       "--no-llm"])
        second = (self.root / "feasibility" / "2026-09-15.md").read_text(encoding="utf-8")

        self.assertIn("## 今日结论", second)


class CooldownIntegrationTests(unittest.TestCase):
    """端到端：同一 plan_family 在 7 天内被冷却跳过，14 天后自然重新合格。"""

    POOL = [
        ("agent", "Agent 编排框架，可接任务与工具。"),
        ("rag", "知识库检索与引用溯源。"),
        ("memory", "长期记忆与会话上下文存储。"),
        ("sandbox", "隔离执行环境与权限边界。"),
        ("observability", "Agent 运行 trace 与成本评测。"),
        ("gateway", "模型网关与用量路由。"),
        ("security", "依赖与代码安全审计。"),
        ("codeintel", "仓库级代码理解与回归对比。"),
        ("design", "设计稿到组件改动规格。"),
        ("document", "文档解析与结构化入库。"),
        ("comm", "渠道消息聚合与回执。"),
        ("local", "本地优先桌面形态，数据不出本机。"),
    ]

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "daily").mkdir()
        (self.root / "weekly").mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def write_daily(self, day, entries):
        lines = []
        for index, (repo, tagline, score) in enumerate(entries, 1):
            lines += [f"### {index}. 爆发型：{repo} — {score}/100", "",
                      f"- 仓库：[{repo}](https://github.com/{repo})",
                      f"- 一句话定位：{tagline}",
                      "- 类型与适合用途：工具 | 适合作为组合组件",
                      "- 风险：无", ""]
        (self.root / "daily" / f"{day}.md").write_text("\n".join(lines),
                                                         encoding="utf-8")

    def write_pool_day(self, day, per_face=24):
        """写一份足够大的合成项目池：每个能力面 FACE_SUPPLY 个候选，保证供给分项达标。"""
        entries = []
        for tag, tagline in self.POOL:
            for index in range(1, per_face + 1):
                entries.append(("owner/{}-{}".format(tag, index), tagline, 90))
        self.write_daily(day, entries)

    def run_day(self, day, repo=None, tagline=None):
        if repo:
            self.write_daily(day, [(repo, tagline or "{}{}".format(repo, " 组件。"), 95)])
        code = analysis.main(["--date", day, "--data-root", str(self.root), "--no-llm"])
        self.assertEqual(code, 0)
        return (self.root / "feasibility" / f"{day}.md").read_text(encoding="utf-8")

    def test_repeated_family_is_cooled_down_then_returns(self):
        self.write_pool_day("2026-09-01")
        first = self.run_day("2026-09-01")
        first_families = [match.group(1) for match in
                          re.finditer(r"plan_family=([^`]+)", first)]

        self.assertTrue(first_families, "首次运行应至少产出 1 个方案")
        second = self.run_day("2026-09-02", "owner/agent-anchor",
                              "Agent 编排框架与任务编排。")

        self.assertIn("冷却与重现", second)
        self.assertIn("冷却期内", second)
        for family in first_families:
            self.assertNotIn("plan_family={}".format(family), second)

        later = self.run_day("2026-09-25", "owner/agent-later",
                             "Agent 编排框架与任务编排。")

        self.assertNotIn("冷却期内", later)


if __name__ == "__main__":
    unittest.main()
