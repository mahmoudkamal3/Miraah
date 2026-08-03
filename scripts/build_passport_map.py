#!/usr/bin/env python3
"""Build a local Natural Earth–based passport access map asset.

Downloads Natural Earth Admin 0 (110m) once into source-data/passport-map/raw/,
writes a compact GeoJSON under public/passport/assets/, and an ISO mapping audit.

Natural Earth data is public domain:
https://www.naturalearthdata.com/about/terms-of-use/

Visitor browsers never fetch Natural Earth at runtime.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import sys
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import passport_locale as locale  # noqa: E402

RAW_DIR = ROOT / "source-data" / "passport-map" / "raw"
OUT_DIR = ROOT / "public" / "passport" / "assets"
OUT_MAP = OUT_DIR / "world-map.json"
AUDIT_PATH = ROOT / "source-data" / "passport-map" / "ISO_MAPPING_AUDIT.md"
MAPPING_JSON = ROOT / "source-data" / "passport-map" / "iso-mapping.json"
INDEX_PATH = ROOT / "public" / "data" / "passports" / "index.json"

# Natural Earth 110m Admin 0 countries (GeoJSON mirror of the public-domain dataset).
NE_GEOJSON_URL = (
    "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
    "master/geojson/ne_110m_admin_0_countries.geojson"
)
NE_SOURCE_PAGE = "https://www.naturalearthdata.com/downloads/110m-cultural-vectors/110m-admin-0-countries/"
USER_AGENT = "MirahPassportMapBuild/1.0 (https://miraah.mirapp.workers.dev/; offline map asset builder)"

# Explicit passport ISO3 → Natural Earth feature matching.
# Never silently invent codes: every destination must appear in mapping output.
EXPLICIT_NE_ISO_OVERRIDES: dict[str, str] = {
    # Natural Earth may store these under alternate ISO_A3 fields.
    "XKX": "XKX",  # Kosovo — verify against feature properties at build time
    "PSE": "PSE",
    "TWN": "TWN",
    "HKG": "HKG",  # often absent at 110m → marker
    "MAC": "MAC",
    "VAT": "VAT",
    "SGP": "SGP",
    "MLT": "MLT",
    "BHR": "BHR",
    "MDV": "MDV",
    "CPV": "CPV",
    "SYC": "SYC",
    "MUS": "MUS",
    "COM": "COM",
    "STP": "STP",
    "AND": "AND",
    "MCO": "MCO",
    "SMR": "SMR",
    "LIE": "LIE",
}

# Curated approximate centroids (WGS84) for destinations that need markers.
# Used only when no reliable clickable polygon exists at 110m. Explicit, reviewed.
MARKER_CENTROIDS: dict[str, tuple[float, float]] = {
    "ATG": (-61.7964, 17.0608),
    "BHS": (-77.3963, 25.0343),
    "BRB": (-59.5432, 13.1939),
    "DMA": (-61.3705, 15.4149),
    "GRD": (-61.6790, 12.1165),
    "KNA": (-62.7829, 17.3578),
    "LCA": (-60.9789, 13.9094),
    "VCT": (-61.2872, 13.2528),
    "TTO": (-61.2225, 10.6918),
    "HKG": (114.1694, 22.3193),
    "MAC": (113.5439, 22.1987),
    "SGP": (103.8198, 1.3521),
    "MLT": (14.5146, 35.8989),
    "BHR": (50.5577, 26.0667),
    "MDV": (73.5093, 4.1755),
    "VAT": (12.4534, 41.9029),
    "MCO": (7.4246, 43.7384),
    "SMR": (12.4578, 43.9424),
    "AND": (1.5218, 42.5063),
    "LIE": (9.5554, 47.1660),
    "CPV": (-23.6050, 15.1200),
    "SYC": (55.4513, -4.6796),
    "MUS": (57.5012, -20.1609),
    "COM": (43.3333, -11.6455),
    "STP": (6.6131, 0.1864),
    "WSM": (-171.7513, -13.7590),
    "TON": (-175.1982, -21.1789),
    "TUV": (179.1940, -8.5200),
    "NRU": (166.9315, -0.5228),
    "PLW": (134.5825, 7.5150),
    "FSM": (158.2150, 6.9248),
    "MHL": (171.1845, 7.1315),
    "KIR": (173.0340, 1.4510),
    "VUT": (168.3273, -17.7333),
    "SLB": (160.1562, -9.6457),
    "FJI": (178.0650, -17.7134),
    "TLS": (125.7275, -8.8742),
    "BRN": (114.7277, 4.5353),
    "XKX": (20.9020, 42.6026),
    "PSE": (35.2332, 31.9522),
    "GUM": (144.7937, 13.4443),  # not in dataset usually
}


def utc_now_note() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def download(url: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and dest.stat().st_size > 1000:
        return dest
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as resp:
        dest.write_bytes(resp.read())
    return dest


def load_passports() -> list[dict[str, Any]]:
    payload = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    return payload["passports"]


def destination_iso3_set() -> set[str]:
    # All destinations from one by-code file (matrix is square: 199 incl home).
    sample = ROOT / "public" / "data" / "passports" / "by-code" / "MLT.json"
    data = json.loads(sample.read_text(encoding="utf-8"))
    return {d["iso3"] for d in data["destinations"]}


def feature_iso_candidates(props: dict[str, Any]) -> list[str]:
    keys = (
        "ISO_A3_EH",
        "ISO_A3",
        "ADM0_A3",
        "ADM0_A3_US",
        "ADM0_A3_IS",
        "GU_A3",
        "SOV_A3",
        "BRK_A3",
    )
    out: list[str] = []
    for key in keys:
        val = props.get(key)
        if isinstance(val, str) and len(val) == 3 and val not in {"-99", "-1", "N/A"}:
            out.append(val.upper())
    return out


def ring_area(ring: list[list[float]]) -> float:
    if len(ring) < 3:
        return 0.0
    area = 0.0
    for i in range(len(ring) - 1):
        x1, y1 = ring[i]
        x2, y2 = ring[i + 1]
        area += x1 * y2 - x2 * y1
    return abs(area) * 0.5


def geometry_bbox_area(geom: dict[str, Any]) -> float:
    coords: list[list[float]] = []

    def walk(g: Any) -> None:
        if isinstance(g, dict):
            if g.get("type") == "Polygon":
                for ring in g.get("coordinates") or []:
                    coords.extend(ring)
            elif g.get("type") == "MultiPolygon":
                for poly in g.get("coordinates") or []:
                    for ring in poly:
                        coords.extend(ring)
        elif isinstance(g, list):
            for item in g:
                walk(item)

    walk(geom)
    if not coords:
        return 0.0
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    return max(0.0, (max(xs) - min(xs)) * (max(ys) - min(ys)))


def simplify_ring(ring: list[list[float]], tol: float = 0.05) -> list[list[float]]:
    """Very light radial-distance simplification (stdlib only)."""
    if len(ring) <= 4:
        return ring
    out = [ring[0]]
    for pt in ring[1:-1]:
        prev = out[-1]
        if abs(pt[0] - prev[0]) >= tol or abs(pt[1] - prev[1]) >= tol:
            out.append(pt)
    out.append(ring[-1])
    if out[0] != out[-1]:
        out.append(out[0])
    return out if len(out) >= 4 else ring


def simplify_geometry(geom: dict[str, Any], tol: float = 0.08) -> dict[str, Any]:
    gtype = geom.get("type")
    if gtype == "Polygon":
        return {
            "type": "Polygon",
            "coordinates": [simplify_ring(ring, tol) for ring in geom.get("coordinates") or []],
        }
    if gtype == "MultiPolygon":
        return {
            "type": "MultiPolygon",
            "coordinates": [
                [simplify_ring(ring, tol) for ring in poly]
                for poly in (geom.get("coordinates") or [])
            ],
        }
    return geom


def centroid_of_geometry(geom: dict[str, Any]) -> tuple[float, float] | None:
    pts: list[tuple[float, float]] = []

    def collect(coords: Any) -> None:
        if not coords:
            return
        if isinstance(coords[0], (int, float)):
            pts.append((float(coords[0]), float(coords[1])))
            return
        for c in coords:
            collect(c)

    collect(geom.get("coordinates"))
    if not pts:
        return None
    # Skip antimeridian-heavy averages poorly; still OK for markers fallback.
    lon = sum(p[0] for p in pts) / len(pts)
    lat = sum(p[1] for p in pts) / len(pts)
    return lon, lat


def build() -> dict[str, Any]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    geo_path = download(NE_GEOJSON_URL, RAW_DIR / "ne_110m_admin_0_countries.geojson")
    ne = json.loads(geo_path.read_text(encoding="utf-8"))

    # Index Natural Earth features by candidate ISO codes.
    by_iso: dict[str, dict[str, Any]] = {}
    disputed_notes: list[str] = []
    for feat in ne.get("features") or []:
        props = feat.get("properties") or {}
        name = props.get("NAME") or props.get("ADMIN") or ""
        for code in feature_iso_candidates(props):
            # Prefer first / EH code; keep largest geometry if duplicates.
            existing = by_iso.get(code)
            if not existing:
                by_iso[code] = feat
            else:
                if geometry_bbox_area(feat.get("geometry") or {}) > geometry_bbox_area(
                    existing.get("geometry") or {}
                ):
                    by_iso[code] = feat
        # Flag disputed / special
        if props.get("BRK_A3") and props.get("BRK_A3") not in {"-99", props.get("ISO_A3")}:
            disputed_notes.append(f"{name}: BRK_A3={props.get('BRK_A3')} ISO_A3={props.get('ISO_A3')}")

    # Kosovo special: Natural Earth often uses -99 for ISO_A3 and XKX/KOS in ADM0_A3
    for feat in ne.get("features") or []:
        props = feat.get("properties") or {}
        name = (props.get("NAME") or props.get("ADMIN") or "").lower()
        adm = str(props.get("ADM0_A3") or "").upper()
        if "kosovo" in name or adm in {"XKX", "KOS"}:
            by_iso.setdefault("XKX", feat)
            by_iso.setdefault("KOS", feat)

    dest_codes = sorted(destination_iso3_set())
    if len(dest_codes) != 199:
        raise SystemExit(f"Expected 199 destination ISO3 codes, found {len(dest_codes)}")

    polygons: list[dict[str, Any]] = []
    markers: list[dict[str, Any]] = []
    not_mappable: list[dict[str, Any]] = []
    mapping_rows: list[dict[str, Any]] = []
    tiny_marker_force = set(MARKER_CENTROIDS)

    # Tiny bbox threshold (degrees²) — force marker overlay for reliable clicking.
    TINY_AREA = 2.5

    for iso3 in dest_codes:
        override = EXPLICIT_NE_ISO_OVERRIDES.get(iso3, iso3)
        feat = by_iso.get(override) or by_iso.get(iso3)
        name_en = locale.NAME_EN.get(iso3, iso3)
        row: dict[str, Any] = {
            "iso3": iso3,
            "nameEn": name_en,
            "neMatchIso": override if feat else None,
            "representation": None,
            "notes": "",
        }

        if feat and iso3 not in {"HKG", "MAC"}:
            # HKG/MAC: prefer dedicated markers even if China polygon would match wrongly.
            geom = simplify_geometry(feat.get("geometry") or {}, tol=0.1)
            area = geometry_bbox_area(geom)
            props = feat.get("properties") or {}
            ne_name = props.get("NAME") or props.get("ADMIN")
            # Avoid assigning China polygon to HKG/MAC via SOV_A3.
            if iso3 in {"HKG", "MAC"} and str(props.get("ISO_A3") or "").upper() in {"CHN", "-99"}:
                feat = None
            elif iso3 == "PSE" and "palestine" not in str(ne_name).lower() and str(
                props.get("ISO_A3") or ""
            ).upper() not in {"PSE", "PSX"}:
                # Only accept an explicit Palestine feature.
                if "west bank" not in str(ne_name).lower() and "gaza" not in str(ne_name).lower():
                    feat = None

        if feat and iso3 not in {"HKG", "MAC"}:
            geom = simplify_geometry(feat.get("geometry") or {}, tol=0.1)
            area = geometry_bbox_area(geom)
            use_marker = iso3 in tiny_marker_force or area < TINY_AREA
            polygons.append(
                {
                    "type": "Feature",
                    "id": iso3,
                    "properties": {
                        "iso3": iso3,
                        "nameEn": name_en,
                        "nameAr": locale.NAME_AR.get(iso3, name_en),
                        "kind": "polygon",
                        "tiny": bool(use_marker),
                    },
                    "geometry": geom,
                }
            )
            if use_marker:
                lonlat = MARKER_CENTROIDS.get(iso3) or centroid_of_geometry(geom)
                if lonlat:
                    markers.append(
                        {
                            "type": "Feature",
                            "id": f"{iso3}-marker",
                            "properties": {
                                "iso3": iso3,
                                "nameEn": name_en,
                                "nameAr": locale.NAME_AR.get(iso3, name_en),
                                "kind": "marker",
                                "reason": "tiny_or_hard_to_click",
                            },
                            "geometry": {"type": "Point", "coordinates": [lonlat[0], lonlat[1]]},
                        }
                    )
                    row["representation"] = "polygon+marker"
                    row["notes"] = "Polygon present; marker added for click reliability."
                else:
                    row["representation"] = "polygon"
                    row["notes"] = "Polygon only."
            else:
                row["representation"] = "polygon"
                row["notes"] = "Direct Natural Earth Admin 0 polygon."
        else:
            lonlat = MARKER_CENTROIDS.get(iso3)
            if lonlat:
                markers.append(
                    {
                        "type": "Feature",
                        "id": f"{iso3}-marker",
                        "properties": {
                            "iso3": iso3,
                            "nameEn": name_en,
                            "nameAr": locale.NAME_AR.get(iso3, name_en),
                            "kind": "marker",
                            "reason": "missing_or_unreliable_110m_polygon",
                        },
                        "geometry": {"type": "Point", "coordinates": [lonlat[0], lonlat[1]]},
                    }
                )
                row["representation"] = "marker"
                row["notes"] = "Explicit curated marker; no reliable 110m polygon."
            else:
                row["representation"] = "not_mappable"
                row["notes"] = "No polygon match and no curated marker — requires follow-up."
                not_mappable.append(row)

        mapping_rows.append(row)

    # Deduplicate polygon features by iso3 (keep first).
    seen_poly: set[str] = set()
    unique_polygons = []
    for f in polygons:
        iso = f["properties"]["iso3"]
        if iso in seen_poly:
            continue
        seen_poly.add(iso)
        unique_polygons.append(f)

    payload = {
        "type": "FeatureCollection",
        "name": "miraah-passport-access-map",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "meta": {
            "generatedAt": utc_now_note(),
            "source": "Natural Earth Admin 0 countries (110m)",
            "sourceUrl": NE_SOURCE_PAGE,
            "license": "Public Domain",
            "licenseUrl": "https://www.naturalearthdata.com/about/terms-of-use/",
            "geometrySourceFile": str(geo_path.relative_to(ROOT)).replace("\\", "/"),
            "destinationCount": 199,
            "travelDestinationCount": 198,
            "polygonCount": len(unique_polygons),
            "markerCount": len(markers),
            "notMappableCount": len(not_mappable),
            "note": "Visa/entry classifications come from Passport Index Data, not Natural Earth.",
        },
        "features": unique_polygons + markers,
    }

    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    OUT_MAP.write_bytes(raw)

    mapping_doc = {
        "generatedAt": utc_now_note(),
        "source": NE_SOURCE_PAGE,
        "license": "Public Domain (Natural Earth)",
        "rows": mapping_rows,
        "notMappable": not_mappable,
        "disputedNotesSample": disputed_notes[:40],
    }
    MAPPING_JSON.write_text(json.dumps(mapping_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    poly_n = sum(1 for r in mapping_rows if r["representation"] == "polygon")
    both_n = sum(1 for r in mapping_rows if r["representation"] == "polygon+marker")
    mark_n = sum(1 for r in mapping_rows if r["representation"] == "marker")
    missing = [r for r in mapping_rows if r["representation"] == "not_mappable"]

    lines = [
        "# Passport map ISO mapping audit",
        "",
        f"- Generated: `{mapping_doc['generatedAt']}`",
        f"- Natural Earth source: {NE_SOURCE_PAGE}",
        f"- License: Public Domain",
        f"- Output asset: `{OUT_MAP.relative_to(ROOT).as_posix()}` ({len(raw)} bytes raw)",
        "",
        "## Counts",
        "",
        f"| Representation | Count |",
        f"| --- | ---: |",
        f"| polygon only | {poly_n} |",
        f"| polygon + marker | {both_n} |",
        f"| marker only | {mark_n} |",
        f"| not mappable | {len(missing)} |",
        f"| **destinations audited** | **{len(mapping_rows)}** |",
        "",
        "## Special / disputed explicit reviews",
        "",
        "| ISO3 | Representation | Notes |",
        "| --- | --- | --- |",
    ]
    special = ["XKX", "PSE", "TWN", "HKG", "MAC", "VAT", "SGP", "MLT", "ESH", "MAR"]
    by_code = {r["iso3"]: r for r in mapping_rows}
    for code in special:
        r = by_code.get(code)
        if not r:
            lines.append(f"| {code} | — | Not in passport destination universe |")
        else:
            lines.append(f"| {code} | {r['representation']} | {r['notes']} |")

    lines += ["", "## Marker-only destinations", ""]
    for r in mapping_rows:
        if r["representation"] == "marker":
            lines.append(f"- `{r['iso3']}` {r['nameEn']} — {r['notes']}")

    lines += ["", "## Not mappable", ""]
    if missing:
        for r in missing:
            lines.append(f"- `{r['iso3']}` {r['nameEn']} — {r['notes']}")
    else:
        lines.append("_None. Every destination has a polygon and/or marker._")

    lines += [
        "",
        "## Integrity rule",
        "",
        "Mappings are explicit. Build fails closed if destination count ≠ 199.",
        "Home destinations are included in geometry so the selected passport’s home can be highlighted;",
        "legend travel totals still exclude home (198).",
        "",
    ]
    AUDIT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    summary = {
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "polygonFeatures": len(unique_polygons),
        "markerFeatures": len(markers),
        "polygonOnly": poly_n,
        "polygonPlusMarker": both_n,
        "markerOnly": mark_n,
        "notMappable": len(missing),
        "out": str(OUT_MAP.relative_to(ROOT)).replace("\\", "/"),
    }
    if missing:
        raise SystemExit(f"Not mappable destinations remain: {[m['iso3'] for m in missing]}")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force-download", action="store_true")
    args = parser.parse_args(argv)
    if args.force_download:
        target = RAW_DIR / "ne_110m_admin_0_countries.geojson"
        if target.exists():
            target.unlink()
    summary = build()
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
