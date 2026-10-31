"""All numbers (data/results.json), the reusable tables in data/, and the page data (data/site.json embedded in the
page; data/points.json loaded by it).

Definitions
- A film is shot abroad in a country when that country is not one of its countries of origin (P495). Co-productions are
  at home in every partner country; a film of a former state (Soviet Union, Yugoslavia, Czechoslovakia) is at home in
  any successor state. Films with no country of origin are left out of every home and abroad figure.
- Host counts use every filming location, whatever its level (a film filmed "in Morocco" was filmed in Morocco).
- Place and hub counts use only city, town and site locations, never whole countries or regions, so a country centroid
  cannot become a hotspot.
- Popularity: the film's number of Wikidata sitelinks (Wikipedia articles in any language and other Wikimedia pages).
"""
import csv, math, statistics
from collections import Counter, defaultdict
from common import *

D = jload(f"{WORK}/geo.json"); M = jload(f"{WORK}/countries.json")
films, locs = D["films"], D["locs"]
L = {l["q"]: l for l in locs}
CN = lambda i: M[i]["name"] if i in M else i
title = lambda f: f["t"] or "(no English title)"
for f in films:
    f["dec"] = (f["y"] // 10) * 10 if f["y"] and f["y"] <= 2026 else None
    f["hosts"] = sorted({L[q]["iso"] for q in f["locs"] if L[q]["iso"]})
    f["has_o"] = bool(f["oiso"])
    f["abroad"] = [h for h in f["hosts"] if f["has_o"] and h not in f["oiso"]]
    f["mapped"] = [q for q in f["locs"] if L[q]["lev"] in ("city", "site")]
    f["bond"] = f["q"] in BONDQ
NF, NL = len(films), len(locs)
pairs = [(f, L[q]) for f in films for q in f["locs"]]
lev = Counter(l["lev"] for l in locs); plev = Counter(l["lev"] for _, l in pairs)
R = {"meta": {"slug": SLUG, "page": PAGE, "repo": REPO, "doi": DOI, "blog": BLOG, "retrieved": RETRIEVED}}
sl = [f["sl"] for f in films]
o_us = sum(1 for f in films if "USA" in f["ocode"])
s = {"n_rows": D["n_rows"], "n_films": NF, "n_locs": NL, "n_pairs": len(pairs), "n_fixed": D["n_fixed"], "n_multi_pts": D["n_multi_pts"],
     "lev": dict(lev), "plev": dict(plev), "plev_pct": {k: 100 * v / len(pairs) for k, v in plev.items()},
     "n_dated": sum(1 for f in films if f["dec"] is not None), "n_undated": sum(1 for f in films if f["dec"] is None),
     "n_origin": sum(1 for f in films if f["has_o"]), "n_no_origin": sum(1 for f in films if not f["has_o"]),
     "n_notitle": sum(1 for f in films if not f["t"]), "n_mapped": sum(1 for f in films if f["mapped"]),
     "n_unmapped": sum(1 for f in films if not f["mapped"]), "mapped_pct": 100 * sum(1 for f in films if f["mapped"]) / NF,
     "median_sl": statistics.median(sl), "sl0": sum(1 for x in sl if x == 0), "sl_ge30": sum(1 for x in sl if x >= 30),
     "median_locs": statistics.median([len(f["locs"]) for f in films]), "one_loc_pct": 100 * sum(1 for f in films if len(f["locs"]) == 1) / NF,
     "n_dir": sum(1 for f in films if f["dir"]), "us_pct": 100 * o_us / NF, "n_us": o_us,
     "n_country_lev_only": sum(1 for f in films if f["locs"] and all(L[q]["lev"] == "country" for q in f["locs"])),
     "n_small_states_city": sorted({CN(l["iso"]) for l in locs if l.get("small")})}
s["n_future"] = sum(1 for f in films if f["y"] and f["y"] > 2026)
s["dated_pct"] = 100 * s["n_dated"] / NF
R["source"] = s

# Indonesia: one country-level location used for thousands of films
idn = [f for f in films if "Q252" in f["locs"]]
R["idn"] = {"n": len(idn), "only": sum(1 for f in idn if f["locs"] == ["Q252"]), "idn_origin_pct": 100 * sum(1 for f in idn if "IDN" in f["ocode"]) / len(idn),
            "pct_of_country_pairs": 100 * len(idn) / plev["country"], "pct_all": 100 * len(idn) / NF}

# origins
oc = Counter(c for f in films for c in f["ocode"])
R["origins"] = {"top": [{"iso": i, "name": CN(i), "n": n, "pct": 100 * n / NF} for i, n in oc.most_common(15)],
                "n_countries": len(oc), "co_pct": 100 * sum(1 for f in films if len(f["ocode"]) > 1) / s["n_origin"],
                "ind": oc.get("IND", 0), "chn": oc.get("CHN", 0), "nga": oc.get("NGA", 0), "jpn": oc.get("JPN", 0), "kor": oc.get("KOR", 0)}

# countries as hosts (all levels)
host = defaultdict(lambda: {"all": set(), "o": set(), "foreign": set(), "dom": set(), "from": Counter(), "sl": 0})
for f in films:
    for h in f["hosts"]:
        H = host[h]; H["all"].add(f["q"])
        if f["has_o"]:
            H["o"].add(f["q"])
            if h in f["oiso"]: H["dom"].add(f["q"])
            else:
                H["foreign"].add(f["q"])
                for c in f["ocode"]: H["from"][c] += 1
HOST = []
for h, H in host.items():
    no = len(H["o"])
    HOST.append({"iso": h, "name": CN(h), "n": len(H["all"]), "n_o": no, "foreign": len(H["foreign"]), "dom": len(H["dom"]),
                 "foreign_pct": 100 * len(H["foreign"]) / no if no else 0, "from": [[c, CN(c), n] for c, n in H["from"].most_common(4)]})
HOST.sort(key=lambda r: -r["foreign"])
HB = {r["iso"]: r for r in HOST}
share = sorted([r for r in HOST if r["n_o"] >= 40], key=lambda r: -r["foreign_pct"])
R["hosts"] = {"n_countries": len(HOST), "top_n": sorted(HOST, key=lambda r: -r["n"])[:15], "top_foreign": HOST[:15], "top_share": share[:15],
              "least_share": [r for r in sorted([r for r in HOST if r["n_o"] >= 150], key=lambda r: r["foreign_pct"])][:8],
              "can": HB["CAN"], "gbr": HB["GBR"], "usa": HB["USA"], "mar": HB["MAR"], "nzl": HB["NZL"], "isl": HB["ISL"], "mlt": HB["MLT"],
              "esp": HB["ESP"], "mex": HB["MEX"], "cze": HB["CZE"], "hun": HB["HUN"], "bgr": HB["BGR"], "jor": HB.get("JOR"), "ind": HB["IND"], "idn": HB["IDN"],
              "can_from_us_pct": 100 * HB["CAN"]["from"][0][2] / HB["CAN"]["foreign"] if HB["CAN"]["from"][0][0] == "USA" else None}
assert HB["CAN"]["from"][0][0] == "USA"

# films of each origin: how often they leave home
og = defaultdict(lambda: [0, 0])
for f in films:
    if f["has_o"] and f["hosts"]:
        for c in f["ocode"]:
            og[c][0] += 1; og[c][1] += bool(f["abroad"])
ORIG = sorted([{"iso": c, "name": CN(c), "n": v[0], "abroad": v[1], "pct": 100 * v[1] / v[0]} for c, v in og.items() if v[0] >= 150], key=lambda r: -r["pct"])
R["leave"] = {"list": ORIG, "usa": next(r for r in ORIG if r["iso"] == "USA"), "gbr": next(r for r in ORIG if r["iso"] == "GBR"),
              "fra": next(r for r in ORIG if r["iso"] == "FRA"), "ind": next(r for r in ORIG if r["iso"] == "IND"), "idn": next(r for r in ORIG if r["iso"] == "IDN")}

# home and abroad overall and by decade
ok = [f for f in films if f["has_o"] and f["hosts"]]
R["abroad"] = {"n": len(ok), "any": sum(1 for f in ok if f["abroad"]), "pct": 100 * sum(1 for f in ok if f["abroad"]) / len(ok),
               "only": sum(1 for f in ok if f["abroad"] and len(f["abroad"]) == len(f["hosts"])),
               "pairs_pct": 100 * sum(len(f["abroad"]) for f in ok) / sum(len(f["hosts"]) for f in ok)}
okx = [f for f in ok if "IDN" not in f["ocode"]]
R["abroad"]["pct_ex_idn"] = 100 * sum(1 for f in okx if f["abroad"]) / len(okx)
decs = list(range(1910, 2030, 10))
DEC = []
for d in decs:
    v = [f for f in ok if f["dec"] == d]; vx = [f for f in v if "IDN" not in f["ocode"]]; vu = [f for f in v if "USA" in f["ocode"]]
    DEC.append({"dec": d, "n": len(v), "abroad": sum(1 for f in v if f["abroad"]), "pct": 100 * sum(1 for f in v if f["abroad"]) / len(v) if v else 0,
                "pct_ex_idn": 100 * sum(1 for f in vx if f["abroad"]) / len(vx) if vx else 0,
                "us_n": len(vu), "us_pct": 100 * sum(1 for f in vu if f["abroad"]) / len(vu) if vu else 0,
                "co_pct": 100 * sum(1 for f in v if len(f["ocode"]) > 1) / len(v) if v else 0,
                "films": sum(1 for f in films if f["dec"] == d)})
R["decades"] = DEC
DD = {d["dec"]: d for d in DEC}
R["abroad"]["d1950"] = DD[1950]["pct_ex_idn"]; R["abroad"]["d2010"] = DD[2010]["pct_ex_idn"]
R["abroad"]["us1950"] = DD[1950]["us_pct"]; R["abroad"]["us2010"] = DD[2010]["us_pct"]
R["abroad"]["peak_dec"] = max([d for d in DEC if d["n"] >= 200], key=lambda d: d["pct_ex_idn"])["dec"]
# hosts of foreign films by decade: Canada, UK, Spain, Morocco, Czechia, Hungary, Bulgaria, New Zealand, Iceland, Malta
HD = defaultdict(Counter)
for f in ok:
    for h in f["abroad"]:
        if f["dec"]: HD[h][f["dec"]] += 1
R["host_decades"] = {h: {str(d): HD[h][d] for d in decs} for h in ("CAN", "GBR", "ESP", "MAR", "CZE", "HUN", "BGR", "NZL", "ISL", "MLT", "MEX", "ITA", "USA", "FRA", "THA", "ZAF")}
DEC_ = Counter(f["dec"] for f in films if f["dec"])
R["host_peak"] = {h: max(v, key=lambda d: v[d]) for h, v in R["host_decades"].items()}
R["films_by_dec"] = {str(d): DEC_[d] for d in sorted(DEC_)}
R["post2000_pct"] = 100 * sum(v for d, v in DEC_.items() if d >= 2000) / s["n_dated"]

# places and hubs (city, town and site only)
hub = defaultdict(lambda: {"films": set(), "locs": set(), "n": "", "pt": None, "iso": None})
for f in films:
    for q in f["mapped"]:
        l = L[q]; H = hub[l["hub"]]; H["films"].add(f["q"]); H["locs"].add(q); H["n"] = l["hub_n"]; H["pt"] = l["hub_pt"]; H["iso"] = l["iso"] if H["iso"] is None else H["iso"]
FB = {f["q"]: f for f in films}
HUBS = []
for k, H in hub.items():
    fs = [FB[q] for q in H["films"]]
    o = [f for f in fs if f["has_o"]]
    fr = [f for f in o if H["iso"] not in f["oiso"]]
    HUBS.append({"k": k, "name": H["n"], "iso": H["iso"], "country": CN(H["iso"]), "lon": H["pt"][0], "lat": H["pt"][1], "n": len(fs), "w": sum(f["sl"] for f in fs),
                 "n_locs": len(H["locs"]), "n_o": len(o), "foreign": len(fr), "foreign_pct": 100 * len(fr) / len(o) if o else 0,
                 "from": [[c, CN(c), n] for c, n in Counter(c for f in fr for c in f["ocode"]).most_common(3)],
                 "top": [[title(f), f["y"] or 0, f["q"]] for f in sorted(fs, key=lambda f: -f["sl"])[:5]]})
HUBS.sort(key=lambda r: -r["n"])
for i, h in enumerate(HUBS): h["rank_n"] = i + 1
for i, h in enumerate(sorted(HUBS, key=lambda r: -r["w"])): h["rank_w"] = i + 1
HK = {h["name"]: h for h in reversed(HUBS)}
byw = sorted(HUBS, key=lambda r: -r["w"])
stand = sorted([h for h in HUBS if h["n_o"] >= 25], key=lambda r: -r["foreign_pct"])
R["hubs"] = {"n": len(HUBS), "top": HUBS[:20], "top_w": byw[:20], "standin": stand[:15],
             "top5_pct": 100 * len(set().union(*[hub[h["k"]]["films"] for h in HUBS[:5]])) / s["n_mapped"],
             "risers": sorted([h for h in byw[:40]], key=lambda h: h["rank_w"] - h["rank_n"])[:6],
             "la": HK["Los Angeles"], "ny": HK["New York City"], "london": HK["London"], "paris": HK["Paris"], "vancouver": HK["Vancouver"]}
R["hubs"]["pick"] = {k: HK[k] for k in ("Almería", "Ouarzazate", "Valletta", "Budapest", "Prague", "Reykjavík", "Wellington", "Auckland", "Sofia", "Ooty", "Long Beach", "Malibu", "Bangkok", "Toronto", "Montreal", "Hong Kong", "Mumbai", "Atlanta") if k in HK}
print("picked", {k: (v["n"], round(v["foreign_pct"])) for k, v in R["hubs"]["pick"].items()})
# individual sites
SITE_L = sorted([l for l in locs if l["lev"] == "site"], key=lambda l: -l["n"])
studio = [l for l in locs if re.search(r"studio|cinecitt|barrandov|stage \d", l["l"] or "", re.I)]
R["sites"] = {"top": [{"q": l["q"], "name": l["l"], "iso": l["iso"], "country": CN(l["iso"]), "n": l["n"], "hub": l["hub_n"]} for l in SITE_L[:15]],
              "pinewood": L["Q661896"]["n"], "n_studio": len(studio), "studio_pairs": sum(l["n"] for l in studio)}
assert R["sites"]["top"][0]["name"] == "Pinewood Studios"
# country and region level
cl = sorted([l for l in locs if l["lev"] in ("country", "region")], key=lambda l: -l["n"])
R["coarse"] = {"top": [{"q": l["q"], "name": l["l"], "lev": l["lev"], "iso": l["iso"], "n": l["n"]} for l in cl[:15]],
               "n_films_coarse_only": sum(1 for f in films if f["locs"] and not f["mapped"]),
               "pct_pairs": 100 * (plev["country"] + plev["region"]) / len(pairs)}

# popularity tiers
R["pop"] = {"tiers": []}
for lo, hi in ((0, 4), (5, 19), (20, 49), (50, 999)):
    v = [f for f in ok if lo <= f["sl"] <= hi]
    R["pop"]["tiers"].append({"lo": lo, "hi": hi, "n": len(v), "pct": 100 * sum(1 for f in v if f["abroad"]) / len(v), "locs": statistics.mean([len(f["locs"]) for f in v])})
R["pop"]["corr_note"] = R["pop"]["tiers"][-1]["pct"] > R["pop"]["tiers"][0]["pct"]

# Bond
BF = []
bl_all = defaultdict(list)
for q, t, y in BOND:
    f = FB[q]
    ls = [L[x] for x in f["locs"]]
    for l in ls: bl_all[l["q"]].append(t)
    BF.append({"q": q, "t": t, "y": y, "sl": f["sl"], "n": len(ls), "countries": sorted({l["iso"] for l in ls if l["iso"]}),
               "abroad": [CN(h) for h in f["abroad"]], "pinewood": "Q661896" in f["locs"],
               "locs": [[l["l"], l["lev"], CN(l["iso"]), l["lon"], l["lat"], l["q"]] for l in ls]})
bc = Counter(h for b in BF for h in b["countries"])
R["bond"] = {"n": len(BF), "films": BF, "n_locs": len(bl_all), "n_pairs": sum(b["n"] for b in BF), "n_countries": len(bc),
             "countries": [[i, CN(i), n] for i, n in bc.most_common()], "pinewood": sum(b["pinewood"] for b in BF),
             "most": max(BF, key=lambda b: b["n"]), "fewest": min(BF, key=lambda b: b["n"]),
             "top_locs": [[L[q]["l"], len(v), CN(L[q]["iso"])] for q, v in sorted(bl_all.items(), key=lambda x: -len(x[1]))[:8]],
             "origin": sorted({c for q, _, _ in BOND for c in FB[q]["ocode"]}),
             "median_sl": statistics.median([b["sl"] for b in BF]),
             "abroad_films": sum(1 for b in BF if b["abroad"])}
R["bond"]["non_uk"] = sorted({h for b in BF for h in b["countries"] if h not in ("GBR", "GIB")})
R["bond"]["n_non_uk"] = len(R["bond"]["non_uk"])
for b in BF:
    b["outside_uk"] = [CN(h) for h in b["countries"] if h not in ("GBR", "GIB")]
R["bond"]["early"] = sum(b["n"] for b in BF if b["y"] < 1990) / sum(1 for b in BF if b["y"] < 1990)
R["bond"]["late"] = sum(b["n"] for b in BF if b["y"] >= 2006) / sum(1 for b in BF if b["y"] >= 2006)
assert R["bond"]["most"]["t"] == "Spectre"
jsave(R, f"{DATA}/results.json", indent=1)

# ---------- reusable tables ----------
with open(f"{DATA}/films.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["wikidata", "title", "year", "countries_of_origin", "sitelinks", "n_locations", "location_countries", "shot_abroad_in", "directors", "eon_bond"])
    for f in sorted(films, key=lambda f: (f["y"] or 9999, f["t"])):
        w.writerow([f["q"], dash(f["t"]), f["y"] or "", ";".join(f["ocode"]), f["sl"], len(f["locs"]), ";".join(f["hosts"]), ";".join(f["abroad"]) if f["has_o"] else "", dash("; ".join(f["dir"])), "yes" if f["bond"] else ""])
with open(f"{DATA}/locations.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["wikidata", "label", "level", "country_code", "country", "lon", "lat", "hub", "films"])
    for l in sorted(locs, key=lambda l: -l["n"]):
        w.writerow([l["q"], dash(l["l"]), l["lev"], l["iso"] or "", CN(l["iso"]) if l["iso"] else "", l["lon"], l["lat"], dash(l.get("hub_n", "")), l["n"]])
with open(f"{DATA}/film_locations.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["film", "location", "location_level", "location_country", "home_or_abroad"])
    for f in films:
        for q in f["locs"]:
            l = L[q]; ha = "" if not f["has_o"] or not l["iso"] else ("home" if l["iso"] in f["oiso"] else "abroad")
            w.writerow([f["q"], q, l["lev"], l["iso"] or "", ha])
with open(f"{DATA}/countries.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["country_code", "country", "films_shot_there", "with_origin", "domestic", "foreign", "foreign_pct", "main_foreign_origins", "films_of_this_origin", "of_which_shot_abroad"])
    for r in sorted(HOST, key=lambda r: -r["n"]):
        g = og.get(r["iso"], [0, 0])
        w.writerow([r["iso"], r["name"], r["n"], r["n_o"], r["dom"], r["foreign"], round(r["foreign_pct"], 1), "; ".join(f"{x[1]} {x[2]}" for x in r["from"]), g[0], g[1]])
with open(f"{DATA}/hubs.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["hub", "country", "lon", "lat", "films", "popularity_weighted", "rank_by_films", "rank_by_weight", "locations", "foreign_pct", "most_popular_films"])
    for h in HUBS:
        w.writerow([dash(h["name"]), h["country"], h["lon"], h["lat"], h["n"], h["w"], h["rank_n"], h["rank_w"], h["n_locs"], round(h["foreign_pct"], 1), dash("; ".join(t[0] for t in h["top"][:3]))])
with open(f"{DATA}/decades.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["decade", "films", "films_with_origin_and_location_country", "shot_partly_abroad", "pct_abroad", "pct_abroad_excluding_indonesia", "us_films", "us_pct_abroad", "coproduction_pct"])
    for d in DEC:
        w.writerow([d["dec"], d["films"], d["n"], d["abroad"], round(d["pct"], 1), round(d["pct_ex_idn"], 1), d["us_n"], round(d["us_pct"], 1), round(d["co_pct"], 1)])

# ---------- page data ----------
# locations on the map (city, town, site), films, and which films used which location
mlocs = [l for l in locs if l["lev"] in ("city", "site")]
li = {l["q"]: i for i, l in enumerate(mlocs)}
coarse = [l for l in locs if l["lev"] in ("country", "region")]
ci = {l["q"]: i for i, l in enumerate(coarse)}
fl = sorted(films, key=lambda f: -f["sl"])
FR = []
for f in fl:
    ml = [li[q] for q in f["locs"] if q in li]; cc = [ci[q] for q in f["locs"] if q in ci]
    FR.append([title(f), f["y"] or 0, ",".join(f["ocode"]), f["sl"], f["q"], "; ".join(f["dir"][:2]), 1 if f["bond"] else 0, ml, cc, ",".join(f["abroad"]) if f["has_o"] else "?"])
jsave({"cols": ["title", "year", "origin", "sitelinks", "wikidata", "director", "bond", "map locations", "country or region locations", "abroad in (? = no origin)"],
       "locs": [[round(l["lon"], 4), round(l["lat"], 4), l["l"] or l["q"], l["iso"] or "", 0 if l["lev"] == "city" else 1, l["q"], l.get("hub_n", "")] for l in mlocs],
       "coarse": [[round((M[l["iso"]]["lx"] if l["lev"] == "country" and l["iso"] in M else l["lon"]), 3), round((M[l["iso"]]["ly"] if l["lev"] == "country" and l["iso"] in M else l["lat"]), 3), l["l"] or l["q"], l["iso"] or "", 0 if l["lev"] == "country" else 1, l["q"]] for l in coarse],
       "films": FR}, f"{DATA}/points.json")
SITE = {"cname": {k: v["name"] for k, v in M.items()},
        "cpos": {k: [v["lx"], v["ly"], v["pop"] or 0] for k, v in M.items()},
        "host": {r["iso"]: [r["n"], r["n_o"], r["foreign"], round(r["foreign_pct"], 1), r["from"][:3], og.get(r["iso"], [0, 0])] for r in HOST},
        "origins": [[i, CN(i), n] for i, n in oc.most_common(40)],
        "bond": [[b["t"], b["y"], b["q"]] for b in BF]}
jsave(SITE, f"{DATA}/site.json")
print("films", NF, "locs", NL, "pairs", len(pairs), "levels", dict(lev), "pair levels", dict(plev))
print("abroad", {k: (round(v, 1) if isinstance(v, float) else v) for k, v in R["abroad"].items()})
print("decades", [(d["dec"], d["n"], round(d["pct_ex_idn"]), round(d["us_pct"])) for d in DEC])
print("top foreign hosts", [(r["name"], r["foreign"], round(r["foreign_pct"])) for r in HOST[:12]])
print("top share", [(r["name"], r["n_o"], round(r["foreign_pct"])) for r in share[:15]])
print("hubs", [(h["name"], h["n"], h["w"]) for h in HUBS[:15]])
print("hubs by weight", [(h["name"], h["rank_n"], h["w"]) for h in byw[:15]])
print("risers", [(h["name"], h["rank_n"], h["rank_w"]) for h in R["hubs"]["risers"]])
print("stand-in", [(h["name"], h["country"], h["n_o"], round(h["foreign_pct"]), h["from"][:2]) for h in stand[:15]])
print("leave", [(r["name"], r["n"], round(r["pct"])) for r in ORIG[:10]], "...", [(r["name"], round(r["pct"])) for r in ORIG[-6:]])
print("pop tiers", R["pop"]["tiers"])
print("bond", R["bond"]["n_locs"], R["bond"]["n_countries"], R["bond"]["pinewood"], R["bond"]["top_locs"], R["bond"]["origin"], R["bond"]["early"], R["bond"]["late"])
print("points.json", os.path.getsize(f"{DATA}/points.json") // 1024, "KB; site", os.path.getsize(f"{DATA}/site.json") // 1024, "KB")
