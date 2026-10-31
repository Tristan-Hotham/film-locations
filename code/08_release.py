"""Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.23847354, https://doi.org/10.5281/zenodo.23847354 and https://blog.tristanhotham.com/2026/10/31/film-locations/ stay as placeholders for the publisher."""
import json as _json, shutil, zipfile
from common import *

R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release"); NAME = "Hotham_Where_Every_Film_Was_Shot"

# facts stated in words in the blog (alt text included); the page build checks the rest
import importlib.util
spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "04_build_site.py")); spec.loader.exec_module(importlib.util.module_from_spec(spec))
assert R["host_decades"]["CAN"]["2000"] == 266 and R["hosts"]["top_foreign"][1]["foreign"] == 292
assert 4 <= R["pop"]["tiers"][3]["pct"] / R["pop"]["tiers"][0]["pct"] < 4.5
st = R["hubs"]["standin"]; assert [h["name"] for h in st[:5]] == ["Valletta", "Bangkok", "Budapest", "Hamilton", "Vancouver"]
D = {d["dec"]: d for d in R["decades"]}; assert all(10 <= D[d]["pct_ex_idn"] <= 16 for d in (1920, 1930, 1940)) and all(23 <= D[d]["pct_ex_idn"] <= 26 for d in (2000, 2010, 2020))
pl = R["source"]["plev_pct"]; assert [round(pl[k]) for k in ("city", "site", "country", "region")] == [37, 29, 20, 14]
post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG|DOI_URL|BLOG_URL|DOI\}\})([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(R, m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert "wp:image" not in post and all(l.startswith("{{IMG|") and l.endswith("}}") for l in post.splitlines() if "{{IMG|" in l)
for bad in ("DSIT", "DCMS", "civil serv"):
    assert bad not in post
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--"):
    assert bad not in vis, bad
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
meta = {"title": "Where every film was shot: film cities, foreign productions and James Bond on one map",
        "slug": "film-locations",
        "excerpt": f"I mapped the filming locations of {R['source']['n_films']:,} films in Wikidata: Los Angeles, New York, London and Paris lead, Canada hosts the most foreign productions, and the 25 Eon Bond films visited {R['bond']['n_countries']} countries and territories.",
        "seo_description": "A map of where films were shot, from Wikidata: the busiest film cities, which countries host foreign productions, and every James Bond location.",
        "tags": ["film", "cinema", "filming locations", "James Bond", "maps", "data visualisation", "Wikidata"],
        "header_alt": f"Title card reading 'Where every film was shot' in black, red and teal on cream, beside a world map of small hexagons shaded yellow to dark purple, densest in the United States and western Europe. Text: {R['source']['n_films']:,} films and {R['source']['n_locs']:,} filming locations in Wikidata, from Los Angeles to Pinewood, plus every Bond location."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# Zenodo
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/film-locations_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("code", "data"):
        for fn in sorted(os.listdir(os.path.join(ROOT, d))):
            if fn.endswith(".pyc") or fn == "__pycache__":
                continue
            z.write(os.path.join(ROOT, d, fn), f"film-locations/{d}/{fn}")
    for fn in ("README.md", "LICENSE"):
        if os.path.exists(os.path.join(ROOT, fn)):
            z.write(os.path.join(ROOT, fn), f"film-locations/{fn}")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&")
zmeta = {"title": "Where Every Film Was Shot: Filming Locations of Films in Wikidata, Film Cities, Foreign Productions and the James Bond Films",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {BLOG}.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["film", "filming locations", "runaway production", "film geography", "James Bond", "Wikidata", "open data", "maps"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "https://www.wikidata.org/", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://www.naturalearthdata.com/", "relation": "isDerivedFrom", "resource_type": "dataset"}],
         "files": sorted(os.listdir(Z))}
s = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in s and "\u2013" not in s and "--" not in s
jsave(zmeta, f"{Z}/metadata.json", indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
