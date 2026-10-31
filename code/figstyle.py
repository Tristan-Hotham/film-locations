"""House style for static figures: fonts (static instances cut from the variable Fraunces in /home/claude/ref/fonts,
written to WORK), the projection-room palette, and Natural Earth outlines in Equal Earth."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly
import numpy as np
from pyproj import Transformer
from common import *

FD = os.path.join(WORK, "fonts"); os.makedirs(FD, exist_ok=True)
if not os.path.exists(f"{FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    for w, nm in ((900, "Black"), (700, "Bold")):
        instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": w, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-{nm}.ttf")
DISP = fm.FontProperties(fname=f"{FD}/Fraunces-Black.ttf")
DISPB = fm.FontProperties(fname=f"{FD}/Fraunces-Bold.ttf")
SERP = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Regular.ttf")
SERB = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Semibold.ttf")
for f in ("IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
MONO = "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 12, "axes.edgecolor": "#67626A", "axes.labelcolor": "#1C1A1F",
                     "xtick.color": "#67626A", "ytick.color": "#67626A"})
BG, FG, MUT, LAND, RULE = "#F6F2EA", "#1C1A1F", "#67626A", "#E4DDD0", "#E2DBCD"
HOT, COOL, GOLD, HOME = "#A3202E", "#1F7A85", "#B8860B", "#B5A892"
RAMP = ["#F3E2B3", "#EBBE69", "#DE8A3A", "#C2512C", "#932233", "#5A1238", "#2A0B2E"]
from matplotlib.colors import LinearSegmentedColormap
CMAP = LinearSegmentedColormap.from_list("film", RAMP)


def hx(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)]) / 255


def lighten(c, t):
    c = np.array(c) if not isinstance(c, str) else hx(c)
    return c * (1 - t) + hx(BG) * t


EE = Transformer.from_crs(4326, 8857, always_xy=True)
W = jload(f"{DATA}/world.json")


def rings(geom):
    cs = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in cs:
        yield np.array(poly[0])


SHAPES = []
for f in W["features"]:
    for ring in rings(f["geometry"]):
        x, y = EE.transform(np.clip(ring[:, 0], -179.9, 179.9), ring[:, 1])
        SHAPES.append((f["properties"]["iso"], np.column_stack([x, y]), ring))
WORLD_EXT = (-12.3e6, 15.6e6, -5.9e6, 8.6e6)


def world(ax, colour_of=lambda iso: None, lw=.3, ext=WORLD_EXT, ec="#FFFFFF", land=LAND, z=1):
    for iso, p, _ in SHAPES:
        c = colour_of(iso)
        ax.add_patch(MPoly(p, closed=True, fc=land if c is None else c, ec=ec, lw=lw, zorder=z))
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal"); ax.axis("off")


def proj(lon, lat):
    return EE.transform(np.asarray(lon), np.asarray(lat))


def save(fig, name, dpi=200):
    fig.savefig(name, dpi=dpi, facecolor=fig.get_facecolor())
    plt.close(fig)


def points():
    """Mapped locations (city, town, site) with their film counts, from data/points.json."""
    P = jload(f"{DATA}/points.json")
    n = [0] * len(P["locs"]); w = [0] * len(P["locs"])
    for f in P["films"]:
        for i in f[7]:
            n[i] += 1; w[i] += f[3]
    A = np.array([[l[0], l[1], n[i], w[i]] for i, l in enumerate(P["locs"])], dtype=float)
    return A, P
