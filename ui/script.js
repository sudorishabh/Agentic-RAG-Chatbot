"use strict";

(function () {
  const SCRIPT = document.currentScript;
  const cfg = (SCRIPT && SCRIPT.dataset) || {};
  const API_BASE = (cfg.apiBase || "http://localhost:8000").replace(/\/+$/, "");
  const TITLE = "TERI AI SARTHI";
  const TOP_K = parseInt(cfg.topK || "", 10);
  const top_k = Number.isInteger(TOP_K) && TOP_K > 0 ? TOP_K : null;

  const ICON = {
    find: '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>',
    compare:
      '<rect x="5" y="5" width="5" height="14" rx="1"/><rect x="14" y="5" width="5" height="14" rx="1"/>',
    track: '<path d="M3 17l6-6 4 4 7-7"/><path d="M21 8v5h-5"/>',
    list: '<path d="M9 6h11M9 12h11M9 18h11"/><circle cx="4.5" cy="6" r="1.2"/><circle cx="4.5" cy="12" r="1.2"/><circle cx="4.5" cy="18" r="1.2"/>',
    analyze: '<path d="M5 21V11M12 21V4M19 21v-7"/>',
    suggest:
      '<path d="M9 18h6M10 21h4"/><path d="M12 3a6 6 0 0 0-4 10c1 1 1 2 1 3h6c0-1 0-2 1-3a6 6 0 0 0-4-10z"/>',
  };
  const SUGGESTIONS = [
    {
      verb: "Find",
      rest: " India's renewable energy capacity targets",
      icon: ICON.find,
      bg: "#e7f0ff",
      color: "#3b73d6",
    },
    {
      verb: "Compare",
      rest: " solar and wind energy adoption across states",
      icon: ICON.compare,
      bg: "#ece8ff",
      color: "#6b53d6",
    },
    {
      verb: "Track",
      rest: " progress on India's net-zero commitments",
      icon: ICON.track,
      bg: "#e2f4f1",
      color: "#1f9c86",
    },
    {
      verb: "List",
      rest: " key recommendations on sustainable water management",
      icon: ICON.list,
      bg: "#fdeaf3",
      color: "#cc4f8e",
    },
    {
      verb: "Analyze",
      rest: " the main drivers of urban air pollution",
      icon: ICON.analyze,
      bg: "#e9f6e6",
      color: "#4c9f38",
    },
    {
      verb: "Suggest",
      rest: " actions to improve industrial energy efficiency",
      icon: ICON.suggest,
      bg: "#fff1e0",
      color: "#d9871f",
    },
  ];

  // Status words cycled while the bot is working, before the first token lands.
  const LOADER_PHASES = [
    "Thinking",
    "Reading relevant sources",
    "Generating your answer",
  ];

  // Guard against double-injection.
  if (document.getElementById("teri-rag-widget")) return;

  const history = [];
  let streaming = false;
  let isOpen = false;
  let loaderTimer = null;
  // In-flight request state: aborting the fetch on "New chat" stops the
  // server-side generation, and the epoch guard keeps a stream that raced the
  // reset from leaking its turn into the fresh conversation's history.
  let currentAbort = null;
  let chatEpoch = 0;

  let host, root, el;

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

  // Reset to a fresh conversation: cancel any in-flight request, drop history,
  // clear messages, show welcome.
  function resetChat() {
    chatEpoch++;
    if (currentAbort) currentAbort.abort();
    setStreaming(false);
    stopLoader();
    history.length = 0;
    el.messages.querySelectorAll(".msg").forEach((n) => n.remove());
    if (el.welcome) el.welcome.hidden = false;
    el.input.value = "";
    autoGrow();
    el.input.focus();
  }

  function renderCards() {
    el.cards.innerHTML = "";
    for (const s of SUGGESTIONS) {
      const card = document.createElement("button");
      card.type = "button";
      card.className = "card";
      card.innerHTML =
        '<span class="card__icon" style="background:' +
        s.bg +
        ";color:" +
        s.color +
        '">' +
        '<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" ' +
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
        s.icon +
        "</svg></span>" +
        '<span class="card__text"><strong>' +
        escapeHtml(s.verb) +
        "</strong>" +
        escapeHtml(s.rest) +
        "</span>";
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

  /* Animated "working" indicator: a shimmering status word that steps through
     LOADER_PHASES, plus three bouncing dots. Runs until the first token arrives
     (see streamChat) or the request settles. */
  function startLoader(bubble) {
    bubble.classList.add("bubble--pending");
    bubble.innerHTML =
      '<span class="loader">' +
      '<span class="loader__text" role="status"></span>' +
      '<span class="loader__dots" aria-hidden="true"><i></i><i></i><i></i></span>' +
      "</span>";

    const textEl = bubble.querySelector(".loader__text");
    let idx = -1;
    const advance = () => {
      idx = Math.min(idx + 1, LOADER_PHASES.length - 1);
      const word = document.createElement("span");
      word.className = "loader__word";
      word.textContent = LOADER_PHASES[idx];
      textEl.textContent = "";
      textEl.appendChild(word);
      if (idx >= LOADER_PHASES.length - 1) stopLoader();
    };
    advance();
    loaderTimer = setInterval(advance, 3200);
  }

  function stopLoader() {
    if (loaderTimer) {
      clearInterval(loaderTimer);
      loaderTimer = null;
    }
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
    startLoader(bubble);

    const epoch = chatEpoch;
    const ctrl = new AbortController();
    currentAbort = ctrl;
    try {
      const { answer, sources } = await streamChat(text, bubble, ctrl.signal);
      stopLoader();
      if (epoch !== chatEpoch) return; // conversation was reset mid-flight
      bubble.classList.remove("bubble--pending");
      if (answer) bubble.innerHTML = renderMarkdown(answer);
      else bubble.textContent = "(no response)";
      if (sources) renderSources(wrap, sources);
      history.push({ role: "user", content: text });
      history.push({ role: "assistant", content: answer });
    } catch (err) {
      stopLoader();
      bubble.classList.remove("bubble--pending");
      // Cancelled by "New chat": the bubble is already gone — stay silent.
      if ((err && err.name === "AbortError") || epoch !== chatEpoch) return;
      bubble.classList.add("bubble--error");
      bubble.textContent =
        "⚠ " + (err && err.message ? err.message : "request failed");
    } finally {
      if (currentAbort === ctrl) currentAbort = null;
      if (epoch === chatEpoch) setStreaming(false);
      scrollToBottom();
    }
  }

  async function streamChat(question, bubble, signal) {
    const body = { question, history };
    if (top_k) body.top_k = top_k;

    const res = await fetch(API_BASE + "/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal,
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
            stopLoader();
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

  // Escapes for both element text and double-quoted attribute values. renderMarkdown
  // escapes the whole source once through here before any inline HTML is built, so
  // quotes must be escaped too — otherwise a quote inside a markdown link URL breaks
  // out of the href attribute and injects handlers (DOM XSS).
  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function renderInline(text) {
    let out = text.replace(/`([^`]+)`/g, (_, c) => "<code>" + c + "</code>");
    out = out.replace(
      /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
      (_, label, url) =>
        `<a href="${url}" target="_blank" rel="noopener noreferrer">${label}</a>`,
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
    return (
      line != null &&
      line.indexOf("|") !== -1 &&
      next != null &&
      isTableSeparator(next)
    );
  }
  function splitTableRow(line) {
    return line
      .trim()
      .replace(/^\|/, "")
      .replace(/\|$/, "")
      .split("|")
      .map((c) => c.trim());
  }
  function tableAligns(sep) {
    return splitTableRow(sep).map((c) => {
      const l = c.startsWith(":");
      const r = c.endsWith(":");
      return l && r ? "center" : r ? "right" : l ? "left" : "";
    });
  }
  function renderTable(header, aligns, rows) {
    const at = (idx) =>
      aligns[idx] ? ' style="text-align:' + aligns[idx] + '"' : "";
    let out = '<div class="table-wrap"><table><thead><tr>';
    header.forEach((c, idx) => {
      out += "<th" + at(idx) + ">" + renderInline(c) + "</th>";
    });
    out += "</tr></thead><tbody>";
    for (const row of rows) {
      out += "<tr>";
      for (let idx = 0; idx < header.length; idx++) {
        out +=
          "<td" +
          at(idx) +
          ">" +
          renderInline(row[idx] != null ? row[idx] : "") +
          "</td>";
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
        while (i < lines.length && !/^```\s*$/.test(lines[i]))
          code.push(lines[i++]);
        i++;
        html.push("<pre><code>" + code.join("\n") + "</code></pre>");
        continue;
      }
      if (isTableStart(line, lines[i + 1])) {
        const header = splitTableRow(line);
        const aligns = tableAligns(lines[i + 1]);
        i += 2;
        const rows = [];
        while (
          i < lines.length &&
          lines[i].indexOf("|") !== -1 &&
          !/^\s*$/.test(lines[i])
        ) {
          rows.push(splitTableRow(lines[i]));
          i++;
        }
        html.push(renderTable(header, aligns, rows));
        continue;
      }
      if (/^\s*[-*]\s+/.test(line)) {
        const items = [];
        while (i < lines.length && /^\s*[-*]\s+/.test(lines[i])) {
          items.push(
            "<li>" +
              renderInline(lines[i].replace(/^\s*[-*]\s+/, "")) +
              "</li>",
          );
          i++;
        }
        html.push("<ul>" + items.join("") + "</ul>");
        continue;
      }
      if (/^\s*\d+\.\s+/.test(line)) {
        const items = [];
        while (i < lines.length && /^\s*\d+\.\s+/.test(lines[i])) {
          items.push(
            "<li>" +
              renderInline(lines[i].replace(/^\s*\d+\.\s+/, "")) +
              "</li>",
          );
          i++;
        }
        html.push("<ol>" + items.join("") + "</ol>");
        continue;
      }
      const heading = line.match(/^(#{1,6})\s+(.*)$/);
      if (heading) {
        const lvl = heading[1].length;
        html.push(
          "<h" + lvl + ">" + renderInline(heading[2]) + "</h" + lvl + ">",
        );
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

  /* ---------------------------------------------------------------- *
   * Citations / sources
   * ---------------------------------------------------------------- */
  function renderSources(wrap, sources) {
    const citations = Array.isArray(sources.citations) ? sources.citations : [];
    if (!citations.length) return;
    const list = document.createElement("div");
    list.className = "citations";
    for (const c of citations) list.appendChild(renderCitation(c));
    wrap.appendChild(list);
  }

  // The backend emits root-relative source links (e.g. "/source/<id>#page=N")
  // when SOURCE_BASE_URL is unset. Resolve those against the API origin so they
  // open the locally-served PDF even when the widget is embedded on another
  // origin. Absolute URLs (remote article pages, configured SOURCE_BASE_URL)
  // are left untouched.
  function resolveUrl(url) {
    if (!url) return "";
    // Absolute http(s) or protocol-relative — safe to open as-is.
    if (/^https?:\/\//i.test(url) || url.slice(0, 2) === "//") return url;
    // Root-relative backend links resolve against the API origin.
    if (url.charAt(0) === "/") return API_BASE + url;
    // Reject anything else (javascript:, data:, mailto:, bare relative) so a
    // hostile citation URL renders as plain text instead of a live link.
    return "";
  }

  function linkOrText(label, url) {
    let node;
    const href = resolveUrl(url);
    if (href) {
      node = document.createElement("a");
      node.href = href;
      node.target = "_blank";
      node.rel = "noopener noreferrer";
    } else {
      node = document.createElement("span");
    }
    node.textContent = label;
    return node;
  }

  function renderCitation(c) {
    const item = document.createElement("div");
    item.className = "citation";

    const marker = document.createElement("span");
    marker.className = "citation__marker";
    marker.textContent = "[" + c.n + "]";
    item.appendChild(marker);

    const body = document.createElement("div");
    body.className = "citation__body";

    const title = linkOrText(
      c.title || c.document_id || c.type || "source",
      c.url,
    );
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
        also.appendChild(
          linkOrText(alt.title || alt.type || "source", alt.url),
        );
        if (idx < c.also_available.length - 1)
          also.appendChild(document.createTextNode(", "));
      });
      body.appendChild(also);
    }

    item.appendChild(body);
    return item;
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
      newChat: $("#new-chat"),
      close: $("#close"),
      expand: $("#expand"),
      messages: $("#messages"),
      welcome: $("#welcome"),
      cards: $("#cards"),
      input: $("#input"),
      send: $("#send"),
    };

    el.launcher.addEventListener("click", () =>
      isOpen ? closePanel() : openPanel(),
    );
    el.newChat.addEventListener("click", resetChat);
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
            <span class="brand__title">${escapeHtml(TITLE)}</span>
          </div>
          <div class="head__actions">
            <button id="new-chat" class="icon-btn" title="New chat" aria-label="New chat">
              <span class="new-chat__label">New chat</span>
            </button>
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
              placeholder="Ask about policies, best practices, or data insights"></textarea>
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
      /* ---- AI Sarthi palette (var names kept to minimise churn) ---- */
      --teri-green: #25705e;
      --teri-green-dark: #1c5648;
      --teri-green-soft: #e3f0ec;
      --teri-ink: #1f2330;
      --teri-dim: #6b7280;
      --teri-bg: #ffffff;
      --teri-surface: #f4f6fb;
      --teri-border: #e6e8ef;
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
      background: linear-gradient(135deg, #e6f2ed 0%, #eef2fa 38%, #f6f0f7 70%, #fef5f2 100%);
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

    /* Expanded: large floating dialog (not full-bleed), centred over a dimmed
       backdrop; content still centred in a readable column. */
    :host(.expanded) .panel {
      inset: 0;
      margin: auto;
      width: min(1100px, calc(100vw - 54px));
      height: min(900px, calc(100vh - 54px));
      max-width: calc(100vw - 64px);
      max-height: calc(100vh - 64px);
      border-radius: var(--radius);
      box-shadow: 0 0 0 100vmax rgba(15,23,42,.45), 0 24px 60px rgba(0,0,0,.35);
    }
    :host(.expanded) .messages,
    :host(.expanded) .composer {
      padding-left: max(20px, calc((100% - 1040px) / 2));
      padding-right: max(20px, calc((100% - 1040px) / 2));
    }
    :host(.expanded) .composer { padding-bottom: 26px; }
    :host(.expanded) .composer__box { max-width: 1040px; margin: 0 auto; border-radius: 18px; padding: 10px 10px 10px 18px; }
    :host(.expanded) .composer__input { min-height: 48px; }

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
    #new-chat {
      padding: 5px 12px;
      border: 1px solid var(--teri-border);
      border-radius: 8px;
      color: var(--teri-green);
    }
    #new-chat:hover { border-color: var(--teri-green); background: var(--teri-green-soft); }
    .new-chat__label { font-size: .82rem; font-weight: 600; }
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
    .welcome__title { margin: 0 0 4px; font-size: 1.4rem; font-weight: 700; letter-spacing: -.01em; color: var(--teri-ink); }
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
    :host(.expanded) .messages { background: linear-gradient(135deg, #e6f2ed 0%, #eef2fa 38%, #f6f0f7 70%, #fef5f2 100%); }
    :host(.expanded) .welcome { margin-top: 7vh; }
    :host(.expanded) .welcome__title { font-size: 2.25rem; margin-bottom: 8px; }
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

    /* ---- Working indicator: shimmering status word + bouncing dots ---- */
    .loader { display: inline-flex; align-items: center; gap: 9px; }
    .loader__text { display: inline-flex; }
    .loader__word {
      display: inline-block;
      font-weight: 600;
      background: linear-gradient(100deg,
        var(--teri-dim) 25%, var(--teri-green) 45%,
        var(--teri-green-dark) 55%, var(--teri-dim) 75%);
      background-size: 220% 100%;
      -webkit-background-clip: text;
              background-clip: text;
      -webkit-text-fill-color: transparent;
      color: transparent;
      animation: word-in .4s ease both, shimmer 2.2s linear infinite;
    }
    .loader__dots { display: inline-flex; align-items: center; gap: 3px; }
    .loader__dots i {
      width: 4px; height: 4px;
      border-radius: 50%;
      background: var(--teri-green);
      animation: dot-bounce 1.2s ease-in-out infinite;
    }
    .loader__dots i:nth-child(2) { animation-delay: .18s; }
    .loader__dots i:nth-child(3) { animation-delay: .36s; }

    @keyframes shimmer {
      0%   { background-position: 220% 0; }
      100% { background-position: -20% 0; }
    }
    @keyframes word-in {
      from { opacity: 0; transform: translateY(3px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes dot-bounce {
      0%, 80%, 100% { opacity: .3; transform: translateY(0); }
      40% { opacity: 1; transform: translateY(-3px); }
    }
    @media (prefers-reduced-motion: reduce) {
      .loader__word, .loader__dots i { animation: none; }
      .loader__word { -webkit-text-fill-color: var(--teri-green); color: var(--teri-green); }
    }

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

    .bubble .table-wrap { overflow-x: auto; margin: 0 0 .55rem; }
    .bubble table { border-collapse: collapse; width: 100%; font-size: .86em; }
    .bubble th, .bubble td {
      border: 1px solid var(--teri-border);
      padding: 6px 10px;
      text-align: left;
      vertical-align: top;
    }
    .bubble thead th { background: var(--teri-surface); font-weight: 700; }
    .bubble tbody tr:nth-child(even) { background: rgba(0,0,0,.025); }

    /* ---- Citations ---- */
    /* Horizontal, scrollable strip so sources don't eat vertical space. */
    .citations {
      margin-top: 6px;
      display: flex;
      flex-direction: row;
      gap: 8px;
      width: 100%;
      overflow-x: auto;
      overflow-y: hidden;
      padding-bottom: 4px;
      scroll-snap-type: x proximity;
    }
    .citations::-webkit-scrollbar { height: 6px; }
    .citations::-webkit-scrollbar-thumb { background: var(--teri-border); border-radius: 999px; }
    .citation {
      display: flex; gap: 7px; font-size: .8rem;
      background: var(--teri-bg);
      border: 1px solid var(--teri-border);
      border-radius: 8px;
      padding: 7px 9px;
      flex: 0 0 220px;
      width: 220px;
      scroll-snap-align: start;
    }
    .citation__marker { color: var(--teri-green-dark); font-weight: 600; flex-shrink: 0; }
    .citation__body { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
    .citation__title { color: var(--teri-ink); word-break: break-word; }
    a.citation__title { color: var(--teri-green-dark); text-decoration: none; }
    a.citation__title:hover { text-decoration: underline; }
    .citation__detail, .citation__also { color: var(--teri-dim); font-size: .74rem; }
    .citation__also a { color: var(--teri-green-dark); text-decoration: none; }
    .citation__also a:hover { text-decoration: underline; }

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
