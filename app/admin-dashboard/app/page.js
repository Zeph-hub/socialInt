"use client";

import {
  Activity,
  BarChart3,
  CheckCircle2,
  Database,
  Download,
  FileJson,
  Files,
  LayoutDashboard,
  LogOut,
  Play,
  RefreshCcw,
  Search,
  ServerCog,
  ShieldCheck,
  Sparkles,
  Table2,
  XCircle,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

const API_BASE = "/api/v1";
const platforms = ["tiktok", "instagram", "x", "facebook", "youtube", "linkedin"];

const platformLabels = {
  tiktok: "TikTok",
  instagram: "Instagram",
  x: "X / Twitter",
  facebook: "Facebook",
  youtube: "YouTube",
  linkedin: "LinkedIn",
};

const navItems = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "actors", label: "Run Actors", icon: Play },
  { id: "data", label: "Data Explorer", icon: Database },
  { id: "reports", label: "Reports", icon: BarChart3 },
  { id: "files", label: "Files", icon: Files },
  { id: "backend", label: "Backend", icon: ServerCog },
];

const placeholders = {
  tiktok: "https://www.tiktok.com/@user/video/1234567890",
  instagram: "nike\nadidas",
  x: "brand name\nfrom:username",
  facebook: "https://www.facebook.com/page",
  youtube: "https://www.youtube.com/@channel",
  linkedin: "https://www.linkedin.com/in/profile",
};

function formatNumber(value) {
  return new Intl.NumberFormat().format(Number(value || 0));
}

function formatDate(value) {
  if (!value) return "Unknown";
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value * 1000));
}

async function fetchJson(path, options) {
  const response = await fetch(`${API_BASE}${path}`, options);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "Request failed");
  }
  return payload;
}

function normalizeRows(data) {
  if (Array.isArray(data)) return data;
  if (data && typeof data === "object") return [data];
  return [];
}

function columnsFor(rows) {
  const preferred = [
    "text",
    "uniqueId",
    "videoWebUrl",
    "createTimeISO",
    "diggCount",
    "replyCommentTotal",
    "ai_language",
    "ai_sentiment",
    "ai_category",
    "kind",
    "name",
    "size_bytes",
    "modified_at",
  ];
  const keys = [...new Set(rows.flatMap((row) => Object.keys(row || {})))];
  return [...preferred.filter((key) => keys.includes(key)), ...keys.filter((key) => !preferred.includes(key))].slice(0, 12);
}

function cellValue(value) {
  if (value === null || value === undefined) return "";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function toCsv(rows) {
  const columns = columnsFor(rows);
  const escape = (value) => `"${cellValue(value).replaceAll('"', '""')}"`;
  return [columns.join(","), ...rows.map((row) => columns.map((column) => escape(row[column])).join(","))].join("\n");
}

function downloadCsv(filename, rows) {
  const blob = new Blob([toCsv(rows)], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function buildDistribution(rows, key) {
  return rows.reduce((accumulator, row) => {
    const value = String(row?.[key] || "unknown").trim() || "unknown";
    accumulator[value] = (accumulator[value] || 0) + 1;
    return accumulator;
  }, {});
}

function DataTable({ rows, compact = false }) {
  const data = normalizeRows(rows);
  const columns = useMemo(() => columnsFor(data), [data]);

  if (!data.length) {
    return <div className="empty-state">No rows to show yet.</div>;
  }

  return (
    <div className={compact ? "table-shell compact" : "table-shell"}>
      <table>
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column}>{column}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, index) => (
            <tr key={row.cid || row.id || row.name || index}>
              {columns.map((column) => (
                <td key={column}>{cellValue(row[column])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Distribution({ title, data }) {
  const entries = Object.entries(data || {}).sort((a, b) => b[1] - a[1]);
  const max = Math.max(...entries.map(([, value]) => value), 1);

  return (
    <article className="panel">
      <div className="panel-title">
        <h3>{title}</h3>
      </div>
      <div className="bar-list">
        {entries.length ? (
          entries.map(([label, value]) => (
            <div className="bar-row" key={label}>
              <div>
                <span>{label || "unknown"}</span>
                <strong>{formatNumber(value)}</strong>
              </div>
              <meter min="0" max={max} value={value} />
            </div>
          ))
        ) : (
          <div className="empty-state">No report data available.</div>
        )}
      </div>
    </article>
  );
}

function LoginScreen({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  function submit(event) {
    event.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError("Enter a username and password.");
      return;
    }
    sessionStorage.setItem("sociaaltool_logged_in", "true");
    onLogin();
  }

  return (
    <main className="login-page">
      <section className="login-copy">
        <p className="eyebrow">Social Intelligence Platform</p>
        <h1>Admin dashboard</h1>
        <p>Run collection jobs, inspect pipeline output, and review reporting signals from one workspace.</p>
      </section>
      <form className="login-card" onSubmit={submit}>
        <div className="login-mark">
          <ShieldCheck size={24} />
        </div>
        <h2>Sign in</h2>
        <label>
          Username or email
          <input value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" placeholder="admin" />
        </label>
        <label>
          Password
          <input value={password} onChange={(event) => setPassword(event.target.value)} type="password" autoComplete="current-password" placeholder="admin123" />
        </label>
        <button type="submit">Log in</button>
        <p className="helper-text">Username: admin and password: admin123.</p>
        {error ? <p className="error-text">{error}</p> : null}
      </form>
    </main>
  );
}

export default function AdminDashboard() {
  const [loggedIn, setLoggedIn] = useState(false);
  const [activePage, setActivePage] = useState("overview");
  const [platform, setPlatform] = useState("tiktok");
  const [status, setStatus] = useState("Ready");
  const [statusType, setStatusType] = useState("");
  const [backend, setBackend] = useState(null);
  const [rawLatest, setRawLatest] = useState(null);
  const [processedLatest, setProcessedLatest] = useState(null);
  const [files, setFiles] = useState([]);
  const [reportSummary, setReportSummary] = useState(null);
  const [reportRows, setReportRows] = useState([]);
  const [dataRows, setDataRows] = useState([]);
  const [dataKind, setDataKind] = useState("processed");
  const [dataMode, setDataMode] = useState("table");
  const [targets, setTargets] = useState("");
  const [enrich, setEnrich] = useState(true);
  const [debug, setDebug] = useState(false);
  const [runResult, setRunResult] = useState(null);
  const [filters, setFilters] = useState({ sentiment: "", language: "", category: "" });
  const [running, setRunning] = useState(false);

  useEffect(() => {
    setLoggedIn(sessionStorage.getItem("sociaaltool_logged_in") === "true");
  }, []);

  async function refreshAll() {
    setStatus("Loading dashboard data...");
    setStatusType("");
    const [rawResult, processedResult, fileResult, backendResult, summaryResult, reportResult] = await Promise.allSettled([
      fetchJson(`/files/latest/${platform}?kind=raw`),
      fetchJson(`/files/latest/${platform}?kind=processed`),
      fetchJson(`/files/list/${platform}?kind=all`),
      fetchJson("/admin/status"),
      fetchJson(`/powerbi/summary/${platform}`),
      fetchJson(`/powerbi/data/${platform}?limit=250&offset=0`),
    ]);

    setRawLatest(rawResult.status === "fulfilled" ? rawResult.value : null);
    setProcessedLatest(processedResult.status === "fulfilled" ? processedResult.value : null);
    setFiles(fileResult.status === "fulfilled" ? fileResult.value.files || [] : []);
    setBackend(backendResult.status === "fulfilled" ? backendResult.value : null);
    setReportSummary(summaryResult.status === "fulfilled" ? summaryResult.value : null);
    setReportRows(reportResult.status === "fulfilled" ? normalizeRows(reportResult.value.data) : []);

    const failures = [rawResult, processedResult, fileResult, backendResult, summaryResult, reportResult].filter((result) => result.status === "rejected");
    if (backendResult.status === "rejected") {
      setStatus(backendResult.reason.message);
      setStatusType("error");
    } else if (failures.length) {
      setStatus(`${platformLabels[platform]} loaded with ${failures.length} unavailable section${failures.length === 1 ? "" : "s"}.`);
      setStatusType("warning");
    } else {
      setStatus("Ready");
      setStatusType("");
    }
  }

  useEffect(() => {
    if (loggedIn) refreshAll();
  }, [loggedIn, platform]);

  useEffect(() => {
    const source = dataKind === "raw" ? rawLatest?.data : processedLatest?.data;
    setDataRows(normalizeRows(source));
  }, [rawLatest, processedLatest, dataKind]);

  async function runActor(event) {
    event.preventDefault();
    const targetList = targets
      .split(/\r?\n/)
      .map((target) => target.trim())
      .filter(Boolean);

    if (!targetList.length) {
      setStatus("Paste at least one target.");
      setStatusType("error");
      return;
    }

    setRunning(true);
    setStatus("Running actor. This can take a little while...");
    setStatusType("");

    try {
      const result = await fetchJson("/ingestion/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ platform, targets: targetList, enrich, debug }),
      });
      setRunResult(result);
      setStatus(result.warning || result.message || "Actor finished.");
      setStatusType(result.warning ? "warning" : "");
      await refreshAll();
    } catch (error) {
      setRunResult({ error: error.message });
      setStatus(error.message);
      setStatusType("error");
    } finally {
      setRunning(false);
    }
  }

  async function loadFilteredReport() {
    const params = new URLSearchParams({ limit: "500", offset: "0" });
    Object.entries(filters).forEach(([key, value]) => {
      if (value.trim()) params.set(key, value.trim());
    });

    setStatus("Loading filtered report...");
    try {
      const result = await fetchJson(`/powerbi/data/${platform}?${params.toString()}`);
      setReportRows(normalizeRows(result.data));
      setStatus(`Loaded ${formatNumber(result.total_records)} report records.`);
      setStatusType("");
    } catch (error) {
      setStatus(error.message);
      setStatusType("error");
    }
  }

  const counts = backend?.file_counts?.[platform] || {};
  const rawRows = normalizeRows(rawLatest?.data);
  const processedRows = normalizeRows(processedLatest?.data);
  const totalEngagement = reportRows.reduce((sum, row) => sum + Number(row.diggCount || 0) + Number(row.replyCommentTotal || 0), 0);
  const hasReportFilters = Object.values(filters).some((value) => value.trim());
  const activeReportSummary =
    hasReportFilters && reportRows.length
      ? {
          total_records: reportRows.length,
          sentiment_distribution: buildDistribution(reportRows, "ai_sentiment"),
          category_distribution: buildDistribution(reportRows, "ai_category"),
          language_distribution: buildDistribution(reportRows, "ai_language"),
        }
      : reportSummary;

  if (!loggedIn) {
    return <LoginScreen onLogin={() => setLoggedIn(true)} />;
  }

  return (
    <main className="admin-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">
            <Activity size={24} />
          </div>
          <div>
            <p className="eyebrow">SociaalTool</p>
            <h1>Admin</h1>
          </div>
        </div>

        <nav className="nav-list" aria-label="Dashboard pages">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button className={activePage === item.id ? "active" : ""} type="button" key={item.id} onClick={() => setActivePage(item.id)}>
                <Icon size={18} />
                {item.label}
              </button>
            );
          })}
        </nav>

        <button
          className="ghost-button logout"
          type="button"
          onClick={() => {
            sessionStorage.removeItem("sociaaltool_logged_in");
            setLoggedIn(false);
          }}
        >
          <LogOut size={18} />
          Log out
        </button>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">{platformLabels[platform]}</p>
            <h2>{navItems.find((item) => item.id === activePage)?.label}</h2>
          </div>
          <div className="topbar-actions">
            <select value={platform} onChange={(event) => setPlatform(event.target.value)} aria-label="Platform">
              {platforms.map((item) => (
                <option key={item} value={item}>
                  {platformLabels[item]}
                </option>
              ))}
            </select>
            <button className="ghost-button" type="button" onClick={refreshAll}>
              <RefreshCcw size={17} />
              Refresh
            </button>
          </div>
        </header>

        <div className={`status-line ${statusType}`}>{status}</div>

        {activePage === "overview" ? (
          <section className="page-stack">
            <div className="metric-grid">
              <article className="metric-card accent-teal">
                <span>Raw records</span>
                <strong>{formatNumber(rawLatest?.total_records || rawRows.length)}</strong>
              </article>
              <article className="metric-card accent-indigo">
                <span>Processed records</span>
                <strong>{formatNumber(processedLatest?.total_records || processedRows.length)}</strong>
              </article>
              <article className="metric-card accent-amber">
                <span>Raw files</span>
                <strong>{formatNumber(counts.raw_files || files.filter((file) => file.kind === "raw").length)}</strong>
              </article>
              <article className="metric-card accent-rose">
                <span>Processed files</span>
                <strong>{formatNumber(counts.processed_files || files.filter((file) => file.kind === "processed").length)}</strong>
              </article>
            </div>

            <div className="split-grid">
              <article className="panel">
                <div className="panel-title">
                  <h3>Latest raw file</h3>
                  <FileJson size={18} />
                </div>
                <p className="large-value">{rawLatest?.source_file || "No raw data found"}</p>
              </article>
              <article className="panel">
                <div className="panel-title">
                  <h3>Latest processed file</h3>
                  <Sparkles size={18} />
                </div>
                <p className="large-value">{processedLatest?.source_file || "No processed data found"}</p>
              </article>
            </div>
          </section>
        ) : null}

        {activePage === "actors" ? (
          <section className="page-stack">
            <article className="panel">
              <div className="panel-title">
                <div>
                  <h3>Run Apify actor</h3>
                  <p>Paste one target per line for {platformLabels[platform]}.</p>
                </div>
                <Play size={18} />
              </div>
              <form className="actor-form" onSubmit={runActor}>
                <label>
                  Targets
                  <textarea value={targets} onChange={(event) => setTargets(event.target.value)} placeholder={placeholders[platform]} />
                </label>
                <div className="control-row">
                  <label className="check-control">
                    <input type="checkbox" checked={enrich} onChange={(event) => setEnrich(event.target.checked)} />
                    Run AI enrichment
                  </label>
                  <label className="check-control">
                    <input type="checkbox" checked={debug} onChange={(event) => setDebug(event.target.checked)} />
                    Debug raw only
                  </label>
                  <button type="submit" disabled={running}>
                    <Play size={17} />
                    {running ? "Running" : "Run actor"}
                  </button>
                </div>
              </form>
            </article>

            <article className="panel">
              <div className="panel-title">
                <h3>Recent run result</h3>
              </div>
              <pre className="json-box">{JSON.stringify(runResult || {}, null, 2)}</pre>
            </article>
          </section>
        ) : null}

        {activePage === "data" ? (
          <section className="page-stack">
            <article className="panel">
              <div className="tool-row">
                <div className="segmented">
                  <button className={dataKind === "processed" ? "active" : ""} type="button" onClick={() => setDataKind("processed")}>
                    Processed
                  </button>
                  <button className={dataKind === "raw" ? "active" : ""} type="button" onClick={() => setDataKind("raw")}>
                    Raw
                  </button>
                </div>
                <div className="segmented">
                  <button className={dataMode === "table" ? "active" : ""} type="button" onClick={() => setDataMode("table")}>
                    <Table2 size={16} />
                    Table
                  </button>
                  <button className={dataMode === "json" ? "active" : ""} type="button" onClick={() => setDataMode("json")}>
                    <FileJson size={16} />
                    JSON
                  </button>
                </div>
              </div>
              <p className="panel-note">
                {formatNumber(dataRows.length)} rows from {(dataKind === "raw" ? rawLatest?.source_file : processedLatest?.source_file) || "latest file"}
              </p>
            </article>
            {dataMode === "table" ? <DataTable rows={dataRows} /> : <pre className="json-box tall">{JSON.stringify(dataRows, null, 2)}</pre>}
          </section>
        ) : null}

        {activePage === "reports" ? (
          <section className="page-stack">
            <div className="metric-grid">
              <article className="metric-card accent-teal">
                <span>Report records</span>
                <strong>{formatNumber(activeReportSummary?.total_records || reportRows.length)}</strong>
              </article>
              <article className="metric-card accent-indigo">
                <span>Loaded sample</span>
                <strong>{formatNumber(reportRows.length)}</strong>
              </article>
              <article className="metric-card accent-amber">
                <span>Engagement</span>
                <strong>{formatNumber(totalEngagement)}</strong>
              </article>
              <article className="metric-card accent-rose">
                <span>Source</span>
                <strong>{platformLabels[platform]}</strong>
              </article>
            </div>

            <article className="panel">
              <div className="report-filter-grid">
                <label>
                  Sentiment
                  <input value={filters.sentiment} onChange={(event) => setFilters({ ...filters, sentiment: event.target.value })} placeholder="positive" />
                </label>
                <label>
                  Language
                  <input value={filters.language} onChange={(event) => setFilters({ ...filters, language: event.target.value })} placeholder="english" />
                </label>
                <label>
                  Category
                  <input value={filters.category} onChange={(event) => setFilters({ ...filters, category: event.target.value })} placeholder="politics" />
                </label>
                <button type="button" onClick={loadFilteredReport}>
                  <Search size={17} />
                  Apply
                </button>
                <button className="ghost-button" type="button" onClick={() => downloadCsv(`${platform}-report.csv`, reportRows)}>
                  <Download size={17} />
                  CSV
                </button>
              </div>
            </article>

            <div className="three-grid">
              <Distribution title="Sentiment" data={activeReportSummary?.sentiment_distribution} />
              <Distribution title="Categories" data={activeReportSummary?.category_distribution} />
              <Distribution title="Languages" data={activeReportSummary?.language_distribution} />
            </div>

            <DataTable rows={reportRows} />
          </section>
        ) : null}

        {activePage === "files" ? (
          <section className="page-stack">
            <article className="panel">
              <div className="panel-title">
                <h3>Saved data files</h3>
                <Files size={18} />
              </div>
              <DataTable
                compact
                rows={files.map((file) => ({
                  ...file,
                  modified_at: formatDate(file.modified_at),
                }))}
              />
            </article>
          </section>
        ) : null}

        {activePage === "backend" ? (
          <section className="page-stack">
            <div className="split-grid">
              <article className="panel">
                <div className="panel-title">
                  <h3>Service status</h3>
                  <ServerCog size={18} />
                </div>
                <div className="status-grid">
                  <div>
                    <span>Project</span>
                    <strong>{backend?.project_name || "Unknown"}</strong>
                  </div>
                  <div>
                    <span>Apify</span>
                    <strong className={backend?.apify_configured ? "ok" : "bad"}>
                      {backend?.apify_configured ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
                      {backend?.apify_configured ? "Configured" : "Missing token"}
                    </strong>
                  </div>
                  <div>
                    <span>Anthropic</span>
                    <strong className={backend?.anthropic_configured ? "ok" : "bad"}>
                      {backend?.anthropic_configured ? <CheckCircle2 size={16} /> : <XCircle size={16} />}
                      {backend?.anthropic_configured ? "Configured" : "Missing key"}
                    </strong>
                  </div>
                  <div>
                    <span>Data directory</span>
                    <strong>{backend?.data_dir || "Unknown"}</strong>
                  </div>
                </div>
              </article>
              <article className="panel">
                <div className="panel-title">
                  <h3>Actor configuration</h3>
                </div>
                <DataTable
                  compact
                  rows={Object.entries(backend?.actor_ids || {}).map(([actorPlatform, actorId]) => ({
                    platform: actorPlatform,
                    actor_id: actorId,
                    raw_files: backend?.file_counts?.[actorPlatform]?.raw_files || 0,
                    processed_files: backend?.file_counts?.[actorPlatform]?.processed_files || 0,
                  }))}
                />
              </article>
            </div>
          </section>
        ) : null}
      </section>
    </main>
  );
}
