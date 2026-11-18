# Spinneret

Spider families of North America (store name **Spinneret**).

Pebble Time 2 watchface cloned from [Fish Time](../fish-of-new-england-pebble-watchface): daily rotation through spider families recorded in North America, with family common name and scientific name (family) below the plate.

- **Preview all families (3 sec)** — default on first install: cycles through all 71 every 3 seconds; turn off in settings for one family per day at midnight.
- Daily mode: 71-day shuffled-looking cycle (no repeat until each family has appeared once).
- **Color illustrations** vs **grayscale plates**, and light or dark background, via Clay settings (same pattern as Fish Time).
- Uses a distinct app UUID so it does not overwrite Fish Time on the watch.

Build: `pebble clean && pebble build` then `pebble install --cloudpebble`.

**Rebble store:** app name **Spinneret** — listing copy and assets in [`store/LISTING.md`](store/LISTING.md); regenerate icons/banner/screenshots with `python3 scripts/make_store_assets.py`.

## Assets

Source illustrations are copied into `originals/` when you run the image script. Pebble-ready bitmaps live in `resources/images/color/` and `resources/images/mono/` (referenced in `package.json` as `images/color/` …). Full sources are kept under `resources/images/reference/`.

After catalog or image changes:

```bash
python3 scripts/optimize_images.py
python3 scripts/gen_spider_resources.py
```

Plates are cropped to remove the printed family name along the bottom edge before resizing.

### Local preview (3s cycle)

```bash
python3 scripts/gen_preview.py
python3 -m http.server 9876
```

Open [http://127.0.0.1:9876/preview/index.html](http://127.0.0.1:9876/preview/index.html) — watchface layout, advances every 3 seconds (Pause / Prev / Next, grayscale and dark background toggles).

`spider_catalog.csv` drives `package.json` resources and `src/spider_table.inc`.

Fork/adaptation of Fish Time. Illustrations are field-guide style family plates (user-provided assets).