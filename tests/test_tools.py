"""End-to-end tests for tools/ on the synthetic fixtures in tests/fixtures/.

Run: python3 -m unittest discover -s tests      (all)
     python3 -m unittest tests.test_tools.ToolsTest.test_rank_order   (one)
Uses a temporary work folder (CVMATCH_WORK), so real prepared data in .work/ is untouched.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIX = ROOT / "tests" / "fixtures"


def run(tool, *args, env):
    return subprocess.run([sys.executable, str(ROOT / "tools" / tool), *map(str, args)],
                          capture_output=True, text=True, env=env, cwd=ROOT)


class ToolsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.env = {**os.environ, "CVMATCH_WORK": str(cls.tmp / "work")}
        out = run("prepare_data.py", "--cvs", FIX / "cvs", "--team", FIX / "team", env=cls.env)
        assert out.returncode == 0, out.stdout + out.stderr
        cls.prepare_out = out.stdout
        cls.manifest = json.loads((cls.tmp / "work" / "manifest.json").read_text())
        cls.people = {p["name"]: p for p in cls.manifest["people"]}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp)

    def fresh_run(self):
        dst = self.tmp / f"run-{self.id().rsplit('.', 1)[-1]}"
        shutil.copytree(FIX / "run-rfp", dst)
        return dst

    def test_name_linking(self):
        p = self.people
        self.assertEqual(p["Anna Maria Müller"]["link"], "strong")          # extra middle name
        self.assertEqual(p["Jörg Weiss"]["link"], "exact")                  # ß/ö spelling, word order
        self.assertEqual(p["Jonas Becker"]["link"], "strong")               # "CV Jonas Peter Becker"
        self.assertEqual(p["Jan Schmidt"]["link"], "probable")              # Jana vs. Jan: flagged
        self.assertEqual(p["Lena Vogel"]["status"], "no_cv")
        self.assertIn("Unknown_Person_CV.pptx", self.manifest["unlinked_cvs"])

    def test_newest_cv_version_and_outdated(self):
        anna = self.people["Anna Maria Müller"]
        self.assertTrue(anna["cv_file"].endswith("2026-02.pptx"))
        self.assertEqual(anna["cv_versions"], 2)
        self.assertTrue(self.people["Jörg Weiss"]["outdated"])
        self.assertFalse(self.people["Jonas Becker"]["outdated"])

    def test_team_list_parsing(self):
        anna = self.people["Anna Maria Müller"]
        self.assertEqual(anna["availability_pct"], 0.0)
        self.assertEqual(anna["available_from"], "2026-11-01")
        self.assertEqual(self.people["Jörg Weiss"]["availability_pct"], 50.0)

    def test_pptx_text(self):
        text = (self.tmp / "work" / "cvs" / "anna-maria-muller.txt").read_text()
        self.assertIn("--- Slide 1 ---", text)
        self.assertIn("Apache Spark, PySpark, Databricks", text)

    def test_verify_catches_invented_quote(self):
        run_dir = self.fresh_run()
        out = run("verify_evidence.py", run_dir, env=self.env)
        self.assertEqual(out.returncode, 1)
        self.assertIn("Jörg Weiss R2", out.stdout)
        out = run("verify_evidence.py", run_dir, "--fix", env=self.env)
        self.assertEqual(out.returncode, 0, out.stdout)
        a = json.loads((run_dir / "assessments" / "jorg-weiss.json").read_text())
        r2 = next(r for r in a["requirements"] if r["id"] == "R2")
        self.assertEqual(r2["state"], "not evidenced")

    def test_rank_order(self):
        run_dir = self.fresh_run()
        run("verify_evidence.py", run_dir, "--fix", env=self.env)
        out = run("rank.py", run_dir, env=self.env)
        self.assertEqual(out.returncode, 0, out.stderr)
        role = json.loads((run_dir / "ranking.json").read_text())["roles"][0]
        order = [r["key"] for r in role["shortlist"]]
        self.assertEqual(order, ["anna-maria-muller", "jonas-becker", "jan-schmidt", "jorg-weiss"])
        tiers = {r["key"]: r["tier"] for r in role["shortlist"]}
        self.assertEqual(tiers["jonas-becker"], "language_gap")             # shown despite German gap
        jonas = next(r for r in role["shortlist"] if r["key"] == "jonas-becker")
        self.assertTrue(any("Language may be an issue" in f for f in jonas["flags"]))

    def test_availability_filter(self):
        run_dir = self.fresh_run()
        run("verify_evidence.py", run_dir, "--fix", env=self.env)
        req = json.loads((run_dir / "request.json").read_text())
        req.update(availability_required=True, needed_from="2026-10-15")
        (run_dir / "request.json").write_text(json.dumps(req))
        run("rank.py", run_dir, env=self.env)
        ranking = json.loads((run_dir / "ranking.json").read_text())
        self.assertEqual([u["key"] for u in ranking["unavailable"]], ["anna-maria-muller"])  # 0 %, free from Nov

    def test_check_report(self):
        run_dir = self.fresh_run()
        run("verify_evidence.py", run_dir, "--fix", env=self.env)
        run("rank.py", run_dir, env=self.env)
        report = run_dir / "report.md"
        report.write_text("# Report\nAnna Maria Müller, Jonas Becker, Jan Schmidt, Jörg Weiss\n"
                          "She is 34 years old.\n{{TODO}}\n")
        out = run("check_report.py", report, run_dir, env=self.env)
        self.assertEqual(out.returncode, 1)
        self.assertIn("Lena Vogel", out.stdout)                               # coverage
        self.assertIn("{{TODO}}", out.stdout)
        self.assertIn("years old", out.stdout)                                # protected attribute warning


if __name__ == "__main__":
    unittest.main()
