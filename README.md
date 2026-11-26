# THE WORLD TODAY, Thursday 26 November 2026

A 1024 x 1024 newspaper front page for one day, drawn from a fixed list of
stories with Pillow, then copied to the output directory by a small Node
program that checks the file first.

Everything printed on the page comes from `../facts26.md`. No other file is
read, no clock and no network are touched, and two runs write the same bytes.

## Run it

```sh
python3 scripts/make_news.py          # draws entry.png and prints the measurements
mkdir -p out
MAKEFUN_OUTPUT_DIR=out node main.ts   # copies entry.png to out/entry.png
```

`node main.ts` refuses with a readable sentence when `entry.png` is missing,
is not a PNG, is larger than 1024 px on a side, or is larger than 1 MiB. With
`MAKEFUN_OUTPUT_DIR` unset it writes to `/output`.

Requires Python 3 with Pillow, and Node 22 (which strips the types in
`main.ts` on its own).

## The page

One image, newsprint `#f4f1e8`, ink `#14120e`, seven region tints reused by
twelve regions.

| band | y | contents |
|------|---|----------|
| masthead | 0-88 | `THE WORLD TODAY` in 44 px bold serif, date and counts at right, 3 px rule |
| ticker | 88-120 | black bar, three headlines at 12.5 px |
| lead | 124-370 | kicker, 3-line 27 px headline, 2-line subhead, dateline, oil/rupee panel, and a 439 x 240 drawn Gulf scene |
| region bar | 374-406 | twelve proportional tint segments, each `LABEL n`, ending `= 40` |
| timeline | 410-444 | one rule, seven ticks, alternating labels above and below |
| grid | 448-866 | 5 x 4 cells of 192 x 100 px, gutters 6 px |
| in numbers | 870-904 | black bar, four hard numbers at 10 px |
| also today | 908-986 | three columns of one-line headlines at 9 px, bullet `▪` |
| footer | 992-1024 | black bar with the paper's name and the date |

Each grid cell holds a region tag (9 px, in the region colour), the field
(9 px, right), a two-line 11 px bold headline, a drawn scene of 88 x 54 px,
and a detail line (9 px).

## Stories

Forty stories, kept in one list of dicts in `scripts/make_news.py`: one lead,
twenty cells that carry a scene, nineteen one-line items. Every count printed
by the program (stories, regions, fields, cell scenes) is computed from that
list, so the masthead, the region bar and the measurements cannot disagree.

Twelve regions: EUROPE 9, LEVANT 5, EAST ASIA 5, AMERICAS 5, GULF 3,
NORTH AFRICA 2, WEST AFRICA 2, CENTRAL AFRICA 2, SOUTH ASIA 2,
SOUTHEAST ASIA 2, PACIFIC 2, SOUTHERN AFRICA 1. That is 40.

Thirty-four distinct fields over those forty stories.

## Scenes

`SCENES` is the table of cells that carry a scene; each entry names its kind,
its tones and a phase. There is one drawing function per kind: tanker,
apartment block, refinery, parliament, checkpoint, helicopter, market screen,
courtroom, stadium, hospital, weather, map. Every scene is flat shapes in
three or four tones with at least one solid mass, and the lead scene (two
tankers, a flame and smoke column, a missile track, a shoreline and a sun) is
drawn separately at 439 x 240.

After drawing, the program downsamples the twenty cell scenes to 64 x 64,
compares every pair and prints the worst intersection-over-union, which must
stay below 0.60.

## What the measurements mean

```
stories on page      = 40    (lead 1 + cells 20 + list 19)
distinct fields      = 34
grid cells           = 20
smallest type px     = 9
headline type px     = 11
scene ink min        = <px>
worst scene IoU      = <x>
grid-band ink %      = <x>
text collisions      = 0
bytes                = <n>
md5 run1 / run2      = <a> / <b>
```

* ink is a pixel below mid-grey, luma < 128. The same threshold is used for a
  scene's ink count and for the ink share of the grid band, so a wash or a
  tint is never counted as ink.
* a text collision is two drawn strings whose ink bounding boxes overlap.
  Every offending pair is printed with both strings and both boxes.
* md5 run1 is the file that was already on disk, md5 run2 the file just
  written; they must match, and the program prints `MATCH` when they do.

## Two places where the brief does not add up

Both were resolved in favour of the numbers the run has to print.

1. `1 lead + 20 cells + 21 list items = 40` is 42. The page carries 40
   stories, which is what the masthead, the region bar and the measurement
   require, so the also-today band carries 19 items in three columns of
   7, 6 and 6. Nothing is duplicated to reach 42.
2. `Also today y 944-988` is 44 px, but seven 9 px lines need about 77 px at
   a leading that keeps their boxes apart. The whole stack below the masthead
   is therefore shifted up, and the band is given 78 px, while the grid keeps
   its 20 cells of 192 x 100 px and the type stays at 9 px or larger.

## Licence

MIT. See `LICENSE`.
