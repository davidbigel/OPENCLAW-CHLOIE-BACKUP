const state = {
  currentQuestionId: null,
  currentQuestion: null,
  currentSources: null,
  currentRequestId: null,
  askController: null,
  statusBaseText: "מוכן לשאלה.",
  runtimeCounterTimer: null,
  runtimeCounterQuestionId: null,
  runtimeCounterStartedAtMs: null,
  runtimeCounterMaxSeconds: 600
};

const el = {
  form: document.getElementById("askForm"),
  input: document.getElementById("questionInput"),
  wiki: document.getElementById("sourceWiki"),
  obsidian: document.getElementById("sourceObsidian"),
  raw: document.getElementById("sourceRaw"),
  statusBar: document.getElementById("statusBar"),
  statusText: document.getElementById("statusText"),
  history: document.getElementById("historyList"),
  refreshHistory: document.getElementById("refreshHistory"),
  questionTitle: document.getElementById("questionTitle"),
  summary: document.getElementById("summaryAnswer"),
  footer: document.getElementById("sourcesFooter"),
  cancel: document.getElementById("cancelButton"),
  rerun: document.getElementById("rerunButton"),
  saveThread: document.getElementById("saveThreadButton"),
  dialog: document.getElementById("citationDialog"),
  citationBody: document.getElementById("citationBody")
};

function cookie(name) {
  const parts = document.cookie.split(";").map(function (part) { return part.trim(); });
  for (const part of parts) {
    if (part.startsWith(name + "=")) return decodeURIComponent(part.slice(name.length + 1));
  }
  return "";
}

function csrf() {
  return cookie("mc_csrf");
}

async function api(path, options) {
  const opts = options || {};
  const headers = Object.assign({"Accept": "application/json"}, opts.headers || {});
  if (opts.body && typeof opts.body !== "string") {
    headers["Content-Type"] = "application/json";
    headers["X-CSRF-Token"] = csrf();
    opts.body = JSON.stringify(opts.body);
  }
  const response = await fetch(path, Object.assign({}, opts, {headers: headers}));
  const data = await response.json();
  if (!response.ok) throw new Error(data.message || data.status || "request failed");
  return data;
}

function setStatus(text, running) {
  state.statusBaseText = text;
  el.statusBar.classList.toggle("running", Boolean(running));
  el.statusBar.classList.toggle("idle", !running);
  if (!running) stopRuntimeCounter();
  renderStatusText();
}

function renderStatusText() {
  let text = state.statusBaseText || "";
  if (state.runtimeCounterStartedAtMs !== null) {
    const elapsedSeconds = Math.max(0, Math.floor((Date.now() - state.runtimeCounterStartedAtMs) / 1000));
    text += " " + elapsedSeconds + "/" + state.runtimeCounterMaxSeconds + "s(max)";
  }
  el.statusText.textContent = text;
}

function startRuntimeCounter(questionId, startedAtMs) {
  const startedMs = Number.isFinite(startedAtMs) ? startedAtMs : Date.now();
  if (state.runtimeCounterQuestionId !== questionId) {
    state.runtimeCounterQuestionId = questionId;
    state.runtimeCounterStartedAtMs = startedMs;
  } else if (state.runtimeCounterStartedAtMs === null || startedMs < state.runtimeCounterStartedAtMs) {
    state.runtimeCounterStartedAtMs = startedMs;
  }
  if (!state.runtimeCounterTimer) {
    state.runtimeCounterTimer = window.setInterval(renderStatusText, 1000);
  }
  renderStatusText();
}

function stopRuntimeCounter() {
  if (state.runtimeCounterTimer) {
    window.clearInterval(state.runtimeCounterTimer);
    state.runtimeCounterTimer = null;
  }
  state.runtimeCounterQuestionId = null;
  state.runtimeCounterStartedAtMs = null;
  el.statusText.textContent = state.statusBaseText || "";
}

function runtimeStartedAtMs(payload) {
  const raw = (payload && (payload.started_at || payload.created_at)) || "";
  const startedAtMs = Date.parse(raw);
  return Number.isFinite(startedAtMs) ? startedAtMs : null;
}

function sourcesFromUi() {
  return {
    wikillm: el.wiki.checked,
    obsidian: el.obsidian.checked,
    raw: el.raw.checked
  };
}

function makeClientRequestId() {
  if (window.crypto && typeof window.crypto.randomUUID === "function") {
    return window.crypto.randomUUID();
  }
  return "mc-" + Date.now() + "-" + Math.random().toString(16).slice(2);
}

async function runQuestionRequest(path, question, sources) {
  state.currentQuestion = question;
  state.currentSources = sources;
  state.currentQuestionId = null;
  state.currentRequestId = makeClientRequestId();
  state.askController = new AbortController();
  stopRuntimeCounter();
  clearAnswer(question, sources);
  startRuntimeCounter(state.currentRequestId, Date.now());
  setStatus("סנורקל עובד, לא לדאוג, תשובה בדרך...", true);
  try {
    const result = await api(path, {
      method: "POST",
      body: {question: question, sources: sources, client_request_id: state.currentRequestId, mode: "deep_answer"},
      signal: state.askController.signal
    });
    if (result.status === "busy") {
      setStatus(result.message, false);
      return;
    }
    renderQuestion(result);
    await loadHistory();
  } catch (error) {
    if (error.name !== "AbortError") setStatus(error.message, false);
  } finally {
    state.currentRequestId = null;
    state.askController = null;
  }
}

el.form.addEventListener("submit", async function (event) {
  event.preventDefault();
  const question = el.input.value.trim();
  if (!question) return;
  await runQuestionRequest("/api/ask", question, sourcesFromUi());
});

el.input.addEventListener("keydown", function (event) {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    el.form.requestSubmit();
  }
});

el.refreshHistory.addEventListener("click", function () {
  loadHistory();
});

el.cancel.addEventListener("click", async function () {
  if (state.currentRequestId) {
    const requestId = state.currentRequestId;
    const controller = state.askController;
    state.currentRequestId = null;
    state.askController = null;
    if (controller) controller.abort();
    try {
      const result = await api("/api/asks/" + encodeURIComponent(requestId) + "/cancel", {method: "POST", body: {}});
      setStatus("השאלה בוטלה.", false);
      if (result.question_id) {
        state.currentQuestionId = result.question_id;
        await loadQuestion(result.question_id);
      }
      await loadHistory();
    } catch (error) {
      setStatus(error.message, false);
    }
    return;
  }
  if (!state.currentQuestionId) return;
  const result = await api("/api/questions/" + state.currentQuestionId + "/cancel", {method: "POST", body: {}});
  setStatus("השאלה בוטלה.", false);
  if (result.question_id) {
    await loadQuestion(result.question_id);
  }
  await loadHistory();
});

el.rerun.addEventListener("click", async function () {
  if (!state.currentQuestionId || !state.currentQuestion) return;
  await runQuestionRequest("/api/questions/" + state.currentQuestionId + "/rerun", state.currentQuestion, sourcesFromUi());
});

el.saveThread.addEventListener("click", async function () {
  if (!state.currentQuestionId) return;
  const result = await api("/api/questions/" + state.currentQuestionId + "/toggle-thread", {method: "POST", body: {}});
  el.saveThread.textContent = result.status === "saved" ? "בטל שמירת ת'רד" : "שמור ת'רד";
  await loadHistory();
});

async function loadQuestion(questionId) {
  const payload = await api("/api/questions/" + questionId);
  renderQuestion(payload);
  return payload;
}

async function loadHistory() {
  const data = await api("/api/questions");
  el.history.innerHTML = "";
  for (const item of data.questions || []) {
    const button = document.createElement("button");
    button.className = "history-item";
    button.innerHTML = "<strong>" + escapeHtml(item.question) + "</strong>"
      + "<span>" + escapeHtml(item.status) + " · " + escapeHtml(item.created_at || "") + "</span>"
      + sourceBadges(item)
      + (item.thread_id ? '<span class="thread-marker">research thread</span>' : "");
    button.addEventListener("click", function () {
      state.currentQuestionId = item.id;
      state.currentQuestion = item.question;
      loadQuestion(item.id);
    });
    el.history.appendChild(button);
  }
}

function sourceBadges(item) {
  const sources = [];
  if (item.selected_wikillm) sources.push("wiki");
  if (item.selected_obsidian) sources.push("obsidian");
  if (item.selected_raw) sources.push("raw");
  return '<span class="source-badges">' + sources.map(function (source) {
    return '<em>' + escapeHtml(source) + '</em>';
  }).join("") + '</span>';
}

function clearAnswer(question, sources) {
  el.questionTitle.textContent = question;
  el.summary.textContent = "ממתין לתשובה...";
  el.footer.textContent = "Sources Used: running";
  for (const source of ["wikillm", "obsidian", "raw"]) {
    const selected = sources && sources[source];
    document.getElementById(source + "Status").textContent = selected ? "queued" : "not_selected";
    document.getElementById(source + "Status").className = "source-status";
    document.getElementById(source + "Answer").textContent = selected ? "" : "not selected";
    document.getElementById(source + "Evidence").innerHTML = "";
  }
  el.cancel.disabled = false;
  el.rerun.disabled = true;
  el.saveThread.disabled = true;
}

function renderQuestion(payload) {
  if (!payload || !payload.question_id) return;
  state.currentQuestionId = payload.question_id;
  state.currentQuestion = payload.question || state.currentQuestion;
  el.questionTitle.textContent = payload.question || payload.question_id;
  el.summary.innerHTML = renderMarkdown(payload.summary_answer_markdown || payload.raw_response_text || "ממתין לתשובה...");
  el.footer.textContent = payload.sources_used_footer || "Sources Used: none";
  const running = ["queued", "running"].includes(payload.status);
  if (running) {
    startRuntimeCounter(payload.question_id, runtimeStartedAtMs(payload));
    setStatus("סנורקל עובד, לא לדאוג, תשובה בדרך...", true);
  } else {
    setStatus("סטטוס: " + payload.status, false);
  }
  el.cancel.disabled = !running && !state.currentRequestId;
  el.rerun.disabled = running || Boolean(state.currentRequestId);
  el.saveThread.disabled = running || Boolean(state.currentRequestId);
  el.saveThread.textContent = payload.thread_id ? "בטל שמירת ת'רד" : "שמור ת'רד";
  renderBoxes(payload.boxes || {});
}

function renderBoxes(boxes) {
  for (const source of ["wikillm", "obsidian", "raw"]) {
    const box = boxes[source] || {status: "not_selected", answer_markdown: "", evidence: []};
    const status = document.getElementById(source + "Status");
    status.textContent = box.status || "waiting";
    status.className = "source-status " + (box.status || "");
    document.getElementById(source + "Answer").innerHTML = renderMarkdown(box.answer_markdown || "");
    renderEvidence(source, box.evidence || []);
  }
}

function renderEvidence(source, evidence) {
  const container = document.getElementById(source + "Evidence");
  container.innerHTML = "";
  if (!evidence.length) {
    container.innerHTML = '<div class="evidence-meta">אין ראיות להצגה.</div>';
    return;
  }
  evidence.forEach(function (item, index) {
    const details = document.createElement("details");
    const summary = document.createElement("summary");
    summary.textContent = (index + 1) + ". " + (item.title || item.path || "source");
    const meta = document.createElement("div");
    meta.className = "evidence-meta";
    meta.textContent = [item.video_id, item.timecode, item.path].filter(Boolean).join(" · ");
    const quote = document.createElement("p");
    quote.textContent = item.quote || item.excerpt || "";
    const button = document.createElement("button");
    button.className = "citation-link";
    button.textContent = "פתח מקור";
    button.addEventListener("click", function () {
      openCitation(item);
    });
    details.appendChild(summary);
    details.appendChild(meta);
    details.appendChild(quote);
    details.appendChild(button);
    container.appendChild(details);
  });
}

function openCitation(item) {
  const rows = [
    ["Title", item.title],
    ["Video ID", item.video_id],
    ["Timecode", item.timecode],
    ["URL", item.url],
    ["Path", item.path],
    ["Source type", item.source_type],
    ["Quote", item.quote],
    ["Excerpt", item.excerpt]
  ];
  el.citationBody.innerHTML = rows.map(function (row) {
    if (!row[1]) return "";
    const value = row[0] === "URL"
      ? '<a href="' + escapeAttr(row[1]) + '" target="_blank" rel="noreferrer">' + escapeHtml(row[1]) + "</a>"
      : escapeHtml(row[1]);
    return "<p><strong>" + escapeHtml(row[0]) + ":</strong> " + value + "</p>";
  }).join("");
  el.dialog.showModal();
}

function renderMarkdown(text) {
  const escaped = escapeHtml(text || "");
  return escaped
    .split("\n")
    .map(function (line) {
      if (!line.trim()) return "<br>";
      if (line.startsWith("- ")) return "<p>• " + line.slice(2) + "</p>";
      return "<p>" + line + "</p>";
    })
    .join("");
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function escapeAttr(value) {
  return escapeHtml(value);
}

loadHistory().catch(function (error) {
  setStatus(error.message, false);
});
