"""Build the paper: fill code/paper_template.tex from data/results.json, add tables, compile with xelatex.
Output: release/paper/<NAME>.pdf and .tex (figures f_*.png sit beside them)."""
import subprocess
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Where_Every_Film_Was_Shot"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")
assert 2.5 < R["pop"]["tiers"][3]["locs"] / R["pop"]["tiers"][0]["locs"] < 3.0


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "pc": return f"{round(float(v))}\\%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "ord": return fmt(v, "ord")
    return tex(str(v))


s = R["source"]; lv = s["lev"]; pl = s["plev"]
TP = ("\\begin{table}[tbp]\\centering\\small\\caption{From query to data.}\\label{tab:pipe}"
      "\\begin{tabular}{p{9.8cm}r}\\toprule Step & Count\\\\\\midrule\n"
      f"Rows returned by the query & {s['n_rows']:,}\\\\\n"
      f"Films & {s['n_films']:,}\\\\\n"
      f"\\quad with a year & {s['n_dated']:,}\\\\\n"
      f"\\quad with a country of origin & {s['n_origin']:,}\\\\\n"
      f"\\quad with at least one city, town or site (mapped) & {s['n_mapped']:,}\\\\\n"
      f"Filming locations & {s['n_locs']:,}\\\\\n"
      f"\\quad countries / regions / cities and towns / sites & {lv['country']:,} / {lv['region']:,} / {lv['city']:,} / {lv['site']:,}\\\\\n"
      f"Film-location pairs & {s['n_pairs']:,}\\\\\n"
      f"\\quad naming a country / region / city or town / site & {pl['country']:,} / {pl['region']:,} / {pl['city']:,} / {pl['site']:,}\\\\\n"
      "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
for r in R["hosts"]["top_foreign"][:15]:
    rows += f"{tex(r['name'])} & {r['n_o']:,} & {r['foreign']:,} & {r['foreign_pct']:.0f}\\% & {tex(', '.join(x[1] + ' ' + str(x[2]) for x in r['from'][:2]))}\\\\\n"
TH = ("\\begin{table}[tbp]\\centering\\small\\caption{Countries hosting most foreign productions: films with a known origin shot there, foreign productions, share, and main origins.}\\label{tab:hosts}"
      "\\begin{tabular}{lrrr>{\\raggedright\\arraybackslash}p{5.2cm}}\\toprule Country & Films & Foreign & Share & Main origins\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
for b in R["bond"]["films"]:
    rows += f"{b['y']} & {tex(b['t'])} & {b['n']} & {'yes' if b['pinewood'] else ''} & {tex(', '.join(b['outside_uk']) or 'none recorded')}\\\\\n"
TB = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{The 25 Eon James Bond films: recorded locations, whether Pinewood Studios is listed, and countries outside the UK.}\\label{tab:bond}"
      "\\begin{tabular}{rlrc>{\\raggedright\\arraybackslash}p{6.4cm}}\\toprule Year & Film & Places & Pinewood & Outside the UK\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
for k in ("page", "repo"):
    t = t.replace("\\url{{{meta.%s}}}" % k, "\\url{%s}" % R["meta"][k])
t = re.sub(r"\{\{(?!TABLE_)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
t = t.replace("{{TABLE_PIPELINE}}", TP).replace("{{TABLE_HOSTS}}", TH).replace("{{TABLE_BOND}}", TB)
assert "{{" not in t.replace("10.5281/zenodo.23847354", "") and "--" not in t and "\u2014" not in t and "\u2013" not in t
t = t.replace("10.5281/zenodo.23847354", "\\{\\{DOI\\}\\}")
t = t.replace("\\href{https://doi.org/\\{\\{DOI\\}\\}}", "\\href{https://doi.org/}").replace("\\url{https://doi.org/\\{\\{DOI\\}\\}}", "https://doi.org/\\{\\{DOI\\}\\}")
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("\u2014") + txt.count("\u2013") + txt.count("--"))
