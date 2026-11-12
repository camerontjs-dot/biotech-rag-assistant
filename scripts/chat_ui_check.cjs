// Chromium driver for scripts/chat_ui_check.py. Not run in CI (needs Playwright + Chromium).
// Usage: node scripts/chat_ui_check.cjs '<json config from chat_ui_check.py>'
"use strict";
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const cfg = JSON.parse(process.argv[2]);
const results = [];
let failures = 0;

function check(name, condition, detail) {
  const ok = Boolean(condition);
  results.push({ name, ok, detail: detail || null });
  if (!ok) failures += 1;
  console.log(`${ok ? "PASS" : "FAIL"} ${name}${detail && !ok ? ` (${detail})` : ""}`);
}

async function shot(page, name) {
  await page.screenshot({ path: path.join(cfg.out, name), fullPage: true });
}

function watch(page) {
  const state = { dialogs: [], errors: [] };
  page.on("dialog", async (d) => { state.dialogs.push(d.message()); await d.dismiss(); });
  page.on("console", (m) => { if (m.type() === "error") state.errors.push(m.text()); });
  page.on("pageerror", (e) => state.errors.push(String(e)));
  return state;
}

async function ask(page, text) {
  const before = await page.locator("article.msg.assistant").count();
  await page.fill("#msg", text);
  await page.click("#send");
  await page.waitForFunction((n) => {
    const all = document.querySelectorAll("article.msg.assistant");
    return all.length > n && !all[all.length - 1].querySelector(".spin");
  }, before, { timeout: 20000 });
  return page.locator("article.msg.assistant").last();
}

const text = async (locator) => (await locator.textContent()) || "";

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 1100, height: 900 }, deviceScaleFactor: 1 });

  // A. Scripted provider over the synthetic corpus.
  const page = await context.newPage();
  const a = watch(page);
  await page.goto(cfg.urls.scripted + "/chat");
  await page.waitForSelector("#provider-pill.on");
  check("A: provider pill names the scripted provider", (await page.textContent("#provider-pill")).includes("scripted"));
  check("A: corpus pill shows the snapshot", (await page.textContent("#corpus-pill")).includes("snapshot"));

  let turn = await ask(page, "How does QA respond to a viable environmental monitoring excursion?");
  check("A1: status chip says answered", (await text(turn.locator(".status").first())).includes("Answered"));
  check("A1: two ordered steps", (await turn.locator(".answer ol li").count()) === 2);
  check("A1: one citation chip per step", (await turn.locator(".answer .cite").count()) === 2);
  check("A1: three passage cards", (await turn.locator(".card").count()) === 3);
  check("A1: cited span highlighted in S2", (await page.locator("#t1-S2 mark").count()) >= 1);
  check("A1: uncited S1 has no highlight", (await page.locator("#t1-S1 mark").count()) === 0);
  check("A1: card shows document, version and status",
    (await text(page.locator("#t1-S2"))).includes("SOP-QA-001") && (await text(page.locator("#t1-S2"))).includes("v1.0")
      && (await text(page.locator("#t1-S2 .badge"))).includes("Approved"));
  check("A1: meta records the reported model", (await text(turn.locator(".meta"))).includes("model scripted-test-double"));
  check("A1: no 'verified' wording anywhere in the turn", !/verified/i.test(await text(turn)));
  await shot(page, "a1-supported-answer.png");

  turn = await ask(page, "Who is responsible?");
  check("A2: interpreted as a follow-up to turn 1", (await text(turn.locator(".interp"))).includes("follow-up to turn 1"));
  check("A2: bullets rendered", (await turn.locator(".answer ul li").count()) === 2);

  turn = await ask(page, "Turn the stated procedure into a checklist");
  check("A3: three checklist items", (await turn.locator("ul.checklist li").count()) === 3);
  await turn.locator(".answer .cite").first().click();
  check("A3: citation chip highlights its source card", (await page.locator(".card.flash").count()) === 1);
  await turn.locator(".card .linkbtn").nth(1).click();
  await page.waitForSelector("#docdlg[open]");
  check("A3: document view highlights the passage in context", (await page.locator("#doc-text mark").count()) === 1);
  check("A3: document view shows full source text", (await text(page.locator("#doc-text"))).includes("Investigation record"));
  await shot(page, "a3-document-view.png");
  await page.click("#doc-close");
  await shot(page, "a3-checklist.png");

  await page.click("#reset");
  await page.waitForFunction(() => document.querySelectorAll("#log article.msg").length === 0, null, { timeout: 5000 });
  check("A4: new conversation clears the log", (await page.locator("#log .msg").count()) === 0);
  turn = await ask(page, "What is the acceptance range for the analytical balance daily check?");
  check("A4: status says not stated", (await text(turn.locator(".status").first())).includes("Not stated"));
  check("A4: withheld box explains the invented value",
    (await turn.locator(".box.withheld").count()) === 1 && (await text(turn.locator(".box.withheld"))).includes("does not appear in its cited passage"));
  check("A4: withheld value text is not displayed", !(await text(turn)).includes("0.1 mg"));
  check("A4: honest statement still shown", (await turn.locator(".answer p").count()) === 1);
  check("A4: missing-information box shown", (await text(turn.locator(".box.missing"))).includes("numeric acceptance range"));
  check("A4: clarifying question shown", (await text(turn.locator(".box.question"))).includes("Would you like"));
  await shot(page, "a4-missing-and-withheld.png");

  turn = await ask(page, "What is the membrane filtration hold time for sterility?");
  check("A5: retired trap says no approved source", (await text(turn.locator(".status").first())).includes("No approved source"));
  check("A5: held-out identity shown", (await text(turn.locator(".heldout"))).includes("SOP-QA-009 v0.8 (Obsolete)"));
  check("A5: retired content is not displayed", !(await page.textContent("#log")).includes("96 hours"));
  check("A5: no model call recorded", (await text(turn.locator(".meta"))).includes("no model call"));

  turn = await ask(page, "How do staff confirm the current approved version of a controlled document?");
  check("A6: timeout shows a failure state", (await text(turn.locator(".status").first())).includes("Model request failed")
    && (await text(turn)).includes("timed out"));
  check("A6: passages still shown after a provider failure", (await turn.locator(".card").count()) > 0);

  turn = await ask(page, "When is gowning requalification required?");
  check("A7: malformed output is rejected", (await text(turn.locator(".status").first())).includes("Model output rejected"));
  check("A7: rejected output text is not displayed", !(await text(turn)).includes("this is not JSON"));
  await shot(page, "a7-failure-states.png");
  check("A: no dialogs", a.dialogs.length === 0, a.dialogs.join("; "));
  check("A: no console errors", a.errors.length === 0, a.errors.join("; "));

  // B. Markup in passages and in model output must stay inert text.
  const pageB = await context.newPage();
  const b = watch(pageB);
  await pageB.goto(cfg.urls.adversarial + "/chat");
  await pageB.waitForSelector("#provider-pill.on");
  turn = await ask(pageB, "How are printed sample labels reconciled before testing?");
  check("B: model markup shown literally", (await text(turn.locator(".answer"))).includes("<img src=x onerror="));
  check("B: injected passage markup shown literally", (await pageB.textContent("#log")).includes("<script>window.__pwned = 1</script>"));
  check("B: no script or img element created in the log",
    (await pageB.locator("#log script").count()) === 0 && (await pageB.locator("#log img").count()) === 0);
  check("B: no injected code ran", (await pageB.evaluate(() => typeof window.__pwned)) === "undefined");
  check("B: no dialogs", b.dialogs.length === 0, b.dialogs.join("; "));
  await shot(pageB, "b-unsafe-markup-inert.png");

  // C. Shipped default: no provider configured.
  const pageC = await context.newPage();
  const c = watch(pageC);
  await pageC.goto(cfg.urls.unconfigured + "/chat");
  await pageC.waitForSelector("#provider-pill.off");
  check("C: unavailable banner explains the setup", (await pageC.textContent("#banner")).includes("No explanation provider is configured"));
  turn = await ask(pageC, "How does QA respond to a viable environmental monitoring excursion?");
  check("C: turn shows explanation unavailable", (await text(turn.locator(".status").first())).includes("Explanation unavailable"));
  check("C: approved passages still shown", (await turn.locator(".card").count()) === 3);
  check("C: no model call recorded", (await text(turn.locator(".meta"))).includes("no model call"));
  check("C: no console errors", c.errors.length === 0, c.errors.join("; "));
  await shot(pageC, "c-provider-unavailable.png");

  // D. API key required.
  const pageD = await context.newPage();
  await pageD.goto(cfg.urls.keyed + "/chat");
  await pageD.waitForSelector("#keybox:not(.hidden)");
  check("D: key prompt shown on 401", true);
  await pageD.fill("#apikey", cfg.apiKey);
  await pageD.click("#savekey");
  await pageD.waitForSelector("#provider-pill.on");
  turn = await ask(pageD, "How does QA respond to a viable environmental monitoring excursion?");
  check("D: answer after supplying the key", (await text(turn.locator(".status").first())).includes("Answered"));

  // E. Phone width: no horizontal page scroll.
  const phone = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1 });
  const pageE = await phone.newPage();
  await pageE.goto(cfg.urls.scripted + "/chat");
  await pageE.waitForSelector("#provider-pill.on");
  await ask(pageE, "How does QA respond to a viable environmental monitoring excursion?");
  const overflow = await pageE.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  check("E: no horizontal overflow at 390px", overflow <= 0, `overflow ${overflow}px`);
  await shot(pageE, "e-phone.png");

  await browser.close();
  fs.writeFileSync(path.join(cfg.out, "results.json"), JSON.stringify({ failures, results }, null, 2));
  console.log(`${results.length - failures}/${results.length} UI checks passed`);
  process.exit(failures ? 1 : 0);
})().catch((error) => { console.error(error); process.exit(2); });
