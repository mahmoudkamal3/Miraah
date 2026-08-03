import { chromium } from "playwright-core";
import fs from "fs";
import http from "http";
import path from "path";
import { fileURLToPath } from "url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const PUBLIC = path.join(ROOT, "public");
const OUT = path.join(ROOT, "scripts", "_homepage_shots");
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
        res.writeHead(200, {
          "Content-Type": MIME[path.extname(file)] || "application/octet-stream",
        });
        res.end(data);
      });
    });
    server.listen(0, "127.0.0.1", () => resolve(server));
  });
}

const server = await serve();
const { port } = server.address();
const base = `http://127.0.0.1:${port}`;
const browser = await chromium.launch({ headless: true, channel: "chrome" });
const results = [];
const check = (label, ok, detail = "") => {
  results.push({ label, ok, detail });
  console.log(ok ? "OK  " : "FAIL", label, detail);
};

try {
  const ctx = await browser.newContext({
    colorScheme: "dark",
    viewport: { width: 1440, height: 900 },
  });
  const page = await ctx.newPage();
  await page.goto(base + "/", { waitUntil: "networkidle" });
  await page.evaluate(() => {
    localStorage.setItem("miraahTheme", "dark");
    localStorage.setItem("miraahLang", "en");
  });
  await page.reload({ waitUntil: "networkidle" });
  let t = await page.evaluate(() => ({
    theme: document.documentElement.dataset.theme,
    hasHero: !!document.querySelector(".home-hero"),
    hasCompareTool: !!document.querySelector("#countrySearchA"),
    navHome: document.getElementById("navHome")?.getAttribute("aria-current"),
  }));
  check("home is homepage", t.hasHero && !t.hasCompareTool && t.navHome === "page", JSON.stringify(t));
  await page.screenshot({ path: path.join(OUT, "home-desktop-dark.png") });

  await page.click("#themeBtn");
  await page.waitForTimeout(100);
  await page.screenshot({ path: path.join(OUT, "home-desktop-light.png") });
  t = await page.evaluate(() => document.documentElement.dataset.theme);
  check("home toggle light", t === "light");

  await page.goto(base + "/compare/", { waitUntil: "networkidle" });
  t = await page.evaluate(() => ({
    theme: document.documentElement.dataset.theme,
    hasTool: !!document.querySelector("#countrySearchA"),
    nav: document.getElementById("navCompare")?.getAttribute("aria-current"),
    stored: localStorage.getItem("miraahTheme"),
  }));
  check("compare page + theme persist", t.hasTool && t.nav === "page" && t.stored === "light", JSON.stringify(t));
  await page.screenshot({ path: path.join(OUT, "compare-desktop-light.png") });

  await page.goto(base + "/passport/", { waitUntil: "networkidle" });
  t = await page.evaluate(() => ({
    theme: document.documentElement.dataset.theme,
    nav: document.getElementById("navPassport")?.getAttribute("aria-current"),
    navHome: !!document.getElementById("navHome"),
    stored: localStorage.getItem("miraahTheme"),
  }));
  check("passport shared header", t.nav === "page" && t.navHome && t.stored === "light", JSON.stringify(t));
  await page.screenshot({ path: path.join(OUT, "passport-desktop-light.png") });

  await page.click("#langBtn");
  await page.waitForTimeout(80);
  const lang = await page.evaluate(() => ({
    lang: document.documentElement.lang,
    theme: localStorage.getItem("miraahTheme"),
  }));
  check("lang switch keeps theme", lang.lang === "ar" && lang.theme === "light", JSON.stringify(lang));

  await ctx.close();

  const mobile = await browser.newContext({
    colorScheme: "dark",
    viewport: { width: 390, height: 844 },
  });
  const mpage = await mobile.newPage();
  await mpage.goto(base + "/", { waitUntil: "networkidle" });
  await mpage.evaluate(() => localStorage.setItem("miraahTheme", "dark"));
  await mpage.reload({ waitUntil: "networkidle" });
  await mpage.screenshot({ path: path.join(OUT, "home-mobile-dark.png") });
  await mpage.click("#themeBtn");
  await mpage.waitForTimeout(80);
  await mpage.screenshot({ path: path.join(OUT, "home-mobile-light.png") });
  check("mobile shots", true);
  await mobile.close();

  // dashboard alias redirect
  const rctx = await browser.newContext({ viewport: { width: 1000, height: 700 } });
  const rpage = await rctx.newPage();
  await rpage.goto(base + "/dashboard.html", { waitUntil: "networkidle" });
  check("dashboard redirects to compare", rpage.url().includes("/compare/"), rpage.url());
  await rctx.close();
} finally {
  await browser.close();
  server.close();
}

const failed = results.filter((r) => !r.ok);
console.log(`\n${results.length - failed.length}/${results.length} passed`);
console.log("shots:", fs.readdirSync(OUT).join(", "));
if (failed.length) process.exit(1);
