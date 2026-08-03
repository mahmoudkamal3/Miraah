# Passport map ISO mapping audit

- Generated: `2026-08-03T15:54:12Z`
- Natural Earth source: https://www.naturalearthdata.com/downloads/110m-cultural-vectors/110m-admin-0-countries/
- License: Public Domain
- Output asset: `public/passport/assets/world-map.json` (253548 bytes raw)

## Counts

| Representation | Count |
| --- | ---: |
| polygon only | 152 |
| polygon + marker | 16 |
| marker only | 31 |
| not mappable | 0 |
| **destinations audited** | **199** |

## Special / disputed explicit reviews

| ISO3 | Representation | Notes |
| --- | --- | --- |
| XKX | polygon+marker | Polygon present; marker added for click reliability. |
| PSE | polygon+marker | Polygon present; marker added for click reliability. |
| TWN | polygon | Direct Natural Earth Admin 0 polygon. |
| HKG | marker | Explicit curated marker; no reliable 110m polygon. |
| MAC | marker | Explicit curated marker; no reliable 110m polygon. |
| VAT | marker | Explicit curated marker; no reliable 110m polygon. |
| SGP | marker | Explicit curated marker; no reliable 110m polygon. |
| MLT | marker | Explicit curated marker; no reliable 110m polygon. |
| ESH | — | Not in passport destination universe |
| MAR | polygon | Direct Natural Earth Admin 0 polygon. |

## Marker-only destinations

- `AND` Andorra — Explicit curated marker; no reliable 110m polygon.
- `ATG` Antigua and Barbuda — Explicit curated marker; no reliable 110m polygon.
- `BHR` Bahrain — Explicit curated marker; no reliable 110m polygon.
- `BRB` Barbados — Explicit curated marker; no reliable 110m polygon.
- `COM` Comoros — Explicit curated marker; no reliable 110m polygon.
- `CPV` Cabo Verde — Explicit curated marker; no reliable 110m polygon.
- `DMA` Dominica — Explicit curated marker; no reliable 110m polygon.
- `FSM` Micronesia — Explicit curated marker; no reliable 110m polygon.
- `GRD` Grenada — Explicit curated marker; no reliable 110m polygon.
- `HKG` Hong Kong — Explicit curated marker; no reliable 110m polygon.
- `KIR` Kiribati — Explicit curated marker; no reliable 110m polygon.
- `KNA` Saint Kitts and Nevis — Explicit curated marker; no reliable 110m polygon.
- `LCA` Saint Lucia — Explicit curated marker; no reliable 110m polygon.
- `LIE` Liechtenstein — Explicit curated marker; no reliable 110m polygon.
- `MAC` Macao — Explicit curated marker; no reliable 110m polygon.
- `MCO` Monaco — Explicit curated marker; no reliable 110m polygon.
- `MDV` Maldives — Explicit curated marker; no reliable 110m polygon.
- `MHL` Marshall Islands — Explicit curated marker; no reliable 110m polygon.
- `MLT` Malta — Explicit curated marker; no reliable 110m polygon.
- `MUS` Mauritius — Explicit curated marker; no reliable 110m polygon.
- `NRU` Nauru — Explicit curated marker; no reliable 110m polygon.
- `PLW` Palau — Explicit curated marker; no reliable 110m polygon.
- `SGP` Singapore — Explicit curated marker; no reliable 110m polygon.
- `SMR` San Marino — Explicit curated marker; no reliable 110m polygon.
- `STP` São Tomé and Príncipe — Explicit curated marker; no reliable 110m polygon.
- `SYC` Seychelles — Explicit curated marker; no reliable 110m polygon.
- `TON` Tonga — Explicit curated marker; no reliable 110m polygon.
- `TUV` Tuvalu — Explicit curated marker; no reliable 110m polygon.
- `VAT` Vatican City — Explicit curated marker; no reliable 110m polygon.
- `VCT` Saint Vincent and the Grenadines — Explicit curated marker; no reliable 110m polygon.
- `WSM` Samoa — Explicit curated marker; no reliable 110m polygon.

## Not mappable

_None. Every destination has a polygon and/or marker._

## Integrity rule

Mappings are explicit. Build fails closed if destination count ≠ 199.
Home destinations are included in geometry so the selected passport’s home can be highlighted;
legend travel totals still exclude home (198).

