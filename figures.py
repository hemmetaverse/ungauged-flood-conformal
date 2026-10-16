"""Tables and figures for the manuscript from conformal.py outputs."""
import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch

import conformal as C

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False,
                     "axes.spines.right": False, "savefig.dpi": 300})
COL = {"QR": "#9e9e9e", "SCP": "#bcaaa4", "CQR": "#64b5f6", "CQR-r": "#1e88e5",
       "RC-CQR": "#7cb342", "DW-CQR": "#ffb300", "DRC-CQR": "#d81b60"}
SCHEME = {"pub": "Random basin holdout (PUB)", "region": "Regional holdout (shift)"}


def summarise(res, scheme, alpha):
    df = pd.read_csv(os.path.join(res, f"metrics_{scheme}_a{int(round(alpha * 100)):02d}.csv"), dtype={"basin": str})
    g = df.groupby("method")
    reg = pd.concat([g[f"cov_reg{r}"].mean() for r in range(5)], axis=1)
    t = pd.DataFrame({
        "Coverage": g["cov"].mean(),
        "Coverage Q95+": g["cov_q95"].mean(),
        "Coverage Q99+": g["cov_q99"].mean(),
        "Missed above Q95+": g["under_q95"].mean(),
        "Regime gap": reg.max(axis=1) - reg.min(axis=1),
        "Rel. width": g["relwidth"].median(),
        "Rel. width Q95+": g["relwidth_q95"].median(),
        "Winkler (median)": g["winkler"].median(),
        "Winkler (mean)": g["winkler"].mean(),
        "Basins under-covered (%)": g["cov"].apply(lambda x: 100 * (x < (1 - alpha) - 0.05).mean()),
    }).loc[C.METHODS]
    return df, t


def fig_framework(path):
    fig, ax = plt.subplots(figsize=(7.2, 3.1))
    ax.axis("off")
    boxes = [
        (0.01, 0.55, 0.2, 0.36, "Donor basins\n(gauged)\nforcing + attributes\n+ discharge", "#e3f2fd"),
        (0.01, 0.08, 0.2, 0.36, "Target basin\n(ungauged)\nforcing + attributes\nno discharge", "#fce4ec"),
        (0.27, 0.55, 0.2, 0.36, "Regional quantile\nLSTM\n(pinball loss,\n11 quantiles)", "#ede7f6"),
        (0.53, 0.55, 0.2, 0.36, "Out-of-fold donor\nscores (1999-2008)\nwidth-normalised\nCQR residuals", "#fff8e1"),
        (0.53, 0.08, 0.2, 0.36, "Gauge-free context\n- simulated flow regime\n- attribute-space\n  donor neighbours", "#f1f8e9"),
        (0.79, 0.30, 0.2, 0.40, "DRC-CQR interval\nweighted, regime-\nconditional quantile\nof donor scores", "#fde0dc"),
    ]
    for x, y, w, h, txt, c in boxes:
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.01", fc=c, ec="#455a64", lw=0.8))
        ax.text(x + w / 2, y + h / 2, txt, ha="center", va="center", fontsize=6.8)
    arr = dict(arrowstyle="-|>", color="#455a64", lw=0.9)
    for (x0, y0), (x1, y1) in [((0.21, 0.73), (0.27, 0.73)), ((0.47, 0.73), (0.53, 0.73)),
                               ((0.21, 0.26), (0.53, 0.26)), ((0.37, 0.55), (0.6, 0.44)),
                               ((0.73, 0.73), (0.79, 0.6)), ((0.73, 0.26), (0.79, 0.4))]:
        ax.annotate("", (x1, y1), (x0, y0), arrowprops=arr)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def fig_map(data, path):
    d = np.load(data, allow_pickle=True)
    huc = d["huc"]
    reg = np.zeros(len(huc), int)
    for i, v in enumerate(C_REGIONS.values()):
        reg[np.isin(huc, v)] = i
    fig, ax = plt.subplots(figsize=(6.5, 3.4))
    cmap = plt.get_cmap("tab10")
    for i, name in enumerate(C_REGIONS):
        m = reg == i
        ax.scatter(d["lon"][m], d["lat"][m], s=9, color=cmap(i), label=f"{name.replace('_', ' ')} (n={m.sum()})")
    ax.set_xlabel("Longitude (°)")
    ax.set_ylabel("Latitude (°)")
    ax.legend(fontsize=6.5, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=3, markerscale=1.5)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def fig_regime(res, alpha, path):
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.9), sharey=True)
    for ax, sch in zip(axes, ["pub", "region"]):
        df, _ = summarise(res, sch, alpha)
        x = np.arange(5)
        for j, m in enumerate(["QR", "CQR", "CQR-r", "RC-CQR", "DRC-CQR"]):
            v = [df[df.method == m][f"cov_reg{r}"].mean() for r in range(5)]
            ax.plot(x, v, "-o", ms=3, color=COL[m], label=m)
        ax.axhline(1 - alpha, color="k", ls="--", lw=0.8)
        ax.set_xticks(x, C.REGIME_NAMES)
        ax.set_xlabel("Simulated-flow regime (percentile)")
        ax.set_title(SCHEME[sch], fontsize=9)
    axes[0].set_ylabel("Mean basin coverage")
    axes[1].legend(fontsize=7, frameon=False, loc="lower left")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def fig_tradeoff(res, alpha, path):
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.9), sharey=True)
    for ax, sch in zip(axes, ["pub", "region"]):
        _, t = summarise(res, sch, alpha)
        for m in C.METHODS:
            ax.scatter(t.loc[m, "Rel. width"], t.loc[m, "Winkler (mean)"], color=COL[m], s=34, zorder=3,
                       label=m, edgecolor="k", lw=0.4)
        ax.set_xlabel("Median relative interval width")
        ax.set_title(SCHEME[sch], fontsize=9)
    axes[0].set_ylabel("Mean relative Winkler score\n(lower is better)")
    axes[1].legend(fontsize=7, frameon=False, loc="upper right")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def fig_basin_cov(res, alpha, path):
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.9), sharey=True)
    for ax, sch in zip(axes, ["pub", "region"]):
        df, _ = summarise(res, sch, alpha)
        data = [df[df.method == m]["cov_q95"].dropna().values for m in C.METHODS]
        bp = ax.boxplot(data, patch_artist=True, showfliers=False, widths=0.6)
        for p, m in zip(bp["boxes"], C.METHODS):
            p.set_facecolor(COL[m])
        ax.axhline(1 - alpha, color="k", ls="--", lw=0.8)
        ax.set_xticks(range(1, len(C.METHODS) + 1), C.METHODS, rotation=35, fontsize=7)
        ax.set_title(SCHEME[sch], fontsize=9)
    axes[0].set_ylabel("Per-basin coverage, days ≥ Q95")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def fig_aridity(res, meta, alpha, path):
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.9), sharey=True)
    for ax, sch in zip(axes, ["pub", "region"]):
        df, _ = summarise(res, sch, alpha)
        df = df.merge(meta[["aridity", "frac_snow"]], left_on="basin", right_index=True)
        df["grp"] = pd.qcut(df["aridity"], 3, labels=["Humid", "Intermediate", "Arid"])
        ms = ["QR", "CQR-r", "RC-CQR", "DRC-CQR"]
        w = 0.2
        for j, m in enumerate(ms):
            v = df[df.method == m].groupby("grp", observed=True)["cov_q95"].mean()
            ax.bar(np.arange(3) + (j - 1.5) * w, v.values, w, color=COL[m], label=m)
        ax.axhline(1 - alpha, color="k", ls="--", lw=0.8)
        ax.set_xticks(range(3), ["Humid", "Intermediate", "Arid"])
        ax.set_xlabel("Aridity tercile (PET/P)")
        ax.set_title(SCHEME[sch], fontsize=9)
    axes[0].set_ylabel("Mean coverage, days ≥ Q95")
    axes[0].set_ylim(0, 1.05)
    axes[1].legend(fontsize=7, frameon=False, loc="upper center", bbox_to_anchor=(-0.1, -0.2), ncol=4)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def fig_hydrograph(data, preds, scheme, alpha, path, gauge=None):
    d = dict(np.load(data, allow_pickle=True))
    nb = len(d["gauges"])
    pred, dates, quantiles, _ = C.load_oof(preds, scheme, nb)
    alld = d["dates"].astype("datetime64[D]")
    Q = d["Q"][:, np.searchsorted(alld, dates[0]):np.searchsorted(alld, dates[-1]) + 1]
    folds = C.fold_of(preds, scheme, nb)
    cal = C.Calibrator(pred, Q, dates, quantiles, d["S"], alpha)
    tst = np.where(cal.tst)[0]
    if gauge is None:  # basin with the largest test-period peak relative to its mean, among decent fits
        rel = np.nanmax(Q[:, tst], 1) / (np.nanmean(Q[:, tst], 1) + 1e-6)
        good = [b for b in np.argsort(-rel) if C.nse(Q[b, tst], cal.md[b, tst]) > 0.6]
        t = good[0] if good else int(np.argsort(-rel)[0])
    else:
        t = int(np.where(d["gauges"] == gauge)[0][0])
    donors = np.where(folds != folds[t])[0]
    import json
    with open(os.path.join(os.path.dirname(preds), f"ktuning_{scheme}_a{int(round(alpha * 100)):02d}.json")) as fh:
        kstar = json.load(fh)[folds[t]]["k"]
    pk = tst[np.nanargmax(Q[t, tst])]
    win = np.arange(max(pk - 60, tst[0]), min(pk + 60, tst[-1]))
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.6), sharey=True)
    for ax, m in zip(axes, ["QR", "CQR-r", "DRC-CQR"]):
        lo, hi = cal.intervals(t, donors, m, k=kstar)
        ax.fill_between(dates[win], lo[win], hi[win], color=COL[m], alpha=0.35, lw=0, label=f"{int((1-alpha)*100)}% interval")
        ax.plot(dates[win], cal.md[t, win], color=COL[m], lw=0.9, label="median")
        ax.plot(dates[win], Q[t, win], "k.", ms=1.8, label="observed")
        ax.set_title(m, fontsize=9)
        import matplotlib.dates as mdates
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
        ax.tick_params(axis="x", labelrotation=35, labelsize=6.5)
    axes[0].set_ylabel("Streamflow (mm/day)")
    axes[0].legend(fontsize=6.5, frameon=False, loc="upper left")
    fig.suptitle(f"USGS {d['gauges'][t]}, {SCHEME[scheme].split(' (')[0].lower()}", fontsize=8.5, y=1.02)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    return d["gauges"][t]


C_REGIONS = None


def main():
    global C_REGIONS
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--meta", required=True)
    ap.add_argument("--res", required=True)
    a = ap.parse_args()
    import train
    C_REGIONS = train.REGIONS
    figdir = os.path.join(a.res, "figures")
    os.makedirs(figdir, exist_ok=True)
    meta = pd.read_csv(a.meta, dtype={"gauge_id": str}).set_index("gauge_id")

    with open(os.path.join(a.res, "tables.md"), "w") as fh:
        for sch in ["pub", "region"]:
            df, _ = summarise(a.res, sch, 0.1)
            pt = df[df.method == "QR"]
            fh.write(f"## Point skill {sch}\nmedian NSE {pt.nse.median():.3f} | median KGE {pt.kge.median():.3f} | "
                     f"NSE<0: {(pt.nse < 0).mean() * 100:.1f}% | n={len(pt)}\n\n")
            per = pt.groupby("fold")[["nse", "kge"]].median().round(3)
            fh.write(per.to_string() + "\n\n")
            for alpha in [0.1, 0.02]:
                _, t = summarise(a.res, sch, alpha)
                fh.write(f"## Intervals {sch} alpha={alpha}\n{t.round(3).to_string()}\n\n")
        from scipy.stats import wilcoxon
        fh.write("## Paired Wilcoxon signed-rank tests across basins (alpha 0.1)\n")
        for sch in ["pub", "region"]:
            df, _ = summarise(a.res, sch, 0.1)
            p = df.pivot_table(index="basin", columns="method", values=["winkler", "cov_q95", "relwidth"])
            for m1, m2 in [("DRC-CQR", "CQR-r"), ("DRC-CQR", "CQR"), ("DRC-CQR", "RC-CQR"), ("DW-CQR", "CQR-r"), ("CQR-r", "CQR")]:
                for v in ["winkler", "cov_q95", "relwidth"]:
                    x, y = p[(v, m1)], p[(v, m2)]
                    ok = x.notna() & y.notna()
                    st = wilcoxon(x[ok], y[ok])
                    fh.write(f"{sch} {v} {m1} vs {m2}: median diff {(x[ok] - y[ok]).median():.4f}, "
                             f"{m1} better in {(x[ok] < y[ok]).mean() * 100 if v != 'cov_q95' else (x[ok] > y[ok]).mean() * 100:.1f}% basins, p={st.pvalue:.2e}\n")
        fh.write("\n")
        df, _ = summarise(a.res, "region", 0.1)
        reg = df[df.method.isin(["QR", "CQR", "CQR-r", "RC-CQR", "DRC-CQR"])].pivot_table(
            index="fold", columns="method", values="cov_q95", aggfunc="mean")
        fh.write("## Region x method coverage Q95+ (alpha 0.1)\n" + reg.round(3).to_string() + "\n\n")
        reg = df[df.method.isin(["QR", "CQR", "CQR-r", "RC-CQR", "DRC-CQR"])].pivot_table(
            index="fold", columns="method", values="cov", aggfunc="mean")
        fh.write("## Region x method coverage overall (alpha 0.1)\n" + reg.round(3).to_string() + "\n\n")

    fig_framework(os.path.join(figdir, "fig1_framework.png"))
    fig_map(a.data, os.path.join(figdir, "fig2_map.png"))
    fig_regime(a.res, 0.1, os.path.join(figdir, "fig3_regime_coverage.png"))
    fig_tradeoff(a.res, 0.1, os.path.join(figdir, "fig4_tradeoff.png"))
    fig_basin_cov(a.res, 0.1, os.path.join(figdir, "fig5_basin_coverage.png"))
    fig_aridity(a.res, meta, 0.1, os.path.join(figdir, "fig6_aridity.png"))
    g = fig_hydrograph(a.data, os.path.join(a.res, "preds"), "region", 0.1, os.path.join(figdir, "fig7_hydrograph.png"))
    print("hydrograph basin", g)


if __name__ == "__main__":
    main()
