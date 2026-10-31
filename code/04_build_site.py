"""Build index.html from code/page_template.html. Every number in the text is a {{path|format}} token filled from
data/results.json; page data (results, site.json, world.json, cities) is embedded; data/points.json is loaded by the page.
Facts stated in words are checked here. The full-screen map snippet (code/fullscreen_snippet.html) is pasted before </body>."""
import json
from common import *

R = jload(f"{DATA}/results.json")
SITE = jload(f"{DATA}/site.json")


def check():
    h = R["hubs"]; top = [x["name"] for x in h["top"]]
    assert top[:5] == ["Los Angeles", "New York City", "London", "Paris", "Vancouver"], top[:5]
    P = h["pick"]
    assert P["Long Beach"]["rank_w"] < P["Long Beach"]["rank_n"] and P["Hong Kong"]["rank_w"] > P["Hong Kong"]["rank_n"]
    assert P["Ooty"]["rank_w"] > 20 and P["Ooty"]["foreign_pct"] < 5
    wtop = {x["name"]: x for x in h["top_w"]}
    assert "Malibu" in wtop and "San Diego" in wtop and wtop["Malibu"]["rank_w"] < wtop["Malibu"]["rank_n"] and wtop["San Diego"]["rank_w"] < wtop["San Diego"]["rank_n"]
    assert R["sites"]["top"][0]["name"] == "Pinewood Studios" and R["sites"]["top"][0]["hub"] == "London"
    tf = [x["iso"] for x in R["hosts"]["top_foreign"]]
    assert tf[:6] == ["CAN", "USA", "GBR", "FRA", "ESP", "MEX"], tf[:6]
    assert R["hosts"]["can"]["from"][0][0] == "USA"
    sh = [x["iso"] for x in R["hosts"]["top_share"]]
    assert sh[0] == "MLT" and {"MAR", "BGR", "ISL"} <= set(sh[:10])
    assert R["hosts"]["usa"]["foreign_pct"] < 10 and R["hosts"]["idn"]["foreign_pct"] < 2
    st = [x["name"] for x in h["standin"]]
    assert st[0] == "Valletta" and {"Budapest", "Vancouver", "Toronto"} <= set(st[:10]), st
    D = {d["dec"]: d for d in R["decades"]}
    assert R["decades"][4]["dec"] == 1950 and R["decades"][5]["dec"] == 1960 and R["decades"][9]["dec"] == 2000 and R["decades"][10]["dec"] == 2010
    assert D[2000]["pct_ex_idn"] > D[1950]["pct_ex_idn"] and D[1960]["us_pct"] > 25
    assert R["host_peak"]["ESP"] == "1960" and R["host_peak"]["CAN"] == "2000" and R["host_peak"]["BGR"] == "2000" and R["host_peak"]["HUN"] == "2010" and R["host_peak"]["ISL"] == "2010"
    assert R["leave"]["gbr"]["pct"] > R["leave"]["usa"]["pct"] > R["leave"]["fra"]["pct"]
    b = R["bond"]; bc = b["countries"]
    assert [c[0] for c in bc[:2]] == ["GBR", "USA"] and {c[0] for c in bc[2:5]} == {"CHE", "ITA", "BHS"} and bc[2][2] == bc[4][2] and bc[5][0] == "ESP"
    assert b["films"][0]["t"] == "Dr. No" and b["films"][24]["t"] == "No Time to Die" and b["most"]["t"] == "Spectre" and b["fewest"]["t"] == "Licence to Kill"
    gf = next(x for x in b["films"] if x["t"] == "Goldfinger"); assert {"CHE", "USA"} <= set(gf["countries"])
    assert R["origins"]["top"][0]["iso"] == "USA" and R["origins"]["top"][1]["iso"] == "IDN"
    assert R["idn"]["idn_origin_pct"] > 95
    assert R["pop"]["tiers"][3]["pct"] > R["pop"]["tiers"][0]["pct"] and R["pop"]["tiers"][3]["locs"] > R["pop"]["tiers"][0]["locs"]
    assert R["hubs"]["pick"]["Wellington"]["n"] < 10 and R["hosts"]["nzl"]["n"] > 200


check()


def build():
    tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
    html = re.sub(r"\{\{([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(R, m.group(1)), m.group(3)), tpl)
    J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    html = html.replace("/*RESULTS*/", J(R)).replace("/*SITE*/", J(SITE))
    html = html.replace("/*WORLD*/", open(f"{DATA}/world.json", encoding="utf-8").read())
    html = html.replace("/*CITIES*/", J([{"name": x["name"], "lat": x["lat"], "lon": x["lon"], "pop": x["pop"]} for x in jload(f"{DATA}/cities.json")]))
    html = html.replace("/*FULLSCREEN*/", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
    assert "{{" not in re.sub(r"<script.*?</script>", "", html, flags=re.S).replace("10.5281/zenodo.23847354", "").replace("https://blog.tristanhotham.com/2026/10/31/film-locations/", "")
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--", "DSIT", "DCMS"):
        assert bad not in vis, bad
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")


if __name__ == "__main__":
    build()
