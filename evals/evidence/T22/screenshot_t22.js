// T22: before/after screenshots of both tabs. Usage: node screenshot_t22.js before|after [width]
const { chromium } = require("playwright");
const path = require("path");

const PREFIX = process.argv[2] || "after";
const WIDTH = Number(process.argv[3] || 1100);
const OUT = "C:/Users/tomo2/OneDrive/Desktop/エンジニアリング/ハリネズミ/evals/evidence/T22";
const PPTX = path.join(__dirname, "sample-pitch.pptx");
const MP4 = path.join(__dirname, "sample-video.mp4");
const suffix = WIDTH < 600 ? "-mobile" : "";

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: WIDTH, height: 900 } });
  const errors = [];
  page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
  page.on("pageerror", (e) => errors.push(String(e)));
  const shot = async (name) => {
    await page.mouse.move(0, 0);
    await page.waitForTimeout(900); // let entry animations settle
    await page.screenshot({ path: `${OUT}/${PREFIX}-${name}${suffix}.png`, fullPage: true });
  };

  // --- pitch-review tab ---
  await page.goto("http://localhost:5173");
  await page.waitForSelector("text=ピッチ審査を添削するAI");
  await page.locator("select").first().selectOption("general");
  await page.getByText("評価項目を自分で指定").click();
  await page.locator("textarea").fill("課題の明確さ\n技術力\nチームワーク");
  await page.getByRole("button", { name: "評価基準を確認する" }).click();
  await page.waitForSelector(".rubric-preview", { timeout: 20000 });
  await page.locator('input[type="file"]').first().setInputFiles(PPTX);
  await shot("01-review-form");

  if (WIDTH >= 600) {
    await page.getByRole("button", { name: "審査を開始する" }).click();
    await page.waitForTimeout(1200);
    await page.screenshot({ path: `${OUT}/${PREFIX}-02-review-loading.png`, fullPage: true });
    await page.waitForSelector(".criterion-card", { timeout: 60000 });
    await page.locator(".criterion-levels").first().evaluate((d) => (d.open = true));
    await shot("03-review-result");
  }

  // --- contest mode ---
  await page.goto("http://localhost:5173");
  await page.locator(".app-mode-tabs").getByText("コンテスト観点モード").click();
  await page.getByPlaceholder("例: 学生ビジネスプランコンテスト2026").fill("学生ビジネスプランコンテスト2026");
  const cards = page.locator(".criterion-input-card");
  await cards.nth(0).getByPlaceholder("例: 課題の明確さ").fill("課題の明確さ");
  await cards.nth(0).locator('input[type="number"]').fill("40");
  await page.getByText("観点を追加する").click();
  await cards.nth(1).getByPlaceholder("例: 課題の明確さ").fill("プレゼンテーション力");
  await cards.nth(1).locator('input[type="number"]').fill("60");
  await shot("04-contest-form");
  if (WIDTH < 600) {
    console.log("CONSOLE_ERRORS:", JSON.stringify(errors));
    await browser.close();
    return;
  }

  await page.getByRole("button", { name: "Questionを生成する" }).click();
  await page.waitForSelector(".question-editor-card", { timeout: 30000 });
  await shot("05-contest-questions");

  await page.getByRole("button", { name: "この内容で音声を採点する" }).click();
  await page.waitForSelector("text=発表を採点する");
  await page.locator('input[type="file"]').nth(0).setInputFiles(PPTX);
  await page.locator('input[type="file"]').nth(1).setInputFiles(MP4);
  await shot("06-contest-upload");

  await page.getByRole("button", { name: "採点する" }).click();
  await page.waitForSelector(".contest-score-result", { timeout: 60000 });
  await shot("07-contest-result");

  console.log("CONSOLE_ERRORS:", JSON.stringify(errors));
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
