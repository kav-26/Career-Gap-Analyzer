import {
  uploadDocument,
  extractSkills,
  extractRequirements,
  createAnalysis,
  withRetry,
} from "./api.js";

export const STEPS = [
  "Uploading documents",
  "Reading your syllabi and the job posting",
  "Matching skills and scoring gaps",
];

// Runs tasks with at most `limit` running at once (keeps free-tier rate limits happy).
async function runLimited(tasks, limit, onEach) {
  let next = 0;
  const results = [];
  async function worker() {
    while (next < tasks.length) {
      const index = next;
      next += 1;
      results[index] = await tasks[index]();
      if (onEach) onEach();
    }
  }
  const workers = Array.from({ length: Math.min(limit, tasks.length) }, worker);
  await Promise.all(workers);
  return results;
}

// Runs the backend flow. Recommendations are loaded separately, in the background.
export async function runPipeline({ syllabusFiles, jobFile, jobText }, onProgress) {
  const progress = (step, state, note = "") => onProgress({ step, state, note });
  const retryNote = (step) => (n) =>
    progress(step, "active", `Rate limit or busy server, retrying (attempt ${n + 1})...`);

  // 1. Upload everything at once
  progress(0, "active");
  const jobToUpload = jobFile || new File([jobText], "job_posting.txt", { type: "text/plain" });
  const [job, ...syllabi] = await Promise.all([
    uploadDocument("job", jobToUpload),
    ...syllabusFiles.map((f) => uploadDocument("syllabus", f)),
  ]);
  const syllabusIds = syllabi.map((d) => d.id);
  progress(0, "done");

  // 2. Read the job posting and all syllabi in parallel (3 at a time)
  progress(1, "active");
  const total = syllabusIds.length + 1;
  let finished = 0;
  const tick = () => {
    finished += 1;
    progress(1, "active", `${finished} of ${total} documents read`);
  };
  const tasks = [
    () => withRetry(() => extractRequirements(job.id), 4, 6000, retryNote(1)),
    ...syllabusIds.map((id) => () => withRetry(() => extractSkills(id), 4, 6000, retryNote(1))),
  ];
  await runLimited(tasks, 3, tick);
  progress(1, "done");

  // 3. Match and score
  progress(2, "active");
  const analysis = await withRetry(() => createAnalysis(job.id, syllabusIds), 4, 6000, retryNote(2));
  progress(2, "done");

  return { analysis, jobName: jobToUpload.name };
}
