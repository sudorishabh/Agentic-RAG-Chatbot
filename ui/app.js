"use strict";

/* ------------------------------------------------------------------ *
 * Config
 * ------------------------------------------------------------------ */
const DEFAULT_API_BASE = "http://localhost:8000";
const STORAGE_KEY = "ragui.apiBase";

function getApiBase() {
  return (localStorage.getItem(STORAGE_KEY) || DEFAULT_API_BASE).replace(/\/+$/, "");
}
function setApiBase(value) {
  localStorage.setItem(STORAGE_KEY, value.replace(/\/+$/, ""));
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
  saveSettings: document.getElementById("saveSettings"),
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
  if (el.emptyState) el.emptyState.remove();
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
  el.send.textContent = on ? "…" : "Send";
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
    bubble.textContent = answer || "(no response)";
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
  const res = await fetch(getApiBase() + "/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, history }),
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
    el.apiBase.focus();
  }
}

function saveSettings() {
  const value = el.apiBase.value.trim() || DEFAULT_API_BASE;
  setApiBase(value);
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

el.apiBase.value = getApiBase();
checkHealth();
