#!/usr/bin/env python3
"""Render the Mir’ah platform homepage (public/index.html)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import miraah_brand as brand  # noqa: E402
import miraah_chrome as chrome  # noqa: E402
import miraah_flags as flags  # noqa: E402
import miraah_theme as theme  # noqa: E402
import passport_core as core  # noqa: E402

INDEX_OUT = ROOT / "public" / "index.html"
PASSPORT_INDEX = core.PUBLIC_DATA / "index.json"
LEADING_COUNT = 8

# Verified from embedded comparison DATA + passport index (see scripts/_count_data.py).
COMPARE_COUNTRIES = 217
COMPARE_INDICATORS = 12
PASSPORT_COUNT = 199
DESTINATION_COUNT = 198


HOME_CSS = chrome.chrome_css_bundle() + flags.FLAG_CSS + r"""
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:radial-gradient(circle at 85% 0,var(--radial-a) 0,transparent 30%),radial-gradient(circle at 5% 50%,var(--radial-b) 0,transparent 28%),var(--bg);color:var(--text);font-family:Inter,"Segoe UI",Tahoma,Arial,sans-serif;min-height:100vh}
button,input,a{font:inherit}
.shell{max-width:1180px;margin:auto;padding:22px}
.btn{border:1px solid var(--line);background:var(--surface-soft);color:var(--text);padding:9px 13px;border-radius:11px;cursor:pointer;text-decoration:none;display:inline-flex;align-items:center;justify-content:center}
.btn:hover,.btn:focus-visible{border-color:var(--btn-hover-border)}
.btn:focus-visible{outline:2px solid var(--brand-cyan);outline-offset:2px}
.lang-btn{min-width:48px;font-weight:800;color:var(--text-on-brand);background:linear-gradient(135deg,var(--brand-cyan),var(--brand-blue-soft));border:0}
.btn-primary{border:0;color:var(--text-on-brand);background:linear-gradient(135deg,var(--brand-cyan),var(--brand-blue-soft));font-weight:700;padding:12px 18px;border-radius:12px}
.btn-secondary{background:var(--surface);border:1px solid var(--border-strong);padding:12px 18px;border-radius:12px;font-weight:650}
.home-hero{display:grid;grid-template-columns:1.05fr .95fr;gap:28px;align-items:center;padding:28px 0 18px}
.eyebrow{display:inline-block;color:var(--brand-cyan);font-size:13px;font-weight:700;letter-spacing:.04em;margin-bottom:12px}
.home-hero h2{margin:0 0 14px;font-size:clamp(32px,5vw,48px);line-height:1.15;letter-spacing:-.03em}
.home-hero .lead{margin:0 0 22px;color:var(--muted);font-size:17px;line-height:1.75;max-width:36em}
.cta-row{display:flex;flex-wrap:wrap;gap:12px}
.hero-preview{position:relative;border:1px solid var(--border);border-radius:24px;background:linear-gradient(160deg,var(--surface-raised),var(--surface));box-shadow:var(--shadow);padding:18px;overflow:hidden;min-height:320px}
.hero-preview[aria-hidden="true"]{pointer-events:none}
.preview-label{position:absolute;inset-inline-end:14px;top:14px;font-size:11px;color:var(--muted);background:var(--surface-soft);border:1px solid var(--border);padding:4px 8px;border-radius:999px;z-index:2}
.preview-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px}
.preview-card{border:1px solid var(--border);border-radius:14px;padding:12px;background:var(--surface-card)}
.preview-card.a{border-top:3px solid var(--brand-cyan)}
.preview-card.b{border-top:3px solid var(--brand-amber)}
.preview-card strong{display:block;font-size:14px;margin-bottom:8px}
.preview-metric{display:flex;justify-content:space-between;font-size:12px;color:var(--muted);margin-top:6px}
.preview-metric b{color:var(--text);font-variant-numeric:tabular-nums}
.preview-lower{display:grid;grid-template-columns:1.1fr .9fr;gap:10px}
.preview-map{border-radius:14px;border:1px solid var(--border);background:var(--map-ocean);min-height:110px;position:relative;overflow:hidden}
.preview-map svg{width:100%;height:100%;display:block}
.preview-pass{border-radius:14px;border:1px solid var(--border);background:linear-gradient(160deg,#1a4a6e,#0d2744);min-height:110px;padding:12px;color:#f4f8ff;display:flex;flex-direction:column;justify-content:space-between}
.preview-pass span{font-size:10px;opacity:.8}
.preview-pass strong{font-size:22px;color:var(--brand-cyan)}
.section{margin:42px 0}
.section h3{margin:0 0 8px;font-size:24px}
.section .section-lead{margin:0 0 18px;color:var(--muted);max-width:40em;line-height:1.6}
.product-cards{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.product-card{display:flex;flex-direction:column;gap:12px;text-decoration:none;color:inherit;background:linear-gradient(160deg,var(--surface-raised),var(--surface));border:1px solid var(--border);border-radius:20px;padding:20px;box-shadow:var(--shadow-soft);transition:border-color .15s ease,transform .15s ease}
.product-card:hover,.product-card:focus-visible{border-color:var(--brand-cyan);transform:translateY(-2px);outline:none}
.product-card:focus-visible{box-shadow:0 0 0 3px var(--focus)}
.product-card h4{margin:0;font-size:18px}
.product-card p{margin:0;color:var(--muted);line-height:1.65;flex:1}
.product-card .card-cta{color:var(--brand-cyan);font-weight:700;font-size:14px}
.mini-viz{height:72px;border-radius:12px;border:1px solid var(--border);background:var(--surface-soft);overflow:hidden}
.mini-viz svg{width:100%;height:100%;display:block}
.explore-head{display:flex;justify-content:space-between;gap:16px;align-items:end;flex-wrap:wrap}
.search-wrap{position:relative;max-width:420px;width:100%}
.country-search{width:100%;background:var(--input-bg);color:var(--text);border:1px solid var(--border-input);border-radius:10px;outline:none;padding:12px 14px}
.country-search:focus{border-color:var(--a);box-shadow:0 0 0 3px var(--focus)}
.suggestions{position:absolute;top:calc(100% + 6px);inset-inline:0;background:var(--input-bg);border:1px solid var(--border-strong);border-radius:12px;max-height:260px;overflow-y:auto;z-index:40;box-shadow:var(--shadow);display:none}
.suggestions.open{display:block}
.suggestion{padding:10px 12px;cursor:pointer;border-bottom:1px solid var(--border);text-decoration:none;color:inherit;display:block}
.suggestion:last-child{border-bottom:0}
.suggestion:hover,.suggestion.active{background:var(--hover)}
.suggestion small{display:block;color:var(--muted);font-size:10px;margin-top:3px}
.pass-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:18px}
.pass-card{display:flex;flex-direction:column;gap:10px;text-decoration:none;color:inherit;background:var(--surface);border:1px solid var(--border);border-radius:16px;padding:14px;min-height:180px}
.pass-card:hover,.pass-card:focus-visible{border-color:var(--brand-cyan);outline:none;box-shadow:0 0 0 3px var(--focus)}
.pass-illus{min-height:88px}
.pass-illus.flag-stage .passport-leader-flag{
  width:clamp(64px,5vw,80px);
  aspect-ratio:4/3;
  height:auto;
  border:1px solid var(--border);
  border-radius:5px;
  box-shadow:0 4px 12px rgb(0 0 0 / 14%)
}
.pass-illus.flag-stage .passport-leader-flag img{
  width:100%;
  height:100%;
  object-fit:contain;
  object-position:center
}
@media(max-width:600px){
  .pass-illus.flag-stage .passport-leader-flag{width:56px}
}
.pass-card h4{margin:0;font-size:15px}
.pass-meta{margin:0;color:var(--muted);font-size:12px;line-height:1.5}
.badge-exp{display:inline-flex;align-items:center;padding:3px 8px;border-radius:999px;border:1px solid var(--badge-exp-border);background:var(--badge-exp-bg);color:var(--badge-exp-fg);font-size:10px;font-weight:700;width:fit-content}
.view-all{margin-top:16px}
.trust-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:10px}
.trust-item{background:var(--surface);border:1px solid var(--border);border-radius:16px;padding:16px;text-align:center}
.trust-item strong{display:block;font-size:28px;color:var(--brand-cyan);font-variant-numeric:tabular-nums}
.trust-item span{display:block;margin-top:6px;color:var(--muted);font-size:12px;line-height:1.4}
.sources-box{margin-top:18px;background:var(--surface-soft);border:1px solid var(--border);border-radius:16px;padding:16px 18px;color:var(--muted);font-size:13px;line-height:1.7}
@media(max-width:980px){
  .home-hero,.product-cards,.preview-lower{grid-template-columns:1fr}
  .pass-grid{grid-template-columns:repeat(2,1fr)}
  .trust-grid{grid-template-columns:repeat(3,1fr)}
}
@media(max-width:560px){
  .shell{padding:14px}
  .pass-grid,.trust-grid,.preview-grid{grid-template-columns:1fr}
  .cta-row .btn-primary,.cta-row .btn-secondary{width:100%}
}
@media(prefers-reduced-motion:reduce){
  .product-card{transition:none}
  html{scroll-behavior:auto}
}
"""


def leading_passports(index: dict, n: int = LEADING_COUNT) -> list[dict]:
    items = []
    for p in index.get("passports", [])[:n]:
        totals = p.get("categoryTotals") or {}
        items.append(
            {
                "slug": p["slug"],
                "iso3": p["iso3"],
                "iso2": p.get("iso2") or "",
                "nameEn": p["nameEn"],
                "nameAr": p["nameAr"],
                "rank": p["rank"],
                "mobilityScore": p["mobilityScore"],
                "visaFree": int(totals.get("visa_free") or 0),
                "voa": int(totals.get("visa_on_arrival") or 0),
                "eta": int(totals.get("eta") or 0),
                "evisa": int(totals.get("evisa") or 0),
            }
        )
    return items


def hero_preview_html() -> str:
    return """
<aside class="hero-preview" aria-hidden="true">
  <span class="preview-label" id="previewLabel"></span>
  <div class="preview-grid">
    <div class="preview-card a"><strong id="previewA"></strong>
      <div class="preview-metric"><span id="previewM1"></span><b>82.4</b></div>
      <div class="preview-metric"><span id="previewM2"></span><b>74%</b></div>
    </div>
    <div class="preview-card b"><strong id="previewB"></strong>
      <div class="preview-metric"><span id="previewM1b"></span><b>79.1</b></div>
      <div class="preview-metric"><span id="previewM2b"></span><b>88%</b></div>
    </div>
  </div>
  <div class="preview-lower">
    <div class="preview-map">
      <svg viewBox="0 0 280 120" role="presentation">
        <rect width="280" height="120" fill="var(--map-ocean)"/>
        <path d="M40 70c20-28 48-34 70-20 18 12 28 8 42-6 16-16 40-10 56 8 12 14 28 18 42 8" fill="none" stroke="var(--map-land-stroke)" stroke-width="10" stroke-linecap="round" opacity=".55"/>
        <circle cx="96" cy="58" r="5" fill="var(--st-vf)"/><circle cx="148" cy="48" r="5" fill="var(--st-voa)"/><circle cx="198" cy="62" r="5" fill="var(--st-ev)"/>
      </svg>
    </div>
    <div class="preview-pass">
      <span id="previewPassLabel"></span>
      <strong>159</strong>
      <span id="previewPassNote"></span>
    </div>
  </div>
</aside>"""


def build_html(
    index: dict,
    *,
    countries: int = COMPARE_COUNTRIES,
    indicators: int = COMPARE_INDICATORS,
    passports: int = PASSPORT_COUNT,
    destinations: int = DESTINATION_COUNT,
) -> str:
    leading = leading_passports(index)
    updated = index.get("datasetUpdateDate") or ""
    origin = brand.CANONICAL_ORIGIN
    og = f"{origin.rstrip('/')}{brand.SOCIAL_CARD}"
    logo = f"{origin.rstrip('/')}{brand.APP_ICON_SVG}"
    title_ar = "مرآة | منصة البيانات العالمية"
    desc_ar = "قارن جودة الحياة والاقتصاد والسعادة بين الدول، واكتشف قوة جواز سفرك والوجهات المتاحة لك — من خلال بيانات واضحة ومصادر معلنة."
    json_ld = {
        "@context": "https://schema.org",
        "@type": "WebApplication",
        "name": "مرآة",
        "alternateName": "Mir’ah",
        "url": origin,
        "description": desc_ar,
        "applicationCategory": "BusinessApplication",
        "operatingSystem": "Any",
        "inLanguage": ["ar", "en"],
        "image": og,
        "logo": logo,
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "hasPart": [
            {
                "@type": "WebApplication",
                "name": "Country comparison",
                "url": f"{origin}compare/",
            },
            {
                "@type": "WebApplication",
                "name": "Passport power",
                "url": f"{origin}passport/",
            },
        ],
    }
    seo = (
        f'<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{title_ar}</title>"
        f'<meta name="description" content="{desc_ar}">'
        f'<meta name="robots" content="index, follow">'
        f'<meta name="googlebot" content="index, follow">'
        f'<link rel="canonical" href="{origin}">'
        f"{brand.brand_head_links(social_card_abs=og)}"
        f'<meta property="og:type" content="website">'
        f'<meta property="og:url" content="{origin}">'
        f'<meta property="og:title" content="{title_ar}">'
        f'<meta property="og:description" content="{desc_ar}">'
        f'<meta property="og:locale" content="ar_AR">'
        f'<meta property="og:locale:alternate" content="en_US">'
        f'<meta name="twitter:title" content="{title_ar}">'
        f'<meta name="twitter:description" content="{desc_ar}">'
        f'<script type="application/ld+json" id="miraah-jsonld">{json.dumps(json_ld, ensure_ascii=False)}</script>'
    )
    card_parts = []
    for p in leading:
        flag = flags.flag_img_html(
            p["iso2"], name=p["nameEn"], size="md", lazy=True, decorative=True
        ).replace("miraah-flag flag-md", "miraah-flag flag-md passport-leader-flag", 1)
        card_parts.append(
            f'<a class="pass-card" href="/passport/{p["slug"]}/" data-slug="{p["slug"]}">'
            f'<div class="pass-illus flag-stage">{flag}</div>'
            f'<span class="badge-exp" data-exp-badge></span>'
            f'<h4 data-name-en="{p["nameEn"]}" data-name-ar="{p["nameAr"]}">{p["nameAr"]}</h4>'
            f'<p class="pass-meta" data-rank="{p["rank"]}" data-score="{p["mobilityScore"]}" '
            f'data-vf="{p["visaFree"]}" data-voa="{p["voa"]}" data-eta="{p["eta"]}" data-ev="{p["evisa"]}"></p>'
            f"</a>"
        )
    cards = "".join(card_parts)
    boot = {
        "passports": [
            {
                "slug": p["slug"],
                "iso3": p["iso3"],
                "iso2": p.get("iso2") or "",
                "nameEn": p["nameEn"],
                "nameAr": p["nameAr"],
                "rank": p["rank"],
                "mobilityScore": p["mobilityScore"],
            }
            for p in index.get("passports", [])
        ],
        "counts": {
            "countries": countries,
            "indicators": indicators,
            "passports": passports,
            "destinations": destinations,
        },
        "datasetUpdateDate": updated,
        "leading": leading,
    }
    body = f"""
<div class="shell">
  {chrome.header_html(current="home")}
  <section class="home-hero">
    <div>
      <span class="eyebrow" id="heroEyebrow"></span>
      <h2 id="heroTitle"></h2>
      <p class="lead" id="heroLead"></p>
      <div class="cta-row">
        <a class="btn btn-primary" href="/compare/" id="ctaCompare"></a>
        <a class="btn btn-secondary" href="/passport/" id="ctaPassport"></a>
      </div>
    </div>
    {hero_preview_html()}
  </section>

  <section class="section" aria-labelledby="productsTitle">
    <h3 id="productsTitle"></h3>
    <p class="section-lead" id="productsLead"></p>
    <div class="product-cards">
      <a class="product-card" href="/compare/" id="cardCompare">
        <div class="mini-viz" aria-hidden="true"><svg viewBox="0 0 240 72"><polyline points="10,50 40,42 70,46 100,28 130,34 160,18 190,24 220,12" fill="none" stroke="var(--brand-cyan)" stroke-width="3"/><polyline points="10,58 40,54 70,50 100,48 130,40 160,38 190,30 220,26" fill="none" stroke="var(--brand-amber)" stroke-width="3"/></svg></div>
        <h4 id="cardCompareTitle"></h4>
        <p id="cardCompareBody"></p>
        <span class="card-cta" id="cardCompareCta"></span>
      </a>
      <a class="product-card" href="/passport/" id="cardPassport">
        <div class="mini-viz" aria-hidden="true"><svg viewBox="0 0 240 72"><rect x="20" y="12" width="70" height="48" rx="8" fill="#1a4a6e"/><rect x="110" y="18" width="100" height="12" rx="4" fill="var(--brand-cyan)" opacity=".85"/><rect x="110" y="38" width="78" height="8" rx="4" fill="var(--border-strong)"/><rect x="110" y="52" width="56" height="8" rx="4" fill="var(--border)"/></svg></div>
        <h4 id="cardPassportTitle"></h4>
        <p id="cardPassportBody"></p>
        <span class="card-cta" id="cardPassportCta"></span>
      </a>
    </div>
  </section>

  <section class="section" aria-labelledby="exploreTitle">
    <div class="explore-head">
      <div>
        <h3 id="exploreTitle"></h3>
        <p class="section-lead" id="exploreLead"></p>
      </div>
      <div class="search-wrap">
        <label class="visually-hidden" for="homePassportSearch" id="homeSearchLabel" style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)"></label>
        <input class="country-search" id="homePassportSearch" role="combobox" aria-autocomplete="list" aria-expanded="false" aria-controls="homeSuggestions" autocomplete="off" spellcheck="false">
        <div class="suggestions" id="homeSuggestions" role="listbox"></div>
      </div>
    </div>
    <div class="pass-grid" id="leadingPassports">{cards}</div>
    <div class="view-all"><a class="btn btn-secondary" href="/passport/" id="viewAllPassports"></a></div>
  </section>

  <section class="section" aria-labelledby="trustTitle">
    <h3 id="trustTitle"></h3>
    <p class="section-lead" id="trustLead"></p>
    <div class="trust-grid" id="trustGrid">
      <div class="trust-item"><strong>{countries}</strong><span id="trustCountries"></span></div>
      <div class="trust-item"><strong>{indicators}</strong><span id="trustIndicators"></span></div>
      <div class="trust-item"><strong>{passports}</strong><span id="trustPassports"></span></div>
      <div class="trust-item"><strong>{destinations}</strong><span id="trustDestinations"></span></div>
      <div class="trust-item"><strong>AR · EN</strong><span id="trustLangs"></span></div>
    </div>
    <div class="sources-box">
      <p id="trustSourcesCompare" style="margin:0 0 8px"></p>
      <p id="trustSourcesPassport" style="margin:0"></p>
      <p id="trustUpdated" style="margin:8px 0 0" data-updated="{updated}"></p>
    </div>
  </section>

  {chrome.footer_html()}
</div>
"""
    js = (
        theme.THEME_JS
        + chrome.CHROME_JS
        + flags.FLAG_JS
        + f"\nconst HOME_BOOT={json.dumps(boot, ensure_ascii=False)};\n"
        + HOME_JS
    )
    return (
        "<!doctype html><html lang=\"ar\" dir=\"rtl\"><head>"
        f"{seo}{theme.NO_FLASH_SCRIPT}<style>{HOME_CSS}</style></head><body>"
        f"{body}<script>{js}</script></body></html>"
    )


HOME_JS = r"""
const $=s=>document.querySelector(s);
const T={
 ar:{
  brand:'مرآة',subtitle:'منصة البيانات العالمية',
  pageTitle:'مرآة | منصة البيانات العالمية',
  pageDescription:'قارن جودة الحياة والاقتصاد والسعادة بين الدول، واكتشف قوة جواز سفرك والوجهات المتاحة لك — من خلال بيانات واضحة ومصادر معلنة.',
  eyebrow:'منصة مرآة للبيانات العالمية',
  hero:'العالم في مرآة',
  lead:'قارن جودة الحياة والاقتصاد والسعادة بين الدول، واكتشف قوة جواز سفرك والوجهات المتاحة لك — من خلال بيانات واضحة ومصادر معلنة.',
  ctaCompare:'قارن بين دولتين',ctaPassport:'اكتشف قوة جواز سفرك',
  previewLabel:'معاينة المنتج',previewA:'دولة أ',previewB:'دولة ب',
  mLife:'العمر المتوقع',mNet:'الإنترنت',passLabel:'درجة التنقل',passNote:'تجريبي · معاينة',
  productsTitle:'ماذا تريد أن تعرف؟',productsLead:'مساران واضحان — مقارنة الدول أو استكشاف قوة جواز السفر.',
  cardCompareTitle:'مقارنة الدول',
  cardCompareBody:'قارن متوسط العمر المتوقع والدخل والبطالة والإنترنت والسلامة والسعادة بين دولتين، مع الاتجاهات التاريخية والترتيب العالمي للمؤشرات.',
  cardCompareCta:'ابدأ المقارنة ←',
  cardPassportTitle:'قوة جواز السفر',
  cardPassportBody:'استكشف درجة التنقل التجريبية من مرآة، وفئات الدخول، وخريطة الوصول التفاعلية عبر الوجهات.',
  cardPassportCta:'استكشف الجوازات ←',
  exploreTitle:'استكشف الجوازات',exploreLead:'ابحث عن جواز أو تصفّح أبرز الجوازات حسب ترتيب مرآة التجريبي.',
  search:'ابحث عن جواز سفر',viewAll:'عرض كل جوازات السفر',
  expRank:'ترتيب مرآة التجريبي',score:'الدرجة',cats:'دخول بدون تأشيرة / عند الوصول',
  expBadge:'تجريبي',
  trustTitle:'حجم المنصة ومصادرها',trustLead:'أرقام مستمدة من مجموعات البيانات الحالية على مرآة.',
  trustCountries:'دولة/اقتصاد في المقارنة',trustIndicators:'مؤشر من البنك الدولي',
  trustPassports:'جواز سفر',trustDestinations:'وجهة سفر',trustLangs:'العربية والإنجليزية',
  trustCompare:'مقارنة الدول: البنك الدولي — مؤشرات التنمية العالمية، وتقرير السعادة العالمي.',
  trustPassport:'جواز السفر: Passport Index Data — مجموعة معلوماتية تجريبية. تحقق من المتطلبات مع السفارة أو شركة الطيران أو جهة رسمية قبل السفر.',
  trustUpdated:'تاريخ تحديث بيانات الجوازات'
 },
 en:{
  brand:'Mir\u2019ah',subtitle:'Global data platform',
  pageTitle:'Mir\u2019ah | Global data platform',
  pageDescription:'Compare quality of life, economies and happiness across countries, then explore passport mobility and destination access through clear, sourced data.',
  eyebrow:'Mir\u2019ah global data platform',
  hero:'See the world in one mirror',
  lead:'Compare quality of life, economies and happiness across countries, then explore passport mobility and destination access through clear, sourced data.',
  ctaCompare:'Compare two countries',ctaPassport:'Explore passport power',
  previewLabel:'Product preview',previewA:'Country A',previewB:'Country B',
  mLife:'Life expectancy',mNet:'Internet use',passLabel:'Mobility score',passNote:'Experimental · preview',
  productsTitle:'What would you like to explore?',productsLead:'Two clear paths — compare countries or explore passport mobility.',
  cardCompareTitle:'Country comparison',
  cardCompareBody:'Compare life expectancy, income, unemployment, internet use, safety and happiness between two countries, with historical trends and indicator rankings.',
  cardCompareCta:'Start comparing →',
  cardPassportTitle:'Passport power',
  cardPassportBody:'Explore the experimental Mir\u2019ah Mobility Score, entry categories and an interactive destination access map.',
  cardPassportCta:'Explore passports →',
  exploreTitle:'Explore passports',exploreLead:'Search for a passport or browse leading passports by experimental Mir\u2019ah rank.',
  search:'Search for a passport',viewAll:'View all passports',
  expRank:'Experimental Mir\u2019ah rank',score:'Score',cats:'Visa-free / on arrival',
  expBadge:'Experimental',
  trustTitle:'Platform scale and sources',trustLead:'Figures derived from the datasets currently published on Mir\u2019ah.',
  trustCountries:'countries/economies in comparison',trustIndicators:'World Bank indicators',
  trustPassports:'passports',trustDestinations:'travel destinations',trustLangs:'Arabic and English',
  trustCompare:'Country comparison: World Bank — World Development Indicators, and the World Happiness Report.',
  trustPassport:'Passport: Passport Index Data — an experimental informational dataset. Verify requirements with an embassy, airline, or official authority before travel.',
  trustUpdated:'Passport dataset update date'
 }
};
const state={lang:localStorage.getItem('miraahLang')||localStorage.getItem('countryMirrorLang')||'ar',open:false,active:-1,matches:[]};
const tr=()=>T[state.lang];
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function setMeta(attr,key,value){let el=document.querySelector(`meta[${attr}="${key}"]`);if(!el){el=document.createElement('meta');el.setAttribute(attr,key);document.head.appendChild(el)}el.setAttribute('content',value)}
function syncSeo(){const t=tr(),locale=state.lang==='ar'?'ar_AR':'en_US';document.title=t.pageTitle;setMeta('name','description',t.pageDescription);setMeta('property','og:title',t.pageTitle);setMeta('property','og:description',t.pageDescription);setMeta('property','og:locale',locale);setMeta('name','twitter:title',t.pageTitle);setMeta('name','twitter:description',t.pageDescription)}
function fillLeading(){
  const t=tr();
  document.querySelectorAll('#leadingPassports .pass-card').forEach(card=>{
    const h=card.querySelector('h4');
    if(h)h.textContent=state.lang==='ar'?h.dataset.nameAr:h.dataset.nameEn;
    const badge=card.querySelector('[data-exp-badge]');if(badge)badge.textContent=t.expBadge;
    const meta=card.querySelector('.pass-meta');
    if(!meta)return;
    const vf=+meta.dataset.vf||0,voa=+meta.dataset.voa||0;
    meta.textContent=`${t.expRank} #${meta.dataset.rank} · ${t.score} ${meta.dataset.score} · ${t.cats}: ${vf+voa}`;
  });
}
function render(){
  const t=tr();
  document.documentElement.lang=state.lang;
  document.documentElement.dir=state.lang==='ar'?'rtl':'ltr';
  syncSeo();syncPlatformChrome(state.lang);
  $('#brandTitle').textContent=t.brand;$('#brandSubtitle').textContent=t.subtitle;
  $('#langBtn').textContent=state.lang==='ar'?'EN':'ع';
  $('#heroEyebrow').textContent=t.eyebrow;$('#heroTitle').textContent=t.hero;$('#heroLead').textContent=t.lead;
  $('#ctaCompare').textContent=t.ctaCompare;$('#ctaPassport').textContent=t.ctaPassport;
  $('#previewLabel').textContent=t.previewLabel;$('#previewA').textContent=t.previewA;$('#previewB').textContent=t.previewB;
  $('#previewM1').textContent=t.mLife;$('#previewM1b').textContent=t.mLife;$('#previewM2').textContent=t.mNet;$('#previewM2b').textContent=t.mNet;
  $('#previewPassLabel').textContent=t.passLabel;$('#previewPassNote').textContent=t.passNote;
  $('#productsTitle').textContent=t.productsTitle;$('#productsLead').textContent=t.productsLead;
  $('#cardCompareTitle').textContent=t.cardCompareTitle;$('#cardCompareBody').textContent=t.cardCompareBody;$('#cardCompareCta').textContent=t.cardCompareCta;
  $('#cardPassportTitle').textContent=t.cardPassportTitle;$('#cardPassportBody').textContent=t.cardPassportBody;$('#cardPassportCta').textContent=t.cardPassportCta;
  $('#exploreTitle').textContent=t.exploreTitle;$('#exploreLead').textContent=t.exploreLead;
  $('#homePassportSearch').placeholder=t.search;$('#homeSearchLabel').textContent=t.search;
  $('#viewAllPassports').textContent=t.viewAll;
  $('#trustTitle').textContent=t.trustTitle;$('#trustLead').textContent=t.trustLead;
  $('#trustCountries').textContent=t.trustCountries;$('#trustIndicators').textContent=t.trustIndicators;
  $('#trustPassports').textContent=t.trustPassports;$('#trustDestinations').textContent=t.trustDestinations;$('#trustLangs').textContent=t.trustLangs;
  $('#trustSourcesCompare').textContent=t.trustCompare;$('#trustSourcesPassport').textContent=t.trustPassport;
  const upd=$('#trustUpdated');if(upd)upd.textContent=upd.dataset.updated?`${t.trustUpdated}: ${upd.dataset.updated}`:'';
  fillLeading();
}
function nameOf(p){return state.lang==='ar'?p.nameAr:p.nameEn}
function getMatches(q){
  const query=(q||'').trim().toLowerCase();
  return HOME_BOOT.passports.filter(p=>{
    if(!query)return true;
    return `${p.nameEn} ${p.nameAr} ${p.iso3} ${p.slug}`.toLowerCase().includes(query);
  }).slice(0,12);
}
function closeSuggestions(){state.open=false;state.active=-1;const box=$('#homeSuggestions'),input=$('#homePassportSearch');box.classList.remove('open');input.setAttribute('aria-expanded','false')}
function openSuggestions(){state.open=true;renderSuggestions();$('#homePassportSearch').setAttribute('aria-expanded','true')}
function renderSuggestions(){
  const box=$('#homeSuggestions'),input=$('#homePassportSearch');
  if(!state.open){box.classList.remove('open');return}
  const matches=getMatches(input.value);state.matches=matches;
  if(!matches.length){box.innerHTML=`<div class="suggestion">${state.lang==='ar'?'لا نتائج':'No results'}</div>`;box.classList.add('open');return}
  box.innerHTML=matches.map((p,i)=>`<a class="suggestion${i===state.active?' active':''}" role="option" href="/passport/${esc(p.slug)}/" data-index="${i}"><b>${flagWithNameHtml(p.iso2,nameOf(p),'sm',{lazy:false})}</b><small>${esc(tr().expRank)} #${p.rank} · ${esc(tr().score)} ${p.mobilityScore}</small></a>`).join('');
  box.classList.add('open');
}
function setupSearch(){
  const input=$('#homePassportSearch'),box=$('#homeSuggestions'),wrap=input.parentElement;
  input.onfocus=()=>openSuggestions();
  input.oninput=()=>{state.active=-1;openSuggestions()};
  input.onkeydown=e=>{
    if(e.key==='ArrowDown'){e.preventDefault();if(!state.open)openSuggestions();state.active=Math.min(state.active+1,state.matches.length-1);renderSuggestions()}
    else if(e.key==='ArrowUp'){e.preventDefault();state.active=Math.max(state.active-1,0);renderSuggestions()}
    else if(e.key==='Enter'){if(state.open&&state.active>=0&&state.matches[state.active]){e.preventDefault();location.href='/passport/'+state.matches[state.active].slug+'/'}}
    else if(e.key==='Escape'){e.preventDefault();closeSuggestions()}
  };
  document.addEventListener('click',e=>{if(!wrap.contains(e.target))closeSuggestions()});
}
function init(){
  initThemeControls();initPlatformNav();setupSearch();
  $('#langBtn').onclick=()=>{state.lang=state.lang==='ar'?'en':'ar';localStorage.setItem('miraahLang',state.lang);localStorage.removeItem('countryMirrorLang');render()};
  render();
}
init();
"""


def write_seo_files() -> None:
    robots = (
        "User-agent: *\n"
        "Allow: /\n"
        "\n"
        f"Sitemap: {brand.CANONICAL_ORIGIN}sitemap.xml\n"
    )
    (ROOT / "public" / "robots.txt").write_text(robots, encoding="utf-8")
    origin = brand.CANONICAL_ORIGIN
    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{origin}</loc>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>{origin}compare/</loc>
    <changefreq>monthly</changefreq>
    <priority>0.9</priority>
  </url>
</urlset>
"""
    (ROOT / "public" / "sitemap.xml").write_text(sitemap, encoding="utf-8")


def main() -> int:
    from sync_flag_assets import main as sync_flags
    sync_flags()
    if not PASSPORT_INDEX.is_file():
        raise SystemExit("Missing passport index — run passport data update first")
    index = json.loads(PASSPORT_INDEX.read_text(encoding="utf-8"))
    passports = len(index.get("passports", []))
    destinations = DESTINATION_COUNT
    if index.get("passports"):
        destinations = int(index["passports"][0].get("destinationCount") or destinations)
    html = build_html(
        index,
        countries=COMPARE_COUNTRIES,
        indicators=COMPARE_INDICATORS,
        passports=passports,
        destinations=destinations,
    )
    INDEX_OUT.write_text(html, encoding="utf-8", newline="\n")
    write_seo_files()
    print(f"wrote {INDEX_OUT.relative_to(ROOT)}")
    print(
        f"counts countries={COMPARE_COUNTRIES} indicators={COMPARE_INDICATORS} "
        f"passports={passports} destinations={destinations}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
