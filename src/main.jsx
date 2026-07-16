import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  Clock3,
  FileSearch,
  FolderSearch,
  History,
  LockKeyhole,
  Search,
  ShieldCheck,
  Upload,
  UserRoundSearch,
  XCircle
} from "lucide-react";
import "./styles.css";

const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
const TOKEN = "demo-reviewer-token";
const states = ["Delhi", "Maharashtra", "West Bengal", "Tamil Nadu", "Uttar Pradesh", "Rajasthan", "Bihar"];

const fallbackCases = [
  { case_id: "PM-DEMO-SEED", report_type: "missing", display_name: "Seed LFW Demo Pending", age: 8, gender: "unknown", region: "Delhi", location: "Run backend seed script", notes: "SYNTHETIC DEMO DATA - LFW public dataset wrappers appear here after seeding.", status: "open", image_url: "", face_url: "" }
];

function authHeaders() {
  return { Authorization: `Bearer ${TOKEN}` };
}

async function apiFetch(path, options = {}) {
  const response = await fetch(`${API}${path}`, {
    ...options,
    headers: { ...authHeaders(), ...(options.headers || {}) }
  });
  const json = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(json.detail?.message || json.detail || "Backend request failed");
  return json;
}

function scoreTone(score) {
  if (score >= 70) return "high";
  if (score >= 50) return "medium";
  return "low";
}

function WatermarkedImage({ src, alt }) {
  return (
    <div className="photo-frame">
      {src ? <img src={`${API}${src}`} alt={alt} /> : <div className="photo-empty">LFW seed pending</div>}
      <strong>SYNTHETIC DEMO DATA - LFW PUBLIC DATASET</strong>
    </div>
  );
}

function App() {
  const [view, setView] = useState("dashboard");
  const [cases, setCases] = useState(fallbackCases);
  const [selected, setSelected] = useState(fallbackCases[0]);
  const [candidates, setCandidates] = useState([]);
  const [coverage, setCoverage] = useState(null);
  const [audit, setAudit] = useState([]);
  const [indexStatus, setIndexStatus] = useState(null);
  const [notice, setNotice] = useState("");
  const [lastSync, setLastSync] = useState(null);

  async function refresh() {
    try {
      const [caseRows, auditRows, vectorStatus] = await Promise.all([apiFetch("/cases"), apiFetch("/audit"), apiFetch("/vector-index")]);
      if (caseRows.length) {
        setCases(caseRows);
        setSelected((current) => caseRows.find((row) => row.case_id === current.case_id) || caseRows[0]);
      }
      setAudit(auditRows);
      setIndexStatus(vectorStatus);
      setLastSync(new Date());
    } catch (error) {
      setNotice(`Backend not ready: ${error.message}`);
    }
  }

  useEffect(() => {
    refresh();
    const timer = window.setInterval(refresh, 10000);
    return () => window.clearInterval(timer);
  }, []);

  const stats = useMemo(() => {
    const missing = cases.filter((item) => item.report_type === "missing").length;
    return [
      ["Missing demo records", missing, "Stored embeddings"],
      ["Found searches", audit.filter((item) => item.action === "candidate_search").length, "Reviewer-only"],
      ["Audit entries", audit.length, "Append-only"],
      ["Open cases", cases.filter((item) => item.status === "open").length, "Awaiting review"]
    ];
  }, [cases, audit]);

  function navigate(next) {
    setView(next);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand"><ShieldCheck size={22} /><div><b>PUNARMILAN</b><span>Case matching and review</span></div></div>
        <div className="identity"><span>Authenticated reviewer</span><b>Demo Reviewer</b><em>NGO / CWC / Police</em></div>
        <nav>
          <button className={view === "dashboard" ? "active" : ""} onClick={() => navigate("dashboard")}><BarChart3 size={18} /> Dashboard</button>
          <button className={view === "queue" ? "active" : ""} onClick={() => navigate("queue")}><FolderSearch size={18} /> Case List</button>
          <button className={view === "detail" ? "active" : ""} onClick={() => navigate("detail")}><UserRoundSearch size={18} /> Case Detail</button>
          <button className={view === "search" ? "active" : ""} onClick={() => navigate("search")}><Search size={18} /> Photo Search</button>
          <button className={view === "missing" ? "active" : ""} onClick={() => navigate("missing")}><FileSearch size={18} /> Report Missing</button>
          <button className={view === "found" ? "active" : ""} onClick={() => navigate("found")}><Upload size={18} /> Report Found</button>
          <button className={view === "audit" ? "active" : ""} onClick={() => navigate("audit")}><History size={18} /> Audit Trail</button>
        </nav>
        <div className="sidebar-note"><LockKeyhole size={16} /><span>Ranked candidates are restricted to authenticated reviewers. Public users only submit reports or check their own status.</span></div>
      </aside>
      <main>
        <header className="topbar">
          <span>Reviewer workspace</span>
          <strong><AlertTriangle size={14} /> SYNTHETIC DEMO DATA - NO REAL CASE RECORDS</strong>
          <button onClick={refresh}>Refresh</button>
        </header>
        <AuditRail audit={audit} lastSync={lastSync} />
        {notice && <div className="notice">{notice}</div>}
        {view === "dashboard" && <Dashboard stats={stats} cases={cases} indexStatus={indexStatus} refresh={refresh} setNotice={setNotice} />}
        {view === "queue" && <CaseQueue cases={cases} select={(row) => { setSelected(row); navigate("detail"); }} />}
        {view === "detail" && <CaseDetail selected={selected} candidates={candidates} setView={navigate} />}
        {view === "search" && <PhotoSearch setCandidates={setCandidates} setCoverage={setCoverage} coverage={coverage} candidates={candidates} setNotice={setNotice} refresh={refresh} />}
        {view === "missing" && <Intake type="missing" setNotice={setNotice} refresh={refresh} />}
        {view === "found" && <Intake type="found" setNotice={setNotice} refresh={refresh} setCandidates={setCandidates} setCoverage={setCoverage} setView={navigate} />}
        {view === "audit" && <AuditPage audit={audit} />}
      </main>
    </div>
  );
}

function AuditRail({ audit, lastSync }) {
  const latest = audit[0];
  return (
    <section className="audit-rail">
      <ShieldCheck size={16} />
      {latest ? (
        <span>Latest audit: {latest.action} by {latest.reviewer_id} at {new Date(latest.timestamp).toLocaleString()}.</span>
      ) : (
        <span>Audit trail active. Searches and reviewer decisions will appear here.</span>
      )}
      {lastSync && <em>Live sync {lastSync.toLocaleTimeString()}</em>}
    </section>
  );
}

function Dashboard({ stats, cases, indexStatus, refresh, setNotice }) {
  async function rebuildIndex() {
    try {
      const result = await apiFetch("/vector-index/rebuild", { method: "POST" });
      setNotice(`FAISS index rebuilt with ${result.records} embedding records.`);
      await refresh();
    } catch (error) {
      setNotice(error.message);
    }
  }
  return (
    <section className="page">
      <p className="eyebrow">System overview</p>
      <h1>Reviewer Dashboard</h1>
      <p className="lede">Face similarity search is decision support only. The system returns ranked candidates for human review, never a binary identification.</p>
      <div className="stats">
        {stats.map(([label, value, detail]) => <div className="stat" key={label}><span>{label}</span><b>{value}</b><small>{detail}</small></div>)}
      </div>
      <section className="panel">
        <div className="section-title">Stored missing-child embedding records</div>
        <DataTable rows={cases.slice(0, 6)} />
      </section>
      <section className="panel index-panel">
        <div>
          <div className="section-title">Vector index status</div>
          <p>Backend: {indexStatus?.index_type || "faiss.IndexFlatIP"}</p>
          <p>Stored missing records: {indexStatus?.stored_missing_records ?? cases.length}</p>
          <p>Mapped embeddings: {indexStatus?.mapped_case_ids ?? 0}</p>
          <p>Persisted artifact: {indexStatus?.index_exists ? "ready" : "not built yet"}</p>
        </div>
        <button className="primary" onClick={rebuildIndex}>Rebuild FAISS index</button>
      </section>
    </section>
  );
}

function DataTable({ rows }) {
  return (
    <div className="table">
      <div className="table-head"><span>Case ID</span><span>Name</span><span>Age</span><span>Gender</span><span>Region</span><span>Status</span></div>
      {rows.map((row) => <div className="table-row" key={row.case_id}><span>{row.case_id}</span><span>{row.display_name}</span><span>{row.age}</span><span>{row.gender}</span><span>{row.region}</span><span>{row.status}</span></div>)}
    </div>
  );
}

function CaseQueue({ cases, select }) {
  return (
    <section className="page">
      <p className="eyebrow">Case list</p>
      <h1>Missing Records</h1>
      <div className="case-list">
        {cases.map((item) => (
          <button className="case-row" key={item.case_id} onClick={() => select(item)}>
            <WatermarkedImage src={item.face_url} alt={item.display_name} />
            <div><span>{item.case_id} - {item.report_type}</span><h3>{item.display_name}</h3><p>Age {item.age} · {item.gender} · {item.location} · {item.region}</p><em>{item.notes}</em></div>
            <strong>{item.status}</strong>
          </button>
        ))}
      </div>
    </section>
  );
}

function CaseDetail({ selected, candidates, setView }) {
  return (
    <section className="page">
      <p className="eyebrow">Case detail</p>
      <h1>{selected.display_name}</h1>
      <div className="detail-layout">
        <aside className="subject panel">
          <WatermarkedImage src={selected.face_url} alt={selected.display_name} />
          <span>{selected.case_id}</span>
          <h2>{selected.report_type}</h2>
          <p>{selected.age} years · {selected.gender}</p>
          <p>{selected.location}, {selected.region}</p>
          <em>{selected.notes}</em>
          <button className="primary" onClick={() => setView("search")}>Run found-photo search</button>
        </aside>
        <section className="panel">
          <div className="section-title">Current ranked candidates</div>
          {candidates.length ? <CandidateList candidates={candidates} /> : <ZeroState />}
        </section>
      </div>
    </section>
  );
}

function PhotoSearch({ candidates, coverage, setCandidates, setCoverage, setNotice, refresh }) {
  const [loading, setLoading] = useState(false);
  async function submit(event) {
    event.preventDefault();
    setLoading(true);
    const form = new FormData(event.currentTarget);
    try {
      const result = await apiFetch("/search", { method: "POST", body: form });
      setCandidates(result.candidates);
      setCoverage(result.coverage);
      setNotice("");
      await refresh();
    } catch (error) {
      setNotice(error.message);
    } finally {
      setLoading(false);
    }
  }
  return (
    <section className="page">
      <p className="eyebrow">Reviewer-only search</p>
      <h1>Upload Found-Child Photo</h1>
      <div className="warning"><AlertTriangle size={18} /><p><b>Candidate search only.</b><br />The API performs real face detection, quality checks, embeddings, and similarity ranking. It never returns “match found.”</p></div>
      <form className="panel form" onSubmit={submit}>
        <label>Approximate age<input name="age" type="number" min="0" placeholder="e.g. 9" /></label>
        <label>Gender<select name="gender"><option value="">Unknown</option><option>Male</option><option>Female</option><option>Other / unknown</option></select></label>
        <label>Region<select name="region"><option value="">Unknown</option>{states.map((state) => <option key={state}>{state}</option>)}</select></label>
        <label className="upload-line"><Upload size={18} /> Upload found-child demo photo<input required name="image" type="file" accept="image/*" /></label>
        <button className="primary" disabled={loading}>{loading ? "Searching..." : "Run ranked similarity search"}</button>
      </form>
      {coverage && <div className="coverage">Searched {coverage.searched_records} records. Returned {coverage.returned_candidates} ranked candidates. {coverage.note}</div>}
      <CandidateList candidates={candidates} refresh={refresh} setNotice={setNotice} />
    </section>
  );
}

function CandidateList({ candidates = [], refresh, setNotice }) {
  async function action(kind, candidate) {
    const form = new FormData();
    form.set("action", kind);
    form.set("case_id", "uploaded-query");
    form.set("candidate_case_id", candidate.case.case_id);
    form.set("similarity_score", candidate.similarity_score);
    try {
      await apiFetch("/review-actions", { method: "POST", body: form });
      setNotice?.(`Decision logged: ${kind.replace("_", " ")} for ${candidate.case.case_id}.`);
      await refresh?.();
    } catch (error) {
      setNotice?.(error.message);
    }
  }
  if (!candidates.length) return null;
  return (
    <div className="ranked-list">
      {candidates.map((candidate) => (
        <article className="candidate" key={candidate.case.case_id}>
          <div className="rank">#{candidate.rank}</div>
          <WatermarkedImage src={candidate.case.face_url} alt={candidate.case.display_name} />
          <div className="candidate-main">
            <div className="candidate-head"><div><span>{candidate.case.case_id}</span><h3>{candidate.case.display_name}</h3></div><Score score={candidate.similarity_score} label={candidate.confidence_label} /></div>
            <p>{candidate.case.age} years · {candidate.case.gender} · {candidate.case.region}. Metadata adjustment: {candidate.metadata_adjustment}.</p>
            <div className="explain">
              {Object.entries(candidate.explanation).map(([key, value]) => <React.Fragment key={key}><span>{key.replace("_", " ")}</span><i style={{ width: `${value}%` }} /></React.Fragment>)}
            </div>
            <div className="actions">
              <button onClick={() => action("confirm_candidate", candidate)}><CheckCircle2 size={16} /> Confirm candidate</button>
              <button onClick={() => action("escalate_candidate", candidate)}><Clock3 size={16} /> Escalate</button>
              <button onClick={() => action("reject_candidate", candidate)}><XCircle size={16} /> Reject</button>
            </div>
          </div>
        </article>
      ))}
    </div>
  );
}

function Score({ score, label }) {
  const tone = scoreTone(score);
  return (
    <div className={`score ${tone}`}>
      <b>{score}%</b>
      <small>{label}</small>
      <div className="bar"><span style={{ width: `${score}%` }} /></div>
    </div>
  );
}

function ZeroState() {
  return <div className="zero"><Search size={24} /><h3>No candidates displayed yet</h3><p>Run a found-photo search. If zero results return, the UI will keep coverage stats and next steps visible.</p></div>;
}

function Intake({ type, setNotice, refresh, setCandidates, setCoverage, setView }) {
  const isMissing = type === "missing";
  const [processing, setProcessing] = useState(false);

  function searchFormFromIntake(form) {
    const searchForm = new FormData();
    const image = form.get("image");
    if (form.get("age")) searchForm.set("age", form.get("age"));
    if (form.get("gender")) searchForm.set("gender", form.get("gender"));
    if (form.get("region")) searchForm.set("region", form.get("region"));
    if (image) searchForm.set("image", image);
    return searchForm;
  }

  async function submit(event) {
    event.preventDefault();
    setProcessing(true);
    const form = new FormData(event.currentTarget);
    form.set("report_type", isMissing ? "missing" : "found");
    const searchForm = !isMissing ? searchFormFromIntake(form) : null;
    try {
      const result = await apiFetch("/cases", { method: "POST", body: form });
      if (isMissing) {
        setNotice(`Submitted ${result.case_id}. Embedding stored once at intake and added to the searchable missing-record set.`);
      } else {
        setNotice(`Submitted ${result.case_id}. Processing found photo and running ranked candidate search...`);
        const search = await apiFetch("/search", { method: "POST", body: searchForm });
        setCandidates?.(search.candidates);
        setCoverage?.(search.coverage);
        setNotice(`Submitted ${result.case_id}. Search complete: ${search.coverage.returned_candidates} candidate records surfaced for reviewer triage.`);
        setView?.("search");
      }
      await refresh();
      event.currentTarget.reset();
    } catch (error) {
      setNotice(error.message);
    } finally {
      setProcessing(false);
    }
  }
  return (
    <section className="page intake">
      <p className="eyebrow">Public intake style</p>
      <h1>{isMissing ? "Report Missing Child" : "Report Found Child"}</h1>
      <div className="warning"><AlertTriangle size={18} /><p><b>Demo data only.</b><br />Use LFW/public benchmark or consented images. Never upload real missing-child case photos.</p></div>
      <form className="panel form" onSubmit={submit}>
        <label>Display name<input name="display_name" required placeholder={isMissing ? "Fictional case name" : "Unidentified child"} /></label>
        <label>Age<input name="age" required type="number" min="0" /></label>
        <label>Gender<select name="gender" required><option value="">Select...</option><option>Male</option><option>Female</option><option>Other / unknown</option></select></label>
        <label>Region<select name="region" required><option value="">Select...</option>{states.map((state) => <option key={state}>{state}</option>)}</select></label>
        <label className="wide">Location<input name="location" required placeholder="Station, shelter, locality, or landmark" /></label>
        <label className="wide">Notes<textarea name="notes" placeholder="Distinguishing features or context" /></label>
        <label className="upload-line"><Upload size={18} /> Upload demo photo<input required name="image" type="file" accept="image/*" /></label>
        <button className="primary" disabled={processing}>{processing ? "Processing image..." : isMissing ? "Submit and store embedding" : "Submit and search candidates"}</button>
      </form>
    </section>
  );
}

function AuditPage({ audit }) {
  return (
    <section className="page">
      <p className="eyebrow">Accountability</p>
      <h1>Audit Trail</h1>
      <div className="audit-table panel">
        <div className="audit-head"><span>Time</span><span>Reviewer</span><span>Action</span><span>Case</span><span>Candidate</span><span>Score</span><span>Detail</span></div>
        {audit.map((row) => <div className="audit-row" key={`${row.timestamp}-${row.action}-${row.candidate_case_id || row.case_id}`}><span>{new Date(row.timestamp).toLocaleString()}</span><span>{row.reviewer_id}</span><span>{row.action}</span><span>{row.case_id}</span><span>{row.candidate_case_id || "-"}</span><span>{row.similarity_score ?? "-"}</span><span>{row.detail}</span></div>)}
      </div>
    </section>
  );
}

createRoot(document.getElementById("root")).render(<App />);
