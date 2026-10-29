import { spawn } from "node:child_process";
import { appendFileSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { createServer } from "node:http";
import { homedir, tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const empty = "";

export function buildResult(feedId, title, entries, decisions) {
  const chosen = [];
  for (const entry of entries) {
    const decision = decisions?.[entry.id];
    if (decision !== "pick" && decision !== "ban") continue;
    chosen.push({
      id: entry.id,
      title: entry.title,
      description: entry.description,
      categories: entry.categories,
      url: entry.url,
      author: entry.author,
      decision,
    });
  }
  return { feedId, title, entries: chosen };
}

export function choicesPath(feedId) {
  return join(tmpdir(), "swxs-folo-ban-pick", String(feedId), "choices.yaml");
}

function yamlQuote(value) {
  return `"${String(value ?? "").replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\r/g, "\\r").replace(/\n/g, "\\n").replace(/\t/g, "\\t")}"`;
}

function yamlUnquote(body) {
  return body.replace(/\\(.)/g, (_, ch) => {
    if (ch === "n") return "\n";
    if (ch === "r") return "\r";
    if (ch === "t") return "\t";
    return ch;
  });
}

export function readChoices(text) {
  const decisions = {};
  const order = [];
  let current = null;
  for (const line of String(text ?? "").split(/\n/)) {
    const idLine = line.match(/^- id: (?:"((?:\\.|[^"\\])*)"|([^\s#]+))\s*$/);
    if (idLine) {
      current = yamlUnquote(idLine[1] != null ? idLine[1] : idLine[2]);
      continue;
    }
    const decisionLine = line.match(/^  decision: (pick|ban)\s*$/);
    if (!decisionLine || current == null) continue;
    const existing = order.indexOf(current);
    if (existing !== -1) order.splice(existing, 1);
    order.push(current);
    decisions[current] = decisionLine[1];
    current = null;
  }
  return { decisions, order };
}

function choiceItem(id, decision) {
  return `- id: ${yamlQuote(id)}\n  decision: ${decision}\n`;
}

function loadChoices(file) {
  try {
    return readChoices(readFileSync(file, "utf8"));
  } catch (error) {
    if (error && error.code === "ENOENT") return { decisions: {}, order: [] };
    throw error;
  }
}

function appendChoice(file, id, decision) {
  mkdirSync(dirname(file), { recursive: true });
  appendFileSync(file, choiceItem(id, decision));
}

function writeChoices(file, saved) {
  mkdirSync(dirname(file), { recursive: true });
  writeFileSync(file, saved.order.map((id) => choiceItem(id, saved.decisions[id])).join(""));
}

export function resultYaml(result) {
  const lines = [`feedId: ${yamlQuote(result.feedId)}`, `title: ${yamlQuote(result.title)}`, "entries:"];
  if (!result.entries.length) {
    lines[2] = "entries: []";
    return `${lines.join("\n")}\n`;
  }
  for (const entry of result.entries) {
    lines.push(`  - id: ${yamlQuote(entry.id)}`);
    lines.push(`    title: ${yamlQuote(entry.title)}`);
    lines.push(`    description: ${yamlQuote(entry.description)}`);
    if (!entry.categories?.length) lines.push("    categories: []");
    else {
      lines.push("    categories:");
      for (const category of entry.categories) lines.push(`      - ${yamlQuote(category)}`);
    }
    lines.push(`    url: ${yamlQuote(entry.url)}`);
    lines.push(`    author: ${yamlQuote(entry.author)}`);
    lines.push(`    decision: ${entry.decision}`);
  }
  return `${lines.join("\n")}\n`;
}

function fail(message) {
  if (message) console.error(message);
  const error = new Error(message || "stop");
  error.code = "BAN_PICK_STOP";
  throw error;
}

function page(entries, decisions) {
  const payload = JSON.stringify({ entries, decisions: decisions || {} }).replace(/</g, "\\u003c");
  return `<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>ban/pick</title>
<style>
  * { box-sizing: border-box; }
  html, body { margin: 0; height: 100%; }
  body { background: #2a2224; color: #f4ecdf; font: 16px/1.45 "Segoe UI", "Microsoft YaHei", sans-serif; }
  button { font: inherit; }
  h2, p { margin: 0; }
  .split { display: grid; grid-template-columns: 1fr 1fr; min-height: 100vh; position: relative; }
  .slab { border: 0; cursor: pointer; color: #f4ecdf; display: flex; flex-direction: column; justify-content: center; gap: 10px; }
  .slab.ban { background: #3c292d; align-items: flex-start; padding-left: 5vw; }
  .slab.pick { background: #1e3832; align-items: flex-end; padding-right: 5vw; }
  .slab strong { font-size: 32px; font-weight: 500; letter-spacing: 0.14em; }
  .slab small { letter-spacing: 0.28em; opacity: 0.68; font-size: 12px; }
  .slab.ban:hover { background: #4a3238; }
  .slab.pick:hover { background: #274840; }
  .slab:disabled { cursor: default; }
  .sheet {
    position: absolute; left: 50%; top: 46%; transform: translate(-50%, -54%);
    width: min(660px, 62vw); background: #fbf7f1; color: #1c1915;
    padding: 54px 51px 42px; box-shadow: 0 28px 70px rgba(0,0,0,.28);
  }
  .sheet h2 { font-family: Georgia, "Palatino Linotype", serif; font-size: 48px; font-weight: 500; line-height: 1.15; margin-bottom: 18px; }
  .kicker { font-size: 12px; letter-spacing: 0.18em; color: #8a8175; margin-bottom: 14px; }
  .cats { margin: 0 0 20px; font-size: 16px; letter-spacing: 0.06em; color: #6f675e; }
  .desc { font-size: 22px; line-height: 1.55; color: #3f3a34; }
  .meta { margin-top: 18px; font-size: 12px; letter-spacing: 0.04em; color: #91897f; }
  .dots { position: fixed; left: 0; right: 0; bottom: 28px; display: flex; justify-content: center; flex-wrap: wrap; z-index: 4; }
  .dots button { border: 0; background: transparent; color: rgba(244,236,223,.38); font-size: 20px; line-height: 1; padding: 4px 2px; cursor: pointer; }
  .dots button.pick { color: #b7d7c6; }
  .dots button.ban { color: #f0c2c6; }
  .dots button.current { transform: translateY(-4px) scale(1.55); color: #fff; }
</style>
</head>
<body>
<div id="app"></div>
<div class="dots" id="dots"></div>
<script id="payload" type="application/json">${payload}</script>
<script>
const DATA = JSON.parse(document.getElementById("payload").textContent);
const ENTRIES = DATA.entries;
const state = { marks: { ...DATA.decisions }, cursor: 0, done: false, saving: false };
const firstOpen = ENTRIES.findIndex((item) => state.marks[item.id] !== "pick" && state.marks[item.id] !== "ban");
state.cursor = firstOpen === -1 ? 0 : firstOpen;
function post(path, body) {
  return fetch(path, { method: "POST", headers: { "content-type": "application/json" }, body: body ? JSON.stringify(body) : "{}" });
}
function choose(kind) {
  if (state.done || state.saving) return;
  const entry = ENTRIES[state.cursor];
  const index = state.cursor;
  state.saving = true;
  render();
  post("/mark", { id: entry.id, decision: kind, finish: index === ENTRIES.length - 1 }).then((res) => {
    if (!res.ok) throw new Error("mark");
    return res.json();
  }).then((body) => {
    if (!body.ok) throw new Error("mark");
    state.marks[entry.id] = kind;
    state.saving = false;
    if (body.done) {
      state.done = true;
      render();
      return;
    }
    if (index < ENTRIES.length - 1) state.cursor = index + 1;
    render();
  }).catch(() => {
    state.saving = false;
    render();
  });
}
function jump(index) {
  if (state.done || state.saving) return;
  state.cursor = index;
  render();
}
function slab(kind, zh, en) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "slab " + kind;
  button.disabled = state.done || state.saving;
  const strong = document.createElement("strong");
  strong.textContent = zh;
  const small = document.createElement("small");
  small.textContent = en;
  button.append(strong, small);
  button.onclick = () => choose(kind);
  return button;
}
function render() {
  const entry = ENTRIES[state.cursor];
  const app = document.getElementById("app");
  const split = document.createElement("div");
  split.className = "split";
  const sheet = document.createElement("div");
  sheet.className = "sheet";
  if (state.done) {
    const title = document.createElement("h2");
    title.textContent = "已记下";
    sheet.append(title);
  } else {
    const kicker = document.createElement("div");
    kicker.className = "kicker";
    kicker.textContent = String(state.cursor + 1).padStart(2, "0") + "  /  " + ENTRIES.length;
    const title = document.createElement("h2");
    title.textContent = entry.title;
    const cats = document.createElement("div");
    cats.className = "cats";
    cats.textContent = entry.categories.length ? entry.categories.join("   ·   ") : "categories 为空";
    const desc = document.createElement("p");
    desc.className = "desc";
    desc.textContent = entry.description || "没有 description";
    const meta = document.createElement("p");
    meta.className = "meta";
    meta.textContent = "url  " + (entry.url || "—") + "     author  " + (entry.author || "—");
    sheet.append(kicker, title, cats, desc, meta);
  }
  split.append(slab("ban", "清理", "Ban"), slab("pick", "留下", "Pick"), sheet);
  app.replaceChildren(split);
  const dots = document.getElementById("dots");
  dots.replaceChildren();
  ENTRIES.forEach((item, index) => {
    const dot = document.createElement("button");
    dot.type = "button";
    dot.textContent = "•";
    dot.title = item.title;
    const mark = state.marks[item.id];
    if (mark) dot.classList.add(mark);
    if (!state.done && index === state.cursor) dot.classList.add("current");
    dot.onclick = () => jump(index);
    dots.append(dot);
  });
}
render();
</script>
</body>
</html>`;
}

function rowsFrom(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.data)) return payload.data;
  if (Array.isArray(payload?.data?.entries)) return payload.data.entries;
  return null;
}

async function loadUnread(feedId) {
  const config = JSON.parse(readFileSync(join(homedir(), ".folo", "config.json"), "utf8"));
  const token = config.token;
  if (!token) fail("missing token");
  const apiUrl = (config.apiUrl || "https://api.folo.is").replace(/\/$/, empty);
  const response = await fetch(`${apiUrl}/entries`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      cookie: `__Secure-better-auth.session_token=${token}; better-auth.session_token=${token}`,
    },
    body: JSON.stringify({ feedId, limit: 50, read: false }),
  });
  const text = await response.text();
  if (!response.ok) fail(`entries ${response.status}`);
  let payload = null;
  try {
    payload = JSON.parse(text);
  } catch {
    fail("entries json");
  }
  const rows = rowsFrom(payload);
  if (!rows) fail("entries shape");
  const entries = rows.slice(0, 50).map((item) => {
    const entry = item.entries ?? item;
    return {
      id: String(entry.id ?? empty),
      title: entry.title || empty,
      description: entry.description || empty,
      categories: Array.isArray(entry.categories) ? entry.categories : [],
      url: entry.url || empty,
      author: entry.author || empty,
      channelTitle: item.subscriptions?.title || item.feeds?.title || empty,
    };
  }).filter((entry) => entry.id);
  const title = entries.find((entry) => entry.channelTitle)?.channelTitle || empty;
  return {
    title,
    entries: entries.map(({ channelTitle, ...entry }) => entry),
  };
}

function readJson(req) {
  return new Promise((resolveBody, reject) => {
    const chunks = [];
    req.on("data", (chunk) => chunks.push(chunk));
    req.on("end", () => {
      const text = Buffer.concat(chunks).toString("utf8");
      if (!text) {
        resolveBody({});
        return;
      }
      try {
        resolveBody(JSON.parse(text));
      } catch (error) {
        reject(error);
      }
    });
    req.on("error", reject);
  });
}

export function serveBanPick(feedId, title, entries, options = {}) {
  let finished = false;
  const choicesFile = options.choicesFile || choicesPath(feedId);
  const html = page(entries, options.decisions || {});
  let resolveUrl = () => {};
  const opened = new Promise((resolve) => {
    resolveUrl = resolve;
  });
  const server = createServer((req, res) => {
    readJson(req).then((body) => {
      if (req.method === "GET" && (req.url === "/" || req.url.startsWith("/?"))) {
        res.writeHead(200, { "content-type": "text/html; charset=utf-8" });
        res.end(html);
        return;
      }
      if (req.method !== "POST" || req.url !== "/mark") {
        res.writeHead(404);
        res.end();
        return;
      }
      const id = String(body.id || "");
      const decision = body.decision;
      if (!entries.some((entry) => entry.id === id) || (decision !== "pick" && decision !== "ban")) {
        res.writeHead(400);
        res.end();
        return;
      }
      appendChoice(choicesFile, id, decision);
      const finish = body.finish === true;
      if (!finish) {
        res.writeHead(200, { "content-type": "application/json" });
        res.end(JSON.stringify({ ok: true, done: false }));
        return;
      }
      if (finished) return;
      finished = true;
      const saved = loadChoices(choicesFile);
      writeChoices(choicesFile, saved);
      const output = resultYaml(buildResult(feedId, title, entries, saved.decisions));
      res.writeHead(200, { "content-type": "application/json", connection: "close" });
      res.end(JSON.stringify({ ok: true, done: true }), () => {
        process.stdout.write(output, () => process.exit(0));
      });
    }).catch(() => {
      if (res.headersSent) return;
      res.writeHead(400);
      res.end();
    });
  });
  server.listen(0, "127.0.0.1", () => {
    const { port } = server.address();
    const url = `http://127.0.0.1:${port}/`;
    console.error(`open ${url} entries ${entries.length}`);
    resolveUrl(url);
    if (options.open !== false) {
      spawn("cmd", ["/c", "start", "", url], { detached: true, stdio: "ignore", windowsHide: true }).unref();
    }
  });
  const stop = () => {
    if (finished) return;
    finished = true;
    server.close();
    process.exit(1);
  };
  process.on("SIGINT", stop);
  process.on("SIGTERM", stop);
  return opened;
}

function emitSaved(feedId, title, entries, choicesFile, saved) {
  writeChoices(choicesFile, saved);
  const output = resultYaml(buildResult(feedId, title, entries, saved.decisions));
  process.stdout.write(output, () => process.exit(0));
}

async function main() {
  const feedId = process.argv[2];
  if (!feedId) fail("usage: node scripts/ban-pick.mjs <feedId>");
  let loaded;
  try {
    loaded = await loadUnread(feedId);
  } catch (error) {
    if (!error || error.code !== "BAN_PICK_STOP") {
      console.error(error instanceof Error ? error.message : "entries");
    }
    process.exitCode = 1;
    return;
  }
  if (!loaded.entries.length) {
    process.exitCode = 1;
    return;
  }
  const choicesFile = choicesPath(feedId);
  const saved = loadChoices(choicesFile);
  const last = loaded.entries[loaded.entries.length - 1];
  if (saved.decisions[last.id] === "pick" || saved.decisions[last.id] === "ban") {
    emitSaved(feedId, loaded.title, loaded.entries, choicesFile, saved);
    return;
  }
  serveBanPick(feedId, loaded.title, loaded.entries, { choicesFile, decisions: saved.decisions });
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  main();
}
