"""Parse the QLever TSV of Wikidata films with filming locations into films, locations and film-location pairs.

Rules
- One record per film (Wikidata item) and one per location. Rows repeat for every combination of publication date,
  country of origin and location country, so values are pooled per item.
- Year: the earliest parsable publication year (P577). Years after 2026 (announced films) are kept but flagged.
- Location point: the first coordinate the query returns for the location (a handful of locations have several).
- One line in the file has two records run together (a missing line break); it is split back into two.
- Directors (P57) come from film_directors.tsv and their English labels from directors.tsv; used only for popups.
"""
import csv, sys
from collections import defaultdict, Counter
from common import *

csv.field_size_limit(sys.maxsize)
POINT = re.compile(r"POINT\(([-\d.eE+]+) ([-\d.eE+]+)\)")
YEAR = re.compile(r'^"?(-?\d{1,4})-\d\d-\d\dT')


def val(v):
    v = (v or "").strip()
    if v.startswith("<" + WD):
        return v[len(WD) + 1:-1]
    m = re.match(r'^"(.*)"(@[\w-]+|\^\^<[^>]+>)?$', v, re.S)
    if m:
        return m.group(1).replace('\\"', '"').replace("\\\\", "\\")
    return v


def rows_of(path, nf):
    lines = open(path, encoding="utf-8").read().split("\n")
    head = [h.lstrip("?") for h in lines[0].split("\t")]
    out, fixed = [], 0
    for l in lines[1:]:
        if not l.strip():
            continue
        f = l.split("\t")
        if len(f) == 2 * nf - 1:            # two records joined: the last field of the first runs into the id of the second
            m = re.match(r"^(.*?)(Q\d+)$", f[nf - 1])
            out.append(f[:nf - 1] + [m.group(1)]); out.append([m.group(2)] + f[nf:]); fixed += 1
        elif len(f) == nf:
            out.append(f)
        else:
            raise ValueError(f"bad line with {len(f)} fields: {l[:120]}")
    return head, [[val(x) for x in r] for r in out], fixed


head, rows, fixed = rows_of(f"{RAW}/film_locations.tsv", 9)
print("rows", len(rows), "joined lines split", fixed)
F = defaultdict(lambda: {"t": "", "years": set(), "orig": set(), "sl": 0, "locs": set()})
L = defaultdict(lambda: {"l": "", "pts": [], "cty": set(), "films": set()})
for r in rows:
    r = dict(zip(head, r))
    f = F[r["film"]]; l = L[r["loc"]]
    if r["filmL"] and not f["t"]: f["t"] = r["filmL"]
    m = YEAR.match(r["date"] or "")
    if m: f["years"].add(int(m.group(1)))
    if r["origin"]: f["orig"].add(r["origin"])
    f["sl"] = max(f["sl"], int(r["sl"] or 0))
    f["locs"].add(r["loc"])
    if r["locL"] and not l["l"]: l["l"] = r["locL"]
    m = POINT.search(r["coord"] or "")
    if m:
        p = (round(float(m.group(1)), 4), round(float(m.group(2)), 4))
        if p not in l["pts"] and -180 <= p[0] <= 180 and -90 <= p[1] <= 90: l["pts"].append(p)
    if r["lcountry"]: l["cty"].add(r["lcountry"])
    l["films"].add(r["film"])

# directors
dh, drows, dfix = rows_of(f"{RAW}/film_directors.tsv", 4)
names = {}
for l in open(f"{RAW}/directors.tsv", encoding="utf-8").read().split("\n")[1:]:
    x = l.split("\t")
    if len(x) > 1 and x[1]:
        names[val(x[0])] = val(x[1])
dirs = defaultdict(list)
for r in drows:
    if r[0] in F and r[1] in names and names[r[1]] not in dirs[r[0]]:
        dirs[r[0]].append(names[r[1]])
print("films with a named director", sum(1 for q in F if dirs.get(q)), "of", len(F))

films = []
for q, f in F.items():
    ys = sorted(y for y in f["years"] if y >= 1880)
    films.append({"q": q, "t": f["t"], "y": ys[0] if ys else None, "orig": sorted(f["orig"]), "sl": f["sl"],
                  "locs": sorted(f["locs"]), "dir": dirs.get(q, [])[:3]})
locs = []
multi = 0
for q, l in L.items():
    multi += len(l["pts"]) > 1
    locs.append({"q": q, "l": l["l"], "lon": l["pts"][0][0], "lat": l["pts"][0][1], "cty": sorted(l["cty"]), "n": len(l["films"])})
pairs = sum(len(f["locs"]) for f in films)
print("films", len(films), "locations", len(locs), "pairs", pairs, "locations with several points", multi)
missing = [b for b in BOND if b[0] not in F]
assert not missing, missing
for q, t, y in BOND:
    fm = next(f for f in films if f["q"] == q)
    assert fm["t"] == t and fm["y"] == y, (q, fm["t"], fm["y"], t, y)
jsave({"n_rows": len(rows), "n_fixed": fixed, "n_multi_pts": multi, "films": films, "locs": locs}, f"{WORK}/parsed.json")
