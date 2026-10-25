import axios from "axios";

const BASE = import.meta.env.VITE_API_URL || "https://career-gap-analyzer-vr3q.onrender.com";

// LLM calls can be slow, so allow up to 3 minutes per request.
export const api = axios.create({ baseURL: BASE, timeout: 180000 });

export function errorMessage(err) {
  const detail = err?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (detail) return JSON.stringify(detail);
  if (err?.code === "ERR_NETWORK") {
    return "Cannot reach the backend. Is it running at " + BASE + " ?";
  }
  return err?.message || "Something went wrong";
}

export async function pingBackend() {
  await api.get("/health", { timeout: 4000 });
}

export async function uploadDocument(kind, file) {
  const form = new FormData();
  form.append("kind", kind);
  form.append("file", file);
  const { data } = await api.post("/documents", form);
  return data;
}

export async function listDocuments() {
  const { data } = await api.get("/documents");
  return data;
}

export async function extractSkills(docId) {
  const { data } = await api.post(`/documents/${docId}/extract-skills`);
  return data;
}

export async function extractRequirements(docId) {
  const { data } = await api.post(`/documents/${docId}/extract-requirements`);
  return data;
}

export async function createAnalysis(jobId, syllabusIds) {
  const { data } = await api.post("/analysis", {
    job_document_id: jobId,
    syllabus_document_ids: syllabusIds,
  });
  return data;
}

export async function listAnalyses() {
  const { data } = await api.get("/analysis");
  return data;
}

export async function getAnalysis(analysisId) {
  const { data } = await api.get(`/analysis/${analysisId}`);
  return data;
}

export async function createRecommendations(analysisId) {
  const { data } = await api.post(`/analysis/${analysisId}/recommendations`);
  return data;
}

export async function getRecommendations(analysisId) {
  const { data } = await api.get(`/analysis/${analysisId}/recommendations`);
  return data;
}

// Retries only on rate limits / temporary server errors (common on free LLM tiers).
export async function withRetry(fn, attempts = 4, delayMs = 6000, onRetry) {
  let last;
  for (let i = 0; i < attempts; i++) {
    try {
      return await fn();
    } catch (e) {
      last = e;
      const status = e?.response?.status;
      const retryable = status === 429 || status === 502 || status === 503;
      if (!retryable || i === attempts - 1) break;
      if (onRetry) onRetry(i + 1);
      await new Promise((r) => setTimeout(r, delayMs * (i + 1)));
    }
  }
  throw last;
}
