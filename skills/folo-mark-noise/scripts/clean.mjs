import { readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const pageSize = 100;
const markSize = 20;
const pageCap = 100;

export function feedIdFromYaml(text) {
  const match = String(text).match(/^feedId:\s*["']?([^"'\s#]+)["']?\s*$/m);
  if (!match) fail("feedId");
  return match[1];
}

export function readIds(text) {
  let payload;
  try {
    payload = JSON.parse(text);
  } catch {
    fail("ids json");
  }
  if (!Array.isArray(payload)) fail("ids array");
  const ids = [];
  const seen = new Set();
  for (const item of payload) {
    const id = item == null ? "" : String(item).trim();
    if (!id || seen.has(id)) continue;
    seen.add(id);
    ids.push(id);
  }
  return ids;
}

export function entryFromRow(item) {
  const entry = item?.entries ?? item;
  const id = entry?.id == null ? "" : String(entry.id).trim();
  if (!id) return null;
  return {
    id,
    title: entry.title || "",
    description: entry.description || "",
    categories: Array.isArray(entry.categories) ? entry.categories.map((value) => String(value)) : [],
    url: entry.url || "",
    author: entry.author || "",
  };
}

export function publishedAtOf(item) {
  const entry = item?.entries ?? item;
  return entry?.publishedAt ? String(entry.publishedAt) : "";
}

export async function pullUnread(fetchPage) {
  const seen = new Set();
  const entries = [];
  let cursor = "";
  for (let page = 0; page < pageCap; page++) {
    const rows = await fetchPage(cursor);
    if (!Array.isArray(rows)) fail("entries shape");
    let added = 0;
    for (const item of rows) {
      const entry = entryFromRow(item);
      if (!entry || seen.has(entry.id)) continue;
      seen.add(entry.id);
      entries.push(entry);
      added += 1;
    }
    if (rows.length < pageSize) return entries;
    const next = publishedAtOf(rows.at(-1));
    if (!next || next === cursor || added === 0) fail("cursor");
    cursor = next;
  }
  fail("pages");
}

function fail(message) {
  if (message) console.error(message);
  const error = new Error(message || "stop");
  error.code = "CLEAN_STOP";
  throw error;
}

function rowsFrom(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.data)) return payload.data;
  if (Array.isArray(payload?.data?.entries)) return payload.data.entries;
  return null;
}

function loadApi() {
  const config = JSON.parse(readFileSync(join(homedir(), ".folo", "config.json"), "utf8"));
  if (!config.token) fail("missing token");
  return {
    token: config.token,
    apiUrl: String(config.apiUrl || "https://api.folo.is").replace(/\/$/, ""),
  };
}

async function postJson(api, path, body) {
  const response = await fetch(`${api.apiUrl}${path}`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      cookie: `__Secure-better-auth.session_token=${api.token}; better-auth.session_token=${api.token}`,
    },
    body: JSON.stringify(body),
  });
  const text = await response.text();
  let payload = null;
  try {
    payload = text ? JSON.parse(text) : null;
  } catch {
    payload = null;
  }
  if (!response.ok || (payload && typeof payload.code === "number" && payload.code !== 0)) {
    fail(`${path} ${response.status}`);
  }
  return payload;
}

async function fetchPage(api, feedId, cursor) {
  const body = { feedId, limit: pageSize, read: false };
  if (cursor) body.publishedAfter = cursor;
  const payload = await postJson(api, "/entries", body);
  const rows = rowsFrom(payload);
  if (!rows) fail("entries shape");
  return rows;
}

async function markChunk(api, ids) {
  try {
    await postJson(api, "/reads", { entryIds: ids });
  } catch (error) {
    if (!error || error.code !== "CLEAN_STOP") console.error(error instanceof Error ? error.message : "reads");
    try {
      await postJson(api, "/reads", { entryIds: ids });
    } catch (retryError) {
      if (!retryError || retryError.code !== "CLEAN_STOP") {
        console.error(retryError instanceof Error ? retryError.message : "reads");
      }
      fail("reads");
    }
  }
}

async function main() {
  const command = process.argv[2];
  const yamlPath = process.argv[3];
  if ((command !== "list" && command !== "mark") || !yamlPath) {
    fail("usage: node scripts/clean.mjs list|mark <yaml> [ids.json]");
  }
  const feedId = feedIdFromYaml(readFileSync(yamlPath, "utf8"));
  const api = loadApi();
  if (command === "list") {
    const entries = await pullUnread((cursor) => fetchPage(api, feedId, cursor));
    process.stdout.write(`${JSON.stringify(entries, null, 2)}\n`);
    return;
  }
  const idsPath = process.argv[4];
  if (!idsPath) fail("usage: node scripts/clean.mjs mark <yaml> <ids.json>");
  const ids = readIds(readFileSync(idsPath, "utf8"));
  const before = (await pullUnread((cursor) => fetchPage(api, feedId, cursor))).length;
  for (let index = 0; index < ids.length; index += markSize) {
    await markChunk(api, ids.slice(index, index + markSize));
  }
  const after = (await pullUnread((cursor) => fetchPage(api, feedId, cursor))).length;
  process.stdout.write(`${before}\n${after}\n`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  main().catch((error) => {
    if (!error || error.code !== "CLEAN_STOP") console.error(error instanceof Error ? error.message : "clean");
    process.exitCode = 1;
  });
}
