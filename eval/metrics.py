"""Scoring helpers for the evaluation. Pure Python, no backend imports."""
import difflib
import re

STOP = {
    "and", "or", "the", "of", "for", "with", "to", "a", "an", "in", "using", "such", "as",
    "basic", "basics", "intro", "introduction", "e.g", "eg", "skills", "knowledge", "experience",
}
STATUS_VALUE = {"covered": 1.0, "partial": 0.5, "missing": 0.0}
IMPORTANCE_WEIGHT = {"must_have": 2, "nice_to_have": 1}
LABELS = ["covered", "partial", "missing"]


def _tokens(text: str) -> set:
    out = set()
    for t in re.findall(r"[a-z0-9+#.]+", text.lower()):
        t = t.strip(".")
        if t and t not in STOP:
            out.add(t)
    return out


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def similarity(a: str, b: str) -> float:
    """0 = no match. 1.0 = same text, 0.9 = one name's words are all inside the other, else fuzzy."""
    na, nb = _norm(a), _norm(b)
    if na == nb:
        return 1.0
    ta, tb = _tokens(a), _tokens(b)
    if ta and tb and (ta <= tb or tb <= ta):
        return 0.9
    ratio = difflib.SequenceMatcher(None, na, nb).ratio()
    return ratio if ratio >= 0.88 else 0.0


def best_sim(name: str, gold_item: dict) -> float:
    names = [gold_item["name"]] + list(gold_item.get("aliases", []))
    return max(similarity(name, n) for n in names)


def align(extracted_names: list, gold_items: list) -> dict:
    """One-to-one matching, best pairs first. Returns {gold_index: extracted_index}."""
    candidates = []
    for gi, g in enumerate(gold_items):
        for ei, e in enumerate(extracted_names):
            s = best_sim(e, g)
            if s > 0:
                candidates.append((s, gi, ei))
    candidates.sort(key=lambda c: (-c[0], c[1], c[2]))
    pairs, used = {}, set()
    for _, gi, ei in candidates:
        if gi in pairs or ei in used:
            continue
        pairs[gi] = ei
        used.add(ei)
    return pairs


def _prf(tp: int, fp: int, fn: int) -> dict:
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"precision": round(precision, 3), "recall": round(recall, 3), "f1": round(f1, 3)}


def evaluate_list(extracted: list, gold_items: list, extras: list, attr: str, ranks: dict | None = None) -> dict:
    """Compare extracted items (dicts with 'name' and attr) with gold items."""
    names = [e["name"] for e in extracted]
    pairs = align(names, gold_items)
    matched_ext = set(pairs.values())

    unmatched = [i for i in range(len(extracted)) if i not in matched_ext]
    # A second name for a labelled skill (for example "Keras" next to "TensorFlow") is a duplicate, not an error.
    duplicates = [i for i in unmatched if any(best_sim(names[i], g) > 0 for g in gold_items)]
    ignored = {i for i in unmatched if i in duplicates or any(similarity(names[i], x) > 0 for x in extras)}
    false_pos = [i for i in unmatched if i not in ignored]

    tp, fp, fn = len(pairs), len(false_pos), len(gold_items) - len(pairs)

    exact = within1 = 0
    for gi, ei in pairs.items():
        g_val, e_val = gold_items[gi].get(attr), extracted[ei].get(attr)
        if g_val == e_val:
            exact += 1
            within1 += 1
        elif ranks and g_val in ranks and e_val in ranks and abs(ranks[g_val] - ranks[e_val]) <= 1:
            within1 += 1

    return {
        "tp": tp, "fp": fp, "fn": fn, **_prf(tp, fp, fn),
        "attr_total": len(pairs), "attr_exact": exact, "attr_within1": within1,
        "missed": [gold_items[i]["name"] for i in range(len(gold_items)) if i not in pairs],
        "false_positives": [names[i] for i in false_pos],
        "duplicates": [names[i] for i in duplicates],
        "matched": [[gold_items[gi]["name"], names[ei]] for gi, ei in pairs.items()],
    }


def coverage_index(items: list):
    total = sum(IMPORTANCE_WEIGHT[i["importance"]] for i in items)
    if not total:
        return None
    return sum(IMPORTANCE_WEIGHT[i["importance"]] * STATUS_VALUE[i["status"]] for i in items) / total


def evaluate_status(system_reqs: list, gold_reqs: list) -> dict:
    """Compare the system's covered/partial/missing labels with the human labels."""
    pairs = align([r["name"] for r in system_reqs], gold_reqs)
    confusion = {g: {p: 0 for p in LABELS} for g in LABELS}
    rows, correct = [], 0
    for gi, g in enumerate(gold_reqs):
        ei = pairs.get(gi)
        if ei is None:
            rows.append({"gold": g["name"], "gold_status": g["status"], "system": None, "system_status": None})
            continue
        s = system_reqs[ei]
        if s["status"] == g["status"]:
            correct += 1
        confusion[g["status"]][s["status"]] += 1
        rows.append({"gold": g["name"], "gold_status": g["status"], "system": s["name"], "system_status": s["status"]})
    return {
        "gold_total": len(gold_reqs),
        "found": len(pairs),
        "correct": correct,
        "rows": rows,
        "confusion": confusion,
        "gold_index": coverage_index(gold_reqs),
        "system_index": coverage_index(system_reqs),
    }


def summarize(results: list) -> dict:
    ok = [r for r in results if not r.get("error")]

    def sums(key):
        return (sum(r[key]["tp"] for r in ok), sum(r[key]["fp"] for r in ok), sum(r[key]["fn"] for r in ok))

    def ratio(num, den):
        return round(num / den, 3) if den else None

    sk, rq = sums("skills"), sums("requirements")
    confusion = {g: {p: 0 for p in LABELS} for g in LABELS}
    gold_total = found = correct = 0
    errors = []
    for r in ok:
        st = r["status"]
        gold_total += st["gold_total"]
        found += st["found"]
        correct += st["correct"]
        for g in LABELS:
            for p in LABELS:
                confusion[g][p] += st["confusion"][g][p]
        if st["gold_index"] is not None and st["system_index"] is not None:
            errors.append(abs(st["gold_index"] - st["system_index"]) * 100)

    return {
        "cases_run": len(ok),
        "cases_failed": len(results) - len(ok),
        "skills": {**_prf(*sk),
                   "level_exact": ratio(sum(r["skills"]["attr_exact"] for r in ok), sum(r["skills"]["attr_total"] for r in ok)),
                   "level_within1": ratio(sum(r["skills"]["attr_within1"] for r in ok), sum(r["skills"]["attr_total"] for r in ok))},
        "requirements": {**_prf(*rq),
                         "importance_acc": ratio(sum(r["requirements"]["attr_exact"] for r in ok), sum(r["requirements"]["attr_total"] for r in ok))},
        "status": {
            "accuracy_found": ratio(correct, found),
            "accuracy_end_to_end": ratio(correct, gold_total),
            "found_rate": ratio(found, gold_total),
            "coverage_index_error_pts": round(sum(errors) / len(errors), 1) if errors else None,
            "confusion": confusion,
        },
    }
