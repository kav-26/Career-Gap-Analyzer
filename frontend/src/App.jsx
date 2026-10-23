import { useEffect, useRef, useState } from "react";
import Sidebar from "./components/Sidebar.jsx";
import UploadPage from "./components/UploadPage.jsx";
import Progress from "./components/Progress.jsx";
import Dashboard from "./components/Dashboard.jsx";
import Recommendations from "./components/Recommendations.jsx";
import History from "./components/History.jsx";
import { runPipeline, STEPS } from "./pipeline.js";
import {
  errorMessage,
  pingBackend,
  createRecommendations,
  getAnalysis,
  getRecommendations,
  withRetry,
} from "./api.js";

const TITLES = {
  running: ["Analyzing...", "Reading your documents and scoring the gaps."],
  overview: ["Overview", "How well your coursework matches this job."],
  skills: ["Skills & gaps", "Every requirement, with the evidence behind its status."],
  projects: ["Recommended projects", "Projects that would close your biggest gaps."],
  history: ["History", "Your earlier analyses."],
};

export default function App() {
  const [view, setView] = useState("upload"); // upload | running | overview | skills | projects | history
  const [progress, setProgress] = useState({ step: 0, state: "active", note: "" });
  const [error, setError] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [jobName, setJobName] = useState("");
  const [recs, setRecs] = useState(null);
  const [recsStatus, setRecsStatus] = useState("idle"); // idle | loading | done | error
  const [recsError, setRecsError] = useState(null);
  const [online, setOnline] = useState(null);
  const recsToken = useRef(0);

  // Backend status light in the sidebar
  useEffect(() => {
    let alive = true;
    async function ping() {
      try {
        await pingBackend();
        if (alive) setOnline(true);
      } catch {
        if (alive) setOnline(false);
      }
    }
    ping();
    const timer = setInterval(ping, 15000);
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, []);

  // Recommendations load in the background so the results appear sooner
  async function loadRecs(analysisId) {
    const token = recsToken.current + 1;
    recsToken.current = token;
    setRecs(null);
    setRecsError(null);
    setRecsStatus("loading");
    try {
      const data = await withRetry(() => createRecommendations(analysisId), 4, 6000);
      if (token !== recsToken.current) return;
      setRecs(data);
      setRecsStatus("done");
    } catch (e) {
      if (token !== recsToken.current) return;
      setRecsError(errorMessage(e));
      setRecsStatus("error");
    }
  }

  async function start(input) {
    setError(null);
    setView("running");
    setProgress({ step: 0, state: "active", note: "" });
    let current = 0;
    try {
      const out = await runPipeline(input, (p) => {
        current = p.step;
        setProgress(p);
      });
      setAnalysis(out.analysis);
      setJobName(out.jobName);
      setView("overview");
      loadRecs(out.analysis.analysis_id);
    } catch (e) {
      setError({ step: current, message: errorMessage(e) });
    }
  }

  // Open an earlier analysis from History
  async function openAnalysis(item) {
    const data = await getAnalysis(item.analysis_id);
    recsToken.current += 1; // cancel any recommendation request still running
    setAnalysis(data);
    setJobName(item.jobName);
    setRecs(null);
    setRecsError(null);
    setView("overview");
    try {
      const saved = await getRecommendations(item.analysis_id);
      setRecs(saved);
      setRecsStatus("done");
    } catch (e) {
      if (e?.response?.status === 404) {
        loadRecs(item.analysis_id);
      } else {
        setRecsStatus("error");
        setRecsError(errorMessage(e));
      }
    }
  }

  function navigate(next) {
    setError(null);
    setView(next);
  }

  const title = TITLES[view];

  return (
    <div className="shell">
      <Sidebar
        view={view}
        onNavigate={navigate}
        hasResult={Boolean(analysis)}
        running={view === "running" && !error}
        score={analysis ? analysis.match_score : null}
        recsStatus={recsStatus}
        recsCount={recs && recs.projects ? recs.projects.length : 0}
        online={online}
      />

      <div className="content">
        {title && (
          <header className="page-bar">
            <h1>{title[0]}</h1>
            <p className="muted">{view === "overview" && jobName ? `Job posting: ${jobName}` : title[1]}</p>
          </header>
        )}

        <main className="container">
          {view === "upload" && <UploadPage onStart={start} />}
          {view === "running" && (
            <Progress steps={STEPS} progress={progress} error={error} onBack={() => navigate("upload")} />
          )}
          {(view === "overview" || view === "skills") && analysis && (
            <Dashboard analysis={analysis} section={view} jobName={jobName} onNavigate={navigate} />
          )}
          {view === "projects" && (
            <Recommendations
              recs={recs}
              status={recsStatus}
              error={recsError}
              onGenerate={() => analysis && loadRecs(analysis.analysis_id)}
            />
          )}
          {view === "history" && <History onOpen={openAnalysis} />}
        </main>
      </div>
    </div>
  );
}
