#!/usr/bin/env python3
"""Write preview/index.html — 3s slideshow of processed color plates."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "spider_catalog.csv"
PREVIEW = ROOT / "preview"
INTERVAL_MS = 3000

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Spider Families — preview (3s)</title>
  <style>
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      font-family: system-ui, sans-serif;
      background: #1a1a1a;
      color: #eee;
    }
    .frame {
      width: 182px;
      background: #fff;
      color: #000;
      border-radius: 24px;
      padding: 8px 8px 10px;
      box-shadow: 0 12px 40px rgba(0,0,0,.45);
    }
    .plate {
      width: 166px;
      height: 94px;
      margin: 0 auto;
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: hidden;
    }
    .plate img {
      max-width: 100%;
      max-height: 100%;
      image-rendering: pixelated;
    }
    .common {
      font-size: 13px;
      font-weight: 700;
      text-align: center;
      margin: 6px 0 2px;
      line-height: 1.2;
    }
    .scientific {
      font-size: 11px;
      text-align: center;
      margin-bottom: 4px;
    }
    .time {
      font-size: 28px;
      font-weight: 700;
      text-align: center;
      letter-spacing: 1px;
    }
    .date {
      font-size: 11px;
      text-align: center;
      color: #333;
    }
    .meta {
      margin-top: 20px;
      text-align: center;
      font-size: 14px;
      color: #aaa;
    }
    .controls {
      margin-top: 12px;
      display: flex;
      gap: 8px;
    }
    button {
      background: #333;
      color: #fff;
      border: 1px solid #555;
      padding: 8px 14px;
      border-radius: 8px;
      cursor: pointer;
    }
    button:hover { background: #444; }
    label { display: flex; align-items: center; gap: 6px; font-size: 13px; }
  </style>
</head>
<body>
  <div class="frame" id="watch">
    <div class="plate"><img id="img" alt="" /></div>
    <div class="common" id="common"></div>
    <div class="scientific" id="scientific"></div>
    <div class="time" id="clock">12:00</div>
    <div class="date" id="date"></div>
  </div>
  <div class="meta">
    <span id="counter"></span> · every <span id="interval-label"></span>s
  </div>
  <div class="controls">
    <button type="button" id="prev">Prev</button>
    <button type="button" id="pause">Pause</button>
    <button type="button" id="next">Next</button>
    <label><input type="checkbox" id="mono" /> Grayscale</label>
    <label><input type="checkbox" id="dark" /> Dark background</label>
  </div>
  <script>
    const ENTRIES = __ENTRIES__;
    const INTERVAL = __INTERVAL__;
    let index = 0;
    let timer = null;
    let paused = false;

    function tickClock() {
      const d = new Date();
      document.getElementById("clock").textContent = d.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
      document.getElementById("date").textContent = d.toLocaleDateString([], { weekday: "short", month: "short", day: "numeric" });
    }

    function show(i) {
      index = (i + ENTRIES.length) % ENTRIES.length;
      const e = ENTRIES[index];
      const mono = document.getElementById("mono").checked;
      document.getElementById("img").src = "../resources/images/" + (mono ? "mono" : "color") + "/" + e.filename;
      document.getElementById("common").textContent = e.common;
      document.getElementById("scientific").textContent = e.scientific;
      document.getElementById("counter").textContent = (index + 1) + " / " + ENTRIES.length + " · " + e.scientific;
    }

    function applyTheme() {
      const dark = document.getElementById("dark").checked;
      const frame = document.getElementById("watch");
      frame.style.background = dark ? "#000" : "#fff";
      frame.style.color = dark ? "#fff" : "#000";
      document.getElementById("date").style.color = dark ? "#ccc" : "#333";
      document.querySelector(".plate").style.background = dark ? "#000" : "#fff";
    }

    function schedule() {
      if (timer) clearInterval(timer);
      timer = setInterval(() => { if (!paused) show(index + 1); }, INTERVAL);
    }

    document.getElementById("prev").onclick = () => show(index - 1);
    document.getElementById("next").onclick = () => show(index + 1);
    document.getElementById("pause").onclick = (ev) => {
      paused = !paused;
      ev.target.textContent = paused ? "Play" : "Pause";
    };
    document.getElementById("mono").onchange = () => show(index);
    document.getElementById("dark").onchange = applyTheme;

    document.getElementById("interval-label").textContent = INTERVAL / 1000;
    tickClock();
    setInterval(tickClock, 1000);
    applyTheme();
    show(0);
    schedule();
  </script>
</body>
</html>
"""


def main() -> None:
    with CATALOG.open(newline="", encoding="utf-8") as fh:
        entries = list(csv.DictReader(fh))
    PREVIEW.mkdir(parents=True, exist_ok=True)
    html = HTML.replace("__ENTRIES__", json.dumps(entries, ensure_ascii=False))
    html = html.replace("__INTERVAL__", str(INTERVAL_MS))
    (PREVIEW / "index.html").write_text(html, encoding="utf-8")
    print(f"Wrote {PREVIEW / 'index.html'} ({len(entries)} families, {INTERVAL_MS // 1000}s interval)")


if __name__ == "__main__":
    main()