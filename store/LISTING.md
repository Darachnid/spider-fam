# Rebble App Store — Spider Fam

Portal: [dev-portal.rebble.io](https://dev-portal.rebble.io) · Category: **Watchfaces**

## Title

**Spider Fam**

## Short description (≤ 250 chars)

71 North American spider-family plates on Pebble Time 2—color or grayscale, optional 3s preview or daily rotation.

## Full description (paste into store)

Spider Fam is a field-guide watchface for **Pebble Time 2 (emery)**: one illustration per spider **family** found in North America, with common and scientific names under the plate and the clock below.

**71 families** — from jumping spiders and orb-weavers to tarantulas and sheetweavers — each as a cropped plate (no stamped label text).

**Art:** full **color** RGB plates or **grayscale** “museum print” style. **White or black** background via phone settings.

**Rotation:** **one family per day** at midnight (71-day shuffled cycle, no repeats within a cycle). Optional **Preview all families (3 sec)** in settings.

**Settings (Clay):** Color illustrations, Preview cycle, Background.

Fork of the Fish Time watchface pattern; distinct app UUID so it installs beside Fish Time.

Open source. Illustrations are user-supplied field-guide style plates, processed for Pebble’s 64-color palette.

## Release notes (0.1.0)

- Initial release: 71 families, color + mono, preview cycle, dark background option
- Plate labels stripped; Pebble-optimized art

## Assets

| File | Use |
|------|-----|
| `store/icon_144x144.png` | Large store icon |
| `store/icon_80x80.png` | Small / list icon |
| `store/icon_48x48.png` | Compact icon |
| `store/watch_menu_icon_25.png` | Locker / menu reference (also `resources/images/icon.png` in .pbw) |
| `store/banner_720x320.png` | Store header banner |
| `store/screenshots/emery_*.png` | Emery screenshots (200×228) — upload under **emery** |

## PBW

Build: `pebble build` → `build/spider-fam-v0.1.0.pbw` (see `store/releases/`).

## UUID

`1262f334-fdac-4839-b251-16e5ef5721a2` — do not change for store updates.

## Optional CLI publish

```bash
pebble login
pebble publish --non-interactive \
  --description "71 spider family plates for Pebble Time 2 — color, grayscale, 3s preview or daily." \
  --release-notes "Initial Spider Fam release." \
  --category watchfaces
```

## Tags (portal)

watchface, spiders, arachnids, field guide, nature, emery, Pebble Time 2