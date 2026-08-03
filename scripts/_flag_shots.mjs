import { chromium } from "playwright-core";
import fs from "fs";
import path from "path";

const base = process.env.MIRAAH_BASE || "http://127.0.0.1:8000";
const outDir = path.resolve("scripts/_flag_shots");
fs.mkdirSync(outDir, { recursive: true });

const browser = await chromium.launch({ headless: true, channel: "chrome" });
const shots = [];

async function shot(name, fn) {
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  try {
    await fn(page);
    const file = path.join(outDir, name);
    await page.screenshot({ path: file, fullPage: false });
    shots.push(file);
    console.log("OK", name);
  } finally {
    await page.close();
  }
}

await shot("homepage-passports-ar-dark.png", async (page) => {
  await page.goto(`${base}/`, { waitUntil: "networkidle" });
  await page.evaluate(() => {
    localStorage.setItem("miraahLang", "ar");
    localStorage.setItem("miraahTheme", "dark");
  });
  await page.reload({ waitUntil: "networkidle" });
  await page.locator("#leadingPassports").scrollIntoViewIfNeeded();
  await page.waitForTimeout(200);
  const box = await page.locator("#leadingPassports").boundingBox();
  if (box) {
    await page.screenshot({
      path: path.join(outDir, "homepage-passports-ar-dark.png"),
      clip: {
        x: Math.max(0, box.x - 24),
        y: Math.max(0, box.y - 80),
        width: Math.min(1400, box.width + 48),
        height: Math.min(700, box.height + 120),
      },
    });
  }
});

await shot("homepage-passports-en-light.png", async (page) => {
  await page.goto(`${base}/`, { waitUntil: "networkidle" });
  await page.evaluate(() => {
    localStorage.setItem("miraahLang", "en");
    localStorage.setItem("miraahTheme", "light");
  });
  await page.reload({ waitUntil: "networkidle" });
  await page.locator("#leadingPassports").scrollIntoViewIfNeeded();
  await page.waitForTimeout(200);
  const box = await page.locator("#leadingPassports").boundingBox();
  if (box) {
    await page.screenshot({
      path: path.join(outDir, "homepage-passports-en-light.png"),
      clip: {
        x: Math.max(0, box.x - 24),
        y: Math.max(0, box.y - 80),
        width: Math.min(1400, box.width + 48),
        height: Math.min(700, box.height + 120),
      },
    });
  }
});

await shot("destination-explorer-ar.png", async (page) => {
  await page.goto(`${base}/passport/`, { waitUntil: "networkidle" });
  await page.evaluate(() => {
    localStorage.setItem("miraahLang", "ar");
    localStorage.setItem("miraahTheme", "dark");
  });
  await page.reload({ waitUntil: "networkidle" });
  await page.locator("#passportSearch").fill("Azerbaijan");
  await page.waitForSelector("#suggestionsPassport .suggestion", { timeout: 5000 });
  await page.locator('#suggestionsPassport .suggestion[data-code="AZE"]').click();
  await page.waitForSelector("#results:not([hidden])");
  await page.waitForSelector("#destBody .miraah-flag img", { timeout: 8000 });
  const table = page.locator("#destBody").locator("xpath=ancestor::table[1]");
  await table.scrollIntoViewIfNeeded();
  await page.waitForTimeout(300);
  const box = await table.boundingBox();
  if (box) {
    await page.screenshot({
      path: path.join(outDir, "destination-explorer-ar.png"),
      clip: {
        x: Math.max(0, box.x - 16),
        y: Math.max(0, box.y - 40),
        width: Math.min(1200, box.width + 32),
        height: Math.min(520, box.height + 60),
      },
    });
  }
});

await shot("azerbaijan-detail-hero.png", async (page) => {
  await page.goto(`${base}/passport/azerbaijan/`, { waitUntil: "networkidle" });
  await page.evaluate(() => {
    localStorage.setItem("miraahLang", "en");
    localStorage.setItem("miraahTheme", "dark");
  });
  await page.reload({ waitUntil: "networkidle" });
  await page.waitForSelector("#passportIdentity .miraah-flag img", { timeout: 8000 });
  await page.waitForTimeout(250);
  const box = await page.locator(".passport-card").boundingBox();
  if (box) {
    await page.screenshot({
      path: path.join(outDir, "azerbaijan-detail-hero.png"),
      clip: {
        x: Math.max(0, box.x - 12),
        y: Math.max(0, box.y - 12),
        width: Math.min(1400, box.width + 24),
        height: Math.min(520, box.height + 24),
      },
    });
  }
});

await shot("mobile-passport-page.png", async (page) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(`${base}/passport/azerbaijan/`, { waitUntil: "networkidle" });
  await page.evaluate(() => {
    localStorage.setItem("miraahLang", "en");
    localStorage.setItem("miraahTheme", "light");
  });
  await page.reload({ waitUntil: "networkidle" });
  await page.waitForSelector("#passportIdentity .miraah-flag img", { timeout: 8000 });
  await page.waitForTimeout(250);
  await page.screenshot({
    path: path.join(outDir, "mobile-passport-page.png"),
    fullPage: false,
  });
});

// Smoke: no ISO-as-art on homepage; flags load locally; no external flag hosts
{
  const page = await browser.newPage();
  const external = [];
  page.on("request", (req) => {
    const u = req.url();
    if (/flagcdn|flagsapi|countryflags|twemoji|jsdelivr.*flag|unpkg.*flag/i.test(u)) {
      external.push(u);
    }
  });
  await page.goto(`${base}/`, { waitUntil: "networkidle" });
  await page.evaluate(() => {
    localStorage.setItem("miraahLang", "en");
    localStorage.setItem("miraahTheme", "dark");
  });
  await page.reload({ waitUntil: "networkidle" });
  const cardArt = await page.evaluate(() => {
    const cards = [...document.querySelectorAll("#leadingPassports .pass-card")];
    return cards.map((c) => {
      const img = c.querySelector(".pass-illus img");
      const illusText = (c.querySelector(".pass-illus")?.textContent || "").trim();
      return {
        src: img?.getAttribute("src") || "",
        illusText,
        hasFlag: !!img,
      };
    });
  });
  const okCards =
    cardArt.length > 0 &&
    cardArt.every((c) => c.hasFlag && c.src.startsWith("/assets/flags/") && !/^[A-Z]{3}$/.test(c.illusText));
  console.log(okCards ? "OK" : "FAIL", "homepage cards use local flags", JSON.stringify(cardArt.slice(0, 2)));
  console.log(external.length === 0 ? "OK" : "FAIL", "no external flag requests", external);

  await page.goto(`${base}/passport/azerbaijan/`, { waitUntil: "networkidle" });
  await page.waitForSelector("#passportIdentity img");
  const hero = await page.evaluate(() => {
    const img = document.querySelector("#passportIdentity img");
    return { src: img?.getAttribute("src"), name: document.querySelector(".identity-name")?.textContent };
  });
  const tableFlags = await page.evaluate(() => {
    const rows = [...document.querySelectorAll("#destBody tr")].slice(0, 8);
    return rows.map((r) => ({
      hasFlag: !!r.querySelector(".miraah-flag img"),
      src: r.querySelector(".miraah-flag img")?.getAttribute("src") || "",
      text: (r.querySelector(".flag-label")?.textContent || "").trim(),
    }));
  });
  console.log(
    hero.src === "/assets/flags/az.svg" ? "OK" : "FAIL",
    "azerbaijan hero flag",
    hero
  );
  console.log(
    tableFlags.every((r) => r.hasFlag && r.src.startsWith("/assets/flags/") && r.text) ? "OK" : "FAIL",
    "destination table flags",
    tableFlags.slice(0, 3)
  );
  await page.close();
}

await browser.close();
console.log("shots=", shots.length);
for (const s of shots) console.log(s);
