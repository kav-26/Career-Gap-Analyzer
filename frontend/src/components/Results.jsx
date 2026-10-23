import { useState } from "react";
import Dashboard from "./Dashboard.jsx";
import Recommendations from "./Recommendations.jsx";
import { createRecommendations, errorMessage } from "../api.js";

export default function Results({ result, onReset }) {
  const [tab, setTab] = useState("gaps");
  const [recs, setRecs] = useState(result.recs);
  const [recsError, setRecsError] = useState(result.recsError);
  const [loading, setLoading] = useState(false);

  async function generate() {
    setLoading(true);
    setRecsError(null);
    try {
      const data = await createRecommendations(result.analysis.analysis_id);
      setRecs(data);
    } catch (e) {
      setRecsError(errorMessage(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <div className="row-between page-head">
        <h1>Your results</h1>
        <button className="btn ghost" onClick={onReset}>
          Analyze another job
        </button>
      </div>

      <div className="tabs">
        <button className={tab === "gaps" ? "tab active" : "tab"} onClick={() => setTab("gaps")}>
          Gap analysis
        </button>
        <button className={tab === "projects" ? "tab active" : "tab"} onClick={() => setTab("projects")}>
          Recommended projects
        </button>
      </div>

      {tab === "gaps" && <Dashboard analysis={result.analysis} />}
      {tab === "projects" && (
        <Recommendations recs={recs} error={recsError} loading={loading} onGenerate={generate} />
      )}
    </div>
  );
}
