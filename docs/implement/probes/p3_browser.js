#!/usr/bin/env node
/**
 * Drive the real Agent Inbox in a real browser, and report what rendered.
 *
 * Answers  — the falsifier's middle clause. "The interrupt list does not render" is a claim about
 *            a browser, and Agent Inbox is a client-only Next.js app: `src/app/page.tsx` begins
 *            `"use client"`, there is no `src/app/api/**`, no middleware and an empty
 *            `next.config.mjs`, so no thread data ever passes through the Next server. Asserting
 *            on `curl` output and calling it "renders" would be an inference dressed as a
 *            reading. This opens the page, lets React run, and reads the DOM.
 *
 * Does not — prove anything about the protocol. `p3_protocol.py` is the other half. If the two
 *            disagree, the disagreement localises to the client, which is the point of splitting
 *            them.
 *
 * Needs no packages. Node 24 has a global WebSocket, and Chrome speaks the DevTools Protocol over
 * one, so the whole driver is this file plus a browser that is already installed. Playwright and
 * Puppeteer are not present on this machine and installing one would have meant reporting a
 * result obtained with a tool brought in for the occasion.
 *
 * **What counts as rendering, decided before the run.** Agent Inbox renders *something* for every
 * payload it cannot parse: `contexts/utils.ts` substitutes an interrupt whose action is the
 * sentinel `improper_schema`, and `interrupted-inbox-item.tsx:30-31` titles such a row with the
 * literal word "Interrupt". A screenshot showing rows is therefore not evidence. The three
 * discriminators below were written from the source before the probe ran:
 *
 *   1. the row title equals the `action_request.action` the graph emitted, and is not "Interrupt";
 *   2. the status pill reads "Requires Action", not "Ignore" -- `statuses.tsx:20-44` prints
 *      "Ignore" when `allow_ignore` is the only flag set, which is what the synthesised
 *      placeholder carries;
 *   3. opening the row shows the controls the interrupt's own config allows, and no others.
 *
 * Exit 0 what was asked for was observed, 1 a falsifier fired, 2 a setup fault.
 */

"use strict";

const CDP_PORT = Number(process.env.P3_CDP_PORT || 9333);

// ---------------------------------------------------------------- a CDP client, and nothing more
async function connect(port) {
  const targets = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  let page = targets.find((t) => t.type === "page");
  if (!page) page = await (await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, { method: "PUT" })).json();
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise((ok, bad) => { ws.onopen = ok; ws.onerror = () => bad(new Error("cannot open a CDP socket")); });

  let id = 0;
  const pending = new Map();
  const events = [];
  ws.onmessage = (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.id !== undefined && pending.has(msg.id)) {
      const { ok, bad } = pending.get(msg.id);
      pending.delete(msg.id);
      msg.error ? bad(new Error(JSON.stringify(msg.error))) : ok(msg.result);
    } else if (msg.method) events.push(msg);
  };
  const send = (method, params = {}) =>
    new Promise((ok, bad) => { const n = ++id; pending.set(n, { ok, bad }); ws.send(JSON.stringify({ id: n, method, params })); });

  return {
    events,
    send,
    close: () => ws.close(),
    async evaluate(expression) {
      const r = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
      if (r.exceptionDetails) throw new Error("page threw: " + r.exceptionDetails.text);
      return r.result.value;
    },
    async goto(url, settleMs = 1500) {
      await send("Page.enable");
      await send("Page.navigate", { url });
      await sleep(settleMs);
    },
  };
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function args() {
  const out = {};
  for (let i = 2; i < process.argv.length; i += 2) out[process.argv[i].replace(/^--/, "")] = process.argv[i + 1];
  return out;
}

// ---------------------------------------------------------------- page-side helpers
//
// These run inside the page. React owns every input here, so a plain `el.value = x` is invisible
// to it: React caches the last value it set on the node and skips the change event when the two
// still match. Going through the prototype's native setter and then dispatching a bubbling
// `input` event is what makes React see a keystroke.
const PAGE_HELPERS = `
window.__p3 = {
  leaves() { return [...document.querySelectorAll('*')].filter(e => e.children.length === 0); },
  byText(t) { return this.leaves().find(e => (e.innerText || '').trim() === t); },
  clickRow(title) {
    const el = this.byText(title);
    if (!el) return 'row not found';
    let n = el;
    for (let i = 0; i < 8 && n; i++) {
      n = n.parentElement;
      if (n && n.className.toString().includes('cursor-pointer')) { n.click(); return 'clicked'; }
    }
    return 'no clickable ancestor';
  },
  clickButton(label) {
    const b = [...document.querySelectorAll('button')].find(x => (x.innerText || '').trim() === label);
    if (!b) return 'button not found: ' + label;
    if (b.disabled) return 'button disabled: ' + label;
    b.click();
    return 'clicked';
  },
  buttons() { return [...document.querySelectorAll('button')].map(b => (b.innerText || '').trim()).filter(Boolean); },
  type(selector, value, nth) {
    const els = [...document.querySelectorAll(selector)];
    const el = els[nth || 0];
    if (!el) return 'no ' + selector + ' at index ' + (nth || 0) + ' (found ' + els.length + ')';
    const proto = el instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
    Object.getOwnPropertyDescriptor(proto, 'value').set.call(el, value);
    el.dispatchEvent(new Event('input', { bubbles: true }));
    return 'typed';
  },
  crashed() { return document.body.innerText.includes("This page couldn") || document.body.innerText.includes('Application error'); }
};
'ready'`;

async function main() {
  const a = args();
  const appUrl = (a.url || "http://localhost:3200").replace(/\/$/, "");
  const deployment = a.deployment || "http://127.0.0.1:2027";
  const graph = a.graph || "p3_hitl";
  const token = a.token || "";
  const expect = a.expect || "";          // the action name the row must be titled with
  const act = a.act || "";                // accept | edit | response | ignore, optional
  const report = { app_url: appUrl, deployment, graph, expected_action: expect, acted: act || null };

  const c = await connect(CDP_PORT);
  await c.send("Runtime.enable");
  const problems = [];
  c.events.length = 0;

  // The two localStorage keys Agent Inbox reads on mount, seeded rather than typed into the Add
  // Inbox dialog. The dialog ends in `window.location.reload()`, and driving it would be testing
  // a form rather than the connection. localStorage is per ORIGIN: seeding at 127.0.0.1 and then
  // loading localhost writes to a store the app never reads, which cost a confused half hour and
  // is why the seed and the load below use one variable.
  await c.goto(appUrl + "/");
  const inbox = { id: "p3-inbox-0001", graphId: graph, deploymentUrl: deployment,
                  name: "P3", selected: true, createdAt: "2026-09-21T00:00:00.000Z" };
  await c.evaluate(
    `localStorage.setItem("inbox:agent_inboxes", ${JSON.stringify(JSON.stringify([inbox]))});` +
    `localStorage.setItem("inbox:langchain_api_key", ${JSON.stringify(token)}); "seeded"`);
  await c.goto(appUrl + "/", 500);
  await sleep(Number(a.settle || 9000));
  await c.evaluate(PAGE_HELPERS);

  // ------------------------------------------------------------ the list
  const bodyText = await c.evaluate("document.body.innerText");
  report.list_empty = bodyText.includes("No threads found");
  report.row_titles = await c.evaluate(
    `JSON.stringify([...new Set(window.__p3.leaves().map(e => (e.innerText||'').trim()).filter(t => t.startsWith('p3_')))])`
  ).then(JSON.parse);
  report.pill_requires_action = bodyText.includes("Requires Action");
  report.placeholder_rows = (bodyText.match(/\bInterrupt\b/g) || []).length;

  if (report.list_empty) problems.push("the inbox rendered 'No threads found' against a deployment that has interrupted threads");
  if (expect && !report.row_titles.includes(expect))
    problems.push(`no row is titled '${expect}'; titles seen: ${JSON.stringify(report.row_titles)}`);

  // ------------------------------------------------------------ the thread
  if (expect) {
    report.open = await c.evaluate(`window.__p3.clickRow(${JSON.stringify(expect)})`);
    await sleep(5000);
    report.detail_crashed = await c.evaluate("window.__p3.crashed()");
    report.detail_text = (await c.evaluate("document.body.innerText")).slice(0, 1200);
    report.detail_buttons = await c.evaluate("JSON.stringify(window.__p3.buttons())").then(JSON.parse);
    report.detail_textareas = await c.evaluate("document.querySelectorAll('textarea').length");
    report.page_errors = c.events
      .filter((e) => e.method === "Runtime.exceptionThrown")
      .map((e) => (e.params.exceptionDetails.exception?.description || e.params.exceptionDetails.text).split("\n")[0])
      .slice(0, 5);
    if (report.detail_crashed)
      problems.push("the thread detail view crashed, so no decision can be made from the inbox: " +
                    (report.page_errors[0] || "no exception captured"));
  }

  // ------------------------------------------------------------ one decision, if asked for
  if (act && !report.detail_crashed) {
    if (act === "response") {
      // The LAST textarea, not the first. With all four flags on the page renders one textarea
      // per argument in the Edit/Accept card and then one more in "Respond to assistant"; typing
      // into index 0 edits an argument and leaves the response box empty, which then submits as
      // an edit. Counted from `detail_textareas` rather than assumed.
      const last = (await c.evaluate("document.querySelectorAll('textarea').length")) - 1;
      report.typed = await c.evaluate(
        `window.__p3.type('textarea', 'Rejected from the inbox: this write needs a WBS node first.', ${last})`);
      await sleep(600);
      report.clicked = await c.evaluate(`window.__p3.clickButton('Send Response')`);
    } else if (act === "edit") {
      report.typed = await c.evaluate(`window.__p3.type('textarea', 'replace', 0)`);
      await sleep(600);
      report.clicked = await c.evaluate(`window.__p3.clickButton('Submit')`);
    } else if (act === "accept") {
      report.clicked = await c.evaluate(`window.__p3.clickButton('Accept')`);
    } else if (act === "ignore") {
      report.clicked = await c.evaluate(`window.__p3.clickButton('Ignore')`);
    } else {
      problems.push(`unknown --act '${act}'`);
    }
    await sleep(Number(a.after || 9000));
    const after = await c.evaluate("document.body.innerText");
    // The success toast fires BEFORE the first stream chunk is read
    // (`use-interrupted-actions.tsx:207-224`), so it is not evidence that the graph resumed. The
    // caller re-reads the thread from Aegra; that is the evidence.
    report.saw_success_toast = after.includes("Response submitted successfully");
    report.saw_stream_finished = after.includes("Successfully finished Graph invocation");
    report.returned_to_list = after.includes("Requires Action") || after.includes("No threads found");
  }

  report.problems = problems;
  if (a.out) require("fs").writeFileSync(a.out, JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
  c.close();
  return problems.length ? 1 : 0;
}

main().then((code) => process.exit(code)).catch((err) => {
  console.error("setup fault: " + err.message);
  process.exit(2);
});
