"""README.md, LICENSE and reddit/post.md, with numbers from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json")
s, h, a, b, hb = R["source"], R["hosts"], R["abroad"], R["bond"], R["hubs"]
N = lambda v: f"{round(v):,}"
D = R["decades"]
readme = f"""# Where every film was shot

A world map of the filming locations of {N(s['n_films'])} films in Wikidata ({N(s['n_locs'])} locations, {N(s['n_pairs'])} film-location pairs): the busiest film cities, which countries host other countries' films and how that changed by decade, cities filmed mostly by foreign productions, and a James Bond layer for the 25 Eon films.

Interactive page: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}

## Headline results

- Film cities: grouping each location with the nearest city of 250,000+ people within 32 km, Los Angeles has {N(hb['la']['n'])} films, New York {N(hb['ny']['n'])}, London {N(hb['london']['n'])}, Paris {N(hb['paris']['n'])} and Vancouver {N(hb['vancouver']['n'])}. Pinewood Studios is the most used single site ({N(R['sites']['pinewood'])} films).
- Home and abroad: {round(a['pct'])}% of films with an origin and a located place were shot at least partly outside their countries of origin ({round(a['pct_ex_idn'])}% excluding Indonesian films). Canada hosts the most foreign productions ({N(h['can']['foreign'])}, {round(h['can_from_us_pct'])}% American); in Malta {round(h['mlt']['foreign_pct'])}%, Morocco {round(h['mar']['foreign_pct'])}%, Bulgaria {round(h['bgr']['foreign_pct'])}% and Iceland {round(h['isl']['foreign_pct'])}% of recorded films are foreign.
- By decade: the share shot abroad rose from {round(D[4]['pct_ex_idn'])}% in the 1950s to {round(D[9]['pct_ex_idn'])}% in the 2000s. Spain's foreign productions peak in the {R['host_peak']['ESP']}s, Canada's and Bulgaria's in the {R['host_peak']['CAN']}s, Hungary's and Iceland's in the {R['host_peak']['HUN']}s.
- Stand-ins: in Valletta {round(hb['pick']['Valletta']['foreign_pct'])}%, Budapest {round(hb['pick']['Budapest']['foreign_pct'])}%, Vancouver {round(hb['vancouver']['foreign_pct'])}% and Toronto {round(hb['pick']['Toronto']['foreign_pct'])}% of films are foreign productions (Wikidata does not say what a place stood in for).
- Bond: the 25 Eon films have {b['n_pairs']} recorded locations, {b['n_locs']} distinct, in {b['n_countries']} countries and territories; Pinewood is listed for {b['pinewood']}. Films before 1990 average {b['early']:.1f} locations, those since 2006 {b['late']:.1f}: documentation, not travel.
- Coverage: {round(s['plev_pct']['country'])}% of film-location records name only a whole country and {round(s['plev_pct']['region'])}% a state or region; these are never mapped as points. {round(s['us_pct'])}% of films are American; India has {R['origins']['ind']}, Nigeria {R['origins']['nga']}.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/04_build_site.py`; page data embedded, `data/points.json` loaded by the page). |
| `header.png` | Social card, 1200 x 630. |
| `data/films.csv` | All {N(s['n_films'])} films: Wikidata ID, title, year, countries of origin, sitelinks, number of locations, location countries, countries where shot abroad, directors, Eon Bond flag. |
| `data/locations.csv` | All {N(s['n_locs'])} locations: Wikidata ID, label, level (country, region, city, site), country, coordinates, city it is grouped with, films. |
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

- Films: every Wikidata item that is an instance of film (Q11424) with a filming location (P915) that has coordinates, from one QLever query ({N(s['n_rows'])} rows; one record per film and per location). Year = earliest publication date.
- Levels: each location is a country (a country's, UK nation's, former state's or continent's Wikidata ID), a region (Natural Earth admin-1 or a listed large area), a city or town (label matches a Natural Earth populated place within 40 km) or a site. Small territories (Hong Kong, Malta, Monaco, Singapore...) count as cities. Only cities, towns and sites are mapped.
- Home and abroad: a location outside every country of origin (P495) is abroad. Co-productions are home in every partner; former states are home in their successors; crown dependencies and overseas territories are home for their parent country. {s['n_no_origin']} films without an origin are excluded.
- Film cities: nearest Natural Earth place of 250,000+ people within 32 km. Popularity: Wikidata sitelinks.
- Bond: hand list of the 25 Eon films' Wikidata IDs in `code/common.py`, checked against title and year; the 1967 Casino Royale is excluded.
- Caveats: Wikidata's filming locations are incomplete and skewed to American, English-language and well-known films; it does not record setting or what a location stood in for.

## How to rerun

Needs Python 3 with numpy, shapely, pyproj, matplotlib and fontTools, xelatex and pdftotext. Raw inputs are read in place (paths in `code/common.py`): `/home/claude/newdata/raw3/film_locations.tsv`, `film_directors.tsv` and `directors.tsv` (QLever results, retrieved {RETRIEVED}) and Natural Earth files in `/home/claude/newdata/raw/geo/`. Intermediate files go to `/dev/shm/films/work` (set `FILMTMP` to change).

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

Hotham, T. (2026) Where every film was shot: filming locations of {N(s['n_films'])} films in Wikidata. Zenodo. https://doi.org/{DOI}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)
lic = open("/home/claude/studies/football-origins/LICENSE", encoding="utf-8").read().split("This licence covers")[0] + """This licence covers the code in code/, reddit/collage.py and the page scripts.
The text of the page, paper and blog post, the figures and the derived data
files in data/ are released under CC BY 4.0. They are derived from Wikidata
(CC0) and Natural Earth (public domain).
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)
post = f"""## Title

[OC] Where every film was shot: {N(s['n_films'])} films in Wikidata mapped by filming location. Canada hosts {N(h['can']['foreign'])} foreign productions, more than anywhere else

## Body

I mapped every film in Wikidata that has a filming location with coordinates. Grouped into cities, Los Angeles ({N(hb['la']['n'])} films), New York ({N(hb['ny']['n'])}), London ({N(hb['london']['n'])}) and Paris ({N(hb['paris']['n'])}) dominate, and Pinewood Studios is the busiest single site. Comparing each location with the film's countries of origin, Canada hosts the most foreign films ({round(h['can_from_us_pct'])}% of them American), while {round(h['mlt']['foreign_pct'])}% of films shot in Malta and {round(h['mar']['foreign_pct'])}% in Morocco are foreign productions. The 25 Eon Bond films list {b['n_locs']} places in {b['n_countries']} countries and territories. Big caveats: {round(s['plev_pct']['country'] + s['plev_pct']['region'])}% of film-location records name only a whole country or state (left off the map so they do not make fake hotspots), and {round(s['us_pct'])}% of the films are American. Interactive map with decade slider, filters and a Bond layer: {PAGE}

## Source comment

Source: Wikidata via QLever, every film (Q11424) with a filming location (P915) with coordinates, plus release dates, countries of origin (P495) and sitelinks (CC0), 2026; Natural Earth outlines, admin-1 and populated places (public domain). Locations classified as country, region, city or site; only cities, towns and sites mapped; "abroad" = outside every country of origin.

Tools: Python (shapely, pyproj, matplotlib); Leaflet for the interactive map.

Interactive version: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}
"""
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
for t in (readme, post):
    for bad in ("—", "–", "--", "DSIT", "DCMS"):
        assert bad not in t.replace("|---|---|", ""), bad
print("README", len(readme.split()), "words; post", len(post.split()))
