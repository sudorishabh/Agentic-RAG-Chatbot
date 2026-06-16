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
  const { bubble } = addMessage("bot", "");
  bubble.classList.add("msg__bubble--pending");
  bubble.textContent = "…";

  try {
    const answer = await streamChat(text, bubble);
    bubble.classList.remove("msg__bubble--pending");
    bubble.textContent = answer || "(no response)";
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
        // Citations rendered in the next step.
      } else if (event.type === "done") {
        return answer;
      }
    }
  }
  return answer;
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
