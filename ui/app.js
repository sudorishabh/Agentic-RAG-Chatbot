"use strict";

/* ------------------------------------------------------------------ *
 * Config
 * ------------------------------------------------------------------ */
const DEFAULT_API_BASE = "http://localhost:8000";
const STORAGE_KEY = "ragui.apiBase";
const TOPK_KEY = "ragui.topK";

function getApiBase() {
  return (localStorage.getItem(STORAGE_KEY) || DEFAULT_API_BASE).replace(/\/+$/, "");
}
function setApiBase(value) {
  localStorage.setItem(STORAGE_KEY, value.replace(/\/+$/, ""));
}
function getTopK() {
  const v = parseInt(localStorage.getItem(TOPK_KEY) || "", 10);
  return Number.isInteger(v) && v > 0 ? v : null;
}
function setTopK(value) {
  if (Number.isInteger(value) && value > 0) localStorage.setItem(TOPK_KEY, String(value));
  else localStorage.removeItem(TOPK_KEY);
}

/* ------------------------------------------------------------------ *
 * Welcome suggestion cards
 * icon = inner SVG paths (stroke, currentColor); bg/color = pastel chip.
 * ------------------------------------------------------------------ */
const ICON = {
  find: '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>',
  compare: '<rect x="5" y="5" width="5" height="14" rx="1"/><rect x="14" y="5" width="5" height="14" rx="1"/>',
  track: '<path d="M3 17l6-6 4 4 7-7"/><path d="M21 8v5h-5"/>',
  list: '<path d="M9 6h11M9 12h11M9 18h11"/><circle cx="4.5" cy="6" r="1.2"/><circle cx="4.5" cy="12" r="1.2"/><circle cx="4.5" cy="18" r="1.2"/>',
  analyze: '<path d="M5 21V11M12 21V4M19 21v-7"/>',
  suggest: '<path d="M9 18h6M10 21h4"/><path d="M12 3a6 6 0 0 0-4 10c1 1 1 2 1 3h6c0-1 0-2 1-3a6 6 0 0 0-4-10z"/>',
};
const SUGGESTIONS = [
  { verb: "Find", rest: " India's renewable energy capacity targets", icon: ICON.find, bg: "#e7f0ff", color: "#3b73d6" },
  { verb: "Compare", rest: " solar and wind energy adoption across states", icon: ICON.compare, bg: "#ece8ff", color: "#6b53d6" },
  { verb: "Track", rest: " progress on India's net-zero commitments", icon: ICON.track, bg: "#e2f4f1", color: "#1f9c86" },
  { verb: "List", rest: " key recommendations on sustainable water management", icon: ICON.list, bg: "#fdeaf3", color: "#cc4f8e" },
  { verb: "Analyze", rest: " the main drivers of urban air pollution", icon: ICON.analyze, bg: "#e9f6e6", color: "#4c9f38" },
  { verb: "Suggest", rest: " actions to improve industrial energy efficiency", icon: ICON.suggest, bg: "#fff1e0", color: "#d9871f" },
];

function renderCards(container) {
  if (!container) return;
  container.innerHTML = "";
  for (const s of SUGGESTIONS) {
    const card = document.createElement("button");
    card.type = "button";
    card.className = "card";
    card.innerHTML =
      '<span class="card__icon" style="background:' + s.bg + ";color:" + s.color + '">' +
      '<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" ' +
      'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' + s.icon + "</svg></span>" +
      '<span class="card__text"><strong>' + escapeHtml(s.verb) + "</strong>" + escapeHtml(s.rest) + "</span>";
    card.addEventListener("click", () => {
      if (streaming) return;
      el.input.value = (s.verb + s.rest).trim();
      autoGrow();
      handleSend();
    });
    container.appendChild(card);
  }
}

/* ------------------------------------------------------------------ *
 * DOM refs
 * ------------------------------------------------------------------ */
const el = {
  messages: document.getElementById("messages"),
  emptyState: document.getElementById("emptyState"),
  input: document.getElementById("input"),
  send: document.getElementById("send"),
  status: document.getElementById("status"),
  statusLabel: document.querySelector("#status .status__label"),
  settingsToggle: document.getElementById("settingsToggle"),
  settingsPanel: document.getElementById("settingsPanel"),
  apiBase: document.getElementById("apiBase"),
  topK: document.getElementById("topK"),
  saveSettings: document.getElementById("saveSettings"),
  clearChat: document.getElementById("clearChat"),
};

/* ------------------------------------------------------------------ *
 * State
 * ------------------------------------------------------------------ */
const history = []; // [{ role: "user" | "assistant", content: string }]
let streaming = false;

/* ------------------------------------------------------------------ *
 * Backend status
 * ------------------------------------------------------------------ */
function setStatus(state, label) {
  el.status.className = "status status--" + state;
  el.statusLabel.textContent = label;
}

async function checkHealth() {
  setStatus("unknown", "checking…");
  try {
    const res = await fetch(getApiBase() + "/health", { method: "GET" });
    if (res.ok) {
      setStatus("ok", "connected");
    } else {
      setStatus("bad", "error " + res.status);
    }
  } catch (err) {
    setStatus("bad", "offline");
  }
}

/* ------------------------------------------------------------------ *
 * Messages
 * ------------------------------------------------------------------ */
function hideEmptyState() {
  if (el.emptyState) {
    el.emptyState.remove();
    el.emptyState = null;
  }
}

function renderEmptyState() {
  const div = document.createElement("div");
  div.id = "emptyState";
  div.className = "welcome";
  div.innerHTML =
    '<h2 class="welcome__title">Welcome to Agentic RAG Chatbot</h2>' +
    '<p class="welcome__hint">What would you like to explore today?</p>' +
    '<div id="cards" class="cards"></div>';
  el.messages.appendChild(div);
  el.emptyState = div;
  renderCards(div.querySelector("#cards"));
}

function clearChat() {
  if (streaming) return;
  history.length = 0;
  el.messages.innerHTML = "";
  el.emptyState = null;
  renderEmptyState();
}

function addMessage(role, text) {
  hideEmptyState();
  const wrap = document.createElement("div");
  wrap.className = "msg msg--" + role;

  const bubble = document.createElement("div");
  bubble.className = "msg__bubble";
  bubble.textContent = text;

  wrap.appendChild(bubble);
  el.messages.appendChild(wrap);
  scrollToBottom();
  return { wrap, bubble };
}

function scrollToBottom() {
  el.messages.scrollTop = el.messages.scrollHeight;
}

/* ------------------------------------------------------------------ *
 * Composer
 * ------------------------------------------------------------------ */
function autoGrow() {
  el.input.style.height = "auto";
  el.input.style.height = Math.min(el.input.scrollHeight, 160) + "px";
}

function setStreaming(on) {
  streaming = on;
  el.send.disabled = on;
  el.send.classList.toggle("busy", on);
}

async function handleSend() {
  if (streaming) return;
  const text = el.input.value.trim();
  if (!text) return;

  addMessage("user", text);
  el.input.value = "";
  autoGrow();

  setStreaming(true);
  const { wrap, bubble } = addMessage("bot", "");
  bubble.classList.add("msg__bubble--pending");
  bubble.textContent = "…";

  try {
    const { answer, sources } = await streamChat(text, bubble);
    bubble.classList.remove("msg__bubble--pending");
    if (answer) bubble.innerHTML = renderMarkdown(answer);
    else bubble.textContent = "(no response)";
    const clicked = new Set();
    if (sources) renderSources(wrap, sources, clicked);
    if (answer) renderFeedback(wrap, text, answer, clicked);
    history.push({ role: "user", content: text });
    history.push({ role: "assistant", content: answer });
  } catch (err) {
    bubble.classList.remove("msg__bubble--pending");
    bubble.classList.add("msg__bubble--error");
    bubble.textContent = "⚠ " + (err && err.message ? err.message : "request failed");
  } finally {
    setStreaming(false);
    scrollToBottom();
  }
}

/* ------------------------------------------------------------------ *
 * Chat streaming (POST SSE)
 * ------------------------------------------------------------------ */
async function streamChat(question, bubble) {
  // history holds prior turns only; the current question goes in `question`.
  const body = { question, history };
  const topK = getTopK();
  if (topK) body.top_k = topK;

  const res = await fetch(getApiBase() + "/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok || !res.body) {
    throw new Error("HTTP " + res.status);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let answer = "";
  let sources = null;

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let idx;
    while ((idx = buffer.indexOf("\n\n")) !== -1) {
      const raw = buffer.slice(0, idx).trim();
      buffer = buffer.slice(idx + 2);
      if (!raw.startsWith("data:")) continue;

      const payload = raw.slice(5).trim();
      if (!payload) continue;

      let event;
      try {
        event = JSON.parse(payload);
      } catch {
        continue;
      }

      if (event.type === "token") {
        if (bubble.classList.contains("msg__bubble--pending")) {
          bubble.classList.remove("msg__bubble--pending");
          bubble.textContent = "";
        }
        answer += event.text;
        bubble.textContent = answer;
        scrollToBottom();
      } else if (event.type === "sources") {
        sources = event;
      } else if (event.type === "done") {
        return { answer, sources };
      }
    }
  }
  return { answer, sources };
}

/* ------------------------------------------------------------------ *
 * Minimal Markdown rendering (HTML-escaped, no dependencies)
 * ------------------------------------------------------------------ */
function escapeHtml(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function renderInline(text) {
  // `text` is already HTML-escaped.
  let out = text.replace(/`([^`]+)`/g, (_, c) => "<code>" + c + "</code>");
  out = out.replace(
    /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
    (_, label, url) => `<a href="${url}" target="_blank" rel="noopener noreferrer">${label}</a>`
  );
  out = out.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  out = out.replace(/__([^_]+)__/g, "<strong>$1</strong>");
  out = out.replace(/(^|[^*])\*([^*]+)\*/g, "$1<em>$2</em>");
  return out;
}

/* GitHub-style tables: a header row, a |---|---| separator, then body rows. */
function isTableSeparator(line) {
  return /^\s*\|?\s*:?-{1,}:?\s*(\|\s*:?-{1,}:?\s*)*\|?\s*$/.test(line);
}
function isTableStart(line, next) {
  return line != null && line.indexOf("|") !== -1 && next != null && isTableSeparator(next);
}
function splitTableRow(line) {
  return line.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map((c) => c.trim());
}
function tableAligns(sep) {
  return splitTableRow(sep).map((c) => {
    const l = c.startsWith(":");
    const r = c.endsWith(":");
    return l && r ? "center" : r ? "right" : l ? "left" : "";
  });
}
function renderTable(header, aligns, rows) {
  const at = (idx) => (aligns[idx] ? ' style="text-align:' + aligns[idx] + '"' : "");
  let out = '<div class="table-wrap"><table><thead><tr>';
  header.forEach((c, idx) => { out += "<th" + at(idx) + ">" + renderInline(c) + "</th>"; });
  out += "</tr></thead><tbody>";
  for (const row of rows) {
    out += "<tr>";
    for (let idx = 0; idx < header.length; idx++) {
      out += "<td" + at(idx) + ">" + renderInline(row[idx] != null ? row[idx] : "") + "</td>";
    }
    out += "</tr>";
  }
  return out + "</tbody></table></div>";
}

function renderMarkdown(src) {
  const lines = escapeHtml(src).split("\n");
  const html = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (/^```/.test(line)) {
      const code = [];
      i++;
      while (i < lines.length && !/^```\s*$/.test(lines[i])) code.push(lines[i++]);
      i++; // skip closing fence
      html.push("<pre><code>" + code.join("\n") + "</code></pre>");
      continue;
    }

    if (isTableStart(line, lines[i + 1])) {
      const header = splitTableRow(line);
      const aligns = tableAligns(lines[i + 1]);
      i += 2;
      const rows = [];
      while (i < lines.length && lines[i].indexOf("|") !== -1 && !/^\s*$/.test(lines[i])) {
        rows.push(splitTableRow(lines[i]));
        i++;
      }
      html.push(renderTable(header, aligns, rows));
      continue;
    }

    if (/^\s*[-*]\s+/.test(line)) {
      const items = [];
      while (i < lines.length && /^\s*[-*]\s+/.test(lines[i])) {
        items.push("<li>" + renderInline(lines[i].replace(/^\s*[-*]\s+/, "")) + "</li>");
        i++;
      }
      html.push("<ul>" + items.join("") + "</ul>");
      continue;
    }

    if (/^\s*\d+\.\s+/.test(line)) {
      const items = [];
      while (i < lines.length && /^\s*\d+\.\s+/.test(lines[i])) {
        items.push("<li>" + renderInline(lines[i].replace(/^\s*\d+\.\s+/, "")) + "</li>");
        i++;
      }
      html.push("<ol>" + items.join("") + "</ol>");
      continue;
    }

    const heading = line.match(/^(#{1,6})\s+(.*)$/);
    if (heading) {
      const lvl = heading[1].length;
      html.push("<h" + lvl + ">" + renderInline(heading[2]) + "</h" + lvl + ">");
      i++;
      continue;
    }

    if (/^\s*$/.test(line)) {
      i++;
      continue;
    }

    const para = [];
    while (
      i < lines.length &&
      !/^\s*$/.test(lines[i]) &&
      !/^```/.test(lines[i]) &&
      !/^\s*[-*]\s+/.test(lines[i]) &&
      !/^\s*\d+\.\s+/.test(lines[i]) &&
      !/^#{1,6}\s+/.test(lines[i]) &&
      !isTableStart(lines[i], lines[i + 1])
    ) {
      para.push(lines[i++]);
    }
    html.push("<p>" + renderInline(para.join("<br>")) + "</p>");
  }

  return html.join("");
}

/* ------------------------------------------------------------------ *
 * Citations / sources rendering
 * ------------------------------------------------------------------ */
function badge(text, modifier) {
  const b = document.createElement("span");
  b.className = "meta__badge" + (modifier ? " " + modifier : "");
  b.textContent = text;
  return b;
}

function renderSources(wrap, sources, clicked) {
  const citations = Array.isArray(sources.citations) ? sources.citations : [];

  const meta = document.createElement("div");
  meta.className = "meta";
  if (sources.intent) meta.appendChild(badge(sources.intent));
  const count = sources.used_chunks || citations.length;
  if (count) meta.appendChild(badge(count + (count === 1 ? " source" : " sources")));
  if (sources.conflict) meta.appendChild(badge("⚠ conflicting sources", "meta__badge--warn"));
  if (meta.childNodes.length) wrap.appendChild(meta);

  if (!citations.length) return;
  const list = document.createElement("div");
  list.className = "citations";
  for (const c of citations) list.appendChild(renderCitation(c, clicked));
  wrap.appendChild(list);
}

function linkOrText(label, url) {
  let node;
  if (url) {
    node = document.createElement("a");
    node.href = url;
    node.target = "_blank";
    node.rel = "noopener noreferrer";
  } else {
    node = document.createElement("span");
  }
  node.textContent = label;
  return node;
}

function renderCitation(c, clicked) {
  const item = document.createElement("div");
  item.className = "citation";
  if (clicked) item.addEventListener("click", () => clicked.add(c.n));

  const marker = document.createElement("span");
  marker.className = "citation__marker";
  marker.textContent = "[" + c.n + "]";
  item.appendChild(marker);

  const body = document.createElement("div");
  body.className = "citation__body";

  const title = linkOrText(c.title || c.document_id || c.type || "source", c.url);
  title.classList.add("citation__title");
  body.appendChild(title);

  const detail = [];
  if (c.type) detail.push(c.type);
  if (c.page != null) detail.push("p. " + c.page);
  if (c.section) detail.push(c.section);
  if (detail.length) {
    const d = document.createElement("span");
    d.className = "citation__detail";
    d.textContent = detail.join(" · ");
    body.appendChild(d);
  }

  if (Array.isArray(c.also_available) && c.also_available.length) {
    const also = document.createElement("span");
    also.className = "citation__also";
    also.appendChild(document.createTextNode("also in: "));
    c.also_available.forEach((alt, i) => {
      also.appendChild(linkOrText(alt.title || alt.type || "source", alt.url));
      if (i < c.also_available.length - 1) also.appendChild(document.createTextNode(", "));
    });
    body.appendChild(also);
  }

  item.appendChild(body);
  return item;
}

/* ------------------------------------------------------------------ *
 * Feedback
 * ------------------------------------------------------------------ */
function renderFeedback(wrap, question, answer, clicked) {
  const row = document.createElement("div");
  row.className = "feedback";

  const up = document.createElement("button");
  up.type = "button";
  up.className = "feedback__btn";
  up.textContent = "👍";
  up.title = "Helpful";

  const down = document.createElement("button");
  down.type = "button";
  down.className = "feedback__btn";
  down.textContent = "👎";
  down.title = "Not helpful";

  const note = document.createElement("span");
  note.className = "feedback__note";

  async function send(rating) {
    if (row.dataset.sent === rating) return;
    up.classList.toggle("feedback__btn--active", rating === "up");
    down.classList.toggle("feedback__btn--active", rating === "down");
    note.textContent = "";
    try {
      const res = await fetch(getApiBase() + "/chat/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question,
          rating,
          answer,
          clicked_citations: Array.from(clicked),
        }),
      });
      if (!res.ok) throw new Error("HTTP " + res.status);
      row.dataset.sent = rating;
      note.textContent = "thanks for the feedback";
    } catch (err) {
      up.classList.remove("feedback__btn--active");
      down.classList.remove("feedback__btn--active");
      note.textContent = "couldn't send feedback";
    }
  }

  up.addEventListener("click", () => send("up"));
  down.addEventListener("click", () => send("down"));

  row.appendChild(up);
  row.appendChild(down);
  row.appendChild(note);
  wrap.appendChild(row);
}

/* ------------------------------------------------------------------ *
 * Settings
 * ------------------------------------------------------------------ */
function toggleSettings() {
  el.settingsPanel.hidden = !el.settingsPanel.hidden;
  if (!el.settingsPanel.hidden) {
    el.apiBase.value = getApiBase();
    const tk = getTopK();
    el.topK.value = tk ? String(tk) : "";
    el.apiBase.focus();
  }
}

function saveSettings() {
  setApiBase(el.apiBase.value.trim() || DEFAULT_API_BASE);
  setTopK(parseInt(el.topK.value, 10));
  el.settingsPanel.hidden = true;
  checkHealth();
}

/* ------------------------------------------------------------------ *
 * Wiring
 * ------------------------------------------------------------------ */
el.send.addEventListener("click", handleSend);
el.input.addEventListener("input", autoGrow);
el.input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    handleSend();
  }
});
el.settingsToggle.addEventListener("click", toggleSettings);
el.saveSettings.addEventListener("click", saveSettings);
el.clearChat.addEventListener("click", clearChat);

el.apiBase.value = getApiBase();
renderCards(document.getElementById("cards"));
checkHealth();
