// T11: one real end-to-end run through the UI (real Claude / Whisper / Jev).
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const OUT = "C:/Users/tomo2/OneDrive/Desktop/エンジニアリング/ハリネズミ/evals/evidence/T11";
const PPTX = "C:/Users/tomo2/OneDrive/Desktop/エンジニアリング/ハリネズミ/pitch/harinezumi_pitch.pptx";
const WAV = path.join(__dirname, "..", "t11_pitch_first2min.wav");
const RESULT = path.join(__dirname, "..", "t11_e2e_result.json");

const CRITERIA = [
  ["課題設定の明確さ", "誰のどんな課題を解くのかが明確で、その課題が本当にあると示せているか", "30"],
  ["AI活用の独自性・技術力", "AIの使い方に独自性があり、プロダクトとして動く仕組みになっているか", "40"],
  ["プレゼンの分かりやすさ", "話の構成が分かりやすく、聞き手を引き込めているか", "30"],
];

(async () => {
  const log = { started_at: new Date().toISOString(), steps: [], console_errors: [] };
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1100, height: 900 } });
  page.on("console", (m) => m.type() === "error" && log.console_errors.push(m.text()));
  page.on("pageerror", (e) => log.console_errors.push(String(e)));

  async function timed(name, urlPart, action) {
    const t0 = Date.now();
    const [response] = await Promise.all([
      page.waitForResponse((r) => r.url().includes(urlPart) && r.request().method() === "POST", { timeout: 300000 }),
      action(),
    ]);
    const body = await response.json();
    log.steps.push({ name, status: response.status(), seconds: (Date.now() - t0) / 1000, body });
    return response.status();
  }

  await page.goto("http://localhost:5173");
  await page.locator(".app-mode-tabs").getByText("コンテスト観点モード").click();
  await page.getByPlaceholder("例: 学生ビジネスプランコンテスト2026").fill("AIハッカソン（T11 通しテスト）");
  const cards = page.locator(".criterion-input-card");
  for (let i = 0; i < CRITERIA.length; i++) {
    if (i > 0) await page.getByText("観点を追加する").click();
    await cards.nth(i).getByPlaceholder("例: 課題の明確さ").fill(CRITERIA[i][0]);
    await cards.nth(i).locator("textarea").fill(CRITERIA[i][1]);
    await cards.nth(i).locator('input[type="number"]').fill(CRITERIA[i][2]);
  }

  const qStatus = await timed("questions", "/api/contest/questions", () =>
    page.getByRole("button", { name: "Questionを生成する" }).click()
  );
  if (qStatus === 200) {
    await page.waitForSelector(".question-editor-card");
    await page.mouse.move(0, 0);
    await page.screenshot({ path: `${OUT}/screenshot-01-generated-questions.png`, fullPage: true });

    await page.getByRole("button", { name: "この内容で音声を採点する" }).click();
    await page.waitForSelector("text=発表を採点する");
    await page.locator('input[type="file"]').nth(0).setInputFiles(PPTX);
    await page.locator('input[type="file"]').nth(1).setInputFiles(WAV);
    const sStatus = await timed("score", "/api/contest/score", () =>
      page.getByRole("button", { name: "採点する" }).click()
    );
    if (sStatus === 200) {
      await page.waitForSelector(".contest-score-result");
      await page.mouse.move(0, 0);
      await page.waitForTimeout(600);
      await page.screenshot({ path: `${OUT}/screenshot-02-score-result.png`, fullPage: true });
    } else {
      await page.screenshot({ path: `${OUT}/screenshot-02-score-error.png`, fullPage: true });
    }
  }

  log.finished_at = new Date().toISOString();
  fs.writeFileSync(RESULT, JSON.stringify(log, null, 2), "utf-8");
  console.log(log.steps.map((s) => `${s.name}: HTTP ${s.status} in ${s.seconds}s`).join("\n"));
  console.log("CONSOLE_ERRORS:", JSON.stringify(log.console_errors));
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
