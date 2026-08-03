import { chromium } from "playwright-core";
import fs from "fs";
import http from "http";
import path from "path";
import { fileURLToPath } from "url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const PUBLIC = path.join(ROOT, "public");
const OUT = path.join(ROOT, "scripts", "_theme_shots");
fs.mkdirSync(OUT, { recursive: true });

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".webmanifest": "application/manifest+json",
};

function serve() {
  return new Promise((resolve) => {
    const server = http.createServer((req, res) => {
      let urlPath = decodeURIComponent((req.url || "/").split("?")[0]);
      if (urlPath.endsWith("/")) urlPath += "index.html";
      const file = path.normalize(path.join(PUBLIC, urlPath));
      if (!file.startsWith(PUBLIC)) {
        res.writeHead(403);
        res.end("forbidden");
        return;
      }
      fs.readFile(file, (err, data) => {
        if (err) {
          res.writeHead(404);
          res.end("not found");
          return;
        }
        res.writeHead(200, { "Content-Type": MIME[path.extname(file)] || "application/octet-stream" });
        res.end(data);
      });
    });
    server.listen(0, "127.0.0.1", () => resolve(server));
  });
}

const results = [];
const check = (label, ok, detail = "") => {
  results.push({ label, ok, detail });
  console.log(ok ? "OK  " : "FAIL", label, detail);
};

async function shot(page, name) {
  await page.screenshot({ path: path.join(OUT, name), fullPage: false });
}

async function setPref(page, pref) {
  await page.evaluate((p) => {
    if (p == null) localStorage.removeItem("miraahTheme");
    else localStorage.setItem("miraahTheme", p);
  }, pref);
}

async function readTheme(page) {
  return page.evaluate(() => ({
    pref: document.documentElement.getAttribute("data-theme-pref"),
    theme: document.documentElement.getAttribute("data-theme"),
    stored: localStorage.getItem("miraahTheme"),
    meta: document.querySelector('meta[name="theme-color"]')?.content || "",
    bg: getComputedStyle(document.body).backgroundColor,
    hasBtn: !!document.getElementById("themeBtn"),
  }));
}

async function forceSystem(page, dark) {
  await page.emulateMedia({ colorScheme: dark ? "dark" : "light" });
}

const server = await serve();
const { port } = server.address();
const base = `http://127.0.0.1:${port}`;

const browser = await chromium.launch({ headless: true, channel: "chrome" });

try {
  // --- First visit system dark ---
  {
    const ctx = await browser.newContext({ colorScheme: "dark", viewport: { width: 1440, height: 900 } });
    const page = await ctx.newPage();
    await page.goto(base + "/", { waitUntil: "networkidle" });
    await page.evaluate(() => {
      localStorage.removeItem("miraahTheme");
      localStorage.setItem("miraahLang", "en");
    });
    await page.reload({ waitUntil: "networkidle" });
    let t = await readTheme(page);
    check("first visit system dark", t.pref === "system" && t.theme === "dark" && t.stored == null, JSON.stringify(t));
    check("theme-color dark", t.meta === "#07111f", t.meta);
    check("themeBtn home", t.hasBtn);
    await shot(page, "home-dark.png");

    // toggle to light (explicit)
    await page.click("#themeBtn");
    await page.waitForTimeout(80);
    t = await readTheme(page);
    check("toggle dark→light", t.theme === "light" && t.stored === "light", JSON.stringify(t));
    check("theme-color light", t.meta === "#e8eef6", t.meta);
    await shot(page, "home-light.png");

    // refresh persistence
    await page.reload({ waitUntil: "networkidle" });
    t = await readTheme(page);
    check("refresh persists light", t.theme === "light" && t.stored === "light", JSON.stringify(t));

    // lang switch does not reset
    await page.click("#langBtn");
    await page.waitForTimeout(80);
    t = await readTheme(page);
    const lang = await page.evaluate(() => document.documentElement.lang);
    check("lang switch keeps theme", t.theme === "light" && t.stored === "light", `lang=${lang} ${JSON.stringify(t)}`);
    const labels = await page.evaluate(() => ({
      light: document.getElementById("themeOptLight")?.textContent,
      dark: document.getElementById("themeOptDark")?.textContent,
      system: document.getElementById("themeOptSystem")?.textContent,
    }));
    // open menu via contextmenu
    await page.click("#themeBtn", { button: "right" });
    await page.waitForTimeout(60);
    const open = await page.evaluate(() => document.getElementById("themeMenu")?.classList.contains("open"));
    check("theme menu opens", open === true);
    const arLabels = await page.evaluate(() => ({
      light: document.getElementById("themeOptLight")?.textContent,
      dark: document.getElementById("themeOptDark")?.textContent,
      system: document.getElementById("themeOptSystem")?.textContent,
      aria: document.getElementById("themeBtn")?.getAttribute("aria-label"),
    }));
    check("AR labels", arLabels.light === "الوضع الفاتح" && arLabels.dark === "الوضع الداكن" && arLabels.system === "استخدام إعداد الجهاز", JSON.stringify(arLabels));

    // navigate to passport
    await page.goto(base + "/passport/", { waitUntil: "networkidle" });
    t = await readTheme(page);
    check("passport keeps light", t.theme === "light" && t.stored === "light", JSON.stringify(t));
    await shot(page, "passport-light.png");

    // toggle to dark on passport
    await page.click("#themeBtn");
    await page.waitForTimeout(80);
    t = await readTheme(page);
    check("passport toggle light→dark", t.theme === "dark" && t.stored === "dark", JSON.stringify(t));
    await shot(page, "passport-dark.png");

    // Malta detail
    await page.goto(base + "/passport/malta/", { waitUntil: "networkidle" });
    t = await readTheme(page);
    check("malta keeps dark", t.theme === "dark" && t.stored === "dark", JSON.stringify(t));
    check("malta themeBtn", t.hasBtn);

    // select Malta if needed and wait for map
    await page.waitForTimeout(400);
    const mapOcean = await page.evaluate(() => {
      const ocean = document.querySelector("#mapSvg rect, #mapSvgMount svg rect");
      return ocean ? ocean.getAttribute("fill") : null;
    });
    // may be null if map not loaded until selection — on detail page map should load
    const hasMapPanel = await page.evaluate(() => !!document.getElementById("mapPanel"));
    check("malta map panel present", hasMapPanel);

    // recolor without refetch: switch theme and check ocean fill changes
    await page.click("#themeBtn"); // to light
    await page.waitForTimeout(200);
    const oceanLight = await page.evaluate(() => {
      const ocean = document.querySelector("#mapSvgMount svg rect, #mapSvg rect");
      return ocean ? ocean.getAttribute("fill") : getComputedStyle(document.documentElement).getPropertyValue("--map-ocean").trim();
    });
    await page.click("#themeBtn"); // back to dark
    await page.waitForTimeout(200);
    const oceanDark = await page.evaluate(() => {
      const ocean = document.querySelector("#mapSvgMount svg rect, #mapSvg rect");
      return ocean ? ocean.getAttribute("fill") : getComputedStyle(document.documentElement).getPropertyValue("--map-ocean").trim();
    });
    check("map ocean token differs by theme", oceanLight !== oceanDark && !!oceanLight && !!oceanDark, `${oceanLight} vs ${oceanDark}`);

    // attributions
    await page.goto(base + "/passport/image-attributions.html", { waitUntil: "networkidle" });
    t = await readTheme(page);
    check("attr page themeBtn", t.hasBtn);
    check("attr keeps theme", t.stored === "dark" || t.stored === "light", JSON.stringify(t));

    await ctx.close();
  }

  // --- First visit system light ---
  {
    const ctx = await browser.newContext({ colorScheme: "light", viewport: { width: 1440, height: 900 } });
    const page = await ctx.newPage();
    await page.goto(base + "/", { waitUntil: "networkidle" });
    await page.evaluate(() => localStorage.removeItem("miraahTheme"));
    await page.reload({ waitUntil: "networkidle" });
    const t = await readTheme(page);
    check("first visit system light", t.pref === "system" && t.theme === "light" && t.stored == null, JSON.stringify(t));
    await ctx.close();
  }

  // --- Charts recolor on home ---
  {
    const ctx = await browser.newContext({ colorScheme: "dark", viewport: { width: 1440, height: 900 } });
    const page = await ctx.newPage();
    await page.goto(base + "/", { waitUntil: "networkidle" });
    await page.evaluate(() => {
      localStorage.setItem("miraahTheme", "dark");
      localStorage.setItem("miraahLang", "en");
    });
    await page.reload({ waitUntil: "networkidle" });
    await page.evaluate(() => {
      state.a = "EGY";
      state.b = "ESP";
      state.queryA = name("EGY");
      state.queryB = name("ESP");
      render();
    });
    await page.waitForTimeout(200);
    const before = await page.evaluate(() => ({ GRID, MUTED, theme: document.documentElement.dataset.theme }));
    await page.click("#themeBtn");
    await page.waitForTimeout(120);
    const after = await page.evaluate(() => ({ GRID, MUTED, theme: document.documentElement.dataset.theme }));
    check("charts recolor without reload", before.theme === "dark" && after.theme === "light" && before.GRID !== after.GRID, JSON.stringify({ before, after }));
    await ctx.close();
  }

  // --- Mobile 390 ---
  {
    const ctx = await browser.newContext({ colorScheme: "dark", viewport: { width: 390, height: 844 } });
    const page = await ctx.newPage();
    await page.goto(base + "/", { waitUntil: "networkidle" });
    await page.evaluate(() => localStorage.setItem("miraahTheme", "dark"));
    await page.reload({ waitUntil: "networkidle" });
    await shot(page, "mobile-dark.png");
    await page.click("#themeBtn");
    await page.waitForTimeout(80);
    await shot(page, "mobile-light.png");
    const t = await readTheme(page);
    check("mobile toggle", t.theme === "light" && t.hasBtn, JSON.stringify(t));
    await ctx.close();
  }

  // --- Direct malta refresh ---
  {
    const ctx = await browser.newContext({ colorScheme: "dark", viewport: { width: 1440, height: 900 } });
    const page = await ctx.newPage();
    await page.goto(base + "/passport/malta/", { waitUntil: "networkidle" });
    await page.evaluate(() => localStorage.setItem("miraahTheme", "light"));
    await page.reload({ waitUntil: "networkidle" });
    const t = await readTheme(page);
    check("direct detail refresh light", t.theme === "light" && t.stored === "light", JSON.stringify(t));
    // no-flash: data-theme set in head
    const boot = await page.evaluate(() => document.documentElement.getAttribute("data-theme"));
    check("data-theme applied", boot === "light");
    await ctx.close();
  }

  // --- Corrupt localStorage ---
  {
    const ctx = await browser.newContext({ colorScheme: "dark", viewport: { width: 800, height: 600 } });
    const page = await ctx.newPage();
    await page.goto(base + "/", { waitUntil: "networkidle" });
    await page.evaluate(() => localStorage.setItem("miraahTheme", "bogus"));
    await page.reload({ waitUntil: "networkidle" });
    const t = await readTheme(page);
    check("corrupt storage falls back system", t.pref === "system" && (t.theme === "dark" || t.theme === "light"), JSON.stringify(t));
    await ctx.close();
  }

  // --- Use device setting menu ---
  {
    const ctx = await browser.newContext({ colorScheme: "light", viewport: { width: 1100, height: 800 } });
    const page = await ctx.newPage();
    await page.goto(base + "/", { waitUntil: "networkidle" });
    await page.evaluate(() => {
      localStorage.setItem("miraahTheme", "dark");
      localStorage.setItem("miraahLang", "en");
    });
    await page.reload({ waitUntil: "networkidle" });
    await page.click("#themeBtn", { button: "right" });
    await page.click('#themeOptSystem');
    await page.waitForTimeout(80);
    const t = await readTheme(page);
    check("use device setting", t.pref === "system" && t.stored === "system" && t.theme === "light", JSON.stringify(t));
    const en = await page.evaluate(() => ({
      light: document.getElementById("themeOptLight")?.textContent,
      dark: document.getElementById("themeOptDark")?.textContent,
      system: document.getElementById("themeOptSystem")?.textContent,
    }));
    // reopen for labels
    await page.click("#themeBtn", { button: "right" });
    const en2 = await page.evaluate(() => ({
      light: document.getElementById("themeOptLight")?.textContent,
      dark: document.getElementById("themeOptDark")?.textContent,
      system: document.getElementById("themeOptSystem")?.textContent,
    }));
    check("EN labels", en2.light === "Light mode" && en2.dark === "Dark mode" && en2.system === "Use device setting", JSON.stringify(en2));
    await ctx.close();
  }
} finally {
  await browser.close();
  server.close();
}

const failed = results.filter((r) => !r.ok);
console.log(`\n${results.length - failed.length}/${results.length} passed`);
console.log("shots:", fs.readdirSync(OUT).join(", "));
if (failed.length) process.exit(1);
