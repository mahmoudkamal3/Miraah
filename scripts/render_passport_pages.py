#!/usr/bin/env python3
"""Render Mir’ah Passport Power static pages and refresh the sitemap."""

from __future__ import annotations

import json
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import passport_core as core  # noqa: E402
import passport_map_ui as map_ui  # noqa: E402
import miraah_brand as brand  # noqa: E402
import miraah_chrome as chrome  # noqa: E402
import miraah_flags as flags  # noqa: E402
import miraah_theme as theme  # noqa: E402

CANONICAL = brand.CANONICAL_ORIGIN
PASSPORT_DIR = ROOT / "public" / "passport"
ASSETS_DIR = PASSPORT_DIR / "assets"
DATA_INDEX = core.PUBLIC_DATA / "index.json"
DATA_META = core.PUBLIC_DATA / "meta.json"

PASSPORT_INDEXING_ENABLED = False  # Flip to True only after commercially reviewed complete data + intentional re-index.
PASSPORT_COUNT_LABEL = 199
TRAVEL_DESTINATION_LABEL = 198

CSS = chrome.chrome_css_bundle() + r'''
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:radial-gradient(circle at 85% 0,var(--radial-a) 0,transparent 30%),radial-gradient(circle at 5% 50%,var(--radial-b) 0,transparent 28%),var(--bg);color:var(--text);font-family:Inter,"Segoe UI",Tahoma,Arial,sans-serif;min-height:100vh}
button,input,select,a{font:inherit}
.shell{max-width:1100px;margin:auto;padding:22px}
.topbar{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:18px;flex-wrap:wrap}
.brand{display:flex;align-items:center;gap:12px;text-decoration:none;color:inherit}
.logo{width:44px;height:44px;border-radius:14px;overflow:hidden;flex-shrink:0;box-shadow:0 8px 30px var(--glow-brand);display:block;padding:0;background:transparent}
.logo-mark{width:44px;height:44px;display:block}
.brand-text{display:flex;flex-direction:column}
.brand h1{margin:0;font-size:22px;font-weight:700;letter-spacing:-.02em;font-family:system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}
.brand p{margin:4px 0 0;color:var(--muted);font-size:12px}
.product-nav{display:flex;gap:6px;padding:4px;border:1px solid var(--line);border-radius:14px;background:var(--surface-soft)}
.product-nav a{text-decoration:none;color:var(--muted);padding:8px 12px;border-radius:10px;font-size:13px;font-weight:650}
.product-nav a:hover,.product-nav a:focus-visible{color:var(--text);background:var(--hover)}
.product-nav a.active,.product-nav a[aria-current="page"]{color:var(--text-on-brand);background:linear-gradient(135deg,var(--brand-cyan),var(--brand-blue-soft))}
.actions{display:flex;gap:8px;align-items:center}
.btn{border:1px solid var(--line);background:var(--surface-soft);color:var(--text);padding:9px 13px;border-radius:11px;cursor:pointer;text-decoration:none;display:inline-flex;align-items:center}
.btn:hover,.btn:focus-visible{border-color:var(--btn-hover-border)}
.lang-btn{min-width:48px;font-weight:800;color:var(--text-on-brand);background:linear-gradient(135deg,var(--brand-cyan),var(--brand-blue-soft));border:0}
.hero{background:linear-gradient(135deg,var(--surface-hero-a),var(--surface-hero-b));border:1px solid var(--line);border-radius:24px;padding:24px;box-shadow:var(--shadow);position:relative;overflow:visible;z-index:20}
.hero h2{margin:0 0 8px;font-size:26px}.hero .lead{color:var(--muted);margin:0;max-width:720px;line-height:1.7}
.warning{margin-top:16px;padding:12px 14px;border-radius:14px;border:1px solid var(--warn-banner-border);background:var(--warn-banner-bg);color:var(--warn-banner-fg);font-size:13px;line-height:1.6}
.select-panel{margin-top:20px;position:relative;z-index:30;max-width:520px}
.select-panel label{display:block;color:var(--muted);font-size:12px;margin-bottom:8px}
.search-wrap{position:relative}
.country-search{width:100%;background:var(--input-bg);color:var(--text);border:1px solid var(--border-input);border-radius:10px;outline:none;padding-block:12px;padding-inline:40px 72px}
.country-search:focus{border-color:var(--a);box-shadow:0 0 0 3px var(--focus)}
.search-icon{position:absolute;inset-inline-start:13px;top:50%;transform:translateY(-50%);color:var(--muted);pointer-events:none}
.field-actions{position:absolute;inset-inline-end:6px;top:50%;transform:translateY(-50%);display:flex;align-items:center;gap:1px}
.clear-btn,.chevron-btn{border:0;background:transparent;color:var(--muted);cursor:pointer;padding:4px 7px;border-radius:6px}
.clear-btn{font-size:16px;display:none}.clear-btn.visible{display:block}
.clear-btn:hover,.chevron-btn:hover{color:var(--text);background:var(--vs-bg)}
.chevron-btn{font-size:11px}.chevron-btn.open{color:var(--text)}
.suggestions{position:absolute;top:calc(100% + 6px);inset-inline:0;background:var(--input-bg);border:1px solid var(--border-strong);border-radius:12px;max-height:260px;overflow-y:auto;z-index:100;box-shadow:var(--shadow);display:none}
.suggestions.open{display:block}
.suggestion{padding:10px 12px;cursor:pointer;border-bottom:1px solid var(--border)}.suggestion:last-child{border-bottom:0}
.suggestion:hover,.suggestion.active{background:var(--hover)}
.suggestion small{display:block;color:var(--muted);font-size:10px;margin-top:3px}
.empty-state{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;padding:48px 16px;color:var(--muted);text-align:center}
.empty-state[hidden],.results[hidden]{display:none}
.empty-state-icon{width:34px;height:34px;border-radius:50%;display:grid;place-items:center;background:var(--table-head);border:1px solid var(--line);color:var(--a)}
.results{margin-top:22px;animation:resultsIn .42s ease}
@keyframes resultsIn{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}
@media (prefers-reduced-motion:reduce){.results{animation:none}html{scroll-behavior:auto}}

/* Passport card: identity | score | illustration */
.passport-card{display:grid;grid-template-columns:1fr 1.15fr 1fr;gap:18px;align-items:stretch;background:linear-gradient(155deg,var(--panel2),var(--panel));border:1px solid var(--line);border-radius:18px;padding:18px}
.passport-visual{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;min-height:220px}
.score-panel{background:var(--surface-card);border:1px solid var(--line);border-radius:16px;padding:18px 20px;display:flex;flex-direction:column;gap:10px;justify-content:center}
.score-main{display:flex;flex-direction:column;gap:4px}
.score-main strong{display:block;font-size:clamp(48px,8vw,68px);line-height:1.05;color:var(--a);font-variant-numeric:tabular-nums;font-feature-settings:"tnum";letter-spacing:-.02em}
.score-main span{font-size:13px;color:var(--muted)}
.rank-secondary{display:flex;flex-wrap:wrap;align-items:baseline;gap:8px;color:var(--muted);font-size:13px}
.rank-secondary b{color:var(--text);font-size:clamp(24px,4vw,34px);font-variant-numeric:tabular-nums;font-feature-settings:"tnum"}
.badge-exp{display:inline-flex;align-items:center;gap:6px;padding:4px 9px;border-radius:999px;border:1px solid var(--badge-exp-border);background:var(--badge-exp-bg);color:var(--badge-exp-fg);font-size:11px;font-weight:700;letter-spacing:.02em}
.coverage-line,.update-line{margin:0;color:var(--muted);font-size:12px;line-height:1.55}
.method-actions{display:flex;flex-wrap:wrap;gap:8px;margin-top:4px}

/* Passport book illustration */
.passport-book{position:relative;width:min(100%,220px);aspect-ratio:3/4;perspective:800px}
.passport-book .passport-shadow{position:absolute;inset:auto 8% -10px 8%;height:18px;background:#0006;border-radius:50%;filter:blur(8px);z-index:0}
.passport-book .passport-spine{position:absolute;inset-inline-start:0;top:4%;bottom:4%;width:12px;border-radius:6px 0 0 6px;background:linear-gradient(90deg,#0006,#0000);z-index:2;pointer-events:none}
.passport-book .passport-cover{position:relative;z-index:1;width:100%;height:100%;border-radius:10px 14px 14px 10px;overflow:hidden;box-shadow:0 16px 40px #0007,inset 0 0 0 1px #ffffff22;display:flex;flex-direction:column;align-items:center;justify-content:space-between;padding:18px 14px 16px;color:#f4f8ff}
.passport-book .passport-pattern{position:absolute;inset:0;opacity:.18;background:
  radial-gradient(circle at 20% 20%,#fff8 0,transparent 40%),
  repeating-linear-gradient(45deg,#fff2 0 1px,transparent 1px 10px),
  repeating-linear-gradient(-45deg,#fff1 0 1px,transparent 1px 12px);
pointer-events:none}
.passport-book .passport-chip{position:relative;z-index:1;align-self:flex-end;margin-inline-end:4px;width:36px;height:28px;opacity:.92}
.passport-book .passport-chip svg{width:100%;height:100%;display:block}
.passport-book .passport-flag{display:none}
.passport-book .passport-emblem{position:relative;z-index:1;width:58px;height:58px;margin:4px 0 2px;filter:drop-shadow(0 2px 6px #0005)}
.passport-book .passport-emblem svg{width:100%;height:100%;display:block}
.passport-book .passport-country{position:relative;z-index:1;text-align:center;font-size:14px;font-weight:800;line-height:1.25;max-width:90%;text-shadow:0 2px 8px #0006;color:#f7e7b0;letter-spacing:.02em}
.passport-book .passport-label{position:relative;z-index:1;font-size:11px;font-weight:700;letter-spacing:.22em;text-transform:uppercase;opacity:.95}
.passport-book .passport-label.gold-type{color:#f0d792;text-shadow:0 1px 0 #5a4418aa}
.passport-book .passport-iso2{display:none}
.passport-book .passport-fallback-note{position:relative;z-index:1;font-size:8px;letter-spacing:.03em;opacity:.72;text-align:center;max-width:92%;line-height:1.35;color:#d7e0ec;padding-top:2px}
.passport-book .passport-cover{justify-content:flex-start;gap:6px;padding:16px 14px 14px}
.passport-book .passport-spine{width:14px;background:linear-gradient(90deg,#0008,#0002 55%,#fff1);box-shadow:inset -1px 0 0 #fff1}
.passport-book.is-photo .passport-spine{opacity:.35}
.passport-book .passport-photo-frame{position:relative;z-index:1;width:100%;height:100%;border-radius:10px 14px 14px 10px;overflow:hidden;box-shadow:0 16px 40px #0007,inset 0 0 0 1px #ffffff22;background:#0a1524}
.passport-book .passport-photo-frame img{display:block;width:100%;height:100%;object-fit:contain;object-position:center;background:#0a1524}
.cover-attribution{display:flex;flex-wrap:wrap;gap:8px;align-items:center;justify-content:center;max-width:260px}
.cover-attribution .btn{font-size:11px;padding:6px 10px;border-radius:9px}
.cover-attr-label{color:var(--muted);font-size:11px;text-align:center;line-height:1.4}
.method-modal .image-attr-box{margin-top:8px;padding:12px;border:1px solid var(--line);border-radius:12px;background:var(--surface-card)}
.method-modal .image-attr-box p{margin:0 0 8px}
.method-modal .image-attr-box p:last-child{margin:0}

.coverage-strip{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:12px}
.coverage-strip .item{background:var(--surface-card);border:1px solid var(--line);border-radius:12px;padding:10px 12px}
.coverage-strip .item span{display:block;color:var(--muted);font-size:11px;margin-bottom:4px}
.coverage-strip .item b{font-size:clamp(22px,3.5vw,28px);line-height:1.25;font-variant-numeric:tabular-nums;font-feature-settings:"tnum"}
.coverage-strip .item.compact b{font-size:13px;font-weight:650;line-height:1.4}

.cats{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:16px}
.cat{background:var(--surface-card);border:1px solid var(--line);border-radius:14px;padding:12px}
.cat b{display:block;font-size:clamp(26px,4vw,34px);margin-top:4px;font-variant-numeric:tabular-nums;font-feature-settings:"tnum"}
.cat span{color:var(--muted);font-size:11px}

.panel{background:linear-gradient(160deg,var(--surface-raised),var(--surface));border:1px solid var(--line);border-radius:18px;padding:17px;margin-top:16px}
.panel h4{margin:0 0 10px;font-size:15px}
.panel p,.panel li{color:var(--muted);font-size:13px;line-height:1.7}
.panel .chart-sub{margin:0 0 12px;color:var(--muted);font-size:12px}

.explorer-row{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:10px 0}
.explorer-row.search-row{margin-top:4px}
.dest-search{width:100%;background:var(--input-bg);color:var(--text);border:1px solid var(--border-input);border-radius:10px;padding:10px 12px}
.filters{display:flex;flex-wrap:wrap;gap:8px;margin:0}
.chip{border:1px solid var(--line);background:var(--surface-soft);color:var(--muted);border-radius:999px;padding:7px 11px;cursor:pointer;font-size:12px}
.chip.active,.chip:hover{color:var(--text);border-color:var(--btn-hover-border);background:var(--hover)}
.region-select{border:1px solid var(--line);background:var(--surface-soft);color:var(--text);border-radius:10px;padding:8px 10px;min-width:200px}
.results-counter{color:var(--muted);font-size:13px;margin-inline-start:auto}
.table-wrap{overflow:auto;max-height:520px;border-radius:12px;border:1px solid var(--line);margin-top:8px}
table{width:100%;border-collapse:collapse;font-size:13px;min-width:640px}
th{position:sticky;top:0;background:var(--table-head);color:var(--table-head-text);text-align:start;padding:11px;z-index:2;box-shadow:0 1px 0 var(--line)}
td{padding:10px 11px;border-top:1px solid var(--table-row)}
tr:hover td{background:var(--table-head)88}
#destBody tr.is-map-active td{background:var(--map-row-active);box-shadow:inset 0 0 0 1px var(--map-row-active-ring)}
.table-empty{padding:28px 16px;text-align:center;color:var(--muted);font-size:13px}
.status-pill{display:inline-block;padding:3px 8px;border-radius:999px;font-size:11px;font-weight:650;border:1px solid transparent}
.status-pill.visa_free{background:var(--pill-vf-bg);color:var(--pill-vf-fg);border-color:var(--st-vf)}
.status-pill.visa_on_arrival{background:var(--pill-voa-bg);color:var(--pill-voa-fg);border-color:var(--st-voa)}
.status-pill.eta{background:var(--pill-eta-bg);color:var(--pill-eta-fg);border-color:var(--st-eta)}
.status-pill.evisa{background:var(--pill-ev-bg);color:var(--pill-ev-fg);border-color:var(--st-ev)}
.status-pill.visa_required{background:var(--pill-vr-bg);color:var(--pill-vr-fg);border-color:var(--st-vr)}
.status-pill.no_admission{background:var(--pill-na-bg);color:var(--pill-na-fg);border-color:var(--st-na)}

.chart{height:360px}.chart svg{width:100%;height:100%}
.bar-label{fill:var(--muted);font-size:12px}
.bar-value{fill:var(--text);font-size:12px;font-variant-numeric:tabular-nums}
.bar{fill:var(--a)}

.source-summary{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-top:4px}
.source-card{background:var(--surface-card);border:1px solid var(--line);border-radius:12px;padding:12px 14px}
.source-card span{display:block;color:var(--muted);font-size:11px;margin-bottom:6px}
.source-card b{display:block;font-size:13px;line-height:1.5;font-weight:650}
.source-actions{margin-top:12px}

.method-details{margin-top:12px;border:1px solid var(--line);border-radius:14px;background:var(--surface-card);padding:12px 14px}
.method-details summary{cursor:pointer;font-weight:700;color:var(--text)}
.method-details[open] summary{margin-bottom:8px}
dialog.method-modal{border:1px solid var(--line);border-radius:16px;background:var(--surface-modal);color:var(--text);padding:0;max-width:min(680px,92vw)}
dialog.method-modal::backdrop{background:var(--surface-backdrop)}
.method-modal .inner{padding:18px}
.method-modal h3{margin:0 0 10px}
.method-modal h4{margin:16px 0 8px;font-size:14px;color:var(--a)}
.method-modal ul{margin:0;padding-inline-start:18px}
.method-modal p,.method-modal li{color:var(--muted);font-size:13px;line-height:1.7}
.method-modal a{color:var(--a)}
.source{margin:18px 2px 4px;color:var(--muted);font-size:11px;line-height:1.7}

@media(max-width:900px){
  .cats,.coverage-strip,.source-summary{grid-template-columns:repeat(2,1fr)}
  .passport-card{grid-template-columns:1fr}
  .chart{height:420px}
}
@media(max-width:650px){
  .shell{padding:12px}
  .topbar{align-items:flex-start;flex-direction:column}
  .cats,.coverage-strip,.source-summary{grid-template-columns:1fr}
  .product-nav{width:100%;overflow:auto}
  .results-counter{margin-inline-start:0;width:100%}
}
''' + flags.FLAG_CSS + map_ui.MAP_CSS

JS = theme.THEME_JS + chrome.CHROME_JS + r'''
const $=s=>document.querySelector(s);
const CANONICAL='https://miraah.mirapp.workers.dev/';
const COVERAGE={passports:199,travelDestinations:198};
const REGION_LABELS={
  'East Asia & Pacific':{en:'East Asia & Pacific',ar:'شرق آسيا والمحيط الهادئ'},
  'Europe & Central Asia':{en:'Europe & Central Asia',ar:'أوروبا وآسيا الوسطى'},
  'Latin America & Caribbean':{en:'Latin America & Caribbean',ar:'أمريكا اللاتينية والكاريبي'},
  'Middle East & North Africa':{en:'Middle East & North Africa',ar:'الشرق الأوسط وشمال أفريقيا'},
  'North America':{en:'North America',ar:'أمريكا الشمالية'},
  'South Asia':{en:'South Asia',ar:'جنوب آسيا'},
  'Sub-Saharan Africa':{en:'Sub-Saharan Africa',ar:'أفريقيا جنوب الصحراء'},
  'Other':{en:'Other',ar:'أخرى'}
};
const T={
 ar:{
  brand:'مرآة',subtitle:'قوة جواز السفر',pageTitleLanding:'مرآة | قوة جواز السفر (تجريبي)',
  pageDescriptionLanding:'مرآة — درجة التنقل التجريبية لجوازات السفر عبر 199 جوازًا و198 وجهة سفر.',
  navHome:'الرئيسية',navCompare:'مقارنة الدول',navPassport:'قوة جواز السفر',
  hero:'قوة جواز السفر، بدرجة مرآة التجريبية',lead:'اختر جواز سفر لعرض درجة التنقل في مرآة وترتيب مرآة التجريبي وفئات الدخول إلى الوجهات.',
  searchLabel:'اختر جواز السفر',search:'ابحث عن دولة',empty:'اختر جواز سفر لعرض قوة التنقل',
  clear:'مسح',toggle:'عرض قائمة الجوازات',score:'درجة التنقل في مرآة',rank:'ترتيب مرآة التجريبي',
  coverage:'محسوب بين 199 جواز سفر وعبر 198 وجهة سفر',experimental:'تجريبي',
  destinations:'وجهات قابلة للمقارنة',passportsRanked:'عدد الجوازات المرتبة',updated:'تاريخ تحديث مجموعة البيانات',retrieved:'تاريخ الاسترجاع',
  dataUpdatedLabel:'آخر تحديث للبيانات',sourceLabel:'المصدر',sourceName:'Passport Index Data',
  sourceHint:'بيانات تجريبية؛ تحقّق من السفارة أو شركة الطيران قبل السفر.',
  methodology:'المنهجية',methodologyOpen:'تفاصيل المصدر والمنهجية',methodologyTitle:'منهجية درجة التنقل في مرآة',
  sourceTechTitle:'تفاصيل المصدر',licenseLabel:'رخصة المستودع',upstreamWarn:'تحذير المصدر الأصلي',
  commercialWarn:'تحذير الحقوق التجارية',repoLabel:'مستودع GitHub',
  cats:{visa_free:'بدون تأشيرة',visa_on_arrival:'تأشيرة عند الوصول (دون موافقة مسبقة)',eta:'تصريح إلكتروني (eTA)',evisa:'تأشيرة إلكترونية',visa_required:'تأشيرة تقليدية مطلوبة',no_admission:'غير مسموح بالدخول',home:'البلد نفسه (مستبعد من الدرجة)'},
  explorer:'مستكشف الوجهات',filterAll:'الكل',regionAll:'كل المناطق',destSearch:'ابحث عن وجهة',days:'مدة الإقامة',
  noResults:'لا توجد وجهات مطابقة',showing:(x,y)=>`عرض ${x} من ${y} وجهة`,
  colDest:'الوجهة',colAccess:'الوصول',colRegion:'المنطقة',colStay:'الإقامة',
  chartTitle:'توزيع الوصول حسب المنطقة',chartSub:'عدد الوجهات حسب المنطقة',
  passportWord:'جواز سفر',
  explain:[
    'نقطة واحدة لكل وجهة بلا تأشيرة، أو بتأشيرة عند الوصول دون موافقة مسبقة قبل السفر، أو بتصريح إلكتروني (eTA).',
    'صفر نقاط للتأشيرة الإلكترونية، أو التأشيرة التقليدية، أو منع الدخول، أو أي متطلب يحتاج موافقة حكومية مسبقة.',
    'وجهة البلد نفسه مستبعدة من الدرجة.',
    'الترتيب كثيف: الدرجات المتساوية تشترك في نفس الترتيب.',
    'التغطية الحالية: 199 جواز سفر و198 وجهة سفر قابلة للمقارنة.',
    'النتائج من منصات تستخدم 227 وجهة أو أكثر ليست قابلة للمقارنة مباشرة مع درجة مرآة الحالية.',
    'البيانات إرشادية ويجب التحقق عبر السفارة أو شركة الطيران أو جهة رسمية.'
  ],
  source:'مصدر البيانات',disclaimerTitle:'تنبيه مهم',
  disclaimer:'قواعد التأشيرات تتغير. معلومات مرآة إرشادية وليست نصيحة سفر قانونية. تحقق دائمًا عبر السفارة أو شركة الطيران أو جهة رسمية.',
  attribution:'بيانات المتطلبات من مستودع imorte/passport-index-data (رخصة MIT على المستودع). حقوق المحتوى/قاعدة البيانات لدى المصدر الأصلي تحتاج مراجعة منفصلة.',
  upstreamDetail:'البيانات مأخوذة من مستودع طرف ثالث وليست من إنتاج مرآة. رخصة MIT على المستودع لا تعني تصفية حقوق قاعدة البيانات/المحتوى لدى المصدر الأصلي.',
  commercialDetail:'هذا المصدر مؤقت. أكمل مراجعة حقوق المصدر الأصلي قبل أي استخدام تجاري أو مطالبات سفر موثوقة.',
  openPage:'صفحة الجواز',close:'إغلاق',
  imageAttr:'إسناد الصورة',imageAttrTitle:'إسناد صورة الغلاف',
  miraahIllustration:'تصميم توضيحي من مرآة — ليس صورة رسمية',
  imageAttrFallback:'لا تُعرض صور أغلفة جوازات حقيقية للعامة حالياً. يُعرض تصميم توضيحي من مرآة — ليس صورة رسمية.',
  imageAttrEmblem:'ترخيص الصورة لا يحسم قيود الشعارات الرسمية أو إعادة إنتاج جوازات السفر.',
  imageAttrAll:'كل إسنادات الصور',
  historicCoverNote:'قد تكون الصورة تاريخية أو غير مؤكدة كغلاف حالي.',
  mapTitle:'خريطة الوصول حول العالم',
  mapLead:'استكشف متطلبات دخول الوجهات باستخدام جواز السفر المحدد',
  mapZoomIn:'تكبير',mapZoomOut:'تصغير',mapReset:'إعادة الضبط',mapFullscreen:'ملء الشاشة',
  mapHomeLabel:'الدولة المُصدرة للجواز',mapUnmapped:'غير مُعيَّن على الخريطة',mapError:'تعذّر تحميل الخريطة المحلية',
  stayOfficial:'حسب الشروط الرسمية',
  mapSourceGeo:'بيانات الخريطة الجغرافية: Natural Earth',
  mapSourceVisa:'تصنيفات الدخول: Passport Index Data — بيانات تجريبية'
 },
 en:{
  brand:'Mir\u2019ah',subtitle:'Passport power',pageTitleLanding:'Mir\u2019ah | Passport power (experimental)',
  pageDescriptionLanding:'Mir\u2019ah — experimental passport mobility scores across 199 passports and 198 travel destinations.',
  navHome:'Home',navCompare:'Compare countries',navPassport:'Passport power',
  hero:'Passport power with an experimental Mir\u2019ah score',lead:'Choose a passport to see the Mir\u2019ah Mobility Score, experimental Mir\u2019ah rank, and destination access categories.',
  searchLabel:'Choose a passport',search:'Search for a country',empty:'Choose a passport to explore mobility power',
  clear:'Clear',toggle:'Show passport list',score:'Mir\u2019ah Mobility Score',rank:'Experimental Mir\u2019ah rank',
  coverage:'Calculated across 199 passports and 198 travel destinations',experimental:'Experimental',
  destinations:'Travel destinations compared',passportsRanked:'Passports ranked',updated:'Dataset update date',retrieved:'Retrieval date',
  dataUpdatedLabel:'Data updated',sourceLabel:'Source',sourceName:'Passport Index Data',
  sourceHint:'Experimental data; verify with an embassy or airline before travel.',
  methodology:'Methodology',methodologyOpen:'Source and methodology details',methodologyTitle:'Mir\u2019ah Mobility Score methodology',
  sourceTechTitle:'Source details',licenseLabel:'Repository license',upstreamWarn:'Upstream source warning',
  commercialWarn:'Commercial-rights warning',repoLabel:'GitHub repository',
  cats:{visa_free:'Visa-free',visa_on_arrival:'Visa on arrival (no pre-departure approval)',eta:'eTA',evisa:'eVisa',visa_required:'Traditional visa required',no_admission:'No admission',home:'Home destination (excluded)'},
  explorer:'Destination explorer',filterAll:'All',regionAll:'All regions',destSearch:'Search destinations',days:'Stay',
  noResults:'No matching destinations',showing:(x,y)=>`Showing ${x} of ${y} destinations`,
  colDest:'Destination',colAccess:'Access',colRegion:'Region',colStay:'Stay',
  chartTitle:'Access distribution by region',chartSub:'Number of destinations by region',
  passportWord:'PASSPORT',
  explain:[
    'One point for visa-free access, visa on arrival without pre-departure approval, and eTA.',
    'Zero points for eVisa, traditional visa, no admission, or any requirement that needs prior government approval.',
    'The passport\u2019s own country is excluded from scoring.',
    'Equal scores receive the same dense rank.',
    'Current coverage is 199 passports and 198 comparable travel destinations.',
    'Results from platforms that use 227+ destinations are not directly comparable to this Mir\u2019ah score.',
    'This information is informational only and must be verified with an embassy, airline, or official authority.'
  ],
  source:'Data source',disclaimerTitle:'Important notice',
  disclaimer:'Visa rules change. Mir\u2019ah information is informational only and is not legal travel advice. Always verify with an embassy, airline, or official authority.',
  attribution:'Requirement data from the imorte/passport-index-data repository (MIT license on the repository). Upstream database/content rights still need separate review.',
  upstreamDetail:'Data comes from a third-party repository and was not produced by Mir\u2019ah. An MIT license on the repository packaging must not be treated as commercially cleared rights to the underlying visa database/content.',
  commercialDetail:'This source is provisional. Complete a separate upstream-rights review before commercial monetization or authoritative travel claims.',
  openPage:'Passport page',close:'Close',
  imageAttr:'Image attribution',imageAttrTitle:'Cover image attribution',
  miraahIllustration:'Mir\u2019ah illustration — not an official reproduction',
  imageAttrFallback:'Real passport-cover photographs are not shown publicly yet. A Mir\u2019ah illustration is displayed and is not an official reproduction.',
  imageAttrEmblem:'A photograph license does not clear separate restrictions on state emblems or passport reproduction.',
  imageAttrAll:'All image attributions',
  historicCoverNote:'This image may be historic or not confirmed as the current cover.',
  mapTitle:'Worldwide access map',
  mapLead:'Explore destination entry requirements for the selected passport',
  mapZoomIn:'Zoom in',mapZoomOut:'Zoom out',mapReset:'Reset view',mapFullscreen:'Fullscreen map',
  mapHomeLabel:'Issuing passport country',mapUnmapped:'Not mapped',mapError:'Could not load the local map asset',
  stayOfficial:'Per official conditions',
  mapSourceGeo:'Geographic map data: Natural Earth',
  mapSourceVisa:'Entry classifications: Passport Index Data — experimental data'
 }
};
const CAT_ORDER=['visa_free','visa_on_arrival','eta','evisa','visa_required','no_admission','home'];
const CAT_FILTER_ORDER=['visa_free','visa_on_arrival','eta','evisa','visa_required','no_admission'];
const REAL_PASSPORT_COVERS_ENABLED=false;
const state={lang:localStorage.getItem('miraahLang')||localStorage.getItem('countryMirrorLang')||'ar',query:'',open:false,activeIndex:-1,matches:[],selected:null,detail:null,index:null,meta:null,covers:null,destQuery:'',statusFilter:'all',regionFilter:'all'};
const tr=()=>T[state.lang];
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
''' + flags.FLAG_JS + r'''
const nameOf=p=>state.lang==='ar'?p.nameAr:p.nameEn;
const searchBlob=p=>`${p.nameEn} ${p.nameAr} ${p.iso3}`.toLowerCase();
function coverFor(p){
  if(!REAL_PASSPORT_COVERS_ENABLED)return null;
  const meta=state.covers?.covers?.[p.iso3]||null;
  if(!meta||!meta.localFile)return null;
  if(meta.deploymentStatus&&meta.deploymentStatus!=='cleared')return null;
  if(meta.emblemRightsReviewRequired)return null;
  return meta;
}
function regionLabel(region){const map=REGION_LABELS[region];if(!map)return region||'—';return state.lang==='ar'?map.ar:map.en}
function formatDate(iso){
  if(!iso)return '—';
  const parts=String(iso).slice(0,10).split('-');
  if(parts.length!==3)return iso;
  const y=+parts[0],m=+parts[1],d=+parts[2];
  if(!y||!m||!d)return iso;
  if(state.lang==='ar'){
    const months=['يناير','فبراير','مارس','أبريل','مايو','يونيو','يوليو','أغسطس','سبتمبر','أكتوبر','نوفمبر','ديسمبر'];
    return `${d} ${months[m-1]} ${y}`;
  }
  const months=['January','February','March','April','May','June','July','August','September','October','November','December'];
  return `${d} ${months[m-1]} ${y}`;
}
function coverColor(iso2, iso3){
  const code=(iso3||iso2||'XX').toUpperCase();
  // Documented public booklet colour families (not official emblems).
  const burgundy=new Set(['AUT','BEL','BGR','HRV','CYP','CZE','DNK','EST','FIN','FRA','DEU','GRC','HUN','IRL','ITA','LVA','LTU','LUX','MLT','NLD','POL','PRT','ROU','SVK','SVN','ESP','SWE','CHE','NOR','ISL','LIE','AND','MCO','SMR','VAT','GBR']);
  const navy=new Set(['USA','CAN','AUS','NZL','MYS','SGP','HKG','MAC','PHL','THA','IDN','IND','PAK','BGD','LKA','NPL','BTN','MDV']);
  const green=new Set(['SAU','ARE','QAT','KWT','BHR','OMN','MAR','DZA','TUN','LBY','MRT','SDN','EGY','JOR','IRQ','YEM','PSE','COM','SEN','MLI','NER','TCD','BFA','GIN','GNB','SLE','LBR','CIV','TGO','BEN','GHA','NGA','CMR','GAB','COG','COD','CAF','GNQ','STP','AGO','MOZ','ZWE','ZMB','MWI','TZA','KEN','UGA','RWA','BDI','ETH','ERI','DJI','SOM','SSD']);
  const red=new Set(['CHN','VNM','PRK','ALB','TUR','MKD','MNE','SRB','BIH']);
  if(burgundy.has(code))return '#6b1f33';
  if(navy.has(code))return '#0f2f5b';
  if(green.has(code))return '#1a4a32';
  if(red.has(code))return '#7a1c1c';
  if(code==='JPN'||code==='KOR')return '#1a1a1a';
  if(code==='RUS'||code==='BLR'||code==='UKR')return '#1a3558';
  if(code==='BRA'||code==='ARG'||code==='CHL'||code==='URY'||code==='PRY'||code==='BOL'||code==='PER'||code==='COL'||code==='VEN'||code==='ECU'||code==='MEX')return '#0f3d2e';
  const s=String(iso2||'XX').toUpperCase();
  let h=0;for(let i=0;i<s.length;i++)h=s.charCodeAt(i)+((h<<5)-h);
  const hue=Math.abs(h)%360;
  return `hsl(${hue} 38% 24%)`;
}
function chipSvg(){
  return `<svg viewBox="0 0 36 28" aria-hidden="true" focusable="false"><rect x="1" y="1" width="34" height="26" rx="4" fill="#d4b76a" stroke="#8a7340" stroke-width="1.2"/><rect x="6" y="7" width="10" height="14" rx="1.5" fill="#b8954f" opacity=".95"/><path d="M18 10h12M18 14h12M18 18h8" stroke="#6e5a30" stroke-width="1.4" stroke-linecap="round"/></svg>`;
}
function emblemSvg(){
  return `<svg viewBox="0 0 64 64" aria-hidden="true" focusable="false"><circle cx="32" cy="32" r="22" fill="none" stroke="#e6c878" stroke-width="1.6" opacity=".9"/><circle cx="32" cy="32" r="14" fill="none" stroke="#e6c878" stroke-width="1.1" opacity=".55"/><path d="M32 12v40M12 32h40" stroke="#e6c878" stroke-width="1.1" opacity=".35"/><path d="M22 24c4 6 8 10 10 18 2-8 6-12 10-18" fill="none" stroke="#f0d792" stroke-width="1.4" stroke-linecap="round" opacity=".85"/></svg>`;
}
function setMeta(attr,key,value){let el=document.querySelector(`meta[${attr}="${key}"]`);if(!el){el=document.createElement('meta');el.setAttribute(attr,key);document.head.appendChild(el)}el.setAttribute('content',value)}
function syncSeo(title,description,canonical){const ogImage='https://miraah.mirapp.workers.dev/assets/brand/miraah-social-card.png';document.title=title;setMeta('name','description',description);setMeta('property','og:title',title);setMeta('property','og:description',description);setMeta('property','og:url',canonical);setMeta('property','og:locale',state.lang==='ar'?'ar_AR':'en_US');setMeta('property','og:image',ogImage);setMeta('name','twitter:title',title);setMeta('name','twitter:description',description);setMeta('name','twitter:image',ogImage);const link=document.querySelector('link[rel="canonical"]');if(link)link.href=canonical}
function destinationUniverse(totals){
  if(!totals)return COVERAGE.travelDestinations;
  return CAT_FILTER_ORDER.reduce((n,k)=>n+(totals[k]||0),0)||COVERAGE.travelDestinations;
}
function fillMethodology(){
  const t=tr();
  const repo=state.meta?.sourceRepository||'https://github.com/imorte/passport-index-data';
  const license=state.meta?.license||'MIT';
  const retrieved=state.meta?.retrievalTimestampUtc||'—';
  const updated=formatDate(state.meta?.datasetUpdateDate);
  $('#explainTitle').textContent=t.methodologyTitle;
  $('#explainList').innerHTML=t.explain.map(x=>`<li>${esc(x)}</li>`).join('');
  $('#methodSummary').textContent=t.methodology;
  $('#methodDates').textContent=`${esc(t.updated)}: ${esc(updated)} · ${esc(t.retrieved)}: ${esc(retrieved)}`;
  $('#methodModalTitle').textContent=t.methodologyTitle;
  $('#methodModalList').innerHTML=t.explain.map(x=>`<li>${esc(x)}</li>`).join('');
  $('#methodModalDates').textContent=`${esc(t.updated)}: ${esc(updated)} · ${esc(t.retrieved)}: ${esc(retrieved)}`;
  $('#methodTechTitle').textContent=t.sourceTechTitle;
  $('#methodRepoLabel').textContent=t.repoLabel;
  $('#methodRepoLink').href=repo;
  $('#methodRepoLink').textContent=repo;
  $('#methodLicenseLabel').textContent=t.licenseLabel;
  $('#methodLicenseBody').textContent=`${license} — ${t.attribution}`;
  $('#methodUpstreamLabel').textContent=t.upstreamWarn;
  $('#methodUpstreamBody').textContent=t.upstreamDetail;
  $('#methodCommercialLabel').textContent=t.commercialWarn;
  $('#methodCommercialBody').textContent=t.commercialDetail;
  $('#methodRetrievedLabel').textContent=t.retrieved;
  $('#methodRetrievedBody').textContent=retrieved;
  $('#methodologyBtn').textContent=t.methodologyOpen;
  const srcBtn=$('#sourceMethodBtn');if(srcBtn)srcBtn.textContent=t.methodologyOpen;
  $('#methodModalClose').textContent=t.close;
  fillImageAttributionModal();
}
function fillImageAttributionModal(){
  const t=tr();
  const title=$('#methodImageAttrTitle');
  const box=$('#methodImageAttrBody');
  const link=$('#methodImageAttrLink');
  if(!title||!box||!link)return;
  title.textContent=t.imageAttrTitle;
  link.textContent=t.imageAttrAll;
  link.href='/passport/image-attributions.html';
  const p=state.selected;
  const cover=p?coverFor(p):null;
  if(cover && REAL_PASSPORT_COVERS_ENABLED){
    const lic=cover.licenseUrl?`<a href="${esc(cover.licenseUrl)}" target="_blank" rel="noopener noreferrer">${esc(cover.licenseName||'')}</a>`:esc(cover.licenseName||'');
    const src=cover.commonsPageUrl?`<a href="${esc(cover.commonsPageUrl)}" target="_blank" rel="noopener noreferrer">${esc(cover.commonsFileTitle||'Wikimedia Commons')}</a>`:'Wikimedia Commons';
    box.innerHTML=`<p>${esc(cover.attributionText||'')}</p>
      <p>${state.lang==='ar'?'المؤلف':'Author'}: ${esc(cover.author||'—')}</p>
      <p>${state.lang==='ar'?'الرخصة':'License'}: ${lic}</p>
      <p>${state.lang==='ar'?'المصدر':'Source'}: ${src}</p>
      <p>${esc(t.imageAttrEmblem)}</p>
      ${cover.currentOrHistoric==='historic'?`<p>${esc(t.historicCoverNote)}</p>`:''}`;
  }else{
    box.innerHTML=`<p><strong>${esc(t.miraahIllustration)}</strong></p><p>${esc(t.imageAttrFallback)}</p>`;
  }
}
function renderPassportBook(p){
  const t=tr();
  const book=$('#passportBook');
  const attr=$('#coverAttribution');
  if(!book||!p)return;
  const label=nameOf(p);
  const cover=coverFor(p);
  if(cover?.localFile){
    const alt=state.lang==='ar'?(cover.altAr||label):(cover.altEn||label);
    const w=cover.width||220;
    const h=cover.height||300;
    book.classList.add('is-photo');
    book.setAttribute('aria-label',alt);
    book.innerHTML=`<div class="passport-shadow" aria-hidden="true"></div>
      <div class="passport-spine" aria-hidden="true"></div>
      <div class="passport-photo-frame">
        <img src="${esc(cover.localFile)}" alt="${esc(alt)}" width="${w}" height="${h}" loading="lazy" decoding="async">
      </div>`;
    if(attr){
      attr.hidden=false;
      attr.innerHTML=`<span class="cover-attr-label">${esc(t.imageAttr)} · ${esc(cover.author||'')}</span>
        <button type="button" class="btn" id="coverAttrBtn">${esc(t.imageAttr)}</button>
        <a class="btn" href="/passport/image-attributions.html">${esc(t.imageAttrAll)}</a>`;
      const btn=$('#coverAttrBtn');if(btn)btn.onclick=openMethodModal;
    }
    return;
  }
  book.classList.remove('is-photo');
  const aria=`${t.passportWord}: ${label} (${t.miraahIllustration})`;
  book.setAttribute('aria-label',aria);
  const base=coverColor(p.iso2,p.iso3);
  book.innerHTML=`<div class="passport-shadow" aria-hidden="true"></div>
    <div class="passport-spine" aria-hidden="true"></div>
    <div class="passport-cover" style="background:
      linear-gradient(145deg,#ffffff14,transparent 34%),
      linear-gradient(160deg,${base},#070d16 128%)">
      <div class="passport-pattern" aria-hidden="true"></div>
      <div class="passport-chip" aria-hidden="true">${chipSvg()}</div>
      <div class="passport-emblem" aria-hidden="true">${emblemSvg()}</div>
      <div class="passport-country">${esc(label)}</div>
      <div class="passport-label gold-type">${esc(t.passportWord)}</div>
      <div class="passport-fallback-note">${esc(t.miraahIllustration)}</div>
    </div>`;
  if(attr){
    attr.hidden=false;
    attr.innerHTML=`<span class="cover-attr-label">${esc(t.miraahIllustration)}</span>
      <button type="button" class="btn" id="coverAttrBtn">${esc(t.imageAttr)}</button>`;
    const btn=$('#coverAttrBtn');if(btn)btn.onclick=openMethodModal;
  }
}
function setStaticText(){
  const t=tr();
  document.documentElement.lang=state.lang;
  document.documentElement.dir=state.lang==='ar'?'rtl':'ltr';
  $('#brandTitle').textContent=t.brand;
  $('#brandSubtitle').textContent=t.subtitle;
  if(typeof syncPlatformChrome==='function')syncPlatformChrome(state.lang);
  $('#langBtn').textContent=state.lang==='ar'?'EN':'ع';
  $('#heroTitle').textContent=t.hero;
  $('#heroLead').textContent=t.lead;
  $('#warningText').textContent=t.disclaimer;
  $('#searchLabel').textContent=t.searchLabel;
  $('#passportSearch').placeholder=t.search;
  $('#emptyStateText').textContent=t.empty;
  $('#clearPassport').setAttribute('aria-label',t.clear);
  $('#chevronPassport').setAttribute('aria-label',t.toggle);
  document.querySelectorAll('.badge-exp').forEach(el=>{el.textContent=t.experimental});
  fillMethodology();
  if(state.selected){
    const p=state.selected;
    syncSeo(`${t.brand} | ${nameOf(p)} (${t.experimental})`, state.lang==='ar'?`درجة التنقل في مرآة لـ ${nameOf(p)} وترتيب مرآة التجريبي — ${t.coverage}.`:`${nameOf(p)} Mir\u2019ah Mobility Score and experimental Mir\u2019ah rank — ${t.coverage}.`, CANONICAL+'passport/'+p.slug+'/');
  }else{
    syncSeo(t.pageTitleLanding,t.pageDescriptionLanding,CANONICAL+'passport/');
  }
}
function getMatches(){const q=state.query.trim().toLowerCase();const list=state.index?.passports||[];return list.filter(p=>!q||searchBlob(p).includes(q)).sort((a,b)=>nameOf(a).localeCompare(nameOf(b),state.lang))}
function syncInput(){const input=$('#passportSearch');input.value=state.query;$('#clearPassport').classList.toggle('visible',!!state.query);input.setAttribute('aria-expanded',state.open?'true':'false')}
function closeSuggestions(){state.open=false;state.activeIndex=-1;$('#suggestionsPassport').classList.remove('open');$('#chevronPassport').classList.remove('open');$('#passportSearch').setAttribute('aria-expanded','false')}
function openSuggestions({resetIndex=true}={}){state.open=true;if(resetIndex)state.activeIndex=-1;renderSuggestions();$('#chevronPassport').classList.add('open');$('#passportSearch').setAttribute('aria-expanded','true')}
function renderSuggestions({keepIndex=false}={}){
  const box=$('#suggestionsPassport');
  if(!state.open){box.classList.remove('open');return}
  const matches=getMatches();
  state.matches=matches;
  if(!keepIndex){
    const prefer=matches.findIndex(p=>state.selected&&p.iso3===state.selected.iso3);
    state.activeIndex=prefer>=0?prefer:(matches.length?0:-1);
  }
  if(!matches.length){
    box.innerHTML=`<div class="suggestion">${esc(tr().noResults)}</div>`;
    box.classList.add('open');
    return;
  }
  box.innerHTML=matches.map((p,i)=>`<div class="suggestion${i===state.activeIndex?' active':''}" role="option" aria-selected="${i===state.activeIndex?'true':'false'}" data-code="${p.iso3}" data-index="${i}"><b>${flagWithNameHtml(p.iso2,nameOf(p),'sm',{lazy:false})}</b><small>${esc(p.iso3)} · ${esc(tr().rank)} #${p.rank}</small></div>`).join('');
  box.classList.add('open');
  box.querySelectorAll('.suggestion').forEach(el=>{
    el.onmousedown=e=>{e.preventDefault();selectPassport(el.dataset.code)};
    el.onmouseenter=()=>{state.activeIndex=+el.dataset.index;box.querySelectorAll('.suggestion').forEach(s=>s.classList.toggle('active',s===el))};
  });
}
function moveActive(delta){
  const matches=state.matches;
  if(!matches.length)return;
  if(!state.open)openSuggestions({resetIndex:false});
  let cur=state.activeIndex;
  if(cur<0)cur=delta>0?-1:0;
  cur=(cur+delta+matches.length*10)%matches.length;
  state.activeIndex=cur;
  renderSuggestions({keepIndex:true});
  const active=$('#suggestionsPassport .suggestion.active');
  if(active)active.scrollIntoView({block:'nearest'});
}
async function selectPassport(code){
  const summary=(state.index?.passports||[]).find(p=>p.iso3===code);
  if(!summary)return;
  state.selected=summary;
  state.query=nameOf(summary);
  closeSuggestions();
  syncInput();
  $('#emptyState').hidden=true;
  $('#results').hidden=false;
  renderHero();
  try{
    const res=await fetch(`${window.MIRAAH_DATA_BASE}/by-code/${code}.json`,{credentials:'same-origin'});
    if(!res.ok)throw new Error('load failed');
    state.detail=await res.json();
    mapState.selectedIso=null;
    hideMapTooltip();updateMapSheet(null);
    renderDetail();
  }catch(err){
    state.detail=null;
    $('#destBody').innerHTML='';
    const empty=$('#tableEmpty');
    if(empty){empty.hidden=false;empty.textContent=tr().noResults}
    console.error(err);
  }
  setStaticText();
}
function clearPassport(){
  state.selected=null;state.detail=null;state.query='';state.destQuery='';state.statusFilter='all';state.regionFilter='all';
  mapState.selectedIso=null;resetMapView();hideMapTooltip();updateMapSheet(null);
  closeSuggestions();syncInput();
  $('#emptyState').hidden=false;$('#results').hidden=true;
  const attr=$('#coverAttribution');if(attr){attr.hidden=true;attr.innerHTML=''}
  const panel=$('#mapPanel');if(panel)panel.hidden=true;
  setStaticText();
}
function renderIdentity(p){
  const el=$('#passportIdentity');if(!el||!p)return;
  const label=nameOf(p);
  el.innerHTML=`<div class="flag-stage">${flagImgHtml(p.iso2,label,'hero',{lazy:false,decorative:false})}</div>`+
    `<h3 class="identity-name">${esc(label)}</h3>`+
    `<p class="identity-code">${esc(p.iso3)}${p.iso2?' · '+esc(String(p.iso2).toUpperCase()):''}</p>`;
}
function renderHero(){
  const t=tr(),p=state.selected;
  if(!p)return;
  renderIdentity(p);
  renderPassportBook(p);
  $('#scoreValue').textContent=String(p.mobilityScore);
  $('#scoreLabel').textContent=t.score;
  $('#rankLabel').textContent=t.rank;
  $('#rankValue').textContent=`#${p.rank}`;
  $('#coverageLine').textContent=t.coverage;
  $('#updateLine').textContent=`${t.dataUpdatedLabel}: ${formatDate(state.meta?.datasetUpdateDate)}`;
  $('#passportPageLink').href=`/passport/${encodeURIComponent(p.slug)}/`;
  $('#passportPageLink').textContent=t.openPage;
  $('#covPassports').innerHTML=`<span>${esc(t.passportsRanked)}</span><b>${COVERAGE.passports}</b>`;
  $('#covDestinations').innerHTML=`<span>${esc(t.destinations)}</span><b>${COVERAGE.travelDestinations}</b>`;
  $('#covUpdated').innerHTML=`<span>${esc(t.dataUpdatedLabel)}</span><b>${esc(formatDate(state.meta?.datasetUpdateDate))}</b>`;
  $('#covSource').classList.add('compact');
  $('#covSource').innerHTML=`<span>${esc(t.sourceLabel)}</span><b>${esc(t.sourceName)}</b>`;
  const cats=$('#categoryCards');
  cats.innerHTML=CAT_ORDER.map(key=>`<div class="cat"><span>${esc(t.cats[key])}</span><b>${p.categoryTotals[key]||0}</b></div>`).join('');
  renderSourceSummary();
  fillMethodology();
  setStaticText();
}
function renderSourceSummary(){
  const t=tr();
  const heading=$('#sourceHeading');if(heading)heading.textContent=t.source;
  const box=$('#sourceSummary');
  if(!box)return;
  box.innerHTML=`
    <div class="source-card"><span>${esc(t.sourceLabel)}</span><b>${esc(t.sourceName)}</b></div>
    <div class="source-card"><span>${esc(t.dataUpdatedLabel)}</span><b>${esc(formatDate(state.meta?.datasetUpdateDate))}</b></div>
    <div class="source-card"><span>${esc(t.disclaimerTitle)}</span><b>${esc(t.sourceHint)}</b></div>
    <div class="source-card"><span>${esc(t.mapSourceGeo)}</span><b>${esc(t.mapSourceVisa)}</b></div>`;
  const hint=$('#sourceHintLine');if(hint)hint.textContent=t.sourceHint;
  const discTitle=$('#disclaimerTitle');if(discTitle)discTitle.textContent=t.disclaimerTitle;
  const discBody=$('#disclaimerBody');if(discBody)discBody.textContent=t.disclaimer;
}
function travelDestinations(){
  if(!state.detail)return [];
  return state.detail.destinations.filter(d=>d.status!=='home');
}
function filteredDestinations(){
  const q=state.destQuery.trim().toLowerCase();
  return travelDestinations().filter(d=>{
    if(state.statusFilter!=='all'&&d.status!==state.statusFilter)return false;
    if(state.regionFilter!=='all'&&d.region!==state.regionFilter)return false;
    if(!q)return true;
    const blob=`${d.nameEn} ${d.nameAr} ${d.iso3}`.toLowerCase();
    return blob.includes(q);
  });
}
function activeFilterUniverse(){
  const totals=state.selected?.categoryTotals||state.detail?.categoryTotals;
  if(state.statusFilter==='all')return destinationUniverse(totals);
  return (totals&&totals[state.statusFilter])||0;
}
function renderDetail(){
  const t=tr();
  if(!state.detail)return;
  $('#explorerTitle').textContent=t.explorer;
  $('#destSearch').placeholder=t.destSearch;
  $('#chartTitle').textContent=t.chartTitle;
  $('#chartSub').textContent=t.chartSub;
  fillMethodology();
  renderSourceSummary();
  $('#tableHead').innerHTML=`<th>${esc(t.colDest)}</th><th>${esc(t.colAccess)}</th><th>${esc(t.colRegion)}</th><th>${esc(t.colStay)}</th>`;
  const totals=state.selected?.categoryTotals||state.detail.categoryTotals||{};
  const allCount=destinationUniverse(totals);
  const chips=$('#statusChips');
  chips.innerHTML=`<button type="button" class="chip${state.statusFilter==='all'?' active':''}" data-status="all">${esc(t.filterAll)} (${allCount})</button>`+
    CAT_FILTER_ORDER.map(key=>`<button type="button" class="chip${state.statusFilter===key?' active':''}" data-status="${key}">${esc(t.cats[key])} (${totals[key]||0})</button>`).join('');
  chips.querySelectorAll('.chip').forEach(btn=>btn.onclick=()=>{state.statusFilter=btn.dataset.status;renderDetail()});
  const regions=[...new Set(travelDestinations().map(d=>d.region).filter(Boolean))].sort((a,b)=>regionLabel(a).localeCompare(regionLabel(b),state.lang));
  const regionSelect=$('#regionFilter');
  regionSelect.innerHTML=`<option value="all">${esc(t.regionAll)}</option>`+regions.map(r=>`<option value="${esc(r)}">${esc(regionLabel(r))}</option>`).join('');
  regionSelect.value=state.regionFilter;
  regionSelect.onchange=e=>{state.regionFilter=e.target.value;renderDetail()};
  const rows=filteredDestinations();
  const y=activeFilterUniverse();
  $('#resultsCounter').textContent=t.showing(rows.length,y);
  const body=$('#destBody');
  const empty=$('#tableEmpty');
  if(!rows.length){
    body.innerHTML='';
    if(empty){empty.hidden=false;empty.textContent=t.noResults}
  }else{
    if(empty)empty.hidden=true;
    body.innerHTML=rows.map(d=>{
      const label=state.lang==='ar'?d.nameAr:d.nameEn;
      const days=d.days!=null?`${d.days}`:'—';
      const active=mapState.selectedIso===d.iso3?' is-map-active':'';
      return `<tr class="${active.trim()}" data-iso3="${esc(d.iso3)}"><td>${flagWithNameHtml(d.iso2,label,'xs')}</td><td><span class="status-pill ${esc(d.status)}">${esc(t.cats[d.status]||d.status)}</span></td><td>${esc(regionLabel(d.region))}</td><td>${esc(days)}</td></tr>`;
    }).join('');
  }
  renderChart();
  refreshMap();
}
function renderChart(){
  const t=tr();
  if(!state.detail)return;
  const regions={};
  travelDestinations().forEach(d=>{
    const key=d.region||'Other';
    if(!regions[key])regions[key]={total:0,mobile:0};
    regions[key].total+=1;
    if(d.status==='visa_free'||d.status==='visa_on_arrival'||d.status==='eta')regions[key].mobile+=1;
  });
  const entries=Object.entries(regions).sort((a,b)=>b[1].total-a[1].total||regionLabel(a[0]).localeCompare(regionLabel(b[0]),state.lang));
  const width=720,height=Math.max(320,entries.length*44+48);
  const padL=state.lang==='ar'?48:190;
  const padR=state.lang==='ar'?190:56;
  const padT=16,padB=24;
  const valueColX=state.lang==='ar'?16:width-padR+12;
  const labelAnchor=state.lang==='ar'?'start':'end';
  const labelX=state.lang==='ar'?width-16:padL-12;
  const barX=padL;
  const innerW=width-padL-padR;
  const innerH=height-padT-padB;
  const max=Math.max(1,...entries.map(([,v])=>v.total));
  const gap=12;
  const barH=Math.min(28,(innerH/Math.max(entries.length,1))-gap);
  let y=padT;
  const bars=entries.map(([region,v])=>{
    const w=Math.max(2,v.total/max*innerW);
    const label=regionLabel(region);
    const row=`<text class="bar-label" text-anchor="${labelAnchor}" x="${labelX}" y="${y+barH*0.72}">${esc(label)}</text>
      <rect class="bar" x="${barX}" y="${y}" width="${w}" height="${barH}" rx="6"></rect>
      <text class="bar-value" text-anchor="start" x="${valueColX}" y="${y+barH*0.72}">${v.total}</text>`;
    y+=barH+gap;
    return row;
  }).join('');
  $('#regionChart').innerHTML=`<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(t.chartTitle)}. ${esc(t.chartSub)}">${bars}</svg>`;
}
function openMethodModal(){
  fillImageAttributionModal();
  const dlg=$('#methodModal');
  if(typeof dlg.showModal==='function')dlg.showModal();
  else{$('#methodologyPanel').open=true;$('#methodologyPanel').scrollIntoView({behavior:'smooth',block:'start'})}
}
function setupSearch(){
  const input=$('#passportSearch'),clear=$('#clearPassport'),chev=$('#chevronPassport'),wrap=input.parentElement;
  input.onfocus=()=>openSuggestions();
  input.onblur=()=>{const token=Symbol();state.blurToken=token;setTimeout(()=>{if(state.blurToken!==token)return;if(wrap.contains(document.activeElement))return;closeSuggestions()},160)};
  input.oninput=()=>{
    state.query=input.value;
    if(!state.query){if(state.selected)clearPassport();else{updateClear();openSuggestions()}return}
    if(state.selected&&state.query!==nameOf(state.selected)){state.selected=null;state.detail=null;$('#emptyState').hidden=false;$('#results').hidden=true}
    updateClear();openSuggestions();
  };
  input.onkeydown=e=>{
    if(e.key==='ArrowDown'){e.preventDefault();moveActive(1)}
    else if(e.key==='ArrowUp'){e.preventDefault();moveActive(-1)}
    else if(e.key==='Enter'){if(state.open&&state.activeIndex>=0&&state.matches[state.activeIndex]){e.preventDefault();selectPassport(state.matches[state.activeIndex].iso3)}}
    else if(e.key==='Escape'){e.preventDefault();closeSuggestions()}
  };
  function updateClear(){$('#clearPassport').classList.toggle('visible',!!state.query)}
  clear.onmousedown=e=>e.preventDefault();
  clear.onclick=e=>{e.preventDefault();clearPassport();input.focus();openSuggestions()};
  chev.onmousedown=e=>e.preventDefault();
  chev.onclick=e=>{e.preventDefault();if(state.open)closeSuggestions();else openSuggestions();input.focus()};
  document.addEventListener('click',e=>{if(!wrap.contains(e.target))closeSuggestions()});
  $('#destSearch').oninput=e=>{state.destQuery=e.target.value;if(state.detail)renderDetail()};
  $('#methodologyBtn').onclick=openMethodModal;
  const srcBtn=$('#sourceMethodBtn');if(srcBtn)srcBtn.onclick=openMethodModal;
  $('#methodModalClose').onclick=()=>$('#methodModal').close();
  $('#methodModal').addEventListener('click',e=>{if(e.target===$('#methodModal'))$('#methodModal').close()});
}
async function init(){
  initThemeControls();
  if(typeof initPlatformNav==='function')initPlatformNav();
  window.onMiraahThemeChange=function(){
    if(typeof refreshMapColors==='function')refreshMapColors();
    if(typeof renderDetail==='function'&&state.selected)renderDetail();
    else if(typeof renderChart==='function'&&state.selected)renderChart();
    if(typeof syncThemeControls==='function')syncThemeControls();
  };
  setupSearch();
  $('#langBtn').onclick=()=>{
    state.lang=state.lang==='ar'?'en':'ar';
    localStorage.setItem('miraahLang',state.lang);
    localStorage.removeItem('countryMirrorLang');
    if(state.selected)state.query=nameOf(state.selected);
    syncInput();setStaticText();
    if(state.selected){renderHero();if(state.detail)renderDetail();refreshMap()}
  };
  setupMapControls();
  const boot=window.MIRAAH_PASSPORT_BOOT||null;
  const [index,meta,covers]=await Promise.all([
    fetch(`${window.MIRAAH_DATA_BASE}/index.json`).then(r=>r.json()),
    fetch(`${window.MIRAAH_DATA_BASE}/meta.json`).then(r=>r.json()),
    fetch(`${window.MIRAAH_DATA_BASE}/covers.json`).then(r=>r.ok?r.json():{covers:{}}).catch(()=>({covers:{}}))
  ]);
  state.index=index;state.meta=meta;state.covers=covers;
  setStaticText();syncInput();
  $('#emptyState').hidden=false;$('#results').hidden=true;
  if(boot?.iso3){await selectPassport(boot.iso3)}
}
init();
'''

# Append map runtime after core JS helpers exist.
JS = JS.replace("init();\n", map_ui.MAP_JS + "\ninit();\n", 1)



def head_html(*, title: str, description: str, canonical: str, json_ld: dict) -> str:
    ld = json.dumps(json_ld, ensure_ascii=False, separators=(",", ":"))
    robots = "index, follow" if PASSPORT_INDEXING_ENABLED else "noindex, follow"
    og_image = f"{CANONICAL.rstrip('/')}{brand.SOCIAL_CARD}"
    return (
        f'<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8">'
        f'{theme.NO_FLASH_SCRIPT}'
        f'<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{escape(title)}</title>"
        f'<meta name="description" content="{escape(description)}">'
        f'<meta name="robots" content="{robots}">'
        f'<meta name="googlebot" content="{robots}">'
        f'<link rel="canonical" href="{escape(canonical, quote=True)}">'
        f"{brand.brand_head_links(social_card_abs=og_image)}"
        f'<meta property="og:type" content="website">'
        f'<meta property="og:url" content="{escape(canonical, quote=True)}">'
        f'<meta property="og:title" content="{escape(title)}">'
        f'<meta property="og:description" content="{escape(description)}">'
        f'<meta property="og:locale" content="ar_AR">'
        f'<meta property="og:locale:alternate" content="en_US">'
        f'<meta name="twitter:title" content="{escape(title)}">'
        f'<meta name="twitter:description" content="{escape(description)}">'
        f'<script type="application/ld+json">{ld}</script>'
        f'<link rel="stylesheet" href="{escape(canonical_asset_href(canonical))}">'
        f"</head>"
    )


def canonical_asset_href(canonical: str) -> str:
    # Landing uses /passport/assets/... ; nested pages use ../assets/...
    if canonical.rstrip("/").endswith("/passport"):
        return "./assets/passport.css"
    return "../assets/passport.css"


def shell_body(*, asset_prefix: str, boot_iso3: str | None = None) -> str:
    boot = (
        f'<script>window.MIRAAH_PASSPORT_BOOT={json.dumps({"iso3": boot_iso3})};'
        f"window.MIRAAH_PASSPORT_ASSET_BASE={json.dumps(asset_prefix)};</script>"
        if boot_iso3
        else f"<script>window.MIRAAH_PASSPORT_ASSET_BASE={json.dumps(asset_prefix)};</script>"
    )
    head = f'''<body>
<div class="shell">
  {chrome.header_html(current="passport")}
  <section class="hero">
    <h2 id="heroTitle"></h2>
    <p class="lead" id="heroLead"></p>
    <div class="warning" id="warningText"></div>
    <div class="select-panel">
      <label id="searchLabel" for="passportSearch"></label>
      <div class="search-wrap">
        <span class="search-icon">⌕</span>
        <input class="country-search" id="passportSearch" role="combobox" aria-autocomplete="list" aria-expanded="false" aria-controls="suggestionsPassport" autocomplete="off" spellcheck="false">
        <div class="field-actions">
          <button type="button" class="clear-btn" id="clearPassport">×</button>
          <button type="button" class="chevron-btn" id="chevronPassport">▾</button>
        </div>
        <div class="suggestions" id="suggestionsPassport" role="listbox"></div>
      </div>
    </div>
  </section>
  <div class="empty-state" id="emptyState"><div class="empty-state-icon" aria-hidden="true">⌕</div><p id="emptyStateText"></p></div>
  <div class="results" id="results" hidden>
    <section class="passport-card">
      <div class="passport-identity" id="passportIdentity"></div>
      <div class="score-panel">
        <div class="score-main"><strong id="scoreValue"></strong><span id="scoreLabel"></span></div>
        <div class="rank-secondary"><span id="rankLabel"></span> <b id="rankValue"></b> <span class="badge-exp"></span></div>
        <p class="coverage-line" id="coverageLine"></p>
        <p class="update-line" id="updateLine"></p>
        <div class="method-actions">
          <button type="button" class="btn" id="methodologyBtn"></button>
          <a class="btn" id="passportPageLink" href="/passport/"></a>
        </div>
      </div>
      <div class="passport-visual">
        <div class="passport-book" id="passportBook" role="img" aria-label=""></div>
        <div class="cover-attribution" id="coverAttribution" hidden></div>
      </div>
    </section>
    <div class="coverage-strip" aria-label="Coverage">
      <div class="item" id="covPassports"></div>
      <div class="item" id="covDestinations"></div>
      <div class="item" id="covUpdated"></div>
      <div class="item compact" id="covSource"></div>
    </div>
    <div class="cats" id="categoryCards"></div>
'''
    tail = f'''
    <details class="method-details" id="methodologyPanel">
      <summary id="methodSummary"></summary>
      <h4 id="explainTitle"></h4>
      <ul id="explainList"></ul>
      <p id="methodDates"></p>
    </details>
    <section class="panel" id="explorerPanel">
      <h4 id="explorerTitle"></h4>
      <div class="explorer-row search-row">
        <input class="dest-search" id="destSearch" type="search">
      </div>
      <div class="explorer-row chips-row">
        <div class="filters" id="statusChips"></div>
      </div>
      <div class="explorer-row meta-row">
        <select class="region-select" id="regionFilter" aria-label="Region"></select>
        <div class="results-counter" id="resultsCounter"></div>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr id="tableHead"></tr></thead>
          <tbody id="destBody"></tbody>
        </table>
        <div class="table-empty" id="tableEmpty" hidden></div>
      </div>
    </section>
    <section class="panel">
      <h4 id="chartTitle"></h4>
      <p class="chart-sub" id="chartSub"></p>
      <div class="chart" id="regionChart"></div>
    </section>
    <section class="panel" id="sourcePanel">
      <h4 id="sourceHeading"></h4>
      <div class="source-summary" id="sourceSummary"></div>
      <p id="sourceHintLine" class="chart-sub"></p>
      <div class="source-actions">
        <button type="button" class="btn" id="sourceMethodBtn"></button>
      </div>
      <h4 id="disclaimerTitle"></h4>
      <p id="disclaimerBody"></p>
    </section>
  </div>
  <p class="source" id="footerNote"></p>
  __PLATFORM_FOOTER__
</div>
<dialog class="method-modal" id="methodModal" aria-labelledby="methodModalTitle">
  <div class="inner">
    <h3 id="methodModalTitle"></h3>
    <ul id="methodModalList"></ul>
    <p id="methodModalDates"></p>
    <h4 id="methodTechTitle"></h4>
    <p><span id="methodRepoLabel"></span>: <a id="methodRepoLink" href="https://github.com/imorte/passport-index-data" target="_blank" rel="noopener noreferrer"></a></p>
    <p><span id="methodLicenseLabel"></span>: <span id="methodLicenseBody"></span></p>
    <p><span id="methodRetrievedLabel"></span>: <span id="methodRetrievedBody"></span></p>
    <h4 id="methodUpstreamLabel"></h4>
    <p id="methodUpstreamBody"></p>
    <h4 id="methodCommercialLabel"></h4>
    <p id="methodCommercialBody"></p>
    <h4 id="methodImageAttrTitle"></h4>
    <div class="image-attr-box" id="methodImageAttrBody"></div>
    <p style="margin-top:10px"><a id="methodImageAttrLink" href="/passport/image-attributions.html"></a></p>
    <button type="button" class="btn" id="methodModalClose"></button>
  </div>
</dialog>
{boot}
<script src="{asset_prefix}passport.js"></script>
</body></html>'''
    tail = tail.replace("__PLATFORM_FOOTER__", chrome.footer_html())
    return head + map_ui.map_panel_html() + tail


def write_assets() -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    (ASSETS_DIR / "passport.css").write_text(CSS, encoding="utf-8", newline="\n")
    prefix = "window.MIRAAH_DATA_BASE=window.MIRAAH_DATA_BASE||'../data/passports';\n"
    js = prefix + JS
    (ASSETS_DIR / "passport.js").write_text(js, encoding="utf-8", newline="\n")


def render_landing() -> str:
    title = "مرآة | قوة جواز السفر (تجريبي)"
    description = (
        "مرآة — درجة التنقل التجريبية لجوازات السفر عبر 199 جوازًا و198 وجهة سفر."
    )
    canonical = f"{CANONICAL}passport/"
    json_ld = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": title,
        "url": canonical,
        "description": description,
        "inLanguage": ["ar", "en"],
        "isPartOf": {
            "@type": "WebApplication",
            "name": "مرآة",
            "alternateName": "Mir’ah",
            "logo": brand.json_ld_logo_abs(),
            "url": CANONICAL,
        },
        "primaryImageOfPage": f"{CANONICAL.rstrip('/')}{brand.SOCIAL_CARD}",
    }
    body = shell_body(asset_prefix="./assets/", boot_iso3=None)
    body = body.replace(
        '<script src="./assets/passport.js"></script>',
        '<script>window.MIRAAH_DATA_BASE="../data/passports";</script><script src="./assets/passport.js"></script>',
    )
    return head_html(title=title, description=description, canonical=canonical, json_ld=json_ld) + body


def render_passport_page(passport: dict) -> str:
    title = f"مرآة | جواز سفر {passport['nameAr']} (تجريبي)"
    description = (
        f"درجة التنقل في مرآة لـ {passport['nameAr']}: {passport['mobilityScore']}، "
        f"ترتيب مرآة التجريبي #{passport['rank']} — محسوب بين 199 جواز سفر وعبر 198 وجهة سفر."
    )
    canonical = f"{CANONICAL}passport/{passport['slug']}/"
    json_ld = {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": title,
        "description": description,
        "url": canonical,
        "license": "https://opensource.org/licenses/MIT",
        "creator": {
            "@type": "Organization",
            "name": "مرآة / Mir’ah",
            "logo": brand.json_ld_logo_abs(),
            "url": CANONICAL,
        },
        "isBasedOn": "https://github.com/imorte/passport-index-data",
        "image": f"{CANONICAL.rstrip('/')}{brand.SOCIAL_CARD}",
    }
    body = shell_body(asset_prefix="../assets/", boot_iso3=passport["iso3"])
    body = body.replace(
        '<script src="../assets/passport.js"></script>',
        '<script>window.MIRAAH_DATA_BASE="../../data/passports";</script><script src="../assets/passport.js"></script>',
    )
    return head_html(title=title, description=description, canonical=canonical, json_ld=json_ld) + body


def write_sitemap(passports: list[dict]) -> None:
    # Passport routes stay out of the sitemap until PASSPORT_INDEXING_ENABLED is flipped.
    urls = [CANONICAL, f"{CANONICAL}compare/"]
    if PASSPORT_INDEXING_ENABLED:
        urls.append(f"{CANONICAL}passport/")
        urls.extend(f"{CANONICAL}passport/{p['slug']}/" for p in passports)
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for index, url in enumerate(urls):
        if index == 0:
            priority = "1.0"
        elif index == 1:
            priority = "0.9"
        else:
            priority = "0.7"
        parts.append("  <url>")
        parts.append(f"    <loc>{url}</loc>")
        parts.append("    <changefreq>monthly</changefreq>")
        parts.append(f"    <priority>{priority}</priority>")
        parts.append("  </url>")
    parts.append("</urlset>")
    parts.append("")
    (ROOT / "public" / "sitemap.xml").write_text("\n".join(parts), encoding="utf-8", newline="\n")


def main() -> int:
    from sync_flag_assets import main as sync_flags
    sync_flags()
    if not DATA_INDEX.is_file() or not DATA_META.is_file():
        raise SystemExit("Missing public/data/passports/*.json — run update_passport_data.py --write first")
    index = json.loads(DATA_INDEX.read_text(encoding="utf-8"))
    passports = index["passports"]
    write_assets()
    PASSPORT_DIR.mkdir(parents=True, exist_ok=True)
    (PASSPORT_DIR / "index.html").write_text(render_landing(), encoding="utf-8", newline="\n")

    # Remove stale slug directories (keep assets/)
    existing_slugs = {p.name for p in PASSPORT_DIR.iterdir() if p.is_dir() and p.name != "assets"}
    wanted = {p["slug"] for p in passports}
    for stale in existing_slugs - wanted:
        stale_index = PASSPORT_DIR / stale / "index.html"
        if stale_index.is_file():
            stale_index.unlink()
        stale_dir = PASSPORT_DIR / stale
        if stale_dir.is_dir() and not any(stale_dir.iterdir()):
            stale_dir.rmdir()

    for passport in passports:
        out_dir = PASSPORT_DIR / passport["slug"]
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "index.html").write_text(render_passport_page(passport), encoding="utf-8", newline="\n")

    write_sitemap(passports)
    print(f"rendered landing + {len(passports)} passport pages")
    print(f"passport_indexing_enabled={PASSPORT_INDEXING_ENABLED}")
    print(f"sitemap urls={2 if not PASSPORT_INDEXING_ENABLED else len(passports) + 3}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
