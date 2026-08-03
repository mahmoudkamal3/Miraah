#!/usr/bin/env python3
"""Shared Mir’ah local SVG flag helpers (no emoji, no CDN)."""
from __future__ import annotations

from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FLAGS_DIR = ROOT / "public" / "assets" / "flags"
FLAGS_URL_BASE = "/assets/flags"
FALLBACK_FILE = "_fallback.svg"
FALLBACK_PATH = FLAGS_DIR / FALLBACK_FILE
FALLBACK_URL = f"{FLAGS_URL_BASE}/{FALLBACK_FILE}"

# Exceptional / alias ISO2 codes → flag-icons filename (lowercase, no extension).
# Kosovo uses user-assigned XK; flag-icons provides xk.svg.
ISO2_ALIASES: dict[str, str] = {
    "xk": "xk",  # Kosovo
    "ps": "ps",  # Palestine
    "tw": "tw",  # Taiwan
    "hk": "hk",  # Hong Kong
    "mo": "mo",  # Macao
    "va": "va",  # Vatican / Holy See
    "gb": "gb",
    "uk": "gb",
}

FLAG_CSS = r"""
.miraah-flag{display:inline-block;flex-shrink:0;overflow:hidden;border-radius:3px;border:1px solid var(--border);background:var(--surface-soft);box-shadow:0 1px 2px #0002;line-height:0;vertical-align:middle}
.miraah-flag img{display:block;width:100%;height:100%;object-fit:contain;object-position:center}
.flag-xs{width:18px;height:13px}
.flag-sm{width:22px;height:16px}
.flag-md{width:40px;height:30px;border-radius:5px}
.flag-hero{width:min(100%,220px);height:auto;aspect-ratio:4/3;border-radius:14px;border-width:1px;box-shadow:var(--shadow-soft)}
.flag-with-name{display:inline-flex;align-items:center;gap:8px;min-width:0;max-width:100%}
.flag-with-name .flag-label{min-width:0;overflow:hidden;text-overflow:ellipsis}
.flag-stage{display:grid;place-items:center;width:100%;border-radius:14px;border:1px solid var(--border);background:
  radial-gradient(circle at 30% 20%,var(--glow-soft),transparent 55%),
  linear-gradient(160deg,var(--surface-raised),var(--surface-soft));
  box-shadow:inset 0 0 0 1px #ffffff08;padding:14px;min-height:78px}
.flag-stage .miraah-flag{box-shadow:0 8px 22px #0003}
.passport-identity{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;background:linear-gradient(160deg,var(--surface-raised),var(--surface));border:1px solid var(--line);border-radius:16px;padding:18px 16px;min-height:220px;text-align:center}
.passport-identity .identity-name{margin:0;font-size:16px;font-weight:750;line-height:1.35}
.passport-identity .identity-code{margin:0;color:var(--muted);font-size:12px;letter-spacing:.04em}
.pass-illus.flag-stage{min-height:88px;padding:12px}
@media(max-width:820px){
  .passport-card{grid-template-columns:1fr!important}
  .passport-identity{order:1;min-height:180px}
  .score-panel{order:2}
  .passport-visual{order:3}
}
"""

FLAG_JS = r"""
const MIRAAH_FLAG_BASE='/assets/flags/';
const MIRAAH_FLAG_FALLBACK='/assets/flags/_fallback.svg';
const MIRAAH_FLAG_ALIAS={uk:'gb'};
function resolveFlagIso2(iso2){
  const raw=String(iso2||'').trim().toLowerCase();
  if(!raw)return '';
  return MIRAAH_FLAG_ALIAS[raw]||raw;
}
function flagUrl(iso2){
  const code=resolveFlagIso2(iso2);
  if(!code)return MIRAAH_FLAG_FALLBACK;
  return MIRAAH_FLAG_BASE+code+'.svg';
}
function flagImgHtml(iso2,name,size,{lazy=true,decorative=true}={}){
  const code=resolveFlagIso2(iso2);
  const src=flagUrl(code);
  const cls='miraah-flag flag-'+(size||'sm');
  const alt=decorative?'':esc(name||code.toUpperCase());
  const aria=decorative?' aria-hidden="true" alt=""':' alt="'+alt+'"';
  const loading=lazy?' loading="lazy"':'';
  const title=name?(' title="'+esc(name)+'"'):'';
  return '<span class="'+cls+'"'+title+'><img src="'+src+'" width="640" height="480" decoding="async"'+loading+aria+' onerror="this.onerror=null;this.src=\''+MIRAAH_FLAG_FALLBACK+'\'"></span>';
}
function flagWithNameHtml(iso2,name,size,{lazy=true}={}){
  return '<span class="flag-with-name">'+flagImgHtml(iso2,name,size,{lazy,decorative:true})+'<span class="flag-label">'+esc(name)+'</span></span>';
}
"""


def normalize_iso2(iso2: str | None) -> str:
    return (iso2 or "").strip().lower()


def resolve_iso2(iso2: str | None) -> str:
    code = normalize_iso2(iso2)
    if not code:
        return ""
    return ISO2_ALIASES.get(code, code)


def flag_url(iso2: str | None) -> str:
    code = resolve_iso2(iso2)
    if not code:
        return FALLBACK_URL
    path = FLAGS_DIR / f"{code}.svg"
    if path.is_file():
        return f"{FLAGS_URL_BASE}/{code}.svg"
    return FALLBACK_URL


def flag_exists(iso2: str | None) -> bool:
    code = resolve_iso2(iso2)
    return bool(code) and (FLAGS_DIR / f"{code}.svg").is_file()


def flag_img_html(
    iso2: str | None,
    *,
    name: str = "",
    size: str = "sm",
    lazy: bool = True,
    decorative: bool = True,
) -> str:
    """size: xs | sm | md | hero"""
    src = flag_url(iso2)
    cls = f"miraah-flag flag-{size}"
    title = f' title="{escape(name)}"' if name else ""
    if decorative:
        aria = ' aria-hidden="true" alt=""'
    else:
        aria = f' alt="{escape(name or resolve_iso2(iso2).upper() or "Flag")}"'
    loading = ' loading="lazy"' if lazy else ""
    return (
        f'<span class="{cls}"{title}>'
        f'<img src="{src}" width="640" height="480" decoding="async"{loading}{aria} '
        f'onerror="this.onerror=null;this.src=\'{FALLBACK_URL}\'">'
        f"</span>"
    )


def flag_with_name_html(
    iso2: str | None,
    name: str,
    *,
    size: str = "sm",
    lazy: bool = True,
) -> str:
    return (
        '<span class="flag-with-name">'
        f"{flag_img_html(iso2, name=name, size=size, lazy=lazy, decorative=True)}"
        f'<span class="flag-label">{escape(name)}</span>'
        "</span>"
    )


def required_iso2_codes(passports: list[dict], destinations: list[dict] | None = None) -> list[str]:
    codes: set[str] = set()
    for p in passports:
        c = resolve_iso2(p.get("iso2"))
        if c:
            codes.add(c)
    for d in destinations or []:
        c = resolve_iso2(d.get("iso2"))
        if c:
            codes.add(c)
    return sorted(codes)


def missing_flag_codes(iso2_codes: list[str]) -> list[str]:
    return [c for c in iso2_codes if not (FLAGS_DIR / f"{c}.svg").is_file()]
