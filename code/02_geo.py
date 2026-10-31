"""Geography: world outlines for the page and figures (Natural Earth 1:50m), a present-day country for every location
and every country of origin, a level for every location (country, region, city or town, site), and a filming hub for
every point that is a city, town or site.

Levels
- country: the location is itself a country (its Wikidata ID is a Natural Earth country's, or a UK nation, a former state,
  a continent or a large world region in LARGE). Its point is a centroid, so it is never drawn as a place on the map.
- region: the location is a first-level division (state, province, region) in Natural Earth admin-1, or a large area
  in LARGE. Also kept off the point map.
- city: the label matches a Natural Earth populated place in the same country within 40 km.
- site: everything else (studios, streets, buildings, parks, villages, islands, mountains...).
Location country: the present-day country its point falls in (Natural Earth 1:10m), else the Wikidata country (P17).
Hubs: every city or site is assigned to the nearest Natural Earth populated place of 250,000 people or more within 40 km,
else to itself. A hub groups a city with its studios and suburbs (Pinewood Studios counts for London).
"""
import math
from collections import Counter, defaultdict
from shapely.geometry import shape, mapping, Point
from shapely.strtree import STRtree
from common import *

# Wikidata items that are whole countries, former states, UK nations, continents or very large regions (treated as country level)
LARGE_C = {"Q21": "GBR", "Q22": "GBR", "Q25": "GBR", "Q26": "GBR", "Q15180": None, "Q36704": None, "Q33946": None,
           "Q713750": "DEU", "Q16957": "DEU", "Q46": None, "Q15": None, "Q48": None, "Q49": None, "Q18": None, "Q51": None, "Q538": None,
           "Q664609": None, "Q27449": None, "Q12542": None, "Q7204": None, "Q55": "NLD", "Q35": "DNK", "Q34": "SWE", "Q20": "NOR", "Q29999": "NLD",
           "Q756617": "DNK", "Q8646": "HKG", "Q14773": "MAC", "Q148": "CHN", "Q865": "TWN", "Q1246": "XKX", "Q23681": None}
# successor states for countries of origin that no longer exist
SUCC = {"Q15180": ["RUS", "UKR", "BLR", "GEO", "ARM", "AZE", "KAZ", "UZB", "TKM", "KGZ", "TJK", "MDA", "LTU", "LVA", "EST"],
        "Q36704": ["SRB", "HRV", "SVN", "BIH", "MKD", "MNE", "KOS"], "Q33946": ["CZE", "SVK"], "Q713750": ["DEU"], "Q16957": ["DEU"],
        "Q43287": ["DEU"], "Q41304": ["DEU"], "Q7318": ["DEU"], "Q1206012": ["DEU"], "Q172579": ["ITA"], "Q174193": ["GBR"], "Q21": ["GBR"],
        "Q22": ["GBR"], "Q25": ["GBR"], "Q26": ["GBR"], "Q1069": ["HKG"], "Q13426199": ["CHN"], "Q8733": ["CHN"], "Q34266": ["RUS"],
        "Q2184": ["RUS"], "Q29999": ["NLD"], "Q756617": ["DNK"], "Q1774": ["TZA"], "Q170072": ["NLD"], "Q12560": ["TUR"], "Q217230": ["VNM"],
        "Q180573": ["VNM"], "Q170468": ["ARE"], "Q207272": ["POL"], "Q28513": ["AUT", "HUN"], "Q153136": ["DEU"], "Q131964": ["AUT"],
        "Q218023": ["ESP"], "Q83286": ["SRB", "MNE"], "Q37024": ["SRB", "MNE"], "Q244165": ["COD"], "Q974": ["COD"], "Q1246": ["KOS"],
        "Q858": ["SYR"], "Q219060": ["PSE"], "Q176": ["CAN"], "Q2895": ["BLR"], "Q32047": ["GBR"], "Q1027": ["MUS"], "Q15102440": ["DEU"]}
iso_of = lambda p: p["ISO_A3_EH"] if p.get("ISO_A3_EH") not in ("-99", None) else p["ADM0_A3"]
FIXISO = {"CNM": "CYP", "ESB": "CYP", "WSB": "CYP", "PSX": "PSE", "SAH": "ESH", "SOL": "SOM", "KAB": "KAZ", "CYN": "CYP", "BJN": "COL", "SER": "COL", "SCR": "CHN", "USG": "CUB"}


def rnd(c, k=2):
    if isinstance(c, (list, tuple)) and c and isinstance(c[0], (int, float)):
        return [round(c[0], k), round(c[1], k)]
    return [rnd(x, k) for x in c]


W50 = jload(f"{GEO}/ne_50m_admin_0_countries.geojson")
feats, meta = [], {}
for f in W50["features"]:
    p = f["properties"]; iso = FIXISO.get(iso_of(p), iso_of(p))
    g = shape(f["geometry"]).simplify(0.05, preserve_topology=True)
    if g.is_empty:
        continue
    gm = mapping(g)
    feats.append({"type": "Feature", "properties": {"iso": iso}, "geometry": {"type": gm["type"], "coordinates": rnd(gm["coordinates"])}})
    if iso in meta:
        continue
    nm = (p["NAME_EN"] or p["NAME"]).replace("People's Republic of China", "China").replace("United States of America", "United States")
    nm = {"The Bahamas": "Bahamas", "Republic of the Congo": "Congo", "Kingdom of the Netherlands": "Netherlands", "The Gambia": "Gambia"}.get(nm, nm)
    meta[iso] = {"name": nm, "cont": p["CONTINENT"], "pop": p["POP_EST"], "lx": round(p["LABEL_X"], 2), "ly": round(p["LABEL_Y"], 2)}
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/world.json")

W10 = jload(f"{GEO}/ne_10m_admin_0_countries.geojson")
QID, geoms = {}, []
for f in W10["features"]:
    p = f["properties"]; iso = FIXISO.get(iso_of(p), iso_of(p))
    if p.get("WIKIDATAID"):
        QID[p["WIKIDATAID"]] = iso
    geoms.append((iso, shape(f["geometry"]).buffer(0)))
    if iso not in meta:
        c = shape(f["geometry"]).representative_point()
        meta[iso] = {"name": p["NAME_EN"] or p["NAME"], "cont": p["CONTINENT"], "pop": p["POP_EST"], "lx": round(c.x, 2), "ly": round(c.y, 2)}
tree = STRtree([g for _, g in geoms])


def at(lon, lat):
    pt = Point(lon, lat)
    hit = [geoms[i][0] for i in tree.query(pt) if geoms[i][1].covers(pt)]
    if hit:
        return hit[0]
    near = [(geoms[i][1].distance(pt), geoms[i][0]) for i in tree.query(pt.buffer(0.3))]
    near = [x for x in near if x[0] < 0.3]
    return min(near)[1] if near else None


def isos(qs):
    out = []
    for q in qs:
        for i in ([QID[q]] if q in QID else SUCC.get(q, [])):
            if i not in out:
                out.append(i)
    return out


A1F = jload(f"{GEO}/ne_10m_admin_1_states_provinces.geojson")["features"]
A1 = {f["properties"]["wikidataid"]: f["properties"]["name"] for f in A1F if f["properties"].get("wikidataid")}
A1N = {(f["properties"]["adm0_a3"], norm(n)) for f in A1F for n in (f["properties"]["name"], f["properties"].get("name_en")) if n}
ALIAS = {"new york city": "new york", "washington d c": "washington d c", "mexico city": "mexico city", "saint petersburg": "st petersburg",
         "kyiv": "kiev", "bengaluru": "bangalore", "mumbai": "mumbai", "chennai": "chennai", "ho chi minh city": "ho chi minh city",
         "kolkata": "kolkata", "beijing": "beijing", "gothenburg": "goteborg", "the hague": "the hague", "lisbon": "lisbon"}
AREA = {}
for f in W10["features"]:
    p = f["properties"]; g = shape(f["geometry"]); c = g.representative_point()
    k_ = FIXISO.get(iso_of(p), iso_of(p)); AREA[k_] = AREA.get(k_, 0) + g.area * 12364 * math.cos(math.radians(c.y))   # rough km2
PP = jload(f"{GEO}/ne_10m_populated_places_simple.geojson")["features"]
pp = []
for f in PP:
    p = f["properties"]
    ns = {norm(re.sub(r"\d+$", "", v)) for v in (p["name"], p["namepar"], p["namealt"], p["nameascii"], p["meganame"], p["ls_name"]) if v and len(v) > 1}
    pp.append({"name": p["namepar"] or p["name"], "ns": ns, "iso": p["adm0_a3"], "lon": p["longitude"], "lat": p["latitude"], "pop": p["pop_max"] or 0})
ppn = defaultdict(list)
for x in pp:
    for n in x["ns"]:
        ppn[n].append(x)
BIG = [x for x in pp if x["pop"] >= 250000]
bigtree = STRtree([Point(x["lon"], x["lat"]) for x in BIG])


def km(a, b, c, d):
    r = math.radians
    s = math.sin(r(b)) * math.sin(r(d)) + math.cos(r(b)) * math.cos(r(d)) * math.cos(r(a - c))
    return 6371 * math.acos(max(-1, min(1, s)))


# extra large areas that are neither countries nor in admin-1 (deserts, seas, ranges, big islands, metropolitan regions)
LARGE_R = re.compile(r"^(Sahara|Alps|Scottish Highlands|Highlands|Himalayas?|Rocky Mountains|Andes|Pacific Ocean|Atlantic Ocean|Mediterranean Sea|"
                     r"Caribbean|Caribbean Sea|Scandinavia|Patagonia|Siberia|Lapland|Arctic|Antarctica|Amazon rainforest|Middle East|Southeast Asia|"
                     r"Balkans|Riviera|French Riviera|Tuscany|Provence|Bavaria|Andalusia|Sicily|Sardinia|Corsica|Crete|Borneo|Java|Sumatra|Bali|"
                     r"Greater London|Apulia|British Columbia|Canary Islands|Basilicata|Galicia|Île-de-France|Normandy|Brittany|Mallorca|Majorca|Burgundy|Alsace|Brittany|Occitania|Catalonia|Basque Country|Lombardy|Veneto|Piedmont|Lazio|Campania|Calabria|Umbria|Liguria|Wallonia|Flanders|Scania|Lombardy|Southern California|Northern Ireland|Western Australia|Outback|Mojave Desert|Sonoran Desert|Hokkaido|Kyushu|"
                     r"Honshu|Long Island|Cape Cod|Upstate New York|New England|Midwest|Sierra Nevada|Black Sea|Baltic Sea|North Sea|Lake District|"
                     r"Yorkshire|Cornwall|Kerala|Kashmir|Rajasthan|Goa|Punjab|Gujarat|Tamil Nadu|Karnataka|Maharashtra)$", re.I)

D = jload(f"{WORK}/parsed.json")
lev, how = Counter(), Counter()
for l in D["locs"]:
    q, lab = l["q"], l["l"]
    wd = isos(l["cty"])
    iso = at(l["lon"], l["lat"])
    nl = ALIAS.get(norm(lab), norm(lab))
    cand = [x for x in ppn.get(nl, []) if km(l["lon"], l["lat"], x["lon"], x["lat"]) < 40]
    if q in QID or q in LARGE_C or (q in l["cty"]):
        iso = QID.get(q) or LARGE_C.get(q) or (wd[0] if wd else iso)
        # a city-state or small territory: its centroid is within a few km of anywhere in it, so it counts as a city
        l["lev"] = "city" if iso and AREA.get(iso, 1e9) < 1500 else "country"
        l["small"] = l["lev"] == "city"
    elif cand:
        l["lev"] = "city"
        for x in cand: x.setdefault("wd", []).append((l["n"], lab))
    elif q in A1 or (iso, norm(lab)) in A1N or LARGE_R.match(lab or ""):
        l["lev"] = "region"
    else:
        l["lev"] = "site"
    if not iso:
        iso = wd[0] if wd else None; how["country from wikidata"] += 1
    else:
        how["country from point or item"] += 1
    iso = FIXISO.get(iso, iso)
    if iso and iso not in meta:
        how["no outline " + iso] += 1
    l["iso"] = iso
    l["wd_iso"] = wd
    lev[l["lev"]] += 1
    # hub
    if l["lev"] in ("city", "site"):
        pt = Point(l["lon"], l["lat"])
        best = None
        for i in bigtree.query(pt.buffer(0.5)):
            x = BIG[i]; d = km(l["lon"], l["lat"], x["lon"], x["lat"])
            if d <= 32 and (best is None or d < best[0]):
                best = (d, x)
        if best:
            x = best[1]; l["hub"] = f"{x['name']}|{x['iso']}"; l["hub_x"] = x; l["hub_pt"] = [round(x["lon"], 3), round(x["lat"], 3)]
        else:
            l["hub"] = l["q"]; l["hub_n"] = lab; l["hub_pt"] = [l["lon"], l["lat"]]
for l in D["locs"]:
    x = l.pop("hub_x", None)
    if x is not None:
        l["hub_n"] = max(x["wd"])[1] if x.get("wd") else x["name"]
print("levels", dict(lev), dict(how))
for lv in ("country", "region", "city", "site"):
    top = sorted([l for l in D["locs"] if l["lev"] == lv], key=lambda l: -l["n"])[:14]
    print(lv, [(l["l"], l["n"], l["iso"]) for l in top])

FORMERC = {"Q15180": "SUN", "Q36704": "YUG", "Q83286": "YUG", "Q37024": "YUG", "Q33946": "CSK", "Q34266": "SUN", "Q2184": "SUN"}
for f in D["films"]:
    f["oiso"] = isos(f["orig"])                       # every present-day country that counts as home
    for par, deps in (("GBR", ["IMN", "JEY", "GGY", "GIB"]), ("USA", ["PRI", "GUM", "VIR", "ASM", "MNP"]), ("FRA", ["PYF", "NCL", "REU", "MTQ", "GLP", "GUF"]),
                      ("NLD", ["ABW", "CUW", "SXM"]), ("DNK", ["GRL", "FRO"])):
        if par in f["oiso"]:
            f["oiso"] += [d for d in deps if d not in f["oiso"]]   # crown dependencies and overseas territories count as home
    oc = []
    for q in f["orig"]:
        c = FORMERC.get(q) or (isos([q])[0] if isos([q]) else None)
        if c and c not in oc:
            oc.append(c)
    f["ocode"] = oc                                   # countries of origin as named (former states kept as such)
meta["SUN"] = {"name": "Soviet Union", "cont": "Europe", "pop": 0, "lx": 60, "ly": 58}
meta["YUG"] = {"name": "Yugoslavia", "cont": "Europe", "pop": 0, "lx": 19, "ly": 44}
meta["CSK"] = {"name": "Czechoslovakia", "cont": "Europe", "pop": 0, "lx": 17, "ly": 49.5}
unm = Counter(q for f in D["films"] for q in f["orig"] if not isos([q]))
print("unmapped origins", unm.most_common(15))
D["levels"] = dict(lev)
jsave(D, f"{WORK}/geo.json")
jsave(meta, f"{WORK}/countries.json")

cities = []
for x in pp:
    if x["pop"] >= 150000 or x["iso"] in ("ISL", "MLT", "NZL", "MAR", "JOR"):
        if x["pop"] >= 40000:
            cities.append({"name": x["name"], "lat": round(x["lat"], 3), "lon": round(x["lon"], 3), "pop": int(x["pop"])})
cities.sort(key=lambda c: -c["pop"])
jsave(cities, f"{DATA}/cities.json")
print("cities", len(cities), "countries", len(meta), "world", os.path.getsize(f"{DATA}/world.json") // 1024, "KB")
