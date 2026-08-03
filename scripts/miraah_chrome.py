#!/usr/bin/env python3
"""Shared Mir’ah platform header/footer chrome for all public pages."""
from __future__ import annotations

from datetime import datetime, timezone

import miraah_brand as brand
import miraah_theme as theme

CHROME_CSS = r"""
.platform-header{display:flex;align-items:center;justify-content:space-between;gap:14px;margin-bottom:20px;flex-wrap:wrap}
.platform-header .brand{display:flex;align-items:center;gap:12px;text-decoration:none;color:inherit;min-width:0}
.platform-header .logo{width:44px;height:44px;border-radius:14px;overflow:hidden;flex-shrink:0;box-shadow:0 8px 30px var(--glow-brand);display:block;padding:0;background:transparent}
.platform-header .logo-mark{width:44px;height:44px;display:block}
.platform-header .brand-text{display:flex;flex-direction:column;min-width:0}
.platform-header .brand h1{margin:0;font-size:22px;font-weight:700;letter-spacing:-.02em;font-family:system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}
.platform-header .brand p{margin:4px 0 0;color:var(--muted);font-size:12px}
.nav-toggle{display:none;border:1px solid var(--line);background:var(--surface-soft);color:var(--text);padding:9px 11px;border-radius:11px;cursor:pointer}
.nav-toggle:focus-visible{outline:2px solid var(--brand-cyan);outline-offset:2px}
.product-nav{display:flex;gap:6px;padding:4px;border:1px solid var(--line);border-radius:14px;background:var(--surface-soft)}
.product-nav a{text-decoration:none;color:var(--muted);padding:8px 12px;border-radius:10px;font-size:13px;font-weight:650;white-space:nowrap}
.product-nav a:hover,.product-nav a:focus-visible{color:var(--text);background:var(--hover)}
.product-nav a[aria-current="page"],.product-nav a.active{color:var(--text-on-brand);background:linear-gradient(135deg,var(--brand-cyan),var(--brand-blue-soft))}
.platform-actions{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-inline-start:auto}
.platform-footer{margin-top:48px;padding:28px 0 12px;border-top:1px solid var(--border);color:var(--muted);font-size:13px;line-height:1.7}
.platform-footer .footer-grid{display:grid;grid-template-columns:1.4fr 1fr 1.4fr;gap:22px}
.platform-footer .footer-brand{display:flex;gap:12px;align-items:flex-start}
.platform-footer .footer-brand img{width:40px;height:40px;border-radius:12px}
.platform-footer strong{color:var(--text);display:block;margin-bottom:6px}
.platform-footer a{color:var(--brand-cyan);text-decoration:none}
.platform-footer a:hover,.platform-footer a:focus-visible{text-decoration:underline}
.platform-footer ul{list-style:none;margin:0;padding:0;display:grid;gap:8px}
.platform-footer .footer-copy{margin-top:22px;padding-top:14px;border-top:1px solid var(--border);font-size:12px}
.platform-footer .footer-credit{margin:0}
.platform-footer .footer-creator{display:inline-flex;align-items:center;gap:5px;vertical-align:baseline;color:var(--brand-cyan);text-decoration:none}
.platform-footer .footer-creator:hover,.platform-footer .footer-creator:focus-visible{text-decoration:underline}
.platform-footer .footer-linkedin-icon{width:14px;height:14px;flex-shrink:0;display:block}
@media(max-width:820px){
  .nav-toggle{display:inline-flex;align-items:center;justify-content:center}
  .product-nav{display:none;width:100%;order:5;flex-direction:column;padding:8px;border-radius:14px}
  .product-nav.open{display:flex}
  .platform-footer .footer-grid{grid-template-columns:1fr}
}
@media(prefers-reduced-motion:reduce){
  .product-nav,.platform-header *{transition:none!important}
}
"""


def brand_link_html() -> str:
    return (
        f'<a class="brand" href="/" aria-label="{brand.HOME_ARIA_AR}" id="brandHome">'
        f'<span class="logo"><img class="logo-mark" src="{brand.APP_ICON_SVG}" width="44" height="44" '
        f'alt="" decoding="async"></span>'
        f'<span class="brand-text"><h1 id="brandTitle"></h1>'
        f'<p id="brandSubtitle"></p></span></a>'
    )


def header_html(*, current: str, extra_actions: str = "", include_lang: bool = True) -> str:
    """current: home | compare | passport | empty."""
    links = (
        f'<a href="/" id="navHome"'
        f'{" aria-current=\"page\" class=\"active\"" if current == "home" else ""}></a>'
        f'<a href="/compare/" id="navCompare"'
        f'{" aria-current=\"page\" class=\"active\"" if current == "compare" else ""}></a>'
        f'<a href="/passport/" id="navPassport"'
        f'{" aria-current=\"page\" class=\"active\"" if current == "passport" else ""}></a>'
    )
    lang = (
        '<button class="btn lang-btn" id="langBtn" type="button" aria-label="Switch language">EN</button>'
        if include_lang
        else ""
    )
    return f"""<header class="topbar platform-header">
  {brand_link_html()}
  <button type="button" class="nav-toggle" id="navToggle" aria-controls="productNav" aria-expanded="false" aria-label="Open menu">☰</button>
  <nav class="product-nav" id="productNav" aria-label="Primary">{links}</nav>
  <div class="platform-actions actions">{theme.theme_control_html()}{lang}{extra_actions}</div>
</header>"""


CREATOR_LINKEDIN = "https://www.linkedin.com/in/mahmoud-kamal-a8a1ba176/"

LINKEDIN_ICON_SVG = (
    '<svg class="footer-linkedin-icon" viewBox="0 0 24 24" width="14" height="14" '
    'aria-hidden="true" focusable="false">'
    '<path fill="currentColor" d="M20.45 20.45h-3.56v-5.57c0-1.33-.02-3.04-1.85-3.04-1.85 '
    "0-2.14 1.45-2.14 2.94v5.67H9.35V9h3.41v1.56h.05c.48-.9 1.64-1.85 3.37-1.85 3.6 0 "
    '4.27 2.37 4.27 5.46v6.28zM5.34 7.43a2.06 2.06 0 1 1 0-4.12 2.06 2.06 0 0 1 0 4.12zM7.12 '
    '20.45H3.56V9h3.56v11.45zM22.23 0H1.77C.79 0 0 .77 0 1.73v20.54C0 23.23.79 24 1.77 '
    '24h20.45c.98 0 1.78-.77 1.78-1.73V1.73C24 .77 23.2 0 22.23 0z"/>'
    "</svg>"
)


def footer_html(*, year: int | None = None, show_passport_links: bool = True) -> str:
    y = year if year is not None else datetime.now(timezone.utc).year
    method = (
        '<li><a href="/passport/" id="footerMethodLink"></a></li>'
        '<li><a href="/passport/image-attributions.html" id="footerAttrLink"></a></li>'
        if show_passport_links
        else ""
    )
    return f"""<footer class="platform-footer" id="platformFooter">
  <div class="footer-grid">
    <div class="footer-brand">
      <img src="{brand.APP_ICON_SVG}" width="40" height="40" alt="" decoding="async">
      <div>
        <strong id="footerBrandName"></strong>
        <p id="footerDesc" style="margin:0"></p>
      </div>
    </div>
    <div>
      <strong id="footerExploreLabel"></strong>
      <ul>
        <li><a href="/" id="footerHome"></a></li>
        <li><a href="/compare/" id="footerCompare"></a></li>
        <li><a href="/passport/" id="footerPassport"></a></li>
        {method}
      </ul>
    </div>
    <div>
      <strong id="footerSourcesLabel"></strong>
      <p id="footerCompareSources" style="margin:0 0 10px"></p>
      <p id="footerPassportSources" style="margin:0"></p>
    </div>
  </div>
  <div class="footer-copy">
    <p id="footerDisclaimer" style="margin:0 0 8px"></p>
    <p class="footer-credit"><span id="footerBrandInline"></span> · <span id="footerYear">{y}</span><span id="footerCreditMid"></span><a class="footer-creator" id="footerCreatorLink" href="{CREATOR_LINKEDIN}" target="_blank" rel="me noopener noreferrer"><span id="footerCreatorName"></span>{LINKEDIN_ICON_SVG}</a></p>
  </div>
</footer>"""


CHROME_JS = r"""
const MiraahNavI18n={
  ar:{home:'الرئيسية',compare:'مقارنة الدول',passport:'قوة جواز السفر',navLabel:'التنقل الرئيسي',menuOpen:'فتح القائمة',menuClose:'إغلاق القائمة',brandHome:'العودة إلى الصفحة الرئيسية',explore:'استكشف',sources:'المصادر',
    footerDesc:'منصة بيانات ثنائية اللغة لمقارنة جودة الحياة وقوة جواز السفر بمصادر معلنة.',
    compareSources:'مقارنة الدول: البنك الدولي (مؤشرات التنمية العالمية) وتقرير السعادة العالمي.',
    passportSources:'جواز السفر: Passport Index Data — مجموعة معلوماتية تجريبية. تحقق من المتطلبات مع السفارة أو شركة الطيران أو جهة رسمية قبل السفر.',
    disclaimer:'مرآة منصة معلوماتية وليست جهة حكومية أو استشارية للسفر.',
    methodology:'منهجية جواز السفر',attributions:'إسناد صور الجوازات',
    creditMid:' — صُممت وطُوّرت بواسطة ',creatorName:'محمود كمال',creatorAria:'محمود كمال على LinkedIn'},
  en:{home:'Home',compare:'Compare countries',passport:'Passport power',navLabel:'Primary',menuOpen:'Open menu',menuClose:'Close menu',brandHome:'Back to homepage',explore:'Explore',sources:'Sources',
    footerDesc:'A bilingual data platform for comparing quality of life and passport mobility with disclosed sources.',
    compareSources:'Country comparison: World Bank World Development Indicators and the World Happiness Report.',
    passportSources:'Passport: Passport Index Data — an experimental informational dataset. Verify requirements with an embassy, airline, or official authority before travel.',
    disclaimer:'Mir’ah is informational and is not a government or travel-advisory body.',
    methodology:'Passport methodology',attributions:'Passport image attributions',
    creditMid:' — Created by ',creatorName:'Mahmoud Kamal',creatorAria:'Mahmoud Kamal on LinkedIn'}
};
function syncPlatformChrome(lang){
  const t=MiraahNavI18n[lang==='en'?'en':'ar'];
  const set=(id,text)=>{const el=document.getElementById(id);if(el)el.textContent=text};
  set('navHome',t.home);set('navCompare',t.compare);set('navPassport',t.passport);
  const nav=document.getElementById('productNav');if(nav)nav.setAttribute('aria-label',t.navLabel);
  const home=document.getElementById('brandHome');if(home)home.setAttribute('aria-label',t.brandHome);
  const toggle=document.getElementById('navToggle');
  if(toggle){const open=toggle.getAttribute('aria-expanded')==='true';toggle.setAttribute('aria-label',open?t.menuClose:t.menuOpen)}
  set('footerBrandName',lang==='en'?'Mir\u2019ah':'مرآة');
  set('footerBrandInline',lang==='en'?'Mir\u2019ah':'مرآة');
  set('footerDesc',t.footerDesc);
  set('footerExploreLabel',t.explore);
  set('footerSourcesLabel',t.sources);
  set('footerHome',t.home);set('footerCompare',t.compare);set('footerPassport',t.passport);
  set('footerCompareSources',t.compareSources);set('footerPassportSources',t.passportSources);
  set('footerDisclaimer',t.disclaimer);
  set('footerMethodLink',t.methodology);set('footerAttrLink',t.attributions);
  set('footerCreditMid',t.creditMid);
  set('footerCreatorName',t.creatorName);
  const creator=document.getElementById('footerCreatorLink');
  if(creator)creator.setAttribute('aria-label',t.creatorAria);
  if(typeof syncThemeControls==='function')syncThemeControls();
}
function initPlatformNav(){
  const toggle=document.getElementById('navToggle'),nav=document.getElementById('productNav');
  if(!toggle||!nav)return;
  toggle.addEventListener('click',()=>{
    const open=!nav.classList.contains('open');
    nav.classList.toggle('open',open);
    toggle.setAttribute('aria-expanded',open?'true':'false');
    const lang=document.documentElement.lang==='en'?'en':'ar';
    const t=MiraahNavI18n[lang];
    toggle.setAttribute('aria-label',open?t.menuClose:t.menuOpen);
  });
  document.addEventListener('keydown',e=>{if(e.key==='Escape'){nav.classList.remove('open');toggle.setAttribute('aria-expanded','false')}});
}
"""


def chrome_css_bundle() -> str:
    return theme.THEME_CSS + CHROME_CSS
