"""Shared paths and helpers for the film-locations project.

Raw inputs (read in place, never modified):
  /home/claude/newdata/raw3/film_locations.tsv   QLever query result on Wikidata (CC0), retrieved 2026: every item that is an
      instance of film (P31 Q11424) with a filming location (P915) that has coordinates (P625). Columns:
      ?film item, ?filmL English label, ?date publication date (P577), ?loc filming location, ?locL its English label,
      ?coord its coordinates, ?lcountry the location's country (P17), ?origin the film's country of origin (P495),
      ?sl the film's number of sitelinks. One row per combination, so a film-location pair repeats per date, origin and country.
  /home/claude/newdata/raw3/film_directors.tsv   QLever result: film, director (P57), date, origin.
  /home/claude/newdata/raw3/directors.tsv        QLever result: director item and English label (and other fields not used).
  /home/claude/newdata/raw/geo/ne_10m_admin_0_countries.geojson, ne_50m_admin_0_countries.geojson,
      ne_10m_admin_1_states_provinces.geojson, ne_10m_populated_places_simple.geojson (Natural Earth, public domain)
"""
import json, gzip, os, re, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("FILM_RAW", "/home/claude/newdata/raw3")
GEO = os.environ.get("FILM_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("FILM_FONTS", "/home/claude/ref/fonts")
DATA = os.path.join(ROOT, "data")
WORK = os.path.join(os.environ.get("FILMTMP", "/dev/shm/films"), "work")   # intermediates live in memory, not in the repo
for d in (DATA, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "film-locations"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
DOI = "10.5281/zenodo.23847354"              # filled in by the publisher
BLOG = "https://blog.tristanhotham.com/2026/10/31/film-locations/"        # filled in by the publisher
RETRIEVED = "2026"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
WD = "http://www.wikidata.org/entity/"

# The 25 official James Bond films made by Eon Productions, 1962 to 2021 (as listed in Wikipedia, "List of James Bond films").
# Q-ids were found by matching title and year in the query result and checked by hand; the 1967 Casino Royale (Q591272,
# not an Eon film) is deliberately left out.
BOND = [("Q102754", "Dr. No", 1962), ("Q106571", "From Russia with Love", 1963), ("Q106440", "Goldfinger", 1964),
        ("Q107724", "Thunderball", 1965), ("Q107761", "You Only Live Twice", 1967), ("Q107894", "On Her Majesty's Secret Service", 1969),
        ("Q107914", "Diamonds Are Forever", 1971), ("Q27204", "Live and Let Die", 1973), ("Q309289", "The Man with the Golden Gun", 1974),
        ("Q320423", "The Spy Who Loved Me", 1977), ("Q334780", "Moonraker", 1979), ("Q332330", "For Your Eyes Only", 1981),
        ("Q204398", "Octopussy", 1983), ("Q332368", "A View to a Kill", 1985), ("Q272064", "The Living Daylights", 1987),
        ("Q309086", "Licence to Kill", 1989), ("Q19089", "GoldenEye", 1995), ("Q207916", "Tomorrow Never Dies", 1997),
        ("Q212145", "The World Is Not Enough", 1999), ("Q30931", "Die Another Day", 2002), ("Q151904", "Casino Royale", 2006),
        ("Q181540", "Quantum of Solace", 2008), ("Q4941", "Skyfall", 2012), ("Q18602670", "Spectre", 2015), ("Q21534241", "No Time to Die", 2021)]
BONDQ = {q for q, _, _ in BOND}


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    """Remove em and en dashes and double hyphens from text taken from Wikidata (house style)."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def jsave(obj, path, indent=None):
    if os.path.abspath(path).startswith(DATA):
        obj = dash(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))


def norm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    return re.sub(r"[\W_]+", " ", s).strip()


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "ord":
        n = int(v); suf = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
        return f"{n}{suf}"
    raise ValueError(f)
