"use strict";

/* ==========================================================================
 * Agentic RAG Chatbot — embeddable widget
 * --------------------------------------------------------------------------
 * A single self-contained script. Drop one tag onto any page (incl. Drupal):
 *
 *   <script src="/path/to/widget.js"
 *           data-api-base="https://chatbot.teriin.org"
 *           data-title="TERI Assistant"></script>
 *
 * It injects a floating launcher button + an overlay chat panel. All markup
 * and styles live inside a Shadow DOM, so the host site's CSS (Drupal theme)
 * cannot leak in and the widget's styles cannot leak out. No build, no deps.
 *
 * Backend contract (unchanged from the standalone UI):
 *   GET  /health          -> connection status
 *   POST /chat            -> SSE: {type:"token",text} / {type:"sources",...} / {type:"done"}
 *   POST /chat/feedback   -> {question, rating, answer, clicked_citations[]}
 * ======================================================================== */

(function () {
  /* ---------------------------------------------------------------- *
   * Config — read from this <script> tag's data-* attributes
   * ---------------------------------------------------------------- */
  const SCRIPT = document.currentScript;
  const cfg = (SCRIPT && SCRIPT.dataset) || {};
  const API_BASE = (cfg.apiBase || "http://localhost:8000").replace(/\/+$/, "");
  const TITLE = cfg.title || "TERI AI";
  const TOP_K = parseInt(cfg.topK || "", 10);
  const top_k = Number.isInteger(TOP_K) && TOP_K > 0 ? TOP_K : null;

  // Example prompts shown on the welcome screen (TERI-relevant).
  // icon = inner SVG paths (stroke, currentColor); bg/color = pastel chip.
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

  // Guard against double-injection.
  if (document.getElementById("teri-rag-widget")) return;

  /* ---------------------------------------------------------------- *
   * State
   * ---------------------------------------------------------------- */
  const history = []; // [{ role:"user"|"assistant", content:string }]
  let streaming = false;
  let isOpen = false;

  /* ---------------------------------------------------------------- *
   * Shadow DOM host (assigned in boot(), once <body> exists)
   * ---------------------------------------------------------------- */
  let host, root, el;

  /* ---------------------------------------------------------------- *
   * Open / close
   * ---------------------------------------------------------------- */
  function openPanel() {
    isOpen = true;
    host.classList.add("open");
    autoGrow();
    el.input.focus();
  }
  function closePanel() {
    isOpen = false;
    host.classList.remove("open");
  }
  function toggleExpand() {
    const expanded = host.classList.toggle("expanded");
    el.expand.title = expanded ? "Shrink" : "Expand";
    el.input.focus();
  }

  /* ---------------------------------------------------------------- *
   * Welcome / suggestion cards
   * ---------------------------------------------------------------- */
  function renderCards() {
    el.cards.innerHTML = "";
    for (const s of SUGGESTIONS) {
      const card = document.createElement("button");
      card.type = "button";
      card.className = "card";
      card.innerHTML =
        '<span class="card__icon" style="background:' + s.bg + ';color:' + s.color + '">' +
        '<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" ' +
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' + s.icon + "</svg></span>" +
        '<span class="card__text"><strong>' + escapeHtml(s.verb) + "</strong>" + escapeHtml(s.rest) + "</span>";
      card.addEventListener("click", () => {
        el.input.value = (s.verb + s.rest).trim();
        handleSend();
      });
      el.cards.appendChild(card);
    }
  }

  function hideWelcome() {
    if (el.welcome && !el.welcome.hidden) el.welcome.hidden = true;
  }
  /* ---------------------------------------------------------------- *
   * Messages
   * ---------------------------------------------------------------- */
  function addMessage(role, text) {
    hideWelcome();
    const wrap = document.createElement("div");
    wrap.className = "msg msg--" + role;
    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.textContent = text;
    wrap.appendChild(bubble);
    el.messages.appendChild(wrap);
    scrollToBottom();
    return { wrap, bubble };
  }

  function scrollToBottom() {
    el.messages.scrollTop = el.messages.scrollHeight;
  }

  const INPUT_MAX = 120;
  function autoGrow() {
    el.input.style.height = "auto";
    const needed = el.input.scrollHeight;
    el.input.style.height = Math.min(needed, INPUT_MAX) + "px";
    // Only show a scrollbar once the box can't grow any further.
    el.input.style.overflowY = needed > INPUT_MAX ? "auto" : "hidden";
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
    bubble.classList.add("bubble--pending");
    bubble.textContent = "…";

    try {
      const { answer, sources } = await streamChat(text, bubble);
      bubble.classList.remove("bubble--pending");
      if (answer) bubble.innerHTML = renderMarkdown(answer);
      else bubble.textContent = "(no response)";
      const clicked = new Set();
      if (sources) renderSources(wrap, sources, clicked);
      if (answer) renderFeedback(wrap, text, answer, clicked);
      history.push({ role: "user", content: text });
      history.push({ role: "assistant", content: answer });
    } catch (err) {
      bubble.classList.remove("bubble--pending");
      bubble.classList.add("bubble--error");
      bubble.textContent = "⚠ " + (err && err.message ? err.message : "request failed");
    } finally {
      setStreaming(false);
      scrollToBottom();
    }
  }

  /* ---------------------------------------------------------------- *
   * Chat streaming (POST SSE)
   * ---------------------------------------------------------------- */
  async function streamChat(question, bubble) {
    const body = { question, history };
    if (top_k) body.top_k = top_k;

    const res = await fetch(API_BASE + "/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok || !res.body) throw new Error("HTTP " + res.status);

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
          if (bubble.classList.contains("bubble--pending")) {
            bubble.classList.remove("bubble--pending");
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

  /* ---------------------------------------------------------------- *
   * Minimal Markdown (HTML-escaped, no dependencies)
   * ---------------------------------------------------------------- */
  function escapeHtml(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function renderInline(text) {
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
        i++;
        html.push("<pre><code>" + code.join("\n") + "</code></pre>");
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
        !/^#{1,6}\s+/.test(lines[i])
      ) {
        para.push(lines[i++]);
      }
      html.push("<p>" + renderInline(para.join("<br>")) + "</p>");
    }
    return html.join("");
  }

  /* ---------------------------------------------------------------- *
   * Citations / sources
   * ---------------------------------------------------------------- */
  function badge(text, warn) {
    const b = document.createElement("span");
    b.className = "badge" + (warn ? " badge--warn" : "");
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
    if (sources.conflict) meta.appendChild(badge("⚠ conflicting sources", true));
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
      c.also_available.forEach((alt, idx) => {
        also.appendChild(linkOrText(alt.title || alt.type || "source", alt.url));
        if (idx < c.also_available.length - 1) also.appendChild(document.createTextNode(", "));
      });
      body.appendChild(also);
    }

    item.appendChild(body);
    return item;
  }

  /* ---------------------------------------------------------------- *
   * Feedback
   * ---------------------------------------------------------------- */
  function renderFeedback(wrap, question, answer, clicked) {
    const row = document.createElement("div");
    row.className = "feedback";

    const up = document.createElement("button");
    up.type = "button";
    up.className = "fb-btn";
    up.textContent = "👍";
    up.title = "Helpful";

    const down = document.createElement("button");
    down.type = "button";
    down.className = "fb-btn";
    down.textContent = "👎";
    down.title = "Not helpful";

    const note = document.createElement("span");
    note.className = "fb-note";

    async function send(rating) {
      if (row.dataset.sent === rating) return;
      up.classList.toggle("fb-btn--active", rating === "up");
      down.classList.toggle("fb-btn--active", rating === "down");
      note.textContent = "";
      try {
        const res = await fetch(API_BASE + "/chat/feedback", {
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
      } catch {
        up.classList.remove("fb-btn--active");
        down.classList.remove("fb-btn--active");
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

  /* ---------------------------------------------------------------- *
   * Boot — build the Shadow DOM and wire events. Runs once <body> exists,
   * so the tag works whether placed in <head>, footer, or before </body>.
   * ---------------------------------------------------------------- */
  function boot() {
    host = document.createElement("div");
    host.id = "teri-rag-widget";
    root = host.attachShadow({ mode: "open" });
    document.body.appendChild(host);
    root.innerHTML = STYLES() + MARKUP();

    const $ = (sel) => root.querySelector(sel);
    el = {
      launcher: $("#launcher"),
      panel: $("#panel"),
      close: $("#close"),
      expand: $("#expand"),
      messages: $("#messages"),
      welcome: $("#welcome"),
      cards: $("#cards"),
      input: $("#input"),
      send: $("#send"),
    };

    el.launcher.addEventListener("click", () => (isOpen ? closePanel() : openPanel()));
    el.close.addEventListener("click", closePanel);
    el.expand.addEventListener("click", toggleExpand);
    el.send.addEventListener("click", handleSend);
    el.input.addEventListener("input", autoGrow);
    el.input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && isOpen) closePanel();
    });

    renderCards();
    autoGrow();
  }

  if (document.body) boot();
  else document.addEventListener("DOMContentLoaded", boot);

  /* ================================================================ *
   * Markup
   * ================================================================ */
  function MARKUP() {
    return `
      <button id="launcher" class="launcher" aria-label="Open ${escapeHtml(TITLE)}">
        <svg class="launcher__chat" viewBox="0 0 24 24" width="26" height="26" aria-hidden="true">
          <path fill="currentColor" d="M12 3C6.5 3 2 6.8 2 11.5c0 2.4 1.2 4.6 3.1 6.1-.1 1.2-.6 2.6-1.6 3.7 1.9-.2 3.5-.9 4.7-1.8 1.2.4 2.5.5 3.8.5 5.5 0 10-3.8 10-8.5S17.5 3 12 3z"/>
        </svg>
        <svg class="launcher__close" viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">
          <path fill="currentColor" d="M18.3 5.7 12 12l6.3 6.3-1.4 1.4L10.6 13.4 4.3 19.7 2.9 18.3 9.2 12 2.9 5.7l1.4-1.4L10.6 10.6l6.3-6.3z"/>
        </svg>
      </button>

      <section id="panel" class="panel" role="dialog" aria-label="${escapeHtml(TITLE)}">
        <header class="head">
          <div class="brand">
            <span class="brand__mark" aria-hidden="true">
              <svg viewBox="0 0 32 32" width="26" height="26">
                <defs><linearGradient id="teriMark" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0" stop-color="#7bd35a"/><stop offset="1" stop-color="#2e7d32"/>
                </linearGradient></defs>
                <circle cx="16" cy="16" r="14" fill="url(#teriMark)"/>
                <path d="M16 7.5l2.1 4.4 4.4 2.1-4.4 2.1L16 20.5l-2.1-4.4L9.5 14l4.4-2.1z" fill="#fff"/>
              </svg>
            </span>
            <span class="brand__title">${escapeHtml(TITLE)}</span>
          </div>
          <div class="head__actions">
            <button id="expand" class="icon-btn" title="Expand" aria-label="Expand">
              <svg class="ic-expand" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3H3v5M16 3h5v5M8 21H3v-5M16 21h5v-5"/></svg>
              <svg class="ic-compress" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 3v5H4M15 3v5h5M9 21v-5H4M15 21v-5h5"/></svg>
            </button>
            <button id="close" class="icon-btn" title="Close" aria-label="Close">
              <svg viewBox="0 0 24 24" width="18" height="18"><path fill="currentColor" d="M18.3 5.7 13.4 10.6 18.3 15.5 16.9 16.9 12 12 7.1 16.9 5.7 15.5 10.6 10.6 5.7 5.7 7.1 4.3 12 9.2 16.9 4.3z"/></svg>
            </button>
          </div>
        </header>

        <main id="messages" class="messages" aria-live="polite">
          <div id="welcome" class="welcome">
            <h2 class="welcome__title">Welcome to ${escapeHtml(TITLE)}</h2>
            <p class="welcome__hint">What would you like to explore today?</p>
            <div id="cards" class="cards"></div>
          </div>
        </main>

        <footer class="composer">
          <div class="composer__box">
            <textarea id="input" class="composer__input" rows="1"
              placeholder="Ask a question…"></textarea>
            <button id="send" class="composer__send" title="Send" aria-label="Send">
              <svg viewBox="0 0 24 24" width="20" height="20"><path fill="currentColor" d="M3 20.5 21 12 3 3.5 3 10l12 2-12 2z"/></svg>
            </button>
          </div>
        </footer>
      </section>
    `;
  }

  /* ================================================================ *
   * Styles — fully scoped inside the shadow root.
   * Tweak the TERI palette here once exact brand hex is confirmed.
   * ================================================================ */
  function STYLES() {
    return `<style>
    :host {
      /* ---- TERI palette (adjust to confirmed brand hex) ---- */
      --teri-green: #4c9f38;
      --teri-green-dark: #3a7d2a;
      --teri-green-soft: #eaf4e6;
      --teri-ink: #1f2a24;
      --teri-dim: #5f6b63;
      --teri-bg: #ffffff;
      --teri-surface: #f6f9f4;
      --teri-border: #e1e8dd;
      --teri-user: var(--teri-green);
      --teri-bad: #d64545;
      --teri-warn: #c8860d;
      --radius: 14px;

      all: initial;
      font-family: "Segoe UI", system-ui, -apple-system, Roboto, Helvetica, Arial, sans-serif;
      font-size: 15px;
      line-height: 1.5;
      color: var(--teri-ink);
    }
    *, *::before, *::after { box-sizing: border-box; }

    /* ---- Launcher ---- */
    .launcher {
      position: fixed;
      right: 22px;
      bottom: 22px;
      width: 60px;
      height: 60px;
      border: none;
      border-radius: 50%;
      background: var(--teri-green);
      color: #fff;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 6px 20px rgba(0,0,0,.22);
      z-index: 2147483646;
      transition: transform .15s ease, background .15s ease;
    }
    .launcher:hover { background: var(--teri-green-dark); transform: translateY(-2px); }
    .launcher__close { display: none; }
    :host(.open) .launcher__chat { display: none; }
    :host(.open) .launcher__close { display: block; }

    /* ---- Panel (same look docked or expanded; only size/position differ) ---- */
    .panel {
      position: fixed;
      right: 22px;
      bottom: 94px;
      width: 400px;
      max-width: calc(100vw - 32px);
      height: 620px;
      max-height: calc(100vh - 120px);
      background: linear-gradient(180deg, #fafdf9 0%, #eef5ea 100%);
      border: 1px solid var(--teri-border);
      border-radius: var(--radius);
      box-shadow: 0 12px 40px rgba(0,0,0,.24);
      display: none;
      flex-direction: column;
      overflow: hidden;
      z-index: 2147483646;
    }
    :host(.open) .panel { display: flex; animation: pop .16s ease; }
    @keyframes pop { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: none; } }

    /* Expanded: full-page overlay; content centred in a readable column. */
    :host(.expanded) .panel {
      inset: 0;
      width: 100%;
      max-width: 100%;
      height: 100%;
      max-height: 100%;
      border-radius: 0;
    }
    :host(.expanded) .messages,
    :host(.expanded) .composer {
      padding-left: max(20px, calc((100% - 1040px) / 2));
      padding-right: max(20px, calc((100% - 1040px) / 2));
    }
    :host(.expanded) .composer { padding-bottom: 26px; }
    :host(.expanded) .composer__box { max-width: 1040px; margin: 0 auto; }

    /* ---- Header: white bar with logo mark + dark title (AI Sarthi look) ---- */
    .head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 16px;
      background: #fff;
      color: var(--teri-ink);
      border-bottom: 1px solid var(--teri-border);
    }
    .brand { display: flex; align-items: center; gap: 9px; min-width: 0; }
    .brand__mark { display: inline-flex; flex-shrink: 0; line-height: 0; }
    .brand__title { font-weight: 700; font-size: 1.05rem; white-space: nowrap; letter-spacing: .01em; }
    .head__actions { display: flex; align-items: center; gap: 6px; }

    /* Expanded header just a touch larger. */
    :host(.expanded) .head { padding: 14px 20px; }
    :host(.expanded) .brand__title { font-size: 1.15rem; }

    .ic-compress { display: none; }
    :host(.expanded) .ic-expand { display: none; }
    :host(.expanded) .ic-compress { display: block; }

    .icon-btn {
      background: transparent;
      border: none;
      color: var(--teri-dim);
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      padding: 4px;
      border-radius: 6px;
    }
    .icon-btn:hover { background: var(--teri-surface); }
    #close { color: var(--teri-bad); }

    /* ---- Messages ---- */
    .messages {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      background: transparent;
    }

    .welcome { margin: auto 0; text-align: center; padding: 8px 4px; }
    .welcome__title { margin: 0 0 4px; font-size: 1.4rem; color: var(--teri-ink); }
    .welcome__hint { margin: 0 0 16px; font-size: .92rem; color: var(--teri-dim); }
    .cards { display: grid; grid-template-columns: 1fr; gap: 10px; }
    .card {
      display: flex;
      align-items: flex-start;
      gap: 10px;
      text-align: left;
      background: var(--teri-bg);
      border: 1px solid var(--teri-border);
      border-radius: 12px;
      padding: 12px 13px;
      font: inherit;
      font-size: .82rem;
      color: var(--teri-ink);
      cursor: pointer;
      transition: border-color .12s ease, box-shadow .12s ease, transform .12s ease;
    }
    .card:hover { border-color: var(--teri-green); box-shadow: 0 4px 14px rgba(0,0,0,.07); transform: translateY(-1px); }
    .card strong { font-weight: 700; }
    .card__icon {
      width: 34px; height: 34px;
      border-radius: 9px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }
    .card__text { line-height: 1.4; }

    /* Expanded body = AI Sarthi look: soft gradient, big centred welcome, 3 cols. */
    :host(.expanded) .messages { background: linear-gradient(180deg, #fafdf9 0%, #eef5ea 100%); }
    :host(.expanded) .welcome { margin-top: 7vh; }
    :host(.expanded) .welcome__title { font-size: 2.1rem; margin-bottom: 8px; }
    :host(.expanded) .welcome__hint { font-size: 1.05rem; margin-bottom: 28px; }
    :host(.expanded) .cards {
      grid-template-columns: repeat(3, 1fr);
      gap: 14px;
      max-width: 1040px;
      margin: 0 auto;
    }
    :host(.expanded) .card { font-size: .9rem; padding: 16px; }
    :host(.expanded) .msg { max-width: 75%; }

    .msg { display: flex; flex-direction: column; max-width: 90%; }
    .msg--user { align-self: flex-end; align-items: flex-end; }
    .msg--bot { align-self: flex-start; align-items: flex-start; }
    .bubble {
      padding: 9px 13px;
      border-radius: var(--radius);
      white-space: pre-wrap;
      word-wrap: break-word;
    }
    .msg--user .bubble { background: var(--teri-user); color: #fff; border-bottom-right-radius: 4px; }
    .msg--bot .bubble { background: var(--teri-bg); border: 1px solid var(--teri-border); border-bottom-left-radius: 4px; }
    .bubble--pending { color: var(--teri-dim); }
    .bubble--error { border-color: var(--teri-bad); color: var(--teri-bad); }

    .bubble p { margin: 0 0 .55rem; }
    .bubble > :last-child { margin-bottom: 0; }
    .bubble ul, .bubble ol { margin: 0 0 .55rem; padding-left: 1.25rem; }
    .bubble li { margin: .12rem 0; }
    .bubble h1, .bubble h2, .bubble h3, .bubble h4, .bubble h5, .bubble h6 {
      margin: .3rem 0 .35rem; font-size: 1.02em;
    }
    .bubble a { color: var(--teri-green-dark); }
    .bubble code {
      background: var(--teri-surface);
      border: 1px solid var(--teri-border);
      border-radius: 4px;
      padding: .05rem .3rem;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: .85em;
    }
    .bubble pre {
      background: var(--teri-surface);
      border: 1px solid var(--teri-border);
      border-radius: 8px;
      padding: .6rem;
      overflow-x: auto;
      margin: 0 0 .55rem;
    }
    .bubble pre code { background: none; border: none; padding: 0; }

    /* ---- Citations ---- */
    .meta { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; }
    .badge {
      font-size: .66rem;
      text-transform: uppercase;
      letter-spacing: .03em;
      color: var(--teri-dim);
      background: var(--teri-bg);
      border: 1px solid var(--teri-border);
      border-radius: 999px;
      padding: 2px 8px;
    }
    .badge--warn { color: var(--teri-warn); border-color: var(--teri-warn); }

    .citations { margin-top: 6px; display: flex; flex-direction: column; gap: 6px; width: 100%; }
    .citation {
      display: flex; gap: 7px; font-size: .8rem;
      background: var(--teri-bg);
      border: 1px solid var(--teri-border);
      border-radius: 8px;
      padding: 7px 9px;
    }
    .citation__marker { color: var(--teri-green-dark); font-weight: 600; flex-shrink: 0; }
    .citation__body { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
    .citation__title { color: var(--teri-ink); word-break: break-word; }
    a.citation__title { color: var(--teri-green-dark); text-decoration: none; }
    a.citation__title:hover { text-decoration: underline; }
    .citation__detail, .citation__also { color: var(--teri-dim); font-size: .74rem; }
    .citation__also a { color: var(--teri-green-dark); text-decoration: none; }
    .citation__also a:hover { text-decoration: underline; }

    /* ---- Feedback ---- */
    .feedback { display: flex; align-items: center; gap: 6px; margin-top: 6px; }
    .fb-btn {
      background: var(--teri-bg);
      border: 1px solid var(--teri-border);
      border-radius: 8px;
      padding: 2px 8px;
      font-size: .9rem;
      line-height: 1;
      cursor: pointer;
    }
    .fb-btn:hover { background: var(--teri-green-soft); }
    .fb-btn--active { border-color: var(--teri-green); background: var(--teri-green-soft); }
    .fb-note { font-size: .74rem; color: var(--teri-dim); }

    /* ---- Composer: a floating rounded box with the send button inside ---- */
    .composer {
      padding: 12px;
      background: transparent;
    }
    .composer__box {
      display: flex;
      gap: 8px;
      align-items: flex-end;
      width: 100%;
      background: #fff;
      border: 1px solid var(--teri-border);
      border-radius: 16px;
      box-shadow: 0 2px 12px rgba(0,0,0,.06);
      padding: 6px 6px 6px 14px;
    }
    .composer__box:focus-within { border-color: var(--teri-green); }
    .composer__input {
      flex: 1;
      resize: none;
      max-height: 120px;
      overflow-y: hidden;
      background: transparent;
      border: none;
      color: var(--teri-ink);
      padding: 8px 0;
      font: inherit;
      line-height: 1.4;
    }
    .composer__input:focus { outline: none; }
    .composer__send {
      flex-shrink: 0;
      width: 42px;
      height: 42px;
      border: none;
      border-radius: 50%;
      background: var(--teri-green);
      color: #fff;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
    }
    .composer__send:hover { background: var(--teri-green-dark); }
    .composer__send:disabled, .composer__send.busy { opacity: .55; cursor: not-allowed; }

    /* ---- Mobile: full screen ---- */
    @media (max-width: 480px) {
      .panel {
        right: 0; bottom: 0; left: 0; top: 0;
        width: 100%; max-width: 100%;
        height: 100%; max-height: 100%;
        border-radius: 0;
      }
      .launcher { right: 16px; bottom: 16px; }
      .cards, :host(.expanded) .cards { grid-template-columns: 1fr; }
      :host(.expanded) .welcome__title { font-size: 1.5rem; }
    }
    </style>`;
  }
})();
