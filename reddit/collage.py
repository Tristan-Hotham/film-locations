"""r/dataisbeautiful collage for film-locations: 2400 x 3200 px, light background. Numbers from data/results.json."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
from figstyle import *
from matplotlib.colors import LogNorm
import matplotlib.patheffects as pe

R = jload(f"{DATA}/results.json")
A, P = points()
BGc = "#F7F4EC"
HALO = [pe.withStroke(linewidth=4, foreground=BGc)]
fig = plt.figure(figsize=(12, 16), dpi=200, facecolor=BGc)
fig.text(.045, .975, "Where every film was shot", fontproperties=DISP, fontsize=50, color=FG, va="top")
fig.text(.045, .928, f"{R['source']['n_films']:,} films and {R['source']['n_locs']:,} filming locations in Wikidata. Hexagons count film-location records at\ncities, towns and sites; locations that are a whole country or state are left off the map so they do not make fake hotspots.",
         fontproperties=SERP, fontsize=14.5, color=FG, va="top", linespacing=1.45)

# main map
ax = fig.add_axes([0, .53, 1, .35])
ext = (-12.6e6, 15.6e6, -6.2e6, 8.6e6)
world(ax, lw=.3, ext=ext, ec=BGc, land="#E3DED2")
X, Y = proj(A[:, 0], A[:, 1]); m = A[:, 2] > 0
hb = ax.hexbin(X[m], Y[m], C=A[m, 2], reduce_C_function=np.sum, gridsize=170, extent=ext, cmap=CMAP, norm=LogNorm(1, 2000), mincnt=1, lw=0, zorder=3)
H = {h["name"]: h for h in R["hubs"]["top"]}
H.update(R["hubs"]["pick"])
LAB = [("Los Angeles", -128, 14), ("Vancouver", -140, 40), ("New York City", -58, 23), ("London", -27, 59), ("Paris", -27, 46),
       ("Ooty", 70, -6), ("Hong Kong", 130, 12), ("Rio de Janeiro", -15, -30), ("Toronto", -41, 33)]
for nm, lx, ly in LAB:
    h = H[nm]
    x0, y0 = proj(h["lon"], h["lat"]); x1, y1 = proj(lx, ly)
    ax.annotate(f"{nm}\n{h['n']:,} films", xy=(x0, y0), xytext=(x1, y1), fontsize=10.5, color=FG, ha="center", va="center", family=MONO, linespacing=1.15,
                arrowprops=dict(arrowstyle="-", color=FG, lw=.7, shrinkA=2, shrinkB=2), zorder=6, path_effects=HALO)
    ax.plot([x0], [y0], "o", ms=3.5, mfc="none", mec=FG, mew=.9, zorder=7)
for t, lo, la in (("PACIFIC OCEAN", -125, -20), ("ATLANTIC OCEAN", -32, 8), ("INDIAN OCEAN", 80, -25)):
    x, y = proj(lo, la); ax.text(x, y, t, fontsize=10, color="#9A948A", ha="center", family=MONO, style="italic", zorder=4)
cax = fig.add_axes([.47, .555, .18, .009]); cb = fig.colorbar(hb, cax=cax, orientation="horizontal")
cb.set_ticks([1, 10, 100, 1000]); cb.set_ticklabels(["1", "10", "100", "1,000+"]); cb.outline.set_visible(False); cax.tick_params(labelsize=9.5, length=0)
cax.set_title("film-location records per hexagon (log scale)", fontsize=9.5, color=MUT, loc="left", pad=3)

# numbers row
nums = [(f"{R['hubs']['la']['n']:,}", HOT, "films shot in and around\nLos Angeles, the busiest\nfilming city in the record"),
        (f"{R['hosts']['can']['foreign']:,}", COOL, f"foreign films shot in\nCanada, the top host;\n{R['hosts']['can_from_us_pct']:.0f}% are American"),
        (f"{R['hosts']['mlt']['foreign_pct']:.0f}%", COOL, "of films shot in Malta\nare foreign productions\n(Morocco " + f"{R['hosts']['mar']['foreign_pct']:.0f}%, Iceland {R['hosts']['isl']['foreign_pct']:.0f}%)"),
        (f"{R['source']['plev_pct']['country'] + R['source']['plev_pct']['region']:.0f}%", "#6E6458", "of film-location records\nname only a whole country\nor state: not mapped")]
for i, (big, col, small) in enumerate(nums):
    xx = .045 + i * .235
    fig.text(xx, .505, big, fontproperties=DISP, fontsize=40, color=col, va="top")
    fig.text(xx, .458, small, family=MONO, fontsize=11, color=FG, va="top", linespacing=1.45)

# bottom left: cities
Ht = R["hubs"]["top"][:12]
a1 = fig.add_axes([.17, .085, .25, .27]); a1.set_facecolor(BGc)
ys = np.arange(len(Ht))[::-1]
a1.barh(ys, [h["n"] for h in Ht], color=HOT, height=.72)
a1.set_yticks(ys); a1.set_yticklabels([h["name"] for h in Ht], fontsize=10)
for y, h in zip(ys, Ht): a1.text(h["n"] + 25, y, f"{h['n']:,}", va="center", fontsize=9.5)
a1.set_xlim(0, 2000); a1.set_xticks([]); [a1.spines[s].set_visible(False) for s in ("top", "right", "bottom")]
a1.set_title("Busiest filming cities\n(films within 32 km)", family=MONO, fontsize=12, color=FG, loc="left", pad=8, x=-.55)

# bottom middle: home vs abroad
T = R["hosts"]["top_foreign"][:10]
a2 = fig.add_axes([.57, .085, .17, .27]); a2.set_facecolor(BGc)
ys = np.arange(len(T))[::-1]
dom = np.array([100 - r["foreign_pct"] for r in T]); fr = np.array([r["foreign_pct"] for r in T])
a2.barh(ys, dom, color=HOME, height=.72); a2.barh(ys, fr, left=dom, color=COOL, height=.72)
a2.set_yticks(ys); a2.set_yticklabels([r["name"].replace("United States", "USA").replace("United Kingdom", "UK").replace("Czech Republic", "Czechia") for r in T], fontsize=10)
for y, r in zip(ys, T): a2.text(102, y, f"{r['foreign']:,}", va="center", fontsize=9.5, color=COOL)
a2.set_xlim(0, 100); a2.set_xticks([0, 50, 100]); a2.set_xticklabels(["0%", "50%", "100%"], fontsize=9); [a2.spines[s].set_visible(False) for s in ("top", "right")]
a2.set_title("Home or abroad?\nTop hosts of foreign films", family=MONO, fontsize=12, color=FG, loc="left", pad=8, x=-.52)
fig.text(.44, .062, "share of films shot there:", family=MONO, fontsize=9.5, color=FG)
fig.patches.append(plt.Rectangle((.645, .062), .012, .008, transform=fig.transFigure, color=HOME)); fig.text(.66, .062, "own", family=MONO, fontsize=9.5)
fig.patches.append(plt.Rectangle((.69, .062), .012, .008, transform=fig.transFigure, color=COOL)); fig.text(.705, .062, "foreign (count right)", family=MONO, fontsize=9.5)

# bottom right: Bond inset
a3 = fig.add_axes([.79, .25, .2, .1])
world(a3, lw=.15, ext=(-11.5e6, 14e6, -4.5e6, 8e6), ec=BGc, land="#E3DED2")
for b in R["bond"]["films"]:
    pts = [l for l in b["locs"] if l[1] in ("city", "site")]
    if pts:
        x, y = proj([l[3] for l in pts], [l[4] for l in pts]); a3.scatter(x, y, s=10, color=GOLD, edgecolor=FG, lw=.3, zorder=5)
fig.text(.8, .355, "007: the Bond films", family=MONO, fontsize=12, color=FG)
fig.text(.8, .24, f"The 25 Eon films list\n{R['bond']['n_locs']} places in {R['bond']['n_countries']} countries\nand territories. Pinewood\nfor {R['bond']['pinewood']} of 25. Spectre has\n{R['bond']['most']['n']} places, Licence to\nKill {R['bond']['fewest']['n']}: early films are\nless documented.", family=MONO, fontsize=9.5, color=FG, va="top", linespacing=1.4)

fig.text(.045, .012, "Source: Wikidata (CC0) via QLever, films (Q11424) with a filming location (P915) with coordinates, 2026; Natural Earth (public domain). Abroad = location\n"
         "outside every country of origin (P495). Coverage is skewed to American and well-known films; locations are incomplete. Bond: Eon films 1962 to 2021.\n"
         "Analysis and chart: Tristan Hotham, with Python and matplotlib  ·  maps.tristanhotham.com/film-locations", family=MONO, fontsize=8.6, color=MUT, linespacing=1.55, va="bottom")
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "where_every_film_was_shot.png")
fig.savefig(out, facecolor=BGc, dpi=200)
print("ok", out)
