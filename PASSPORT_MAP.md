# Passport access world map

Mir’ah Passport Power renders destination entry requirements on a local SVG world map.

## Geographic source

- **Natural Earth** Admin 0 countries, 110m cultural vectors  
- Terms: [Public Domain](https://www.naturalearthdata.com/about/terms-of-use/)  
- Download page: https://www.naturalearthdata.com/downloads/110m-cultural-vectors/110m-admin-0-countries/  
- Build mirror used offline: `source-data/passport-map/raw/ne_110m_admin_0_countries.geojson`

Natural Earth is **not** the visa-data source. Entry classifications come from Passport Index Data (experimental).

## Build

```bash
python scripts/build_passport_map.py
```

Outputs:

| Path | Purpose |
| --- | --- |
| `public/passport/assets/world-map.json` | Compact GeoJSON (polygons + markers) |
| `source-data/passport-map/iso-mapping.json` | Explicit ISO3 mapping rows |
| `source-data/passport-map/ISO_MAPPING_AUDIT.md` | Human-readable audit |

Visitors never fetch Natural Earth. The map asset is loaded only on Passport Power pages after a passport is selected.

## Representation rules

Every one of the **198** compared destinations (plus home for highlighting) is either:

- a Natural Earth polygon, and/or
- a curated clickable marker for tiny / missing geometries

See the ISO mapping audit for Kosovo, Palestine, Taiwan, Hong Kong, Macao, Vatican, Singapore, Malta, and island territories.

## UI

- Mir’ah category colors (visa-free, VOA, eTA, eVisa, visa required, no admission)
- Legend counts from the selected passport’s `categoryTotals` (home shown separately)
- Zoom / reset / fullscreen controls
- Tooltip + mobile detail sheet
- Sync with destination search, region filter, and status chips

## Future (not implemented)

A historical mobility-score line chart requires a properly licensed historical time series. The current snapshot source must not be interpolated or scraped for fake history — see `PASSPORT_DATA.md`.
