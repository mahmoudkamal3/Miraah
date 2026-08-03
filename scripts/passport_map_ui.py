#!/usr/bin/env python3
"""Passport access map UI strings (CSS/JS) for Mir’ah Passport Power.

Bundled into public/passport/assets by render_passport_pages.py.
No external map SDKs. Geometry loads from local world-map.json only.
"""

from __future__ import annotations

MAP_CSS = r'''
.map-panel{margin-top:16px}
.map-panel .map-head{display:flex;flex-wrap:wrap;gap:10px;align-items:flex-end;justify-content:space-between;margin-bottom:12px}
.map-panel .map-head h4{margin:0;font-size:16px}
.map-panel .map-lead{margin:4px 0 0;color:var(--muted);font-size:13px;max-width:640px;line-height:1.55}
.map-controls{display:flex;flex-wrap:wrap;gap:6px}
.map-controls .btn{min-width:40px;justify-content:center;padding:8px 10px}
.map-shell{position:relative;border:1px solid var(--border);border-radius:16px;background:var(--map-ocean);overflow:hidden}
.map-viewport{position:relative;width:100%;height:min(58vh,520px);min-height:360px;touch-action:none;overflow:hidden}
.map-viewport svg{width:100%;height:100%;display:block;cursor:grab}
.map-viewport svg:active{cursor:grabbing}
.map-land{fill:var(--map-land);stroke:var(--map-land-stroke);stroke-width:.35;transition:fill .2s ease,opacity .2s ease,stroke-width .15s ease}
.map-land.is-dim{opacity:.22}
.map-land.is-match{opacity:1}
.map-land.is-home{fill:var(--map-home);stroke:var(--map-home-stroke);stroke-width:1.2}
.map-land.is-selected{stroke:var(--map-selected-stroke);stroke-width:1.4;filter:brightness(1.08)}
.map-land:focus-visible{outline:2px solid var(--a);outline-offset:2px}
.map-marker{stroke:var(--map-marker-stroke);stroke-width:1;cursor:pointer;transition:opacity .2s ease,r .15s ease}
.map-marker.is-dim{opacity:.22}
.map-marker.is-selected{stroke:var(--map-selected-stroke);stroke-width:2}
.map-status-visa_free{fill:var(--st-vf)}
.map-status-visa_on_arrival{fill:var(--st-voa)}
.map-status-eta{fill:var(--map-eta)}
.map-status-evisa{fill:var(--st-ev)}
.map-status-visa_required{fill:var(--map-vr)}
.map-status-no_admission{fill:var(--st-na)}
.map-status-home{fill:var(--map-home-fill)}
.map-status-unknown{fill:var(--map-unknown)}
.map-legend{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}
.map-legend .chip{border:1px solid var(--border);background:var(--surface-soft);color:var(--muted);border-radius:999px;padding:7px 11px;cursor:pointer;font-size:12px;display:inline-flex;align-items:center;gap:7px}
.map-legend .chip.active,.map-legend .chip:hover,.map-legend .chip:focus-visible{color:var(--text);border-color:var(--border-strong);background:var(--hover)}
.map-legend .swatch{width:10px;height:10px;border-radius:3px;display:inline-block}
.map-home-note{margin-top:8px;color:var(--muted);font-size:12px}
.map-tooltip{position:fixed;z-index:80;max-width:min(280px,86vw);padding:10px 12px;border-radius:12px;border:1px solid var(--border);background:var(--map-tooltip);color:var(--text);box-shadow:var(--shadow);pointer-events:none;font-size:12px;line-height:1.45;display:none}
.map-tooltip strong{display:block;font-size:13px;margin-bottom:4px}
.map-tooltip .muted{color:var(--muted)}
.map-sheet{position:absolute;inset-inline:10px;bottom:10px;z-index:5;border:1px solid var(--border);border-radius:14px;background:var(--map-sheet);backdrop-filter:blur(8px);padding:12px 14px;display:none;color:var(--text)}
.map-sheet.open{display:block}
.map-sheet .sheet-close{float:inline-end;border:0;background:transparent;color:var(--muted);cursor:pointer;font-size:16px}
.map-loading,.map-error{position:absolute;inset:0;display:grid;place-items:center;color:var(--muted);font-size:13px;padding:20px;text-align:center}
.map-shell.is-fullscreen{position:fixed;inset:12px;z-index:90;height:auto}
.map-shell.is-fullscreen .map-viewport{height:calc(100vh - 120px);min-height:280px}
@media(max-width:900px){
  .map-viewport{height:400px;min-height:360px}
}
@media(max-width:650px){
  .map-viewport{height:380px}
  .map-legend{flex-wrap:nowrap;overflow:auto;padding-bottom:4px;-webkit-overflow-scrolling:touch}
  .map-legend .chip{flex:0 0 auto}
}
@media(prefers-reduced-motion:reduce){
  .map-land,.map-marker{transition:none}
}
'''

MAP_JS = r'''
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
'''


def map_panel_html() -> str:
    return '''
    <section class="panel map-panel" id="mapPanel" hidden>
      <div class="map-head">
        <div>
          <h4 id="mapTitle"></h4>
          <p class="map-lead" id="mapLead"></p>
        </div>
        <div class="map-controls" role="toolbar" aria-label="Map controls">
          <button type="button" class="btn" id="mapZoomIn" aria-label="Zoom in">+</button>
          <button type="button" class="btn" id="mapZoomOut" aria-label="Zoom out">−</button>
          <button type="button" class="btn" id="mapReset" aria-label="Reset">↺</button>
          <button type="button" class="btn" id="mapFullscreen" aria-label="Fullscreen" aria-pressed="false">⛶</button>
        </div>
      </div>
      <div class="map-shell" id="mapShell">
        <div class="map-viewport" id="mapViewport">
          <div id="mapSvgMount"></div>
          <div class="map-loading" id="mapLoading" hidden></div>
          <div class="map-error" id="mapError" hidden></div>
          <div class="map-sheet" id="mapSheet"></div>
        </div>
      </div>
      <div class="map-legend" id="mapLegend" role="group" aria-label="Map legend"></div>
      <p class="map-home-note" id="mapHomeNote"></p>
    </section>
'''
