# Where every film was shot

A world map of the filming locations of 23,468 films in Wikidata (7,926 locations, 35,108 film-location pairs): the busiest film cities, which countries host other countries' films and how that changed by decade, cities filmed mostly by foreign productions, and a James Bond layer for the 25 Eon films.

Interactive page: https://maps.tristanhotham.com/film-locations/
Paper: https://doi.org/10.5281/zenodo.23847354
Blog post: https://blog.tristanhotham.com/2026/10/31/film-locations/

## Headline results

- Film cities: grouping each location with the nearest city of 250,000+ people within 32 km, Los Angeles has 1,514 films, New York 1,350, London 1,118, Paris 933 and Vancouver 452. Pinewood Studios is the most used single site (645 films).
- Home and abroad: 19% of films with an origin and a located place were shot at least partly outside their countries of origin (21% excluding Indonesian films). Canada hosts the most foreign productions (717, 95% American); in Malta 96%, Morocco 82%, Bulgaria 79% and Iceland 78% of recorded films are foreign.
- By decade: the share shot abroad rose from 20% in the 1950s to 25% in the 2000s. Spain's foreign productions peak in the 1960s, Canada's and Bulgaria's in the 2000s, Hungary's and Iceland's in the 2010s.
- Stand-ins: in Valletta 96%, Budapest 66%, Vancouver 63% and Toronto 56% of films are foreign productions (Wikidata does not say what a place stood in for).
- Bond: the 25 Eon films have 248 recorded locations, 179 distinct, in 36 countries and territories; Pinewood is listed for 22. Films before 1990 average 6.6 locations, those since 2006 19.6: documentation, not travel.
- Coverage: 20% of film-location records name only a whole country and 14% a state or region; these are never mapped as points. 40% of films are American; India has 614, Nigeria 13.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/04_build_site.py`; page data embedded, `data/points.json` loaded by the page). |
| `header.png` | Social card, 1200 x 630. |
| `data/films.csv` | All 23,468 films: Wikidata ID, title, year, countries of origin, sitelinks, number of locations, location countries, countries where shot abroad, directors, Eon Bond flag. |
| `data/locations.csv` | All 7,926 locations: Wikidata ID, label, level (country, region, city, site), country, coordinates, city it is grouped with, films. |
| `data/film_locations.csv` | Every film-location pair with level, country and home or abroad. |
| `data/countries.csv` | Per country: films shot there, own and foreign, foreign share and main origins; films of that origin and how many were shot abroad. |
| `data/hubs.csv` | Film cities: films, popularity-weighted count and ranks, foreign share, best-known films. |
| `data/decades.csv` | Films per decade, share shot abroad (all, excluding Indonesia, American films), co-production share. |
| `data/results.json` | Every number used in the page, paper, blog and collage. |
| `data/points.json`, `data/site.json`, `data/world.json`, `data/cities.json` | Page data. |
| `code/` | Scripts, run in order (below), and the page, paper and blog templates. |
| `release/` | Paper PDF and LaTeX source with figures (`paper/`), blog post, figures and meta (`blog/`), Zenodo files (`zenodo/`). |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |
| `qa/` | Screenshots of the page at desktop and phone widths. |

## Method in brief

- Films: every Wikidata item that is an instance of film (Q11424) with a filming location (P915) that has coordinates, from one QLever query (119,808 rows; one record per film and per location). Year = earliest publication date.
- Levels: each location is a country (a country's, UK nation's, former state's or continent's Wikidata ID), a region (Natural Earth admin-1 or a listed large area), a city or town (label matches a Natural Earth populated place within 40 km) or a site. Small territories (Hong Kong, Malta, Monaco, Singapore...) count as cities. Only cities, towns and sites are mapped.
- Home and abroad: a location outside every country of origin (P495) is abroad. Co-productions are home in every partner; former states are home in their successors; crown dependencies and overseas territories are home for their parent country. 228 films without an origin are excluded.
- Film cities: nearest Natural Earth place of 250,000+ people within 32 km. Popularity: Wikidata sitelinks.
- Bond: hand list of the 25 Eon films' Wikidata IDs in `code/common.py`, checked against title and year; the 1967 Casino Royale is excluded.
- Caveats: Wikidata's filming locations are incomplete and skewed to American, English-language and well-known films; it does not record setting or what a location stood in for.

## How to rerun

Needs Python 3 with numpy, shapely, pyproj, matplotlib and fontTools, xelatex and pdftotext. Raw inputs are read in place (paths in `code/common.py`): `/home/claude/newdata/raw3/film_locations.tsv`, `film_directors.tsv` and `directors.tsv` (QLever results, retrieved 2026) and Natural Earth files in `/home/claude/newdata/raw/geo/`. Intermediate files go to `/dev/shm/films/work` (set `FILMTMP` to change).

```
python3 code/01_parse.py        # films, locations, pairs, directors
python3 code/02_geo.py          # outlines, location levels and countries, film cities
python3 code/03_results.py      # results.json, data tables, page data
python3 code/04_build_site.py   # index.html (with checks of facts stated in words)
python3 code/05_figures.py      # header, blog and paper figures
python3 code/06_paper.py        # paper PDF
python3 code/07_readme.py       # README, LICENSE, Reddit post
python3 code/08_release.py      # blog post, Zenodo files
python3 reddit/collage.py       # collage
```

## Sources and licences

- Wikidata, via QLever (https://qlever.cs.uni-freiburg.de/wikidata). CC0.
- Natural Earth countries, states and provinces, and populated places (https://www.naturalearthdata.com/). Public domain.
- Base map tiles on the page: © Esri.

## Citation

Hotham, T. (2026) Where every film was shot: filming locations of 23,468 films in Wikidata. Zenodo. https://doi.org/10.5281/zenodo.23847354

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
