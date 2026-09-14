import tempfile
import unittest
from pathlib import Path

from scripts import opportunity_analysis as analysis


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
        project = {
            "id": "owner/tool",
            "repo": "owner/tool",
            "url": "https://github.com/owner/tool",
            "score": 85,
            "stars": 100,
            "tags": {"agent": 5},
            "source": "daily",
            "source_date": "2026-09-07",
            "fields": {
                "value": "完成最小任务闭环。",
                "risks": "需先在隔离环境验证。",
                "quality": "",
                "activity": "",
                "metrics": "MIT",
            },
        }
        combo = {
            "name": "test plan",
            "score": 80,
            "score_parts": [("组件可靠度", 30, 35)],
            "plan_family": "test-family",
            "variant": "test-variant",
            "pitch": "test pitch",
            "target": "test audience",
            "market": "test market",
            "rationale": "test rationale",
            "picks": {"Agent 编排": project},
            "slot_supply": {"agent": 1},
            "min_supply": 1,
            "total": 1,
            "today_count": 1,
            "stars": 100,
            "differentiation": "test differentiation",
            "mvp": "test mvp",
        }

        report = analysis.render(
            [project], [project], [combo], [], "2026-09-07", "2026-06-09",
            "2026-09-07", 1, 0, None,
        )

        self.assertIn("| 角色 | 项目 | 入选理由 |", report)
        self.assertNotIn("| 角色 | 项目 | 来源 | 许可证 | 入选理由 |", report)
        self.assertIn(
            "| Agent 编排 | [`owner/tool`](https://github.com/owner/tool) | 完成最小任务闭环。 |",
            report,
        )


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

    def test_freshness_matches_family_not_wording(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "feasibility").mkdir()
            for day, title in (("2026-09-10", "本地优先 · 知识增强 · Agent 工作台"),
                               ("2026-09-11", "本地优先 · 多模型 · Agent 工作台")):
                (root / "feasibility" / f"{day}.md").write_text(
                    "## 可行性方案\n\n"
                    f"### 1. {title}（组合 3 个项目，今日锚点 3 个）\n\n"
                    "**方案身份**：`plan_family=biz-1a2b3c4d5e6f` · `variant=v1`\n",
                    encoding="utf-8",
                )

            blocked = analysis.load_recent_families(root, "2026-09-12")

        self.assertEqual(set(blocked), {"biz-1a2b3c4d5e6f"})


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

    def test_needs_one_anchor_plus_two_complementary_projects(self):
        projects = self.anchors()[:2]

        self.assertEqual(
            analysis.build_exploratory_combos(projects, projects,
                                              {p["id"] for p in projects}),
            [],
        )

    def test_exploratory_combo_is_business_identified_and_to_validate(self):
        projects = self.anchors()

        combos = analysis.build_exploratory_combos(projects, projects,
                                                  {p["id"] for p in projects})

        self.assertEqual(len(combos), 1)
        combo = combos[0]
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
        self.assertEqual(combo["name"], "本地优先 · 知识增强 · Agent 工作台")

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
        family = analysis.build_exploratory_combos(
            projects, projects, {p["id"] for p in projects})[0]["plan_family"]

        combos = analysis.build_exploratory_combos(
            projects, projects, {p["id"] for p in projects},
            blocked_families={family})

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
            "track": track, "score": 80, "score_parts": [("组件可靠度", 30, 35)],
            "plan_family": "biz-1a2b3c4d5e6f", "variant": "test-variant",
            "pitch": "按'本地优先 · 知识增强 · Agent 工作台'方向组合今日项目。",
            "target": "重视数据留在本机的个人与小型团队", "market": "test market",
            "rationale": "test rationale", "picks": {"Agent 编排": project},
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
        return analysis.render([project], [project], [combo], [], "2026-09-14",
                               "2026-06-16", "2026-09-14", 1, 0, None)

    def test_render_exposes_track_and_machine_readable_business_semantics(self):
        project = self.project("owner/tool", {"agent": 5}, "任务闭环工具。")

        report = self.render(self.combo("exploratory", project), project)

        self.assertIn("**业务轨道**：探索方向（待验证）", report)
        self.assertIn("`track=exploratory`", report)
        self.assertIn("`problem=资料散落各处，答案没有出处可查`", report)
        self.assertIn("**待验证说明**", report)
        self.assertIn("探索方向：由今日锚点直接拼接", report)

    def test_render_marks_mature_track_without_validation_notice(self):
        project = self.project("owner/tool", {"agent": 5}, "任务闭环工具。")
        combo = self.combo("mature", project)
        combo["business"]["evidence_status"] = analysis.EVIDENCE_VERIFIED

        report = self.render(combo, project)

        self.assertIn("**业务轨道**：成熟方向（组件供给已核对）", report)
        self.assertNotIn("**待验证说明**", report)

    def test_render_states_when_no_plan_qualified(self):
        report = analysis.render([], [], [], [], "2026-09-14", "2026-06-16",
                                 "2026-09-14", 0, 0, None)

        self.assertIn("本轮无合格方案", report)


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
    """KUN-TASK.md 的数量契约必须与双轨机制一致（1–3 个，允许少于 3 个）。"""

    @classmethod
    def setUpClass(cls):
        cls.path = (Path(__file__).resolve().parent.parent
                    / "data" / "github-project-digest" / "feasibility" / "KUN-TASK.md")
        cls.text = cls.path.read_text(encoding="utf-8") if cls.path.is_file() else ""

    def test_contract_uses_the_dual_track_range(self):
        self.assertTrue(self.text, "KUN-TASK.md 缺失")
        self.assertIn("1–3", self.text)
        self.assertIn("成熟方向", self.text)
        self.assertIn("探索方向", self.text)

    def test_contract_defines_zero_qualified_plan_behaviour(self):
        self.assertIn("无合格方案", self.text)

    def test_contract_drops_the_fixed_three_plan_claim(self):
        self.assertNotIn("每天输出 3 个", self.text)
        self.assertNotIn("报告含 3 个方案", self.text)

    def test_contract_requires_post_generation_naming_step(self):
        self.assertIn("命名标准", self.text)
        self.assertIn("生成后", self.text)
        self.assertIn("plan_family", self.text)
        self.assertIn("8–20", self.text)


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


if __name__ == "__main__":
    unittest.main()
