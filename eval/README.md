# Evaluation

Measures how well the system agrees with human labels.

## What is measured
| Metric | Question it answers |
|---|---|
| Skill extraction precision / recall / F1 | Does it find the skills a syllabus really teaches, without inventing others? |
| Level accuracy | Does it grade depth (exposure / working / proficient) like a human? |
| Requirement extraction precision / recall / F1 | Does it find the real job requirements, without duplicates? |
| Gap status accuracy | Does covered / partial / missing agree with a human? |
| Coverage-index error | How far is the overall score from the human one? (covered = 1, partial = 0.5, missing = 0, must-have counts double) |

## How to label a new case
1. Put the syllabus and the job posting as .txt (or .pdf / .docx) files in `eval/samples/`.
2. Copy `cases/_template.json` to `cases/caseNN_name.json` and fill it in.
3. **Label before you run the system**, so the output cannot influence you.
4. `gold_skills`: skills the syllabus clearly teaches. Add `aliases` for other names of the same skill.
5. `acceptable_extras`: skills the system may list without being counted as wrong.
6. `gold_requirements`: the job's requirements as YOU would list them (one per idea; "X or Y" is one requirement), with `importance` and a `status`:

| Status | Meaning |
|---|---|
| covered | The coursework clearly teaches AND practices it (lab, assignment or project) |
| partial | Only introduced or mentioned briefly, or only a related skill is taught |
| missing | Not in the coursework at all |

Tip: for 2 or 3 cases, ask a classmate to label independently and report how often you agree. Labels are partly subjective, and reporting agreement makes the evaluation more honest.

## Run (from the backend folder, venv active)
    python ..\eval\run_eval.py --label gemini-3.5-flash-lite
    python ..\eval\run_eval.py --compare

AI answers are cached in `eval/.cache`, so re-running costs no quota unless the prompt or model changes.
Use `--no-cache` to force fresh answers.
