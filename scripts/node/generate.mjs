// Generate a dataset with Node.js 18 or newer (no packages needed).
//
//   export GRD_API_KEY=grd_live_...
//   node generate.mjs
//
// Starts a dataset from a description, waits for it and saves the file.
// API reference: https://generaterealdata.com/docs/api/
import { writeFile } from "node:fs/promises";

const API = "https://generaterealdata.com/api/v1";
const KEY = process.env.GRD_API_KEY;
if (!KEY) {
  console.error("Set the GRD_API_KEY environment variable to your API key first.");
  process.exit(1);
}
const headers = { Authorization: `Bearer ${KEY}`, "Content-Type": "application/json" };
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/** One request. Waits and retries when rate-limited or while another dataset is still running. */
async function call(method, path, body) {
  for (;;) {
    const res = await fetch(API + path, { method, headers, body: body ? JSON.stringify(body) : undefined });
    const data = await res.json();
    if (res.status === 429 || data?.error?.code === "run_in_progress") {
      await sleep(1000 * Number(res.headers.get("Retry-After") ?? 15));
      continue;
    }
    if (!res.ok) throw new Error(`${data.error.code}: ${data.error.message}`);
    return data;
  }
}

/** Starts a dataset, waits until it is ready and saves the file. Returns the final status. */
export async function generate(spec, outPath) {
  let ds = await call("POST", "/datasets", spec);
  while (!["ready", "failed"].includes(ds.status)) {
    await sleep(5000);
    ds = await call("GET", `/datasets/${ds.id}`);
  }
  if (ds.status === "failed") throw new Error(`${ds.error.code}: ${ds.error.message}`);
  // The download address answers with a redirect to the file. The file host must not receive the API key,
  // so the redirect is followed by hand, without the Authorization header.
  const hop = await fetch(`${API}/datasets/${ds.id}/download`, { headers, redirect: "manual" });
  const location = hop.headers.get("location");
  if (!location) throw new Error(`Download failed: ${hop.status}`);
  const file = await fetch(location);
  if (!file.ok) throw new Error(`Download failed: ${file.status}`);
  await writeFile(outPath, Buffer.from(await file.arrayBuffer()));
  return ds;
}

const ds = await generate(
  {
    mode: "prompt",
    description: "A project tracker with teams, projects, tasks and comments",
    rows: 2000,
    format: "json",
    seed: 7,
  },
  "project_tracker.json",
);
console.log(`${ds.rows_generated} rows:`, ds.rows_per_table);
console.log(`schema_id ${ds.schema_id}, seed ${ds.seed} (send both to get the same data again)`);
