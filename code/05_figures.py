"""Header card, blog figures (release/blog/b_*.png) and paper figures (release/paper/f_*.png)."""
from matplotlib.colors import LogNorm
from matplotlib.patches import Patch
from figstyle import *
from matplotlib.colors import LinearSegmentedColormap

R = jload(f"{DATA}/results.json"); SITE = jload(f"{DATA}/site.json")
A, P = points()
BL = os.path.join(ROOT, "release", "blog"); PA = os.path.join(ROOT, "release", "paper")
os.makedirs(BL, exist_ok=True); os.makedirs(PA, exist_ok=True)
X, Y = proj(A[:, 0], A[:, 1])
CN = lambda i: SITE["cname"].get(i, i)


def both(fig, name):
    fig.savefig(os.path.join(PA, "f_" + name + ".png"), dpi=200, facecolor=fig.get_facecolor())
    fig.savefig(os.path.join(BL, "b_" + name + ".png"), dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)


def spines(ax):
    for s in ("top", "right"): ax.spines[s].set_visible(False)


def density(ax, ext=WORLD_EXT, grid=150, alpha=.92):
    m = A[:, 2] > 0
    hb = ax.hexbin(X[m], Y[m], C=A[m, 2], reduce_C_function=np.sum, gridsize=grid, extent=ext, cmap=CMAP, norm=LogNorm(1, 2000), mincnt=1, lw=0, alpha=alpha, zorder=3)
    return hb


# 1. world density map
fig = plt.figure(figsize=(12, 6.7), facecolor=BG)
ax = fig.add_axes([0, .1, 1, .9])
world(ax, lw=.3)
hb = density(ax)
cax = fig.add_axes([.5, .085, .36, .02]); cb = fig.colorbar(hb, cax=cax, orientation="horizontal")
cb.set_ticks([1, 10, 100, 1000]); cb.set_ticklabels(["1", "10", "100", "1,000+"]); cb.outline.set_visible(False); cax.tick_params(labelsize=10, length=0)
cax.set_title("film-location records per hexagon (log scale)", fontsize=10, color=MUT, loc="left", pad=3)
fig.text(.5, .012, ha="center", s=f"{R['source']['n_mapped']:,} films with a city, town or site as a filming location in Wikidata. Whole countries and states are not mapped.", fontsize=9.5, color=MUT)
both(fig, "world")

# 2. busiest filming cities
H = R["hubs"]["top"][:20]
fig, ax = plt.subplots(figsize=(10, 7.2), facecolor=BG); ax.set_facecolor(BG)
ys = np.arange(len(H))[::-1]
ax.barh(ys, [h["n"] for h in H], color=HOT, height=.72)
ax.set_yticks(ys); ax.set_yticklabels([(h['name'] if h['name'] == h['country'] else f"{h['name']}, {h['country']}").replace("United States", "US").replace("United Kingdom", "UK") for h in H], fontsize=10)
for y, h in zip(ys, H):
    ax.text(h["n"] + 15, y, f"{h['n']:,}", va="center", fontsize=9.5)
    ax.text(1780, y, f"#{h['rank_w']}", va="center", ha="right", fontsize=9.5, color=GOLD)
ax.text(1780, len(H) - .2, "rank by\npopularity", ha="right", va="bottom", fontsize=9, color=GOLD)
ax.set_xlim(0, 1800); ax.set_xlabel("films with a filming location within 32 km"); spines(ax)
fig.tight_layout()
both(fig, "cities")

# 3. hosts: own and foreign (top 15) and share
T = R["hosts"]["top_foreign"][:15]; S_ = R["hosts"]["top_share"][:15]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.5, 6.4), facecolor=BG, gridspec_kw={"width_ratios": [1.25, 1], "wspace": .62})
for a in (a1, a2): a.set_facecolor(BG); spines(a)
ys = np.arange(len(T))[::-1]
a1.barh(ys, [r["foreign"] for r in T], color=COOL, height=.72)
a1.set_xlim(0, 1050)
a1.set_yticks(ys); a1.set_yticklabels([r["name"] for r in T], fontsize=10)
for y, r in zip(ys, T):
    a1.text(r["foreign"] + 12, y, f"{r['foreign']:,} of {r['n_o']:,}", va="center", fontsize=9.5)
a1.set_xlabel("foreign productions shot there (of all films shot there)"); a1.set_title("Most foreign productions hosted", loc="left", fontproperties=SERB, fontsize=14)
ys = np.arange(len(S_))[::-1]
a2.barh(ys, [r["foreign_pct"] for r in S_], color=COOL, height=.72)
a2.set_yticks(ys); a2.set_yticklabels([r["name"] for r in S_], fontsize=10); a2.set_xlim(0, 115)
for y, r in zip(ys, S_):
    a2.text(r["foreign_pct"] + 1.5, y, f"{r['foreign_pct']:.0f}%", va="center", fontsize=9.5)
a2.set_xticks([0, 25, 50, 75, 100]); a2.set_xlabel("share of films shot there that are foreign")
a2.set_title("Where foreign films are the majority", loc="left", fontproperties=SERB, fontsize=14)
fig.subplots_adjust(left=.13, right=.97, top=.92, bottom=.12)
both(fig, "hosts")

# 4. decades
D = [d for d in R["decades"] if d["dec"] >= 1920]
HD = R["host_decades"]; ds = ["1950", "1960", "1970", "1980", "1990", "2000", "2010", "2020"]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.5, 5.2), facecolor=BG, gridspec_kw={"wspace": .25})
for a in (a1, a2): a.set_facecolor(BG); spines(a); a.grid(axis="y", color=RULE); a.set_axisbelow(True)
xs = np.arange(len(D))
a1.plot(xs, [d["pct_ex_idn"] for d in D], "-o", color=HOT, lw=2.4, ms=5, label="all films (excl. Indonesia)")
a1.plot(xs, [d["us_pct"] for d in D], "-o", color=COOL, lw=2.4, ms=5, label="American films")
a1.set_xticks(xs[::2]); a1.set_xticklabels([f"{d['dec']}s" for d in D][::2], fontsize=10); a1.set_ylim(0, 40)
a1.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{int(v)}%"))
a1.set_title("Films shot at least partly abroad", loc="left", fontproperties=SERB, fontsize=14); a1.legend(frameon=False, fontsize=9.5, loc="upper left")
COLS = [("CAN", COOL), ("GBR", HOT), ("ESP", "#D98A2B"), ("BGR", "#6A4C93"), ("HUN", "#3E7D3A"), ("MAR", GOLD)]
xs = np.arange(len(ds))
ends = []
for iso, c in COLS:
    v = [HD[iso][d] for d in ds]; a2.plot(xs, v, "-o", color=c, lw=2.2, ms=4); ends.append([v[-1], iso, c])
ends.sort()
for k in range(1, len(ends)):
    ends[k][0] = max(ends[k][0], ends[k - 1][0] + 13)
for yv, iso, c in ends:
    a2.text(xs[-1] + .15, yv, CN(iso), color=c, fontsize=9.5, va="center")
a2.text(xs[-1], -22, "to 2026", ha="center", fontsize=8.5, color=MUT)
a2.set_xticks(xs); a2.set_xticklabels([d + "s" for d in ds], fontsize=9.5); a2.set_xlim(-.3, len(ds) + .9)
a2.set_title("Foreign productions hosted, per decade", loc="left", fontproperties=SERB, fontsize=14)
fig.subplots_adjust(left=.06, right=.97, top=.9, bottom=.1)
both(fig, "decades")

# 5. stand-in cities
St = R["hubs"]["standin"][:15]
fig, ax = plt.subplots(figsize=(10, 6.6), facecolor=BG); ax.set_facecolor(BG); spines(ax)
ys = np.arange(len(St))[::-1]
ax.barh(ys, [h["foreign_pct"] for h in St], color=COOL, height=.72)
ax.set_yticks(ys); ax.set_yticklabels([h['name'] if h['name'] == h['country'] else f"{h['name']}, {h['country']}" for h in St], fontsize=10)
for y, h in zip(ys, St):
    fr = ", ".join(f"{x[1].replace('United States', 'US').replace('United Kingdom', 'UK')} {x[2]}" for x in h["from"][:2])
    ax.text(h["foreign_pct"] + 1.2, y, f"{h['foreign_pct']:.0f}% of {h['n_o']}  ({fr})", va="center", fontsize=9)
ax.set_xlim(0, 150); ax.set_xticks([0, 25, 50, 75, 100]); ax.set_xlabel("share of films shot there that are foreign productions")
fig.tight_layout()
both(fig, "standin")

# 6. Bond map
B = R["bond"]["films"]
fig = plt.figure(figsize=(12, 6.9), facecolor=BG)
ax = fig.add_axes([0, .08, 1, .9])
bc = {c[0]: c[2] for c in R["bond"]["countries"]}
world(ax, lambda iso: lighten(GOLD, 1 - min(1, .25 + bc[iso] / 10)) if iso in bc else None, lw=.3, ext=(-12.5e6, 15.2e6, -5.6e6, 8.4e6))
cmap = LinearSegmentedColormap.from_list("bond", ["#1F7A85", "#B8860B", "#A3202E", "#2A0B2E"])
for b in B:
    pts = [l for l in b["locs"] if l[1] in ("city", "site")]
    if not pts: continue
    x, y = proj([l[3] for l in pts], [l[4] for l in pts])
    ax.scatter(x, y, s=26, color=cmap((b["y"] - 1962) / (2021 - 1962)), edgecolor="#1C1A1F", lw=.5, zorder=5)
cax = fig.add_axes([.06, .06, .3, .022])
cax.imshow(np.array([[cmap(t) for t in np.linspace(0, 1, 100)]]), aspect="auto", extent=(1962, 2021, 0, 1)); cax.set_yticks([]); cax.set_xticks([1962, 1980, 2000, 2021]); cax.tick_params(labelsize=9.5, length=0)
for s_ in cax.spines.values(): s_.set_visible(False)
cax.set_title("dots: places, by film year", fontsize=10, color=MUT, loc="left", pad=3)
fig.text(.42, .075, f"Countries shaded by how many of the 25 Eon films list a location there\n(UK {bc['GBR']}, US {bc['USA']}, Switzerland, Italy and Bahamas {bc['CHE']} each).\nDots are cities, towns and sites; whole-country entries count only in the shading.", fontsize=9.5, color=MUT, va="center", linespacing=1.4)
both(fig, "bond")

# 7. coverage
fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(13.5, 5.2), facecolor=BG, gridspec_kw={"wspace": .8, "width_ratios": [1, 1, .9]})
for a in (a1, a2, a3): a.set_facecolor(BG); spines(a)
p = R["source"]["plev"]; n = R["source"]["n_pairs"]
lv = [("site", "Sites", HOT), ("city", "Cities, towns", "#D98A2B"), ("region", "States, regions", "#9A8A74"), ("country", "Whole countries", "#6E6458")]
a1.barh(range(4)[::-1], [p[k] for k, _, _ in lv], color=[c for _, _, c in lv], height=.7); a1.set_yticks(range(4)[::-1]); a1.set_yticklabels([nm for _, nm, _ in lv], fontsize=10)
for y, (k, _, _) in zip(range(4)[::-1], lv): a1.text(p[k] + 200, y, f"{100 * p[k] / n:.0f}%", va="center", fontsize=9.5)
a1.set_xlim(0, 17000); a1.set_xticks([0, 5000, 10000, 15000]); a1.set_title("What the location is", loc="left", fontproperties=SERB, fontsize=13); a1.set_xlabel("film-location records"); a1.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{int(v/1000)}k"))
O = R["origins"]["top"][:8]
a2.barh(range(len(O))[::-1], [o["n"] for o in O], color=HOT, height=.7); a2.set_yticks(range(len(O))[::-1]); a2.set_yticklabels([o["name"] for o in O], fontsize=10)
for y, o in zip(range(len(O))[::-1], O): a2.text(o["n"] + 150, y, f"{o['pct']:.0f}%", va="center", fontsize=9.5)
a2.set_xlim(0, 12500); a2.set_xticks([0, 4000, 8000, 12000]); a2.set_title("Where the films come from", loc="left", fontproperties=SERB, fontsize=13); a2.set_xlabel("films"); a2.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{int(v/1000)}k"))
Tt = R["pop"]["tiers"]; labs = ["0 to\n4", "5 to\n19", "20 to\n49", "50\nor more"]
a3.bar(range(4), [t["pct"] for t in Tt], color=COOL, width=.7); a3.set_xticks(range(4)); a3.set_xticklabels(labs, fontsize=10)
for i, t in enumerate(Tt): a3.text(i, t["pct"] + 1, f"{t['pct']:.0f}%\n{t['locs']:.1f} loc.", ha="center", fontsize=9)
a3.set_ylim(0, 60); a3.set_xlabel("sitelinks (popularity)"); a3.set_title("Shot abroad, by popularity", loc="left", fontproperties=SERB, fontsize=13)
a3.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{int(v)}%"))
fig.subplots_adjust(left=.14, right=.98, top=.88, bottom=.2)
both(fig, "coverage")

# header card 1200 x 630
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
ax = fig.add_axes([.34, .04, .66, .92])
world(ax, lw=.25, ext=(-12.0e6, 15.0e6, -5.5e6, 8.4e6))
density(ax, ext=(-12.0e6, 15.0e6, -5.5e6, 8.4e6), grid=110)
fig.text(.045, .87, "Where", fontproperties=DISP, fontsize=50, color=FG, va="top")
fig.text(.045, .74, "every film", fontproperties=DISP, fontsize=50, color=HOT, va="top")
fig.text(.045, .61, "was shot", fontproperties=DISP, fontsize=50, color=COOL, va="top")
fig.text(.045, .44, f"{R['source']['n_films']:,} films and {R['source']['n_locs']:,} filming\nlocations in Wikidata, from Los Angeles\nto Pinewood, plus every Bond location.", fontproperties=SERP, fontsize=15.5, color=FG, va="top", linespacing=1.3)
fig.text(.045, .14, "hexagons: filming locations, darker = more films", fontsize=9.5, color=MUT)
fig.text(.045, .04, "maps.tristanhotham.com/film-locations", fontsize=11, color=MUT)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=BG)
plt.close(fig)
print("figures done", sorted(os.listdir(BL)), sorted(x for x in os.listdir(PA) if x.endswith(".png")))
