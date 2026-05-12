const $ = (id) => {
  const el = document.getElementById(id);
  if (!el) throw new Error(`Missing #${id}`);
  return el;
};

const statusEl = $("status");
const errorEl = $("error");
const tbody = $("tbody");
const qInput = $("q");
const typeRatingSel = $("typeRating");
const routeSel = $("route");
const pageSizeSel = $("pageSize");
const prevBtn = $("prev");
const nextBtn = $("next");
const pageInfo = $("pageInfo");

let db = null;

let page = 1;
let totalMatching = 0;

function showError(message) {
  errorEl.textContent = message;
  errorEl.classList.remove("hidden");
}

function clearError() {
  errorEl.textContent = "";
  errorEl.classList.add("hidden");
}

function escapeLike(s) {
  return s.replace(/\\/g, "\\\\").replace(/%/g, "\\%").replace(/_/g, "\\_");
}

function populateDistincts() {
  if (!db) return;

  const types = db.exec(
    "SELECT DISTINCT type_rating FROM sponsors WHERE type_rating != '' ORDER BY type_rating COLLATE NOCASE"
  );
  const routes = db.exec(
    "SELECT DISTINCT route FROM sponsors WHERE route != '' ORDER BY route COLLATE NOCASE"
  );

  const typeRows = types[0]?.values ?? [];
  const routeRows = routes[0]?.values ?? [];

  for (const [t] of typeRows) {
    const opt = document.createElement("option");
    opt.value = String(t);
    opt.textContent = String(t);
    typeRatingSel.appendChild(opt);
  }
  for (const [r] of routeRows) {
    const opt = document.createElement("option");
    opt.value = String(r);
    opt.textContent = String(r);
    routeSel.appendChild(opt);
  }
}

function buildWhere() {
  const parts = [];
  const params = [];

  const raw = qInput.value.trim();
  if (raw) {
    const term = `%${escapeLike(raw)}%`;
    parts.push(
      "(organisation_name LIKE ? ESCAPE '\\' OR town_city LIKE ? ESCAPE '\\' OR county LIKE ? ESCAPE '\\')"
    );
    params.push(term, term, term);
  }

  const tr = typeRatingSel.value;
  if (tr) {
    parts.push("type_rating = ?");
    params.push(tr);
  }

  const rt = routeSel.value;
  if (rt) {
    parts.push("route = ?");
    params.push(rt);
  }

  const whereSql = parts.length ? `WHERE ${parts.join(" AND ")}` : "";
  return { whereSql, params };
}

function countRows() {
  if (!db) return 0;
  const { whereSql, params } = buildWhere();
  const stmt = db.prepare(`SELECT COUNT(*) AS c FROM sponsors ${whereSql}`);
  stmt.bind(params);
  stmt.step();
  const c = stmt.getAsObject().c;
  stmt.free();
  return Number(c);
}

function appendCell(tr, text) {
  const td = document.createElement("td");
  td.textContent = text;
  tr.appendChild(td);
}

function renderPage() {
  if (!db) return;

  const pageSize = Number(pageSizeSel.value) || 50;
  const { whereSql, params } = buildWhere();

  totalMatching = countRows();
  const totalPages = Math.max(1, Math.ceil(totalMatching / pageSize));
  if (page > totalPages) page = totalPages;

  const offset = (page - 1) * pageSize;

  const stmt = db.prepare(
    `SELECT id, organisation_name, town_city, county, type_rating, route
     FROM sponsors ${whereSql}
     ORDER BY organisation_name COLLATE NOCASE
     LIMIT ? OFFSET ?`
  );
  stmt.bind([...params, pageSize, offset]);

  tbody.replaceChildren();
  let rowNum = offset;
  while (stmt.step()) {
    rowNum += 1;
    const r = stmt.getAsObject();
    const tr = document.createElement("tr");
    appendCell(tr, String(rowNum));
    appendCell(tr, String(r.organisation_name ?? ""));
    appendCell(tr, String(r.town_city ?? ""));
    appendCell(tr, String(r.county ?? ""));
    appendCell(tr, String(r.type_rating ?? ""));
    appendCell(tr, String(r.route ?? ""));
    tbody.appendChild(tr);
  }
  stmt.free();

  pageInfo.textContent =
    totalMatching === 0
      ? "No rows match."
      : `Page ${page} of ${totalPages} · ${totalMatching.toLocaleString()} row(s)`;

  prevBtn.disabled = page <= 1;
  nextBtn.disabled = page >= totalPages;
}

async function init() {
  clearError();

  const initSqlJs = window.initSqlJs;
  if (typeof initSqlJs !== "function") {
    showError("sql.js failed to load. Check your network connection.");
    statusEl.textContent = "";
    return;
  }

  statusEl.textContent = "Loading sql.js…";
  const SQL = await initSqlJs({
    locateFile: (file) => `https://cdn.jsdelivr.net/npm/sql.js@1.10.3/dist/${file}`,
  });

  statusEl.textContent = "Loading sponsors.db (about 20 MB)…";
  let buf;
  try {
    const res = await fetch("sponsors.db");
    if (!res.ok) {
      throw new Error(`HTTP ${res.status} loading sponsors.db`);
    }
    buf = await res.arrayBuffer();
  } catch (e) {
    const msg =
      e instanceof TypeError
        ? "Could not load sponsors.db. Open this site via a local HTTP server from the public folder (file:// blocks fetch)."
        : String(e instanceof Error ? e.message : e);
    showError(msg);
    statusEl.textContent = "";
    return;
  }

  statusEl.textContent = "Opening database…";
  try {
    db = new SQL.Database(new Uint8Array(buf));
  } catch (e) {
    showError(String(e instanceof Error ? e.message : e));
    statusEl.textContent = "";
    return;
  }

  populateDistincts();
  page = 1;
  renderPage();
  statusEl.textContent = "";
}

function debounce(fn, ms) {
  let t = 0;
  return () => {
    window.clearTimeout(t);
    t = window.setTimeout(fn, ms);
  };
}

const scheduleRender = debounce(() => {
  page = 1;
  renderPage();
}, 200);

qInput.addEventListener("input", scheduleRender);
typeRatingSel.addEventListener("change", () => {
  page = 1;
  renderPage();
});
routeSel.addEventListener("change", () => {
  page = 1;
  renderPage();
});
pageSizeSel.addEventListener("change", () => {
  page = 1;
  renderPage();
});

prevBtn.addEventListener("click", () => {
  page = Math.max(1, page - 1);
  renderPage();
});
nextBtn.addEventListener("click", () => {
  page += 1;
  renderPage();
});

init();
