#!/usr/bin/env python
"""Evaluation for the Career Gap Analyzer.

Run from the backend folder with the venv active:

    python ..\\eval\\run_eval.py --label my-first-run     (run all cases, save results)
    python ..\\eval\\run_eval.py --only case01_dbms_vs_backend
    python ..\\eval\\run_eval.py --no-cache              (ignore saved AI answers)
    python ..\\eval\\run_eval.py --compare               (table of all saved runs)
"""
import argparse
import datetime
import hashlib
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

EVAL_DIR = Path(__file__).resolve().parent
BACKEND_DIR = EVAL_DIR.parent / "backend"
sys.path.insert(0, str(EVAL_DIR))
import metrics  # noqa: E402

LEVEL_RANKS = {"exposure": 1, "working": 2, "proficient": 3}


def load_backend() -> SimpleNamespace:
    os.chdir(BACKEND_DIR)  # so the .env file is found
    sys.path.insert(0, str(BACKEND_DIR))
    from app.config import settings
    from app.services.llm.base import LLMClient
    from app.services.llm.factory import get_llm
    from app.services.parsing import extract_text
    from app.services.skill_extraction import extract_skills
    from app.services.job_extraction import extract_requirements
    from app.services.matching import match_requirements
    from app.services.gap_analysis import LEVEL_RANK, LEVEL_SCORE, RELATION_FACTOR, status_for
    return SimpleNamespace(
        settings=settings, LLMClient=LLMClient, get_llm=get_llm, extract_text=extract_text,
        extract_skills=extract_skills, extract_requirements=extract_requirements,
        match_requirements=match_requirements, LEVEL_RANK=LEVEL_RANK, LEVEL_SCORE=LEVEL_SCORE,
        RELATION_FACTOR=RELATION_FACTOR, status_for=status_for,
    )


def make_caching_llm(B, use_cache: bool):
    """Wraps the real LLM and saves every answer to disk, so re-runs cost no quota.
    The cache key includes the prompt and model, so changing either gives fresh answers."""
    cache_dir = EVAL_DIR / ".cache"
    cache_dir.mkdir(exist_ok=True)
    inner = B.get_llm()
    model = f"{B.settings.llm_provider}:{B.settings.llm_model}"

    class CachingLLM(B.LLMClient):
        def complete_json(self, system, user, schema):
            key = hashlib.sha256(json.dumps([model, system, user, schema], sort_keys=True).encode()).hexdigest()
            path = cache_dir / f"{key}.json"
            if use_cache and path.exists():
                return json.loads(path.read_text(encoding="utf-8"))
            out = inner.complete_json(system, user, schema)
            path.write_text(json.dumps(out), encoding="utf-8")
            return out

    return CachingLLM()


def run_case(case_file: Path, llm, B) -> dict:
    case = json.loads(case_file.read_text(encoding="utf-8"))
    base = case_file.parent

    def read(rel: str) -> str:
        p = (base / rel).resolve()
        return B.extract_text(p.name, p.read_bytes())

    # 1. Skills from all syllabi (same merge rule as the app: keep the highest level)
    merged = {}
    for rel in case["syllabi"]:
        for s in B.extract_skills(read(rel), llm):
            cur = merged.get(s.name.lower())
            if cur is None or B.LEVEL_RANK[s.level] > B.LEVEL_RANK[cur.level]:
                merged[s.name.lower()] = s
    skills = list(merged.values())

    # 2. Job requirements, matching and status (same scoring rules as the app)
    reqs = B.extract_requirements(read(case["job"]), llm)
    matches = B.match_requirements([r.name for r in reqs], [s.name for s in skills], llm)
    by_skill = {s.name.lower(): s for s in skills}
    system_reqs = []
    for r, m in zip(reqs, matches):
        sk = by_skill.get(m.matched_skill.lower()) if m.matched_skill else None
        score = B.LEVEL_SCORE[sk.level] * B.RELATION_FACTOR[m.relation] if sk else 0.0
        system_reqs.append({
            "name": r.name, "importance": r.importance, "status": B.status_for(score),
            "matched_skill": sk.name if sk else None, "relation": m.relation,
        })

    return {
        "id": case["id"],
        "description": case.get("description", ""),
        "skills": metrics.evaluate_list(
            [{"name": s.name, "level": s.level} for s in skills],
            case["gold_skills"], case.get("acceptable_extras", []), "level", LEVEL_RANKS),
        "requirements": metrics.evaluate_list(
            [{"name": r.name, "importance": r.importance} for r in reqs],
            case["gold_requirements"], [], "importance"),
        "status": metrics.evaluate_status(system_reqs, case["gold_requirements"]),
        "system_requirements": system_reqs,
    }


def pct(x):
    return "n/a" if x is None else f"{x * 100:.0f}%"


def print_case(r: dict):
    print(f"\n== {r['id']}: {r['description']}")
    if r.get("error"):
        print("   FAILED:", r["error"])
        return
    s, q, st = r["skills"], r["requirements"], r["status"]
    print(f"   skills        P {pct(s['precision'])}  R {pct(s['recall'])}  F1 {pct(s['f1'])}")
    print(f"   requirements  P {pct(q['precision'])}  R {pct(q['recall'])}  F1 {pct(q['f1'])}")
    print(f"   status        {st['correct']}/{st['found']} correct among {st['gold_total']} labelled requirements")
    if s["missed"]:
        print("   missed skills:       ", ", ".join(s["missed"]))
    if s["false_positives"]:
        print("   extra skills:        ", ", ".join(s["false_positives"]))
    if s.get("duplicates"):
        print("   duplicates (not counted as errors):", ", ".join(s["duplicates"]))
    if q["missed"]:
        print("   missed requirements: ", ", ".join(q["missed"]))
    if q["false_positives"]:
        print("   extra requirements:  ", ", ".join(q["false_positives"]))
    for row in st["rows"]:
        if row["system_status"] != row["gold_status"]:
            print(f"   status differs: {row['gold']}: you={row['gold_status']}, system={row['system_status']}")


def print_summary(sm: dict):
    print("\n==================== SUMMARY ====================")
    print(f"cases run: {sm['cases_run']}   failed: {sm['cases_failed']}")
    k, q, st = sm["skills"], sm["requirements"], sm["status"]
    print(f"Skill extraction        precision {pct(k['precision'])}  recall {pct(k['recall'])}  F1 {pct(k['f1'])}")
    print(f"   level exact {pct(k['level_exact'])}   within one level {pct(k['level_within1'])}")
    print(f"Requirement extraction  precision {pct(q['precision'])}  recall {pct(q['recall'])}  F1 {pct(q['f1'])}   importance {pct(q['importance_acc'])}")
    print(f"Gap status              accuracy {pct(st['accuracy_found'])} (found), {pct(st['accuracy_end_to_end'])} (end to end)")
    print(f"   coverage-index error {st['coverage_index_error_pts']} points   requirements found {pct(st['found_rate'])}")
    print("\nConfusion matrix (rows = your label, columns = system):")
    print(f"{'':10}" + "".join(f"{p:>10}" for p in metrics.LABELS))
    for g in metrics.LABELS:
        print(f"{g:10}" + "".join(f"{st['confusion'][g][p]:>10}" for p in metrics.LABELS))


def compare():
    files = sorted((EVAL_DIR / "results").glob("*.json"))
    if not files:
        print("No saved results yet. Run an evaluation first.")
        return
    print("| Run | Model | Cases | Skill P | Skill R | Skill F1 | Req P | Req R | Req F1 | Status acc (end to end) | Index error (pts) |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for f in files:
        d = json.loads(f.read_text(encoding="utf-8"))
        s = d["summary"]
        print(f"| {d['label']} | {d['model']} | {s['cases_run']} | {pct(s['skills']['precision'])} | {pct(s['skills']['recall'])} | "
              f"{pct(s['skills']['f1'])} | {pct(s['requirements']['precision'])} | {pct(s['requirements']['recall'])} | "
              f"{pct(s['requirements']['f1'])} | {pct(s['status']['accuracy_end_to_end'])} | {s['status']['coverage_index_error_pts']} |")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", default="run")
    ap.add_argument("--only", help="run just one case id")
    ap.add_argument("--no-cache", action="store_true")
    ap.add_argument("--compare", action="store_true")
    args = ap.parse_args()

    if args.compare:
        compare()
        return

    B = load_backend()
    llm = make_caching_llm(B, use_cache=not args.no_cache)
    case_files = sorted(p for p in (EVAL_DIR / "cases").glob("*.json") if not p.name.startswith("_"))
    if args.only:
        case_files = [p for p in case_files if args.only in p.stem]
    if not case_files:
        print("No case files found in eval/cases.")
        return

    print(f"Model: {B.settings.llm_provider}:{B.settings.llm_model}   cases: {len(case_files)}")
    results = []
    for cf in case_files:
        print(f"Running {cf.stem} ...", flush=True)
        try:
            results.append(run_case(cf, llm, B))
        except Exception as e:  # keep going if one case fails
            results.append({"id": cf.stem, "description": "", "error": f"{type(e).__name__}: {e}"})
        print_case(results[-1])

    summary = metrics.summarize(results)
    print_summary(summary)

    out_dir = EVAL_DIR / "results"
    out_dir.mkdir(exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    out = out_dir / f"{args.label}_{stamp}.json"
    out.write_text(json.dumps({
        "label": args.label, "model": f"{B.settings.llm_model}", "timestamp": stamp,
        "summary": summary, "cases": results,
    }, indent=2), encoding="utf-8")
    print(f"\nSaved: {out}")


if __name__ == "__main__":
    main()
