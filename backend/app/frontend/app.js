const apiBase = "/api/v1";

const pageTitles = {
  overview: ["Overview", "Pipeline overview"],
  actors: ["Actor Runs", "Run backend actors"],
  raw: ["Raw Data", "Raw JSON and table"],
  processed: ["Processed Data", "Processed JSON and table"],
  files: ["Files", "Saved data files"],
  backend: ["Backend", "Service status"],
};

const platformPlaceholders = {
  tiktok: "Paste TikTok video URLs, one per line\nhttps://www.tiktok.com/@user/video/1234567890",
  instagram: "Paste Instagram usernames, one per line\nnike\nadidas",
  x: "Paste X/Twitter search terms, one per line\nbrand name\nfrom:username",
  facebook: "Paste Facebook page URLs, one per line\nhttps://www.facebook.com/page",
  youtube: "Paste YouTube channel or video URLs, one per line\nhttps://www.youtube.com/@channel",
  linkedin: "Paste LinkedIn profile URLs, one per line\nhttps://www.linkedin.com/in/profile",
};

const els = {
  loginView: document.querySelector("#loginView"),
  appView: document.querySelector("#appView"),
  loginForm: document.querySelector("#loginForm"),
  loginButton: document.querySelector("#loginButton"),
  loginError: document.querySelector("#loginError"),
  emailInput: document.querySelector("#emailInput"),
  passwordInput: document.querySelector("#passwordInput"),
  logoutButton: document.querySelector("#logoutButton"),
  refreshButton: document.querySelector("#refreshButton"),
  platformInput: document.querySelector("#platformInput"),
  pageEyebrow: document.querySelector("#pageEyebrow"),
  pageTitle: document.querySelector("#pageTitle"),
  statusMessage: document.querySelector("#statusMessage"),
  rawCount: document.querySelector("#rawCount"),
  processedCount: document.querySelector("#processedCount"),
  rawFileCount: document.querySelector("#rawFileCount"),
  processedFileCount: document.querySelector("#processedFileCount"),
  rawFile: document.querySelector("#rawFile"),
  processedFile: document.querySelector("#processedFile"),
  scrapeForm: document.querySelector("#scrapeForm"),
  scrapeButton: document.querySelector("#scrapeButton"),
  targetInput: document.querySelector("#targetInput"),
  enrichInput: document.querySelector("#enrichInput"),
  actorHelp: document.querySelector("#actorHelp"),
  runResult: document.querySelector("#runResult"),
  rawMeta: document.querySelector("#rawMeta"),
  processedMeta: document.querySelector("#processedMeta"),
  rawJson: document.querySelector("#rawJson"),
  processedJson: document.querySelector("#processedJson"),
  rawTable: document.querySelector("#rawTable"),
  processedTable: document.querySelector("#processedTable"),
  filesTable: document.querySelector("#filesTable"),
  backendCards: document.querySelector("#backendCards"),
  actorConfigTable: document.querySelector("#actorConfigTable"),
};

const state = {
  activePage: "overview",
  raw: [],
  processed: [],
  files: [],
  backend: null,
};

function setStatus(message, type = "") {
  els.statusMessage.textContent = message;
  els.statusMessage.className = `status-message ${type}`.trim();
}

function showApp() {
  els.loginView.hidden = true;
  els.appView.hidden = false;
  navigate("overview");
}

function showLogin() {
  els.loginView.hidden = false;
  els.appView.hidden = true;
}

function doLogin(event) {
  event.preventDefault();
  if (!els.emailInput.value.trim() || !els.passwordInput.value.trim()) {
    els.loginError.textContent = "Enter a username and password.";
    els.loginError.hidden = false;
    return;
  }

  els.loginError.hidden = true;
  sessionStorage.setItem("sociaaltool_logged_in", "true");
  showApp();
}

function updatePageTitle(page) {
  const [eyebrow, title] = pageTitles[page] || pageTitles.overview;
  els.pageEyebrow.textContent = eyebrow;
  els.pageTitle.textContent = title;
}

function navigate(page) {
  state.activePage = page;
  updatePageTitle(page);

  document.querySelectorAll(".page").forEach((section) => {
    section.classList.toggle("active-page", section.id === `${page}Page`);
  });
  document.querySelectorAll(".main-nav button").forEach((button) => {
    button.classList.toggle("active", button.dataset.page === page);
  });

  refreshCurrentPage();
}

function updatePlatformHelp() {
  const platform = els.platformInput.value;
  els.targetInput.placeholder = platformPlaceholders[platform] || "Paste URLs or targets, one per line";
  els.actorHelp.textContent = platformPlaceholders[platform].split("\n")[0];
}

async function fetchJson(url, options) {
  const response = await fetch(url, options);
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

function formatJson(data) {
  return JSON.stringify(data ?? [], null, 2);
}

function cellValue(value) {
  if (value === null || value === undefined) return "";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
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
  ];
  const keys = [...new Set(rows.flatMap((row) => Object.keys(row)))];
  return [...preferred.filter((key) => keys.includes(key)), ...keys.filter((key) => !preferred.includes(key))].slice(0, 12);
}

function renderTable(container, rows) {
  const data = normalizeRows(rows);
  if (!data.length) {
    container.innerHTML = '<div class="empty-state">No rows to show yet.</div>';
    return;
  }

  const columns = columnsFor(data);
  const header = columns.map((column) => `<th>${column}</th>`).join("");
  const body = data
    .map((row) => `<tr>${columns.map((column) => `<td>${cellValue(row[column])}</td>`).join("")}</tr>`)
    .join("");

  container.innerHTML = `<table><thead><tr>${header}</tr></thead><tbody>${body}</tbody></table>`;
}

function clearDataset(kind, message) {
  if (kind === "raw") {
    state.raw = [];
    els.rawCount.textContent = "0";
    els.rawFile.textContent = "None";
    els.rawMeta.textContent = message;
    els.rawJson.textContent = "[]";
    renderTable(els.rawTable, []);
    return;
  }

  state.processed = [];
  els.processedCount.textContent = "0";
  els.processedFile.textContent = "None";
  els.processedMeta.textContent = message;
  els.processedJson.textContent = "[]";
  renderTable(els.processedTable, []);
}

function renderDataset(kind, response) {
  const data = response.data ?? [];
  const rows = normalizeRows(data);

  if (kind === "raw") {
    state.raw = rows;
    els.rawCount.textContent = rows.length;
    els.rawFile.textContent = response.source_file || "None";
    els.rawMeta.textContent = `${response.total_records ?? rows.length} records from ${response.source_file || "latest file"}`;
    els.rawJson.textContent = formatJson(data);
    renderTable(els.rawTable, rows);
    return;
  }

  state.processed = rows;
  els.processedCount.textContent = rows.length;
  els.processedFile.textContent = response.source_file || "None";
  els.processedMeta.textContent = `${response.total_records ?? rows.length} records from ${response.source_file || "latest file"}`;
  els.processedJson.textContent = formatJson(data);
  renderTable(els.processedTable, rows);
}

async function loadLatestData() {
  const platform = els.platformInput.value;
  const [rawResult, processedResult] = await Promise.allSettled([
    fetchJson(`${apiBase}/files/latest/${platform}?kind=raw`),
    fetchJson(`${apiBase}/files/latest/${platform}?kind=processed`),
  ]);

  rawResult.status === "fulfilled"
    ? renderDataset("raw", rawResult.value)
    : clearDataset("raw", rawResult.reason.message);

  processedResult.status === "fulfilled"
    ? renderDataset("processed", processedResult.value)
    : clearDataset("processed", processedResult.reason.message);
}

async function loadFileList() {
  const platform = els.platformInput.value;
  const response = await fetchJson(`${apiBase}/files/list/${platform}?kind=all`);
  state.files = response.files || [];
  els.rawFileCount.textContent = state.files.filter((file) => file.kind === "raw").length;
  els.processedFileCount.textContent = state.files.filter((file) => file.kind === "processed").length;
  renderTable(els.filesTable, state.files);
}

function renderBackendStatus(status) {
  const cards = [
    ["Project", status.project_name],
    ["Apify", status.apify_configured ? "Configured" : "Missing token"],
    ["Anthropic", status.anthropic_configured ? "Configured" : "Missing key"],
    ["Data directory", status.data_dir],
  ];

  els.backendCards.innerHTML = cards
    .map(([label, value]) => `<div><span>${label}</span><strong>${value}</strong></div>`)
    .join("");

  const actorRows = Object.entries(status.actor_ids || {}).map(([platform, actor_id]) => ({
    platform,
    actor_id,
    raw_files: status.file_counts?.[platform]?.raw_files ?? 0,
    processed_files: status.file_counts?.[platform]?.processed_files ?? 0,
  }));
  renderTable(els.actorConfigTable, actorRows);
}

async function loadBackendStatus() {
  state.backend = await fetchJson(`${apiBase}/admin/status`);
  renderBackendStatus(state.backend);
}

async function refreshCurrentPage() {
  setStatus("Loading...");
  updatePlatformHelp();

  try {
    if (["overview", "raw", "processed"].includes(state.activePage)) {
      await loadLatestData();
      await loadFileList();
    }
    if (state.activePage === "files") {
      await loadFileList();
    }
    if (state.activePage === "backend") {
      await loadBackendStatus();
    }
    setStatus("Ready");
  } catch (error) {
    setStatus(error.message, "error");
  }
}

async function runActor(event) {
  event.preventDefault();
  const targets = els.targetInput.value
    .split(/\r?\n/)
    .map((target) => target.trim())
    .filter(Boolean);

  if (!targets.length) {
    setStatus("Paste at least one target.", "error");
    return;
  }

  els.scrapeButton.disabled = true;
  setStatus("Running actor. This can take a little while...");

  try {
    const result = await fetchJson(`${apiBase}/ingestion/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        platform: els.platformInput.value,
        targets,
        enrich: els.enrichInput.checked,
      }),
    });

    els.runResult.textContent = formatJson(result);
    setStatus(result.warning || result.message || "Actor finished.", result.warning ? "warning" : "");
    await loadLatestData();
    await loadFileList();
  } catch (error) {
    setStatus(error.message, "error");
    els.runResult.textContent = formatJson({ error: error.message });
  } finally {
    els.scrapeButton.disabled = false;
  }
}

function switchTab(event) {
  const button = event.target.closest("button[data-tab]");
  if (!button) return;

  const viewer = button.parentElement.dataset.viewer;
  const tab = button.dataset.tab;
  button.parentElement.querySelectorAll("button").forEach((item) => item.classList.remove("active"));
  button.classList.add("active");
  document.querySelector(`#${viewer}Json`).hidden = tab !== "json";
  document.querySelector(`#${viewer}Table`).hidden = tab !== "table";
}

els.loginForm.addEventListener("submit", doLogin);
els.loginButton.addEventListener("click", doLogin);
els.logoutButton.addEventListener("click", () => {
  sessionStorage.removeItem("sociaaltool_logged_in");
  showLogin();
});
els.refreshButton.addEventListener("click", refreshCurrentPage);
els.platformInput.addEventListener("change", refreshCurrentPage);
els.scrapeForm.addEventListener("submit", runActor);
document.querySelector(".main-nav").addEventListener("click", (event) => {
  const button = event.target.closest("button[data-page]");
  if (button) navigate(button.dataset.page);
});
document.querySelectorAll(".tabs").forEach((tabs) => tabs.addEventListener("click", switchTab));

updatePlatformHelp();

if (sessionStorage.getItem("sociaaltool_logged_in") === "true") {
  showApp();
} else {
  showLogin();
}
