#!/usr/bin/env python3
"""Draw THE WORLD TODAY, front page for Thursday 26 November 2026.

Every fact on the page comes from ../facts26.md.  Nothing else is read: no
clock, no network, no environment, no randomness.  Two runs write the same
bytes.

The page is built from one list of story dicts (STORIES).  Counts printed at
the end are computed from that list, never typed twice.
"""

from __future__ import annotations

import hashlib
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(ROOT, "entry.png")

W = H = 1024
PAPER = "#f4f1e8"
INK = "#14120e"

F_SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
F_SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
F_SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
F_MONO_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

# --------------------------------------------------------------------------
# vertical budget (the brief's own bands overflow by ~24 px: 944-988 cannot
# hold seven 9 px lines, so the stack is shifted up and the also-today band
# given the height it needs)
# --------------------------------------------------------------------------
MAST_H = 88
TICKER_Y, TICKER_H = 88, 32
LEAD_Y, LEAD_H = 124, 246
BAR_Y, BAR_H = 374, 32
TL_Y, TL_H = 410, 34
GRID_Y, GRID_H = 448, 418
CELL_W, CELL_H, GUT = 192, 100, 6
NUM_Y, NUM_H = 870, 34
ALSO_Y, ALSO_H = 908, 78
FOOT_Y, FOOT_H = 992, 32

MARGIN = 20
COL_W = 984

# --------------------------------------------------------------------------
# palette: newsprint, ink, seven region tints (twelve regions reuse them)
# --------------------------------------------------------------------------
TINTS = ["#d9c08a", "#c9b3a0", "#a9b48f", "#b6c3cc", "#c6c2d2", "#d2b6b0", "#a8c0b4"]
REGION_INK = {
    "EUROPE": "#3a3550",
    "LEVANT": "#5a3a28",
    "EAST ASIA": "#243a4a",
    "AMERICAS": "#5a2f2c",
    "GULF": "#5c4415",
    "NORTH AFRICA": "#584018",
    "WEST AFRICA": "#3f4520",
    "CENTRAL AFRICA": "#2f4230",
    "SOUTH ASIA": "#4a3220",
    "SOUTHEAST ASIA": "#26443a",
    "PACIFIC": "#254352",
    "SOUTHERN AFRICA": "#3a4430",
}
# bar order: biggest first, tints cycled so neighbours never match
BAR_ORDER = [
    "EUROPE", "LEVANT", "EAST ASIA", "AMERICAS", "GULF", "NORTH AFRICA",
    "WEST AFRICA", "CENTRAL AFRICA", "SOUTH ASIA", "SOUTHEAST ASIA",
    "PACIFIC", "SOUTHERN AFRICA",
]
REGION_TINT = {name: TINTS[i % len(TINTS)] for i, name in enumerate(BAR_ORDER)}
# short labels for the region bar, where twelve segments share 920 px
REGION_SHORT = {
    "EUROPE": "EUROPE", "LEVANT": "LEVANT", "EAST ASIA": "E. ASIA",
    "AMERICAS": "AMERICAS", "GULF": "GULF", "NORTH AFRICA": "N. AFRICA",
    "WEST AFRICA": "W. AFRICA", "CENTRAL AFRICA": "C. AFRICA",
    "SOUTH ASIA": "S. ASIA", "SOUTHEAST ASIA": "SE. ASIA",
    "PACIFIC": "PACIFIC", "SOUTHERN AFRICA": "S. AFRICA",
}

# scene tones: sky / ground-or-water / mid / accent
P = {
    "sky_pale": "#cfe0e6", "sky_sand": "#e2d8c0", "sky_grey": "#c6cfd8",
    "sky_dusk": "#b9b0a8", "sky_hot": "#e8d3b4",
    "water_deep": "#2f4f63", "water_dark": "#26404f", "water_grey": "#4a5b66",
    "ground_brown": "#4a3f33", "ground_dark": "#3b332b", "ground_clay": "#5a4634",
    "ground_olive": "#41452f",
    "mid_stone": "#8a7a63", "mid_grey": "#6d6a63", "mid_steel": "#7d8790",
    "mid_plum": "#5b4a63", "mid_sage": "#6b7a5e",
    "flame": "#c25a22", "flame_deep": "#a8451c",
    "accent_red": "#7d2f2a", "accent_green": "#2e5a44", "accent_blue": "#2b4a6b",
    "accent_gold": "#8a6a1f", "accent_plum": "#5c3a63",
    "light_warm": "#efe6d0", "light_cool": "#e6e9ea",
}

# --------------------------------------------------------------------------
# the forty stories.  role: lead / grid / list.  grid stories carry a scene.
# --------------------------------------------------------------------------
STORIES = [
    # ---- the lead -------------------------------------------------------
    dict(
        role="lead", region="GULF", field="AIR DEFENCE",
        headline="Houthi missiles at Riyadh are intercepted as a tanker blast shakes the Gulf",
        subhead="An explosion shook Sanaa after strikes near its airport, and UKMTO said a "
                "tanker master saw a blast 50 nautical miles west of Dubai",
        dateline="RIYADH \u00b7 26 NOVEMBER 2026 \u00b7 AL JAZEERA, REUTERS",
        scene="lead", tones=("sky_hot", "water_deep", "mid_stone", "flame"),
    ),
    # ---- twenty cells, each with a drawn scene --------------------------
    dict(role="grid", region="GULF", field="SHIPPING",
         headline="Tanker master reports blast 93 km west of Dubai",
         detail="No injuries, no damage: UKMTO. Unknown projectile.",
         scene="tanker", phase=0,
         tones=("sky_pale", "water_deep", "mid_steel", "flame")),
    dict(role="grid", region="GULF", field="AIR STRIKES",
         headline="Houthi shelling of Taiz kills a woman, wounds seven",
         detail="The city was shelled on 26 November, Al Jazeera reports.",
         scene="checkpoint", phase=0,
         tones=("sky_sand", "ground_brown", "mid_stone", "accent_red")),
    dict(role="grid", region="EUROPE", field="AIR WARFARE",
         headline="Ukraine hits Savasleyka, damaging five jets",
         detail="Three MiG-31s and two Su-34s at the Nizhny Novgorod base.",
         scene="helicopter", phase=0,
         tones=("sky_grey", "ground_dark", "mid_steel", "accent_green")),
    dict(role="grid", region="EUROPE", field="REFINING",
         headline="Drone strikes cut Russian refining by 45 per cent",
         detail="Processing volumes have fallen since late October.",
         scene="refinery", phase=0,
         tones=("sky_dusk", "ground_dark", "mid_steel", "flame")),
    dict(role="grid", region="EUROPE", field="BUDGET",
         headline="EU leaders open budget summit in Brussels",
         detail="2028-34 budget, a \u20ac45bn loan plan, ECB leadership.",
         scene="parliament", phase=0,
         tones=("sky_grey", "ground_dark", "mid_stone", "accent_blue")),
    dict(role="grid", region="EUROPE", field="REFINING",
         headline="Serbia warns its only refinery may halt in days",
         detail="Vucic says NIS needs US Treasury sanctions relief.",
         scene="refinery", phase=1,
         tones=("sky_sand", "ground_clay", "mid_grey", "flame_deep")),
    dict(role="grid", region="LEVANT", field="AIR STRIKES",
         headline="Israeli strike on a Gaza apartment kills two",
         detail="Central Gaza, 26 November, per Al Jazeera.",
         scene="apartment", phase=0,
         tones=("sky_sand", "ground_brown", "mid_stone", "accent_red")),
    dict(role="grid", region="LEVANT", field="HUMANITARIAN AID",
         headline="Rain floods 70,000 tents; six water plants shut",
         detail="Oxfam report; a US senator demands a halt to military aid.",
         scene="weather", phase=0,
         tones=("sky_grey", "ground_olive", "mid_sage", "accent_blue")),
    dict(role="grid", region="LEVANT", field="INSURGENCY",
         headline="ISIL kills two Syrian security men in Hasakah",
         detail="Five wounded; all four assailants died, two by suicide blast.",
         scene="checkpoint", phase=1,
         tones=("sky_dusk", "ground_dark", "mid_grey", "accent_red")),
    dict(role="grid", region="LEVANT", field="MARITIME LAW",
         headline="Lebanon and Cyprus sign sea boundary deal",
         detail="Ends two decades of deadlock; exploration is unblocked.",
         scene="map", phase=0,
         tones=("sky_pale", "water_dark", "mid_sage", "accent_gold")),
    dict(role="grid", region="NORTH AFRICA", field="ROAD SAFETY",
         headline="Fuel tanker explodes on Cairo ring road, 31 dead",
         detail="15 taken to hospital, four critical, 39 ambulances sent.",
         scene="tanker", phase=1,
         tones=("sky_hot", "ground_dark", "mid_grey", "flame")),
    dict(role="grid", region="WEST AFRICA", field="MILITANCY",
         headline="JNIM hands Tonka in Mali an ultimatum",
         detail="The al-Qaeda-linked group, per France 24.",
         scene="map", phase=1,
         tones=("sky_sand", "ground_olive", "mid_sage", "accent_red")),
    dict(role="grid", region="CENTRAL AFRICA", field="VACCINES",
         headline="Ebola vaccine trials begin in Bunia, Ituri",
         detail="ChAdOx1 and mRNA-1469, phase 2, 26-27 November.",
         scene="hospital", phase=0,
         tones=("sky_pale", "ground_olive", "mid_sage", "accent_green")),
    dict(role="grid", region="EAST ASIA", field="NUCLEAR POLICY",
         headline="Kim orders wider tactical nuclear deployment",
         detail="South Korea estimates 80-120 warheads.",
         scene="map", phase=2,
         tones=("sky_grey", "water_grey", "mid_steel", "accent_red")),
    dict(role="grid", region="EAST ASIA", field="HOUSING",
         headline="Hong Kong marks fire anniversary: 168 dead",
         detail="Wang Fuk Court, the city's deadliest; two firms charged.",
         scene="apartment", phase=1,
         tones=("sky_dusk", "ground_dark", "mid_grey", "flame_deep")),
    dict(role="grid", region="AMERICAS", field="COASTAL FLOODING",
         headline="King tide sets records; Pacifica pier collapses",
         detail="Charleston, Oregon: 1.12 m above mean high water, a record.",
         scene="weather", phase=1,
         tones=("sky_pale", "water_dark", "mid_steel", "accent_blue")),
    dict(role="grid", region="AMERICAS", field="PUBLIC EVENTS",
         headline="Storms postpone Macy's parade to 28 November",
         detail="First postponement in 100 editions; gusts to 97 km/h.",
         scene="weather", phase=2,
         tones=("sky_grey", "ground_clay", "mid_stone", "accent_red")),
    dict(role="grid", region="AMERICAS", field="EQUITIES",
         headline="Nvidia closes at $149.30, down 3.9 per cent",
         detail="$2.3tn below its October peak of $243.37.",
         scene="market", phase=0,
         tones=("sky_pale", "ground_dark", "mid_steel", "accent_green")),
    dict(role="grid", region="AMERICAS", field="BROADCAST LAW",
         headline="Judge bars FCC move on Disney's eight ABC stations",
         detail="A federal judge ruled on 26 November, per Reuters.",
         scene="courtroom", phase=0,
         tones=("sky_sand", "ground_brown", "mid_stone", "accent_blue")),
    dict(role="grid", region="EUROPE", field="FOOTBALL",
         headline="Europa League matchday five: Benfica top on 12",
         detail="Eighteen fixtures; the 36-team table, per UEFA.",
         scene="stadium", phase=0,
         tones=("sky_dusk", "ground_olive", "mid_sage", "accent_gold")),
    # ---- nineteen more in the also-today columns ------------------------
    dict(role="list", region="EUROPE", field="WAR DATA",
         headline="Peskov shrugs off report of 470,000-700,000 war dead",
         detail="Hacked Rosstat data; Dawn, 26 Nov"),
    dict(role="list", region="EUROPE", field="DIPLOMACY",
         headline="Lukashenko offers Minsk as a venue for peace talks",
         detail="BELTA; a Witkoff-led US team to visit Moscow"),
    dict(role="list", region="EUROPE", field="DIPLOMACY",
         headline="Russian and Ukrainian envoys met in Abu Dhabi",
         detail="Ushakov: US officials met the Russian side"),
    dict(role="list", region="EUROPE", field="DEFENCE PACT",
         headline="Macron: France and Britain to coordinate guarantees",
         detail="A workshop for Ukraine, with US involvement"),
    dict(role="list", region="LEVANT", field="AID FINANCE",
         headline="Germany pledges \u20ac149.65m ($173.19m) to Lebanon",
         detail="For education, water and social protection"),
    dict(role="list", region="NORTH AFRICA", field="CEASEFIRE",
         headline="Egypt, Qatar and T\u00fcrkiye meet in Cairo on Gaza",
         detail="Israel says six died at a Rafah tunnel shaft"),
    dict(role="list", region="WEST AFRICA", field="KIDNAPPING",
         headline="Saudi citizen kidnapped in Niger by gunmen",
         detail="Suspected IS Sahel branch, Reuters reports"),
    dict(role="list", region="CENTRAL AFRICA", field="COUNTER-INSURGENCY",
         headline="Ituri fighting resumes, hampering Ebola response",
         detail="Army against CRP rebels in DR Congo"),
    dict(role="list", region="SOUTHERN AFRICA", field="CIVIL LIBERTIES",
         headline="Zambia bans march against term-limit change",
         detail="Hichilema could stay past 2031"),
    dict(role="list", region="EAST ASIA", field="INTEREST RATES",
         headline="BOJ's Tamura: respond swiftly, accelerate hikes",
         detail="Japan's policy rate stands at 1.25%"),
    dict(role="list", region="EAST ASIA", field="INTEREST RATES",
         headline="Bank of Korea lifts base rate 25 bp to 3.25%",
         detail="Third 2026 hike; October CPI 2.8%"),
    dict(role="list", region="EAST ASIA", field="EQUITIES",
         headline="Asian shares rally: Nikkei +1.6%, KOSPI +1.9%",
         detail="Japan -8% and Korea -16% in November"),
    dict(role="list", region="SOUTH ASIA", field="TRADE BLOC",
         headline="Sri Lanka advances application to join RCEP",
         detail="Cabinet approves the initial questionnaire"),
    dict(role="list", region="SOUTH ASIA", field="CURRENCY",
         headline="Rupee seen opening 92.32-92.36 to the dollar",
         detail="Wednesday closed 92.23 on the oil move"),
    dict(role="list", region="SOUTHEAST ASIA", field="MARITIME LAW",
         headline="Mekong patrol number 159 begins against border crime",
         detail="China, Laos, Myanmar and Thailand take part"),
    dict(role="list", region="SOUTHEAST ASIA", field="AIR QUALITY",
         headline="Thailand passes Clean Air Bill unanimously, 431-0",
         detail="Fines to 50m baht; SET -1.59% to 1,428.50"),
    dict(role="list", region="PACIFIC", field="PARTY POLITICS",
         headline="Leah Blyth defects to One Nation on the final day",
         detail="First South Australian senator for the party"),
    dict(role="list", region="PACIFIC", field="MILITARY APOLOGY",
         headline="Australia apologises to ADF members discharged",
         detail="Delivered in parliament by Richard Marles"),
    dict(role="list", region="AMERICAS", field="TARIFFS",
         headline="White House proposes 20-40% tariffs on 14 partners",
         detail="China steepest: 20% on top of first-term duties"),
]

# every grid cell names its scene kind and its tones in the table above
SCENES = [s for s in STORIES if s["role"] == "grid"]

# --------------------------------------------------------------------------
# text plumbing: every string drawn is registered with its ink bbox so that
# collisions can be counted and printed
# --------------------------------------------------------------------------
TEXT_BOXES = []   # (label, bbox, size)
SIZES_USED = set()
_font_cache = {}


def font(path, size):
    key = (path, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(path, size)
    return _font_cache[key]


def text(d, xy, s, path, size, fill=INK, anchor="la", label=None):
    f = font(path, size)
    box = d.textbbox(xy, s, font=f, anchor=anchor)
    d.text(xy, s, font=f, fill=fill, anchor=anchor)
    TEXT_BOXES.append((label if label else s, box, size))
    SIZES_USED.add(size)
    return box


def wrap(s, path, size, width, max_lines):
    f = font(path, size)
    words = s.split()
    lines, cur, i = [], "", 0
    while i < len(words) and len(lines) < max_lines:
        cand = (cur + " " + words[i]).strip()
        if f.getlength(cand) <= width:
            cur = cand
            i += 1
        elif cur:
            lines.append(cur)
            cur = ""
        else:
            cur = words[i]
            i += 1
    if cur:
        lines.append(cur)
    if i < len(words) and lines:
        last = lines[-1]
        while last and f.getlength(last + "\u2026") > width:
            last = last[:-1]
        lines[-1] = last.rstrip(" ,.;:") + "\u2026"
    return lines


# --------------------------------------------------------------------------
# drawing primitives
# --------------------------------------------------------------------------
def _r(d, x, y, w, h, c):
    d.rectangle([x, y, x + w - 1, y + h - 1], fill=c)


def _p(d, pts, c):
    d.polygon(pts, fill=c)


def _e(d, x, y, w, h, c):
    d.ellipse([x, y, x + w - 1, y + h - 1], fill=c)


def _l(d, pts, c, width=2):
    d.line(pts, fill=c, width=width)


def _tone(name):
    return P[name]


# --------------------------------------------------------------------------
# one drawing function per kind of scene (88 x 54 cells)
# --------------------------------------------------------------------------
def scene_tanker(d, x, y, t, phase):
    """Crude carrier.  phase 0: at sea, holed and burning.  phase 1: road tanker."""
    sky, water, mid, flame = (_tone(v) for v in t)
    ground = water
    if phase == 0:
        _r(d, x, y, 88, 20, sky)
        _r(d, x, y + 20, 88, 34, water)
        _p(d, [(x + 8, y + 33), (x + 62, y + 33), (x + 56, y + 44), (x + 14, y + 44)], mid)
        _r(d, x + 40, y + 24, 11, 10, mid)
        _r(d, x + 43, y + 18, 3, 7, flame)
        _p(d, [(x + 20, y + 32), (x + 27, y + 18), (x + 34, y + 32)], flame)
        _e(d, x + 24, y + 8, 14, 9, mid)
        _e(d, x + 30, y + 3, 15, 8, mid)
        _p(d, [(x + 66, y + 29), (x + 86, y + 29), (x + 84, y + 34), (x + 68, y + 34)], mid)
        _e(d, x + 4, y + 4, 9, 9, flame)
        _l(d, [(x + 6, y + 47), (x + 18, y + 47)], sky, 1)
        _l(d, [(x + 40, y + 48), (x + 54, y + 48)], sky, 1)
    else:
        _r(d, x, y, 88, 16, sky)
        _r(d, x, y + 16, 88, 38, P["light_warm"])     # pale asphalt
        for i in range(4):
            _r(d, x + 4 + i * 22, y + 46, 12, 2, mid)
        _e(d, x + 8, y + 22, 42, 22, ground)          # overturned barrel
        _r(d, x + 12, y + 30, 34, 8, ground)
        _r(d, x + 46, y + 26, 12, 12, mid)            # cab
        _e(d, x + 47, y + 38, 6, 6, ground)
        _p(d, [(x + 26, y + 22), (x + 34, y + 4), (x + 42, y + 22)], flame)
        _e(d, x + 28, y - 4, 14, 8, mid)
        _r(d, x + 64, y + 30, 18, 12, sky)            # ambulance
        _r(d, x + 71, y + 32, 3, 8, flame)
        _r(d, x + 68, y + 34, 9, 3, flame)
        _e(d, x + 62, y + 40, 5, 5, ground)
        _e(d, x + 80, y + 40, 5, 5, ground)


def scene_apartment(d, x, y, t, phase):
    """Flats.  phase 0: block hit, corner gone.  phase 1: tower on fire."""
    sky, ground, mid, flame = (_tone(v) for v in t)
    if phase == 0:
        _r(d, x, y, 88, 54, sky)
        _r(d, x, y + 44, 88, 10, ground)
        _r(d, x + 12, y + 8, 44, 38, mid)
        for row in range(4):
            for col in range(3):
                _r(d, x + 16 + col * 13, y + 12 + row * 9, 7, 5, sky)
        _p(d, [(x + 56, y + 8), (x + 78, y + 22), (x + 62, y + 46), (x + 56, y + 46)], ground)
        _e(d, x + 46, y + 2, 18, 10, mid)
        _e(d, x + 52, y - 4, 16, 9, mid)
        _p(d, [(x + 66, y + 26), (x + 74, y + 14), (x + 80, y + 30)], flame)
        _r(d, x + 4, y + 40, 6, 8, mid)
        _e(d, x + 3, y + 34, 8, 8, mid)
        _l(d, [(x + 2, y + 49), (x + 86, y + 49)], sky, 1)
    else:
        _r(d, x, y, 88, 54, sky)
        _r(d, x, y + 46, 88, 8, ground)
        _r(d, x + 6, y + 6, 30, 42, mid)
        for row in range(5):
            for col in range(2):
                _r(d, x + 11 + col * 13, y + 10 + row * 8, 8, 5, sky)
        _p(d, [(x + 30, y + 6), (x + 40, y + 2), (x + 44, y + 20), (x + 34, y + 26)], flame)
        _e(d, x + 36, y - 6, 16, 9, mid)
        _r(d, x + 52, y + 22, 26, 26, ground)
        _r(d, x + 56, y + 26, 8, 8, sky)
        _r(d, x + 68, y + 26, 6, 8, sky)
        _l(d, [(x + 50, y + 4), (x + 62, y + 48)], mid, 2)   # ladder
        _e(d, x + 78, y + 40, 7, 7, mid)
        _r(d, x + 77, y + 47, 9, 3, ground)


def scene_refinery(d, x, y, t, phase):
    """Distillation towers.  phase 0: flare right.  phase 1: tanks right."""
    sky, ground, mid, flame = (_tone(v) for v in t)
    if phase == 0:
        _r(d, x, y, 88, 54, sky)
        _r(d, x, y + 40, 88, 14, ground)
        for i, (bx, bh, bw) in enumerate([(10, 26, 9), (24, 34, 10), (38, 22, 8)]):
            _r(d, x + bx, y + 40 - bh, bw, bh, mid)
            _r(d, x + bx - 1, y + 40 - bh - 3, bw + 2, 3, ground)
        _l(d, [(x + 4, y + 34), (x + 52, y + 34)], mid, 2)
        _r(d, x + 58, y + 14, 4, 26, mid)
        _p(d, [(x + 58, y + 14), (x + 62, y + 2), (x + 66, y + 14)], flame)
        _e(d, x + 60, y - 4, 12, 7, mid)
        _r(d, x + 70, y + 30, 14, 10, ground)
        _e(d, x + 70, y + 26, 14, 8, mid)
        _l(d, [(x + 2, y + 45), (x + 86, y + 45)], sky, 1)
    else:
        _r(d, x, y, 88, 54, sky)
        _r(d, x, y + 44, 88, 10, ground)
        _e(d, x + 52, y + 28, 20, 16, mid)
        _e(d, x + 70, y + 30, 14, 14, mid)
        _r(d, x + 8, y + 12, 7, 32, mid)
        _r(d, x + 20, y + 20, 6, 24, mid)
        _p(d, [(x + 30, y + 30), (x + 37, y + 8), (x + 44, y + 30)], flame)
        _e(d, x + 33, y - 2, 12, 8, mid)
        _l(d, [(x + 2, y + 38), (x + 50, y + 38)], ground, 3)
        _l(d, [(x + 2, y + 42), (x + 46, y + 42)], mid, 1)
        _r(d, x + 76, y + 40, 8, 4, ground)


def scene_parliament(d, x, y, t, phase):
    """Hemicycle.  phase 0: EU chamber, flag right."""
    sky, ground, mid, accent = (_tone(v) for v in t)
    if phase == 0:
        _r(d, x, y, 88, 54, sky)
        _r(d, x, y + 46, 88, 8, ground)
        d.pieslice([x + 8, y + 12, x + 80, y + 66], 180, 360, fill=mid)
        _r(d, x + 6, y + 39, 76, 7, ground)
        for i in range(5):
            _e(d, x + 14 + i * 14, y + 30, 7, 7, sky)
        _r(d, x + 38, y + 20, 12, 14, accent)
        _e(d, x + 40, y + 14, 8, 8, ground)
        _r(d, x + 76, y + 4, 2, 22, ground)
        _r(d, x + 78, y + 4, 9, 7, accent)
        _l(d, [(x + 2, y + 50), (x + 86, y + 50)], sky, 1)
    else:
        _r(d, x, y, 88, 54, sky)
        _r(d, x, y + 48, 88, 6, ground)
        _r(d, x + 4, y + 10, 80, 6, ground)
        for i in range(4):
            _r(d, x + 8, y + 20 + i * 7, 72, 4, mid)
        _r(d, x + 30, y + 34, 28, 12, accent)
        _e(d, x + 40, y + 26, 8, 8, ground)
        _e(d, x + 52, y + 28, 7, 7, mid)
        _l(d, [(x + 14, y + 48), (x + 14, y + 30)], mid, 2)
        _l(d, [(x + 74, y + 48), (x + 74, y + 30)], mid, 2)


def scene_checkpoint(d, x, y, t, phase):
    """Roadblock.  phase 0: barrier and sentry.  phase 1: burnt car, rubble."""
    sky, ground, mid, accent = (_tone(v) for v in t)
    if phase == 0:
        _r(d, x, y, 88, 54, sky)
        _r(d, x, y + 34, 88, 20, P["light_warm"])      # pale road
        _r(d, x + 4, y + 12, 22, 20, mid)              # hut
        _r(d, x + 8, y + 16, 14, 8, sky)
        _l(d, [(x + 26, y + 26), (x + 76, y + 36)], accent, 4)
        _l(d, [(x + 26, y + 36), (x + 76, y + 26)], accent, 4)
        _e(d, x + 58, y + 14, 8, 8, mid)               # sentry
        _r(d, x + 57, y + 22, 10, 14, mid)
        _r(d, x + 54, y + 36, 16, 3, ground)
        for i in range(3):
            _e(d, x + 34 + i * 9, y + 32, 10, 7, ground)
        _r(d, x + 2, y + 44, 24, 2, ground)
        _r(d, x + 40, y + 48, 30, 2, ground)
    else:
        _r(d, x, y, 88, 54, sky)
        _r(d, x, y + 30, 88, 24, P["light_warm"])
        _e(d, x + 8, y + 20, 32, 16, mid)              # burnt car
        _r(d, x + 12, y + 26, 24, 8, mid)
        _e(d, x + 12, y + 32, 7, 7, ground)
        _e(d, x + 28, y + 32, 7, 7, ground)
        _p(d, [(x + 40, y + 34), (x + 52, y + 12), (x + 66, y + 34)], ground)
        _p(d, [(x + 58, y + 34), (x + 68, y + 18), (x + 82, y + 34)], mid)
        _e(d, x + 44, y + 4, 12, 8, mid)
        _r(d, x + 74, y + 8, 12, 22, mid)
        _r(d, x + 78, y + 4, 5, 5, accent)
        _r(d, x + 2, y + 44, 20, 2, ground)


def scene_helicopter(d, x, y, t, phase):
    """Airbase.  phase 0: helicopter over hangar and runway."""
    sky, ground, mid, accent = (_tone(v) for v in t)
    _r(d, x, y, 88, 54, sky)
    _r(d, x, y + 38, 88, 16, ground)
    d.pieslice([x + 6, y + 18, x + 54, y + 62], 180, 360, fill=mid)
    _r(d, x + 6, y + 38, 48, 6, mid)
    _r(d, x + 18, y + 32, 16, 8, ground)
    _e(d, x + 46, y + 18, 26, 11, mid)          # fuselage
    _r(d, x + 68, y + 20, 16, 3, mid)           # tail boom
    _p(d, [(x + 82, y + 15), (x + 86, y + 21), (x + 82, y + 27)], mid)
    _l(d, [(x + 42, y + 12), (x + 78, y + 12)], accent, 2)   # rotor
    _l(d, [(x + 59, y + 12), (x + 59, y + 18)], accent, 2)
    _r(d, x + 48, y + 27, 4, 5, ground)
    _r(d, x + 64, y + 27, 4, 5, ground)
    _r(d, x + 2, y + 44, 24, 2, sky)
    _r(d, x + 40, y + 46, 30, 2, sky)
    _r(d, x + 10, y + 50, 18, 2, sky)


def scene_market(d, x, y, t, phase):
    """Trading screen: candlesticks and a falling line."""
    sky, ground, mid, accent = (_tone(v) for v in t)
    _r(d, x, y, 88, 54, sky)
    _r(d, x + 4, y + 4, 80, 36, ground)
    _r(d, x + 8, y + 8, 72, 28, sky)
    bars = [(14, 16, 22), (24, 12, 26), (34, 18, 20), (44, 22, 26), (54, 26, 30), (64, 20, 24)]
    for i, (bx, top, bot) in enumerate(bars):
        _r(d, x + bx, y + top, 5, bot - top, accent if i % 2 == 0 else mid)
        _l(d, [(x + bx + 2, y + top - 3), (x + bx + 2, y + bot + 3)], mid, 1)
    _l(d, [(x + 12, y + 16), (x + 28, y + 20), (x + 44, y + 24), (x + 60, y + 30), (x + 76, y + 33)], ground, 2)
    _r(d, x + 4, y + 42, 80, 8, ground)
    for i in range(6):
        _r(d, x + 8 + i * 12, y + 45, 6, 2, sky)


def scene_courtroom(d, x, y, t, phase):
    """Judge, bench, gavel, two counsel."""
    sky, ground, mid, accent = (_tone(v) for v in t)
    _r(d, x, y, 88, 54, sky)
    _r(d, x, y + 50, 88, 4, ground)
    _r(d, x + 6, y + 26, 76, 16, mid)            # bench
    _r(d, x + 6, y + 24, 76, 3, ground)
    _e(d, x + 38, y + 12, 12, 12, ground)        # judge head
    _p(d, [(x + 34, y + 26), (x + 54, y + 26), (x + 50, y + 20), (x + 38, y + 20)], accent)
    _l(d, [(x + 60, y + 10), (x + 66, y + 16)], ground, 3)   # gavel
    _r(d, x + 64, y + 6, 8, 5, ground)
    _e(d, x + 14, y + 28, 9, 9, mid)             # counsel left
    _r(d, x + 12, y + 37, 12, 9, accent)
    _e(d, x + 68, y + 28, 9, 9, mid)             # counsel right
    _r(d, x + 66, y + 37, 12, 9, accent)
    _r(d, x + 82, y + 4, 2, 22, ground)          # flag
    _r(d, x + 84, y + 4, 4, 8, accent)
    _l(d, [(x + 2, y + 46), (x + 86, y + 46)], ground, 1)


def scene_stadium(d, x, y, t, phase):
    """Floodlit pitch, two players, goal."""
    sky, ground, mid, accent = (_tone(v) for v in t)
    _r(d, x, y, 88, 54, sky)
    _r(d, x, y + 8, 88, 8, ground)               # stand
    for i in range(9):
        _e(d, x + 4 + i * 10, y + 10, 6, 5, mid)
    _r(d, x, y + 16, 88, 30, P["light_warm"])    # pale pitch
    _r(d, x + 6, y + 20, 76, 22, mid)
    _r(d, x + 6, y + 29, 3, 4, P["light_warm"])
    _r(d, x + 79, y + 29, 3, 4, P["light_warm"])
    _e(d, x + 42, y + 26, 12, 12, P["light_warm"])
    _l(d, [(x + 48, y + 20), (x + 48, y + 44)], P["light_warm"], 1)
    _e(d, x + 22, y + 28, 6, 6, accent)
    _r(d, x + 21, y + 34, 8, 7, accent)
    _e(d, x + 62, y + 30, 6, 6, accent)
    _r(d, x + 61, y + 36, 8, 6, accent)
    _r(d, x + 8, y + 2, 10, 3, ground)
    _e(d, x + 74, y + 1, 6, 5, accent)
    _l(d, [(x + 2, y + 48), (x + 86, y + 48)], ground, 1)


def scene_hospital(d, x, y, t, phase):
    """Field hospital: ward block, cross, ambulance, bed."""
    sky, ground, mid, accent = (_tone(v) for v in t)
    _r(d, x, y, 88, 54, sky)
    _r(d, x, y + 42, 88, 12, ground)
    _r(d, x + 4, y + 12, 40, 30, mid)
    _r(d, x + 16, y + 4, 16, 8, mid)
    _r(d, x + 20, y + 18, 8, 18, accent)          # cross
    _r(d, x + 14, y + 22, 20, 8, accent)
    _r(d, x + 6, y + 32, 10, 10, sky)
    _r(d, x + 50, y + 24, 28, 18, sky)            # ambulance
    _r(d, x + 60, y + 30, 3, 8, accent)
    _r(d, x + 57, y + 33, 9, 3, accent)
    _e(d, x + 52, y + 38, 6, 6, ground)
    _e(d, x + 70, y + 38, 6, 6, ground)
    _p(d, [(x + 44, y + 20), (x + 50, y + 12), (x + 56, y + 20)], mid)  # tent
    _e(d, x + 76, y + 8, 7, 7, mid)
    _r(d, x + 74, y + 15, 10, 3, mid)


def scene_weather(d, x, y, t, phase):
    """phase 0: rain on tents.  phase 1: storm surge at a pier.  phase 2: wind."""
    sky, ground, mid, accent = (_tone(v) for v in t)
    if phase == 0:
        _r(d, x, y, 88, 54, sky)
        _r(d, x, y + 48, 88, 6, ground)
        for i in range(9):
            _l(d, [(x + 2 + i * 10, y + 2), (x + 6 + i * 10, y + 16)], mid, 1)
        for i in range(3):
            _p(d, [(x + 6 + i * 26, y + 46), (x + 18 + i * 26, y + 24), (x + 30 + i * 26, y + 46)], accent)
            _r(d, x + 16 + i * 26, y + 40, 4, 6, ground)
        _r(d, x + 2, y + 50, 26, 2, ground)
        _r(d, x + 60, y + 50, 24, 2, ground)
    elif phase == 1:
        _r(d, x, y, 88, 54, sky)
        _r(d, x, y + 20, 88, 34, P["light_cool"])   # pale, wind-whipped sea
        for i in range(3):
            _p(d, [(x + 2 + i * 30, y + 34), (x + 18 + i * 30, y + 22),
                   (x + 32 + i * 30, y + 34), (x + 16 + i * 30, y + 40)], ground)
        _r(d, x + 48, y + 34, 38, 4, mid)            # pier deck
        _r(d, x + 52, y + 38, 3, 12, mid)
        _r(d, x + 64, y + 38, 3, 12, mid)
        _r(d, x + 78, y + 38, 3, 12, mid)
        _p(d, [(x + 70, y + 34), (x + 86, y + 46), (x + 70, y + 46)], mid)
        _r(d, x, y + 50, 88, 4, ground)
        _e(d, x + 6, y + 3, 11, 11, accent)
    else:
        _r(d, x, y, 88, 54, sky)
        _r(d, x, y + 40, 88, 14, ground)
        _r(d, x + 2, y + 22, 30, 18, mid)         # buildings
        _r(d, x + 8, y + 16, 18, 8, mid)
        _e(d, x + 44, y + 6, 16, 18, accent)      # balloon
        _l(d, [(x + 52, y + 24), (x + 46, y + 36)], ground, 1)
        _e(d, x + 66, y + 10, 12, 14, mid)
        _l(d, [(x + 72, y + 24), (x + 70, y + 34)], ground, 1)
        for i in range(3):
            _l(d, [(x + 40 + i * 12, y + 30), (x + 34 + i * 12, y + 40)], sky, 2)
        _r(d, x + 4, y + 44, 20, 2, sky)


def scene_map(d, x, y, t, phase):
    """phase 0: sea boundary.  phase 1: land with strike marks.  phase 2: peninsula."""
    sea, land, mid, accent = (_tone(v) for v in t)
    if phase == 0:
        _r(d, x, y, 88, 54, sea)
        _p(d, [(x, y), (x + 26, y), (x + 18, y + 20), (x + 24, y + 40), (x + 12, y + 54), (x, y + 54)], land)
        _p(d, [(x + 88, y), (x + 62, y), (x + 70, y + 22), (x + 64, y + 42), (x + 74, y + 54), (x + 88, y + 54)], land)
        for i in range(6):
            _r(d, x + 43, y + 4 + i * 8, 2, 4, accent)
        _e(d, x + 20, y + 12, 4, 4, accent)
        _e(d, x + 66, y + 32, 4, 4, accent)
    elif phase == 1:
        _r(d, x, y, 88, 54, sea)
        _p(d, [(x + 8, y + 10), (x + 44, y + 2), (x + 74, y + 14), (x + 66, y + 44), (x + 30, y + 50), (x + 6, y + 32)], land)
        for i, (dx, dy) in enumerate([(24, 18), (40, 12), (52, 24), (34, 34)]):
            _e(d, x + dx, y + dy, 7, 7, accent)
            _e(d, x + dx + 2, y + dy + 2, 3, 3, land)
        _l(d, [(x + 4, y + 46), (x + 20, y + 40)], mid, 2)
        _r(d, x + 70, y + 40, 12, 2, mid)
    else:
        _r(d, x, y, 88, 54, sea)
        _p(d, [(x + 30, y + 2), (x + 56, y + 6), (x + 60, y + 26), (x + 50, y + 46), (x + 34, y + 48), (x + 26, y + 24)], land)
        _l(d, [(x + 28, y + 18), (x + 62, y + 18)], accent, 2)
        _e(d, x + 38, y + 28, 6, 6, accent)
        _e(d, x + 48, y + 34, 5, 5, accent)
        _r(d, x + 4, y + 44, 16, 3, mid)
        _r(d, x + 70, y + 8, 14, 3, mid)


SCENE_FUNCS = {
    "tanker": scene_tanker,
    "apartment": scene_apartment,
    "refinery": scene_refinery,
    "parliament": scene_parliament,
    "checkpoint": scene_checkpoint,
    "helicopter": scene_helicopter,
    "market": scene_market,
    "courtroom": scene_courtroom,
    "stadium": scene_stadium,
    "hospital": scene_hospital,
    "weather": scene_weather,
    "map": scene_map,
}


def draw_scene(d, kind, x, y, w, h, tones, phase=0):
    """Dispatch to the kind's function; the functions are written for 88x54."""
    if (w, h) != (88, 54):
        raise ValueError("cell scenes are 88x54, got %dx%d" % (w, h))
    SCENE_FUNCS[kind](d, x, y, tones, phase)


# --------------------------------------------------------------------------
# the lead scene: the Gulf, 439 x 240 (the 46 per cent column)
# --------------------------------------------------------------------------
def draw_lead_scene(d, x, y, w, h):
    """The Gulf: two tankers, a flame and smoke column, a missile trail, a
    shoreline and a sun.  Four tones, flat shapes, nothing outline-only."""
    sky = P["sky_hot"]
    sea = "#4a6f80"
    sand = P["mid_stone"]
    flame = P["flame"]
    hull = P["ground_dark"]
    smoke = P["mid_grey"]
    horizon = y + int(h * 0.45)

    _r(d, x, y, w, horizon - y, sky)
    _r(d, x, horizon, w, y + h - horizon, sea)
    _e(d, x + 26, y + 18, 44, 44, flame)                  # sun
    # far shoreline: a low strip on the right, not a wall
    _p(d, [(x + 286, horizon), (x + 350, horizon - 20), (x + w, horizon - 26),
           (x + w, horizon), (x + 286, horizon)], sand)
    _r(d, x + 330, horizon - 34, 10, 14, hull)            # terminal stack
    _p(d, [(x + 330, horizon - 34), (x + 340, horizon - 52), (x + 348, horizon - 34)], flame)

    def tanker(bx, by, s, tone):
        _p(d, [(bx, by), (bx + int(150 * s), by), (bx + int(138 * s), by + int(26 * s)),
               (bx + int(12 * s), by + int(26 * s))], tone)
        _r(d, bx + int(96 * s), by - int(22 * s), int(28 * s), int(22 * s), tone)
        _r(d, bx + int(104 * s), by - int(36 * s), int(7 * s), int(15 * s), flame)
        _r(d, bx + int(18 * s), by - int(5 * s), int(62 * s), int(5 * s), P["ground_dark"])

    tanker(x + 34, horizon + 40, 0.9, hull)
    tanker(x + 232, horizon + 86, 1.15, P["mid_plum"])
    # flame and smoke column over the near tanker
    _p(d, [(x + 96, horizon + 38), (x + 112, horizon - 34), (x + 128, horizon + 38)], flame)
    _e(d, x + 100, horizon - 74, 46, 34, smoke)
    _e(d, x + 112, horizon - 110, 52, 38, smoke)
    _e(d, x + 100, horizon - 142, 46, 34, smoke)
    # missile track, arcing in from the left
    pts = [(x + 6, y + h - 22), (x + 62, y + 104), (x + 138, y + 58), (x + 206, y + 40)]
    for i in range(len(pts) - 1):
        _l(d, [pts[i], pts[i + 1]], P["light_warm"], 2)
    _p(d, [(x + 206, y + 40), (x + 222, y + 32), (x + 210, y + 52)], flame)
    # wave marks
    for i in range(8):
        wx = x + 10 + i * 56
        wy = horizon + 22 + (i % 3) * 18
        _l(d, [(wx, wy), (wx + 30, wy)], P["light_cool"], 2)
    d.rectangle([x, y, x + w - 1, y + h - 1], outline=INK, width=2)


# --------------------------------------------------------------------------
# page
# --------------------------------------------------------------------------
def build():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    lead = STORIES[0]
    cells = [s for s in STORIES if s["role"] == "grid"]
    listed = [s for s in STORIES if s["role"] == "list"]

    # ---- 1. masthead ----------------------------------------------------
    text(d, (MARGIN, 14), "THE WORLD TODAY", F_SERIF_B, 44, INK)
    n_stories = len(STORIES)
    n_regions = len({s["region"] for s in STORIES})
    n_fields = len({s["field"] for s in STORIES})
    text(d, (W - MARGIN, 22), "THURSDAY 26 NOVEMBER 2026", F_SANS_B, 14, INK, anchor="ra")
    text(d, (W - MARGIN, 42), "%d STORIES \u00b7 %d REGIONS \u00b7 %d FIELDS" % (n_stories, n_regions, n_fields),
         F_SANS_B, 14, INK, anchor="ra")
    text(d, (MARGIN, 64),
         "LATE EDITION \u00b7 COMPILED 04:30 UTC, 26 NOVEMBER 2026 \u00b7 REUTERS, AL JAZEERA, AP, "
         "ABC, FRANCE 24, NHAN DAN, EUOBSERVER, S&P GLOBAL, UEFA, DAWN",
         F_SANS, 9.5, "#5b544a")
    _r(d, 0, MAST_H - 3, W, 3, INK)

    # ---- 2. ticker ------------------------------------------------------
    _r(d, 0, TICKER_Y, W, TICKER_H, INK)
    ticker = "  \u00b7  ".join([
        "MISSILES INTERCEPTED OVER RIYADH",
        "TANKER BLAST 93 KM WEST OF DUBAI",
        "CAIRO RING ROAD TANKER FIRE KILLS 31",
    ])
    text(d, (MARGIN, TICKER_Y + 10), ticker, F_SANS_B, 12.5, PAPER)

    # ---- 3. lead --------------------------------------------------------
    left_w = int(COL_W * 0.54)
    text(d, (MARGIN, LEAD_Y), "MIDDLE EAST", F_SANS_B, 10.5, REGION_INK["GULF"])
    y = LEAD_Y + 16
    for line in wrap(lead["headline"], F_SERIF_B, 27, left_w - 8, 3):
        text(d, (MARGIN, y), line, F_SERIF_B, 27, INK)
        y += 30
    y += 2
    for line in wrap(lead["subhead"], F_SANS, 14, left_w - 8, 2):
        text(d, (MARGIN, y), line, F_SANS, 14, INK)
        y += 16
    y += 6
    dt = text(d, (MARGIN, y), lead["dateline"], F_SANS_B, 10.5, "#5b544a")

    # a small numbers panel fills the foot of the lead column with hard figures
    px0, py0, pw, ph = MARGIN, dt[3] + 8, left_w - 14, 74
    _r(d, px0, py0, pw, ph, "#e7dfc9")
    d.rectangle([px0, py0, px0 + pw - 1, py0 + ph - 1], outline=INK, width=1)
    text(d, (px0 + 8, py0 + 5), "OIL, THE RUPEE AND THE REFINERY", F_SANS_B, 9, "#5b544a")
    text(d, (px0 + 8, py0 + 17), "$94.81", F_SERIF_B, 22, INK)
    text(d, (px0 + 8, py0 + 44), "BRENT, +0.2%", F_SANS_B, 10, INK)
    text(d, (px0 + 118, py0 + 17), "$84.24", F_SERIF_B, 22, INK)
    text(d, (px0 + 118, py0 + 44), "WTI, +0.6%", F_SANS_B, 10, INK)
    text(d, (px0 + 224, py0 + 18), "Rupee seen at", F_SANS, 9, INK)
    text(d, (px0 + 224, py0 + 29), "92.32-92.36", F_SANS_B, 11, INK)
    text(d, (px0 + 224, py0 + 44), "to the dollar", F_SANS, 9, INK)
    text(d, (px0 + 8, py0 + 58), "Ras Tanura claim: a 550,000 bpd refinery, smoke over ~600 sq km",
         F_SANS, 9, INK)

    sc_x = MARGIN + left_w + 14
    sc_w = W - MARGIN - sc_x
    # The lead scene is drawn on its own canvas and then pasted, the way the cell
    # scenes already are. A smoke plume that rises above the panel is then cut at the
    # panel's edge instead of spilling across the ticker above it.
    sc = Image.new("RGB", (sc_w, 240), P["sky_hot"])
    draw_lead_scene(ImageDraw.Draw(sc), 0, 0, sc_w, 240)
    img.paste(sc, (sc_x, LEAD_Y))

    # ---- 4. region bar --------------------------------------------------
    counts = {r: 0 for r in BAR_ORDER}
    for s in STORIES:
        counts[s["region"]] += 1
    seg_x = MARGIN
    seg_w_total = COL_W - 64
    seg_edges = []
    for r in BAR_ORDER:
        wseg = int(round(seg_w_total * counts[r] / n_stories))
        _r(d, seg_x, BAR_Y, wseg, BAR_H, REGION_TINT[r])
        seg_edges.append((seg_x, seg_x + wseg))
        seg_x += wseg
    _r(d, 0, BAR_Y, W, 1, INK)
    _r(d, 0, BAR_Y + BAR_H - 1, W, 1, INK)
    row_y = [BAR_Y + 4, BAR_Y + 18]
    labels = [("%s %d" % (REGION_SHORT[r], counts[r]), r) for r in BAR_ORDER]

    def plan(size):
        """Greedy two-row packing (label + tint swatch); None if it overflows."""
        cursor = [MARGIN, MARGIN]
        out = []
        for label, r in labels:
            lw = font(F_SANS_B, size).getlength(label) + 17
            for row in (0, 1):
                lx = cursor[row] + 7
                if lx + lw <= MARGIN + seg_w_total:
                    out.append((lx, row, label, r))
                    cursor[row] = lx + lw
                    break
            else:
                return None
        return out

    for size in (10.5, 10, 9.5, 9):
        placed = plan(size)
        if placed:
            if max(p[1] for p in placed) == 0:
                row_y = [BAR_Y + 11, BAR_Y + 25]     # one row: centre it
            else:
                # a short second row is packed from the right, so its labels
                # sit under the segments they belong to
                row1 = [p for p in placed if p[1] == 1]
                widths = [font(F_SANS_B, size).getlength(p[2]) + 17 for p in row1]
                x = MARGIN + seg_w_total - sum(widths) + 7
                shifted = []
                for p, wdt in zip(row1, widths):
                    shifted.append((x, 1, p[2], p[3]))
                    x += wdt
                placed = [p for p in placed if p[1] == 0] + shifted
            for lx, row, label, r in placed:
                _r(d, lx, row_y[row] + 1, 8, 8, REGION_TINT[r])
                d.rectangle([lx, row_y[row] + 1, lx + 7, row_y[row] + 8], outline=INK, width=1)
                text(d, (lx + 11, row_y[row]), label, F_SANS_B, size, REGION_INK[r])
            break
    else:
        raise RuntimeError("region bar labels do not fit")

    text(d, (W - MARGIN - 2, BAR_Y + 6), "= %d" % n_stories, F_SANS_B, 12, INK, anchor="ra")

    # ---- 5. timeline ----------------------------------------------------
    # only times the facts file states; no clock time means OVERNIGHT or a date
    ticks = [
        ("LATE 25 NOV", "RAS TANURA"),
        ("WED 25 NOV", "ABU DHABI"),
        ("OVERNIGHT", "RIYADH"),
        ("04:30 UTC", "WIRE"),
        ("THU 26 NOV", "CAIRO"),
        ("26-27 NOV", "BRUSSELS"),
        ("SAT 28 NOV", "NEW YORK"),
    ]
    rule_y = TL_Y + 16
    _r(d, MARGIN, rule_y, COL_W, 2, INK)
    step = COL_W // len(ticks)
    for i, (when, where) in enumerate(ticks):
        tx = MARGIN + i * step
        up = (i % 2 == 0)
        _r(d, tx, rule_y - 5 if up else rule_y + 2, 2, 5, INK)
        label = "%s %s" % (when, where)
        if up:
            text(d, (tx, rule_y - 16), label, F_SANS_B, 9.5, INK)
        else:
            text(d, (tx, rule_y + 7), label, F_SANS_B, 9.5, INK)

    # ---- 6. grid --------------------------------------------------------
    for idx, s in enumerate(cells):
        c, r = idx % 5, idx // 5
        cx = MARGIN + c * (CELL_W + GUT)
        cy = GRID_Y + r * (CELL_H + GUT)
        text(d, (cx + 2, cy + 1), s["region"], F_SANS_B, 9, REGION_INK[s["region"]])
        text(d, (cx + CELL_W - 2, cy + 1), s["field"], F_SANS, 9, "#6b6459", anchor="ra")
        hy = cy + 12
        for line in wrap(s["headline"], F_SANS_B, 11, CELL_W - 4, 2):
            text(d, (cx + 2, hy), line, F_SANS_B, 11, INK)
            hy += 13
        draw_scene(d, s["scene"], cx + 2, cy + 38, 88, 54, s["tones"], s.get("phase", 0))
        dy = cy + 38
        for line in wrap(s["detail"], F_SANS, 9, CELL_W - 96, 4):
            text(d, (cx + 94, dy), line, F_SANS, 9, "#3f3a33")
            dy += 10
        _r(d, cx, cy + CELL_H - 3, CELL_W, 1, "#8d8578")

    # ---- 7. in numbers --------------------------------------------------
    _r(d, 0, NUM_Y, W, NUM_H, INK)
    items = ["$94.81 BRENT", "3.25% BOK RATE", "31 CAIRO FIRE", "5,568 EBOLA DEATHS"]
    fnum = font(F_SANS_B, 10)
    widths = [fnum.getlength(s) for s in items]
    sep = "\u00b7"
    sepw = fnum.getlength(sep)
    slack = COL_W - (sum(widths) + sepw * 3)
    gap = slack / 6.0
    nx = float(MARGIN)
    for i, s in enumerate(items):
        text(d, (nx, NUM_Y + 11), s, F_SANS_B, 10, PAPER)
        nx += widths[i]
        if i < len(items) - 1:
            nx += gap
            text(d, (nx, NUM_Y + 11), sep, F_SANS_B, 10, "#a49a88")
            nx += sepw + gap

    # ---- 8. also today --------------------------------------------------
    col_w = (COL_W - 24) // 3
    per_col = [7, 6, 6]
    i = 0
    for col, n in enumerate(per_col):
        bx = MARGIN + col * (col_w + 12)
        for row in range(n):
            if i >= len(listed):
                break
            s = listed[i]
            i += 1
            by = 910 + row * 11
            text(d, (bx, by), "\u25aa", F_SANS, 9, REGION_INK[s["region"]])
            head = s["headline"]
            box_w = col_w - 10
            f = font(F_SANS, 9)
            while head and f.getlength(head) > box_w:
                head = head[:-1]
            if head != s["headline"]:
                head = head.rstrip(" ,.;:") + "\u2026"
            text(d, (bx + 9, by), head, F_SANS, 9, INK)

    # ---- 9. footer ------------------------------------------------------
    _r(d, 0, FOOT_Y, W, FOOT_H, INK)
    foot = ("THE WORLD TODAY \u00b7 THURSDAY 26 NOVEMBER 2026 \u00b7 "
            "DRAWN BY AN AI AGENT FOR make.fun")
    fw = font(F_SANS_B, 9.5).getlength(foot)
    text(d, ((W - fw) / 2, FOOT_Y + 11), foot, F_SANS_B, 9.5, PAPER)

    return img


# --------------------------------------------------------------------------
# measurements
# --------------------------------------------------------------------------
def luma(rgb):
    return 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]


# "ink" here means a pixel below mid-grey (luma < 128): a mark on the page,
# not a wash or a tint.  The same threshold is used for scene ink and for the
# grid-band ink percentage.
INK_LUMA = 128


def ink_mask(img, box=None):
    """Boolean mask of ink pixels (luma < INK_LUMA) in the whole image or a box."""
    if box:
        img = img.crop(box)
    px = img.load()
    w, h = img.size
    mask = []
    for yy in range(h):
        row = []
        for xx in range(w):
            row.append(1 if luma(px[xx, yy]) < INK_LUMA else 0)
        mask.append(row)
    return mask


def scene_bitmap(kind, tones, phase):
    img = Image.new("RGB", (88, 54), PAPER)
    d = ImageDraw.Draw(img)
    draw_scene(d, kind, 0, 0, 88, 54, tones, phase)
    return img


def measure(img):
    cells = [s for s in STORIES if s["role"] == "grid"]

    # scene ink and 64x64 masks
    inks, masks = [], []
    for s in cells:
        bmp = scene_bitmap(s["scene"], s["tones"], s.get("phase", 0))
        m = ink_mask(bmp)
        inks.append(sum(sum(r) for r in m))
        small = bmp.convert("L").resize((64, 64), Image.Resampling.BILINEAR)
        sm = small.load()
        masks.append([[1 if sm[i, j] < INK_LUMA else 0 for i in range(64)] for j in range(64)])

    pairs = []
    for i in range(len(masks)):
        for j in range(i + 1, len(masks)):
            a, b = masks[i], masks[j]
            inter = union = 0
            for yy in range(64):
                ra, rb = a[yy], b[yy]
                for xx in range(64):
                    x, y2 = ra[xx], rb[xx]
                    if x or y2:
                        union += 1
                        if x and y2:
                            inter += 1
            iou = inter / union if union else 0.0
            pairs.append((iou, cells[i]["scene"] + "/" + str(cells[i].get("phase", 0)),
                          cells[j]["scene"] + "/" + str(cells[j].get("phase", 0))))
    pairs.sort(reverse=True)
    worst = pairs[0][0]
    worst_pair = (pairs[0][1], pairs[0][2])

    band = ink_mask(img, (0, GRID_Y, W, GRID_Y + GRID_H))
    band_px = sum(sum(r) for r in band)
    band_pct = 100.0 * band_px / (W * GRID_H)

    collisions = []
    for i in range(len(TEXT_BOXES)):
        for j in range(i + 1, len(TEXT_BOXES)):
            b1, b2 = TEXT_BOXES[i][1], TEXT_BOXES[j][1]
            if b1[0] < b2[2] and b2[0] < b1[2] and b1[1] < b2[3] and b2[1] < b1[3]:
                collisions.append((TEXT_BOXES[i][0], TEXT_BOXES[j][0], b1, b2))

    return dict(inks=inks, worst=worst, worst_pair=worst_pair, closest=pairs,
                band_pct=band_pct, collisions=collisions)


def main():
    img = build()
    meas = measure(img)

    old_md5 = None
    if os.path.exists(OUT_PATH):
        with open(OUT_PATH, "rb") as fh:
            old_md5 = hashlib.md5(fh.read()).hexdigest()

    img.save(OUT_PATH, format="PNG", optimize=True)
    with open(OUT_PATH, "rb") as fh:
        raw = fh.read()
    new_md5 = hashlib.md5(raw).hexdigest()

    n_stories = len(STORIES)
    n_lead = sum(1 for s in STORIES if s["role"] == "lead")
    n_cells = sum(1 for s in STORIES if s["role"] == "grid")
    n_list = sum(1 for s in STORIES if s["role"] == "list")
    n_fields = len({s["field"] for s in STORIES})
    n_regions = len({s["region"] for s in STORIES})
    smallest = min(SIZES_USED)
    headline_px = 11

    print("stories on page      = %d    (lead %d + cells %d + list %d)"
          % (n_stories, n_lead, n_cells, n_list))
    print("distinct fields      = %d    (regions %d)" % (n_fields, n_regions))
    print("grid cells           = %d" % n_cells)
    print("smallest type px     = %g" % smallest)
    print("headline type px     = %d" % headline_px)
    print("scene ink min        = %d" % min(meas["inks"]))
    print("worst scene IoU      = %.3f  (%s vs %s)"
          % (meas["worst"], meas["worst_pair"][0], meas["worst_pair"][1]))
    print("grid-band ink %%      = %.2f" % meas["band_pct"])
    if meas["collisions"]:
        print("text collisions      = %d" % len(meas["collisions"]))
        for a, b, b1, b2 in meas["collisions"]:
            print("   overlap: %r %s  <->  %r %s" % (a, b1, b, b2))
    else:
        print("text collisions      = 0")
    print("bytes                = %d" % len(raw))
    print("md5 run1 / run2      = %s / %s%s"
          % (old_md5 or "(first run)", new_md5,
             "   MATCH" if old_md5 == new_md5 else "   (rerun to compare)"))

    ok = (n_stories == 40 and n_fields >= 30 and n_cells == 20 and smallest >= 9
          and min(meas["inks"]) >= 620 and meas["worst"] < 0.60
          and 8 <= meas["band_pct"] <= 18 and not meas["collisions"]
          and len(raw) <= 1048576)
    print("bars                 = %s" % ("ALL PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
