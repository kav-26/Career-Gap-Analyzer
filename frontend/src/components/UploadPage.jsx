import { useState } from "react";
import FileDrop from "./FileDrop.jsx";

export default function UploadPage({ onStart }) {
  const [syllabi, setSyllabi] = useState([]);
  const [mode, setMode] = useState("paste"); // paste | upload
  const [jobText, setJobText] = useState("");
  const [jobFiles, setJobFiles] = useState([]);

  const jobReady = mode === "paste" ? jobText.trim().length >= 30 : jobFiles.length === 1;
  const ready = syllabi.length > 0 && jobReady;

  function submit() {
    onStart({
      syllabusFiles: syllabi,
      jobFile: mode === "upload" ? jobFiles[0] : null,
      jobText: mode === "paste" ? jobText : "",
    });
  }

  return (
    <div>
      <section className="hero">
        <h1>How ready are you for your target job?</h1>
        <p className="muted">
          Upload your course syllabi and a job posting. The app finds the skills you were taught,
          compares them with what the job needs, and suggests projects to close the gaps.
        </p>
      </section>

      <div className="grid2">
        <section className="card">
          <h2>1. Your courses</h2>
          <p className="muted">Add one or more syllabi (PDF, DOCX or TXT).</p>
          <FileDrop
            files={syllabi}
            onChange={setSyllabi}
            multiple
            hint="Text-based PDFs work best. Scanned images are not supported yet."
          />
        </section>

        <section className="card">
          <h2>2. Target job</h2>
          <div className="tabs small">
            <button className={mode === "paste" ? "tab active" : "tab"} onClick={() => setMode("paste")}>
              Paste text
            </button>
            <button className={mode === "upload" ? "tab active" : "tab"} onClick={() => setMode("upload")}>
              Upload file
            </button>
          </div>
          {mode === "paste" ? (
            <textarea
              className="textarea"
              rows={9}
              placeholder="Paste the full job posting here..."
              value={jobText}
              onChange={(e) => setJobText(e.target.value)}
            />
          ) : (
            <FileDrop files={jobFiles} onChange={setJobFiles} multiple={false} hint="One job posting file." />
          )}
        </section>
      </div>

      <div className="actions">
        <button className="btn primary" disabled={!ready} onClick={submit}>
          Analyze my gaps
        </button>
        {!ready && <span className="muted">Add at least one syllabus and a job posting to continue.</span>}
      </div>
      <p className="muted note">
        Your documents are sent to the AI provider configured in the backend. If that is a free tier,
        the provider may use the content, so avoid uploading personal details.
      </p>
    </div>
  );
}
