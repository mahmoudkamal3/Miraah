window.MIRAAH_DATA_BASE=window.MIRAAH_DATA_BASE||'../data/passports';

const MIRAAH_THEME_KEY='miraahTheme';
const ThemeI18n={
  ar:{light:'الوضع الفاتح',dark:'الوضع الداكن',system:'استخدام إعداد الجهاز',toLight:'التبديل إلى الوضع الفاتح',toDark:'التبديل إلى الوضع الداكن'},
  en:{light:'Light mode',dark:'Dark mode',system:'Use device setting',toLight:'Switch to light mode',toDark:'Switch to dark mode'}
};
function themePref(){try{const s=localStorage.getItem(MIRAAH_THEME_KEY);if(s==='light'||s==='dark'||s==='system')return s;if(s!=null)localStorage.removeItem(MIRAAH_THEME_KEY)}catch(e){}return 'system'}
function systemIsDark(){try{return !!(window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches)}catch(e){return true}}
function effectiveTheme(pref){const p=pref||themePref();return p==='system'?(systemIsDark()?'dark':'light'):p}
function setThemeMetaColor(eff){const c=eff==='light'?'#e8eef6':'#07111f';let el=document.querySelector('meta[name="theme-color"]');if(!el){el=document.createElement('meta');el.setAttribute('name','theme-color');document.head.appendChild(el)}el.setAttribute('content',c)}
function applyTheme(pref,{persist=true}={}){
  const p=(pref==='light'||pref==='dark'||pref==='system')?pref:'system';
  const eff=effectiveTheme(p);
  document.documentElement.setAttribute('data-theme',eff);
  document.documentElement.setAttribute('data-theme-pref',p);
  document.documentElement.style.colorScheme=eff;
  if(persist){try{localStorage.setItem(MIRAAH_THEME_KEY,p)}catch(e){}}
  setThemeMetaColor(eff);
  syncThemeControls();
  if(typeof window.onMiraahThemeChange==='function'){try{window.onMiraahThemeChange(eff,p)}catch(err){}}
}
function syncThemeControls(){
  const pref=themePref(),eff=effectiveTheme(pref),lang=(document.documentElement.lang==='en'?'en':'ar'),t=ThemeI18n[lang];
  const btn=document.getElementById('themeBtn');
  if(btn){btn.setAttribute('aria-label',eff==='dark'?t.toLight:t.toDark);btn.title=btn.getAttribute('aria-label')}
  [['light','themeOptLight'],['dark','themeOptDark'],['system','themeOptSystem']].forEach(([k,id])=>{
    const el=document.getElementById(id);if(!el)return;el.textContent=t[k];el.setAttribute('aria-checked',pref===k?'true':'false');
  });
}
function toggleThemeMenu(force){
  const menu=document.getElementById('themeMenu'),btn=document.getElementById('themeBtn');
  if(!menu||!btn)return;
  const open=force!=null?force:!menu.classList.contains('open');
  menu.classList.toggle('open',open);menu.hidden=!open;btn.setAttribute('aria-expanded',open?'true':'false');
}
function cycleThemeFromButton(){applyTheme(effectiveTheme()==='dark'?'light':'dark');toggleThemeMenu(false)}
function initThemeControls(){
  const btn=document.getElementById('themeBtn'),menu=document.getElementById('themeMenu'),ctl=document.getElementById('themeCtl');
  if(!btn)return;
  applyTheme(themePref(),{persist:false});
  btn.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();cycleThemeFromButton()});
  btn.addEventListener('contextmenu',e=>{e.preventDefault();toggleThemeMenu(true)});
  btn.addEventListener('dblclick',e=>{e.preventDefault();toggleThemeMenu(true)});
  let pressTimer=null;
  btn.addEventListener('pointerdown',()=>{pressTimer=setTimeout(()=>toggleThemeMenu(true),500)});
  ['pointerup','pointerleave','pointercancel'].forEach(ev=>btn.addEventListener(ev,()=>{if(pressTimer)clearTimeout(pressTimer)}));
  if(menu){menu.querySelectorAll('[data-theme-pref]').forEach(el=>{el.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();applyTheme(el.getAttribute('data-theme-pref'));toggleThemeMenu(false)})})}
  document.addEventListener('click',e=>{if(ctl&&!ctl.contains(e.target))toggleThemeMenu(false)});
  document.addEventListener('keydown',e=>{if(e.key==='Escape')toggleThemeMenu(false)});
  try{const mq=window.matchMedia('(prefers-color-scheme: dark)');const onChange=()=>{if(themePref()==='system')applyTheme('system',{persist:false})};if(mq.addEventListener)mq.addEventListener('change',onChange);else if(mq.addListener)mq.addListener(onChange)}catch(e){}
  syncThemeControls();
}
function cssVar(name,fallback){const v=getComputedStyle(document.documentElement).getPropertyValue(name).trim();return v||fallback}
function chartPalette(){return{A:cssVar('--brand-cyan','#38d6b0'),B:cssVar('--brand-amber','#ffb15c'),MUTED:cssVar('--chart-label','#8fa6bf'),GRID:cssVar('--chart-grid','#203752'),STROKE:cssVar('--chart-plot-stroke','#07111f'),TEXT:cssVar('--text','#ecf4ff')}}

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
  navCompare:'مقارنة الدول',navPassport:'قوة جواز السفر',
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
  navCompare:'Country comparison',navPassport:'Passport power',
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
function flagEmoji(iso2){if(!iso2||iso2==='XK')return '🏳️';return String.fromCodePoint(...[...iso2.toUpperCase()].map(c=>127397+c.charCodeAt(0)))}
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
      <div class="passport-flag" aria-hidden="true">${esc(flagEmoji(p.iso2))}</div>
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
  const home=$('#brandHome');if(home)home.setAttribute('aria-label',state.lang==='ar'?'العودة إلى الصفحة الرئيسية':'Back to homepage');
  if(typeof syncThemeControls==='function')syncThemeControls();
  $('#navCompare').textContent=t.navCompare;
  $('#navPassport').textContent=t.navPassport;
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
  box.innerHTML=matches.map((p,i)=>`<div class="suggestion${i===state.activeIndex?' active':''}" role="option" aria-selected="${i===state.activeIndex?'true':'false'}" data-code="${p.iso3}" data-index="${i}"><b>${esc(flagEmoji(p.iso2))} ${esc(nameOf(p))}</b><small>${esc(p.iso3)} · ${esc(tr().rank)} #${p.rank}</small></div>`).join('');
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
function renderHero(){
  const t=tr(),p=state.selected;
  if(!p)return;
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
      return `<tr class="${active.trim()}" data-iso3="${esc(d.iso3)}"><td>${esc(flagEmoji(d.iso2))} ${esc(label)}</td><td><span class="status-pill ${esc(d.status)}">${esc(t.cats[d.status]||d.status)}</span></td><td>${esc(regionLabel(d.region))}</td><td>${esc(days)}</td></tr>`;
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

const MAP_STATUS_ORDER=['visa_free','visa_on_arrival','eta','evisa','visa_required','no_admission'];
function mapColors(){const g=n=>getComputedStyle(document.documentElement).getPropertyValue(n).trim();
return{visa_free:g('--st-vf')||'#2d9f7f',visa_on_arrival:g('--st-voa')||'#3b82c4',eta:g('--map-eta')||'#7c6cf0',evisa:g('--st-ev')||'#c9a227',visa_required:g('--map-vr')||'#e07070',no_admission:g('--st-na')||'#5a1f32',home:g('--map-home-fill')||'#2a3548',unknown:g('--map-unknown')||'#3a4658'}}
const MAP_COLORS=mapColors();
const mapState={
  loading:false,ready:false,error:null,data:null,byIso:{},
  zoom:1,panX:0,panY:0,width:960,height:520,
  dragging:false,dragStart:null,selectedIso:null,ro:null
};
function mapAssetUrl(){
  const base=(window.MIRAAH_PASSPORT_ASSET_BASE||'./assets/').replace(/\/?$/,'/');
  return base+'world-map.json';
}
function project(lon,lat,w,h){return [(lon+180)/360*w,(90-lat)/180*h]}
function ringPath(ring,w,h){
  if(!ring||ring.length<2)return '';
  let d='';
  ring.forEach((pt,i)=>{const [x,y]=project(pt[0],pt[1],w,h);d+=(i?'L':'M')+x.toFixed(2)+' '+y.toFixed(2)+' ';});
  return d+'Z';
}
function geomPath(geom,w,h){
  if(!geom)return '';
  if(geom.type==='Polygon')return (geom.coordinates||[]).map(r=>ringPath(r,w,h)).join('');
  if(geom.type==='MultiPolygon')return (geom.coordinates||[]).map(poly=>(poly||[]).map(r=>ringPath(r,w,h)).join('')).join('');
  return '';
}
function destByIso(iso){
  if(!state.detail)return null;
  return (state.detail.destinations||[]).find(d=>d.iso3===iso)||null;
}
function statusOfIso(iso){
  const d=destByIso(iso);
  return d?d.status:'unknown';
}
function stayText(d){
  const t=tr();
  if(!d)return '—';
  if(d.days!=null)return String(d.days);
  if(d.status==='eta'||d.status==='evisa')return t.stayOfficial;
  return '—';
}
function mapMatchesFilters(iso){
  const d=destByIso(iso);
  if(!d)return false;
  if(d.status==='home')return state.statusFilter==='all'||state.statusFilter==='home';
  if(state.statusFilter!=='all'&&d.status!==state.statusFilter)return false;
  if(state.regionFilter!=='all'&&d.region!==state.regionFilter)return false;
  const q=state.destQuery.trim().toLowerCase();
  if(q){
    const blob=`${d.nameEn} ${d.nameAr} ${d.iso3}`.toLowerCase();
    if(!blob.includes(q))return false;
  }
  return true;
}
function ensureMapTooltip(){
  let tip=document.getElementById('mapTooltip');
  if(!tip){
    tip=document.createElement('div');
    tip.id='mapTooltip';
    tip.className='map-tooltip';
    tip.setAttribute('role','tooltip');
    document.body.appendChild(tip);
  }
  return tip;
}
function hideMapTooltip(){
  const tip=ensureMapTooltip();
  tip.style.display='none';
  tip.innerHTML='';
}
function placeTooltip(clientX,clientY){
  const tip=ensureMapTooltip();
  tip.style.display='block';
  const pad=12;
  const rect=tip.getBoundingClientRect();
  let left=clientX+16;
  let top=clientY+16;
  if(left+rect.width>window.innerWidth-pad)left=clientX-rect.width-12;
  if(top+rect.height>window.innerHeight-pad)top=clientY-rect.height-12;
  left=Math.max(pad,left);top=Math.max(pad,top);
  tip.style.left=left+'px';tip.style.top=top+'px';
}
function tooltipHtml(iso){
  const t=tr();
  const d=destByIso(iso);
  if(!d)return `<strong>${esc(iso)}</strong><div class="muted">${esc(t.mapUnmapped)}</div>`;
  const name=state.lang==='ar'?d.nameAr:d.nameEn;
  const status=t.cats[d.status]||d.status;
  return `<strong>${esc(flagEmoji(d.iso2))} ${esc(name)}</strong>
    <div>${esc(status)}</div>
    <div class="muted">${esc(t.colStay)}: ${esc(stayText(d))}</div>
    <div class="muted">${esc(regionLabel(d.region))}</div>`;
}
function showTooltipFor(iso,clientX,clientY){
  const tip=ensureMapTooltip();
  tip.innerHTML=tooltipHtml(iso);
  placeTooltip(clientX,clientY);
}
function updateMapSheet(iso){
  const sheet=$('#mapSheet');
  if(!sheet)return;
  if(!iso){sheet.classList.remove('open');sheet.innerHTML='';return}
  const t=tr();
  const d=destByIso(iso);
  const name=d?(state.lang==='ar'?d.nameAr:d.nameEn):iso;
  sheet.classList.add('open');
  sheet.innerHTML=`<button type="button" class="sheet-close" id="mapSheetClose" aria-label="${esc(t.close)}">×</button>
    <strong>${esc(d?flagEmoji(d.iso2)+' '+name:name)}</strong>
    <div>${esc(d?(t.cats[d.status]||d.status):t.mapUnmapped)}</div>
    <div class="muted">${esc(t.colStay)}: ${esc(stayText(d))}</div>
    <div class="muted">${esc(d?regionLabel(d.region):'—')}</div>`;
  const close=$('#mapSheetClose');if(close)close.onclick=()=>{mapState.selectedIso=null;updateMapSheet(null);colorMap();hideMapTooltip()};
}
function applyMapTransform(){
  const g=$('#mapWorld');
  if(!g)return;
  const cx=mapState.width/2,cy=mapState.height/2;
  g.setAttribute('transform',`translate(${mapState.panX} ${mapState.panY}) translate(${cx} ${cy}) scale(${mapState.zoom}) translate(${-cx} ${-cy})`);
}
function resetMapView(){
  mapState.zoom=1;mapState.panX=0;mapState.panY=0;applyMapTransform();
}
function zoomMap(factor){
  mapState.zoom=Math.min(8,Math.max(1,mapState.zoom*factor));
  if(mapState.zoom===1){mapState.panX=0;mapState.panY=0}
  applyMapTransform();
}
function colorMap(){
  if(!mapState.ready)return;
  const svg=$('#mapSvg');if(!svg)return;
  svg.querySelectorAll('[data-iso3]').forEach(el=>{
    const iso=el.getAttribute('data-iso3');
    const status=statusOfIso(iso);
    const match=mapMatchesFilters(iso)||(status==='home'&&state.statusFilter==='all');
    el.classList.remove('is-dim','is-match','is-home','is-selected');
    MAP_STATUS_ORDER.concat(['home','unknown']).forEach(s=>el.classList.remove('map-status-'+s));
    el.classList.add('map-status-'+(status||'unknown'));
    if(status==='home')el.classList.add('is-home');
    if(mapState.selectedIso===iso)el.classList.add('is-selected');
    if(state.statusFilter!=='all'||state.regionFilter!=='all'||state.destQuery.trim()){
      el.classList.add(match?'is-match':'is-dim');
    }
  });
}
function selectMapDestination(iso,{scrollTable=true}={}){
  mapState.selectedIso=iso;
  updateMapSheet(window.matchMedia('(max-width:650px)').matches?iso:null);
  colorMap();
  if(!iso||!scrollTable)return;
  const row=[...document.querySelectorAll('#destBody tr')].find(tr=>tr.dataset.iso3===iso);
  if(row){
    document.querySelectorAll('#destBody tr.is-map-active').forEach(r=>r.classList.remove('is-map-active'));
    row.classList.add('is-map-active');
    row.scrollIntoView({block:'nearest',behavior:window.matchMedia('(prefers-reduced-motion:reduce)').matches?'auto':'smooth'});
  }
  if(state.statusFilter==='all'||!state.statusFilter){
    /* keep filters; selection alone is enough */
  }
}
function renderMapLegend(){
  const t=tr();
  const box=$('#mapLegend');if(!box)return;
  const totals=state.selected?.categoryTotals||state.detail?.categoryTotals||{};
  const all=destinationUniverse(totals);
  const items=[{key:'all',label:t.filterAll,count:all,color:(getComputedStyle(document.documentElement).getPropertyValue('--text-muted').trim()||'#8fa6bf')}].concat(
    MAP_STATUS_ORDER.map(key=>({key,label:t.cats[key],count:totals[key]||0,color:mapColors()[key]}))
  );
  box.innerHTML=items.map(it=>`<button type="button" class="chip${state.statusFilter===it.key?' active':''}" data-map-status="${it.key}" aria-pressed="${state.statusFilter===it.key?'true':'false'}">
    <span class="swatch" style="background:${it.color}"></span>${esc(it.label)} (${it.count})</button>`).join('');
  box.querySelectorAll('[data-map-status]').forEach(btn=>{
    btn.onclick=()=>{
      const key=btn.dataset.mapStatus;
      state.statusFilter=(state.statusFilter===key?'all':key);
      if(state.detail)renderDetail();
      else {renderMapLegend();colorMap()}
    };
  });
  const homeNote=$('#mapHomeNote');
  if(homeNote)homeNote.textContent=`${t.mapHomeLabel}: ${totals.home||1}`;
}
function bindMapInteractions(svg){
  svg.addEventListener('pointerdown',e=>{
    if(e.button!=null&&e.button!==0)return;
    mapState.dragging=true;
    mapState.dragStart={x:e.clientX,y:e.clientY,panX:mapState.panX,panY:mapState.panY};
    svg.setPointerCapture?.(e.pointerId);
  });
  svg.addEventListener('pointermove',e=>{
    const target=e.target.closest?.('[data-iso3]');
    if(target&&!mapState.dragging){
      const iso=target.getAttribute('data-iso3');
      showTooltipFor(iso,e.clientX,e.clientY);
    }else if(!target){hideMapTooltip()}
    if(!mapState.dragging||!mapState.dragStart)return;
    if(mapState.zoom<=1)return;
    mapState.panX=mapState.dragStart.panX+(e.clientX-mapState.dragStart.x);
    mapState.panY=mapState.dragStart.panY+(e.clientY-mapState.dragStart.y);
    applyMapTransform();
  });
  const endDrag=e=>{
    if(!mapState.dragging)return;
    const dx=Math.abs(e.clientX-(mapState.dragStart?.x||0));
    const dy=Math.abs(e.clientY-(mapState.dragStart?.y||0));
    mapState.dragging=false;mapState.dragStart=null;
    const target=e.target.closest?.('[data-iso3]');
    if(target&&dx<5&&dy<5){
      const iso=target.getAttribute('data-iso3');
      selectMapDestination(iso);
      if(!window.matchMedia('(max-width:650px)').matches)showTooltipFor(iso,e.clientX,e.clientY);
    }
  };
  svg.addEventListener('pointerup',endDrag);
  svg.addEventListener('pointercancel',()=>{mapState.dragging=false;mapState.dragStart=null});
  svg.addEventListener('pointerleave',()=>{if(!mapState.dragging)hideMapTooltip()});
  svg.addEventListener('keydown',e=>{
    const target=e.target.closest?.('[data-iso3]');
    if(!target)return;
    if(e.key==='Enter'||e.key===' '){e.preventDefault();selectMapDestination(target.getAttribute('data-iso3'))}
    if(e.key==='Escape'){hideMapTooltip();selectMapDestination(null,{scrollTable:false})}
  });
  svg.addEventListener('focusin',e=>{
    const target=e.target.closest?.('[data-iso3]');
    if(!target)return;
    const rect=target.getBoundingClientRect();
    showTooltipFor(target.getAttribute('data-iso3'),rect.left+rect.width/2,rect.top);
  });
}
function drawMap(){
  const viewport=$('#mapViewport');
  const mount=$('#mapSvgMount');
  if(!viewport||!mount||!mapState.data)return;
  const t=tr();
  const w=mapState.width,h=mapState.height;
  const parts=[];
  (mapState.data.features||[]).forEach(f=>{
    const iso=f.properties?.iso3;if(!iso)return;
    const kind=f.properties?.kind||'polygon';
    if(kind==='polygon'||f.geometry?.type==='Polygon'||f.geometry?.type==='MultiPolygon'){
      if(f.geometry?.type==='Point')return;
      const d=geomPath(f.geometry,w,h);if(!d)return;
      const label=state.lang==='ar'?(f.properties.nameAr||iso):(f.properties.nameEn||iso);
      parts.push(`<path class="map-land" data-iso3="${esc(iso)}" d="${d}" tabindex="0" role="button" aria-label="${esc(label)}"></path>`);
    }
  });
  (mapState.data.features||[]).forEach(f=>{
    if(f.properties?.kind!=='marker'&&f.geometry?.type!=='Point')return;
    const iso=f.properties?.iso3;if(!iso)return;
    const [lon,lat]=f.geometry.coordinates||[];
    const [x,y]=project(lon,lat,w,h);
    const label=state.lang==='ar'?(f.properties.nameAr||iso):(f.properties.nameEn||iso);
    parts.push(`<circle class="map-marker" data-iso3="${esc(iso)}" cx="${x.toFixed(2)}" cy="${y.toFixed(2)}" r="4.5" tabindex="0" role="button" aria-label="${esc(label)}"></circle>`);
  });
  mount.innerHTML=`<svg id="mapSvg" viewBox="0 0 ${w} ${h}" role="img" aria-label="${esc(t.mapTitle)}"><rect width="${w}" height="${h}" fill="var(--map-ocean)"></rect><g id="mapWorld">${parts.join('')}</g></svg>`;
  bindMapInteractions($('#mapSvg'));
  applyMapTransform();
  colorMap();
}
async function ensureMapLoaded(){
  if(mapState.ready||mapState.loading)return;
  mapState.loading=true;
  const loading=$('#mapLoading');if(loading)loading.hidden=false;
  try{
    const res=await fetch(mapAssetUrl(),{credentials:'same-origin'});
    if(!res.ok)throw new Error('map asset missing');
    mapState.data=await res.json();
    mapState.ready=true;
    mapState.error=null;
    drawMap();
  }catch(err){
    mapState.error=String(err);
    const errEl=$('#mapError');if(errEl){errEl.hidden=false;errEl.textContent=tr().mapError}
    console.error(err);
  }finally{
    mapState.loading=false;
    if(loading)loading.hidden=true;
  }
}
function refreshMap(){
  const panel=$('#mapPanel');if(!panel)return;
  panel.hidden=!state.selected;
  if(!state.selected){hideMapTooltip();updateMapSheet(null);return}
  renderMapLegend();
  const title=$('#mapTitle');if(title)title.textContent=tr().mapTitle;
  const lead=$('#mapLead');if(lead)lead.textContent=tr().mapLead;
  ['mapZoomIn','mapZoomOut','mapReset','mapFullscreen'].forEach(id=>{
    const el=$('#'+id);if(!el)return;
    const labels={mapZoomIn:tr().mapZoomIn,mapZoomOut:tr().mapZoomOut,mapReset:tr().mapReset,mapFullscreen:tr().mapFullscreen};
    el.setAttribute('aria-label',labels[id]);el.title=labels[id];
  });
  ensureMapLoaded().then(()=>{if(mapState.ready){if(!$('#mapSvg'))drawMap();else colorMap();renderMapLegend()}});
}
function setupMapControls(){
  const zin=$('#mapZoomIn');if(zin)zin.onclick=()=>zoomMap(1.25);
  const zout=$('#mapZoomOut');if(zout)zout.onclick=()=>zoomMap(1/1.25);
  const reset=$('#mapReset');if(reset)reset.onclick=()=>resetMapView();
  const fs=$('#mapFullscreen');
  if(fs)fs.onclick=()=>{
    const shell=$('#mapShell');if(!shell)return;
    shell.classList.toggle('is-fullscreen');
    fs.setAttribute('aria-pressed',shell.classList.contains('is-fullscreen')?'true':'false');
  };
  document.addEventListener('keydown',e=>{
    if(e.key==='Escape'){
      hideMapTooltip();
      const shell=$('#mapShell');
      if(shell?.classList.contains('is-fullscreen'))shell.classList.remove('is-fullscreen');
      if(mapState.selectedIso){mapState.selectedIso=null;updateMapSheet(null);colorMap()}
    }
  });
}
function refreshMapColors(){
  const ocean=document.querySelector('#mapSvg rect');
  if(ocean)ocean.setAttribute('fill',getComputedStyle(document.documentElement).getPropertyValue('--map-ocean').trim()||'#07111f');
  if(typeof renderMapLegend==='function')renderMapLegend();
  if(typeof colorMap==='function')colorMap();
}

init();
