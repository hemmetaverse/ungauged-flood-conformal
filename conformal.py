"""Gauge-free conformal calibration of quantile-LSTM intervals for ungauged basins, and evaluation.

All calibration information comes from *donor* basins (other folds/regions) during the training
period 1999-2008. The target basin contributes only forcings and static attributes; its discharge
is used solely to score the intervals in the 1989-1999 evaluation period.

Methods
  QR        raw quantile-LSTM interval (no calibration)
  SCP       split conformal on |y - median| scaled by the target's simulated mean flow
  CQR       conformalized quantile regression, additive score (Romano et al., 2019)
  CQR-r     CQR with width-normalised (multiplicative) score
  RC-CQR    CQR-r, Mondrian over simulated flow regime (regime-conditional)
  DW-CQR    CQR-r, donor basins weighted by catchment-attribute similarity
  DRC-CQR   proposed: donor-weighted + regime-conditional CQR-r
"""
import argparse
import glob
import json
import os

import numpy as np
import pandas as pd

CAL = ("1999-10-01", "2008-09-30")
TEST = ("1989-10-01", "1999-09-30")
REGIME_EDGES = np.array([0.0, 0.5, 0.8, 0.95, 0.99, 1.0 + 1e-9])  # percentiles of simulated flow
REGIME_NAMES = ["<P50", "P50-80", "P80-95", "P95-99", ">P99"]
METHODS = ["QR", "SCP", "CQR", "CQR-r", "RC-CQR", "DW-CQR", "DRC-CQR"]


# ----------------------------------------------------------------------------------------------
def load_oof(pred_dir, scheme, nb):
    """Merge out-of-fold predictions of all folds (averaging seeds, if several) into (nb, T, nq)."""
    files = sorted(glob.glob(os.path.join(pred_dir, f"{scheme}_*_s*.npz")))
    acc, cnt, dates, qs = None, np.zeros(nb), None, None
    for f in files:
        z = np.load(f, allow_pickle=True)
        if acc is None:
            acc = np.zeros((nb,) + z["pred"].shape[1:], dtype=np.float64)
            dates, qs = z["dates"].astype("datetime64[D]"), z["quantiles"]
        acc[z["basins"]] += z["pred"]
        cnt[z["basins"]] += 1
    assert (cnt > 0).all(), "some basins lack out-of-fold predictions"
    return (acc / cnt[:, None, None]).astype(np.float32), dates, qs, files


def fold_of(pred_dir, scheme, nb):
    lab = np.empty(nb, dtype=object)
    for f in glob.glob(os.path.join(pred_dir, f"{scheme}_*_s*.npz")):
        z = np.load(f, allow_pickle=True)
        lab[z["basins"]] = os.path.basename(f)[len(scheme) + 1:].rsplit("_s", 1)[0]
    return lab


def weighted_quantile(values, weights, level):
    """Upper weighted empirical quantile with a point mass at +inf (finite-sample conformal)."""
    if level >= 1.0 or len(values) == 0:
        return np.inf
    o = np.argsort(values)
    v, w = values[o], weights[o]
    c = np.cumsum(w) / w.sum()
    k = np.searchsorted(c, level, side="left")
    return v[min(k, len(v) - 1)] if k < len(v) else np.inf


def conformal_level(alpha, w_basin):
    """Finite-sample corrected level, using basins as the exchangeable unit (two-layer
    hierarchical conformal, Dunn et al., 2022) with Kish effective sample size for weights."""
    n_eff = w_basin.sum() ** 2 / (w_basin ** 2).sum()
    return min(1.0, (1 - alpha) * (1 + 1 / n_eff))


# ----------------------------------------------------------------------------------------------
class Calibrator:
    def __init__(self, pred, Q, dates, quantiles, S, alpha):
        self.alpha = alpha
        qs = list(np.round(quantiles, 4))
        self.lo_i, self.hi_i = qs.index(round(alpha / 2, 4)), qs.index(round(1 - alpha / 2, 4))
        self.md_i = qs.index(0.5)
        self.cal = (dates >= np.datetime64(CAL[0])) & (dates <= np.datetime64(CAL[1]))
        self.tst = (dates >= np.datetime64(TEST[0])) & (dates <= np.datetime64(TEST[1]))
        self.pred, self.Q = pred, Q
        lo, hi, md = pred[..., self.lo_i], pred[..., self.hi_i], pred[..., self.md_i]
        self.lo, self.hi, self.md = lo, hi, md
        # Gauge-free scale and regime: both derived from the *simulated* median in the cal period.
        self.sim_mean = md[:, self.cal].mean(1) + 1e-3
        self.delta = 0.01 * self.sim_mean[:, None]  # width floor for the multiplicative score
        sim_sorted = np.sort(md[:, self.cal], axis=1)
        self.pct = np.stack([np.searchsorted(sim_sorted[b], md[b], side="right") / sim_sorted.shape[1]
                             for b in range(md.shape[0])])
        self.regime = np.clip(np.searchsorted(REGIME_EDGES, self.pct, side="right") - 1, 0, 4)
        Sz = (S - S.mean(0)) / (S.std(0) + 1e-9)
        self.D = np.sqrt(((Sz[:, None, :] - Sz[None, :, :]) ** 2).sum(-1))
        # Conformity scores on every basin's calibration period (each out-of-fold).
        y = Q
        self.s_abs = np.abs(y - md) / self.sim_mean[:, None]
        self.s_add = np.maximum(lo - y, y - hi)
        self.s_mul = np.maximum(lo - y, y - hi) / (hi - lo + self.delta)
        self._cache, self._thr = {}, {}

    def donor_weights(self, target, donors, k):
        if k is None or k >= len(donors):
            return np.ones(len(donors))
        order = np.argsort(self.D[target, donors])
        w = np.zeros(len(donors))
        w[order[:k]] = 1.0
        return w

    def _per_basin(self, name, d, regime):
        """Calibration-period scores of donor d (optionally one regime), cached."""
        key = (name, d, regime)
        if key not in self._cache:
            m = self.cal & ~np.isnan(self.Q[d])
            if regime is not None:
                m &= self.regime[d] == regime
            self._cache[key] = getattr(self, name)[d, m]
        return self._cache[key]

    def threshold(self, name, donors, w_basin, regime=None):
        key = (name, regime, donors.tobytes(), w_basin.tobytes())
        if key in self._thr:
            return self._thr[key]
        vals, wts = [], []
        for d, wb in zip(donors, w_basin):
            if wb == 0:
                continue
            v = self._per_basin(name, d, regime)
            if len(v):
                vals.append(v)
                wts.append(np.full(len(v), wb / len(v)))  # each donor basin carries its weight once
        if vals:
            qhat = weighted_quantile(np.concatenate(vals), np.concatenate(wts),
                                     conformal_level(self.alpha, w_basin[w_basin > 0]))
        else:
            qhat = np.inf
        self._thr[key] = qhat
        return qhat

    def intervals(self, target, donors, method, k=None):
        lo, hi, md = self.lo[target], self.hi[target], self.md[target]
        if method == "QR":
            return lo, hi
        if method == "SCP":
            qhat = self.threshold("s_abs", donors, np.ones(len(donors)))
            r = qhat * self.sim_mean[target]
            return np.maximum(md - r, 0), md + r
        if method == "CQR":
            qhat = self.threshold("s_add", donors, np.ones(len(donors)))
            return np.maximum(lo - qhat, 0), hi + qhat
        w = self.donor_weights(target, donors, k if method in ("DW-CQR", "DRC-CQR") else None)
        width = hi - lo + self.delta[target]
        if method in ("CQR-r", "DW-CQR"):
            qhat = self.threshold("s_mul", donors, w)
            return np.maximum(lo - qhat * width, 0), hi + qhat * width
        # Regime-conditional (Mondrian) variants.
        qreg = np.array([self.threshold("s_mul", donors, w, r) for r in range(5)])
        qhat = qreg[self.regime[target]]
        return np.maximum(lo - qhat * width, 0), hi + qhat * width


# ----------------------------------------------------------------------------------------------
def nse(y, p):
    m = ~np.isnan(y)
    return 1 - np.sum((y[m] - p[m]) ** 2) / np.sum((y[m] - y[m].mean()) ** 2)


def kge(y, p):
    m = ~np.isnan(y)
    y, p = y[m], p[m]
    r = np.corrcoef(y, p)[0, 1]
    return 1 - np.sqrt((r - 1) ** 2 + (p.std() / y.std() - 1) ** 2 + (p.mean() / y.mean() - 1) ** 2)


def interval_metrics(y, lo, hi, alpha, regime):
    m = ~np.isnan(y)
    y, lo, hi, regime = y[m], lo[m], hi[m], regime[m]
    ybar = y.mean() + 1e-6
    cov = (y >= lo) & (y <= hi)
    width = hi - lo
    wink = width + (2 / alpha) * (np.where(y < lo, lo - y, 0) + np.where(y > hi, y - hi, 0))
    q95, q99 = np.quantile(y, 0.95), np.quantile(y, 0.99)
    peak = y >= q95
    out = dict(cov=cov.mean(), relwidth=width.mean() / ybar, winkler=wink.mean() / ybar,
               cov_q95=cov[peak].mean(), cov_q99=cov[y >= q99].mean(),
               relwidth_q95=width[peak].mean() / ybar,
               under_q95=(y[peak] > hi[peak]).mean())
    for r, name in enumerate(REGIME_NAMES):
        sel = regime == r
        out[f"cov_reg{r}"] = cov[sel].mean() if sel.any() else np.nan
        out[f"n_reg{r}"] = int(sel.sum())
    return out


def tune_k(cal, donors, grid, alpha):
    """Target-free choice of the donor-neighbourhood size: leave-one-donor-out on donors only,
    minimising mean absolute coverage error in the >=P95 simulated regimes plus overall."""
    rng = np.random.RandomState(0)
    probe = rng.choice(donors, size=min(60, len(donors)), replace=False)
    best, scores = None, {}
    # Neighbourhoods too small to give a finite threshold at this alpha are inadmissible.
    grid = [k for k in grid if conformal_level(alpha, np.ones(min(k, len(donors) - 1))) < 1.0]
    for k in grid:
        err = []
        for t in probe:
            others = donors[donors != t]
            lo, hi = cal.intervals(t, others, "DRC-CQR", k=min(k, len(others)))
            y = cal.Q[t]
            m = cal.cal & ~np.isnan(y)
            c = (y[m] >= lo[m]) & (y[m] <= hi[m])
            hiflow = cal.regime[t][m] >= 3
            err.append(abs(c.mean() - (1 - alpha)) + (abs(c[hiflow].mean() - (1 - alpha)) if hiflow.any() else 0))
        scores[k] = float(np.mean(err))
        if best is None or scores[k] < scores[best]:
            best = k
    return best, scores


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--preds", required=True)
    ap.add_argument("--scheme", required=True)
    ap.add_argument("--alpha", type=float, default=0.1)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    d = dict(np.load(a.data, allow_pickle=True))
    nb = len(d["gauges"])
    pred, dates, quantiles, files = load_oof(a.preds, a.scheme, nb)
    alld = d["dates"].astype("datetime64[D]")
    Q = d["Q"][:, np.searchsorted(alld, dates[0]):np.searchsorted(alld, dates[-1]) + 1]
    folds = fold_of(a.preds, a.scheme, nb)
    cal = Calibrator(pred, Q, dates, quantiles, d["S"], a.alpha)

    rows, ks = [], {}
    for f in sorted(set(folds)):
        targets = np.where(folds == f)[0]
        donors = np.where(folds != f)[0]
        k, kscores = tune_k(cal, donors, [25, 50, 100, 200, len(donors)], a.alpha)
        ks[f] = dict(k=int(k), scores=kscores)
        print(a.scheme, f, "targets", len(targets), "donors", len(donors), "k*", k, flush=True)
        for t in targets:
            y = Q[t]
            ts = cal.tst
            base = dict(basin=d["gauges"][t], fold=f, nse=nse(y[ts], cal.md[t, ts]), kge=kge(y[ts], cal.md[t, ts]))
            for meth in METHODS:
                lo, hi = cal.intervals(t, donors, meth, k=k)
                r = interval_metrics(y[ts], lo[ts], hi[ts], a.alpha, cal.regime[t, ts])
                rows.append(dict(base, method=meth, **r))
    df = pd.DataFrame(rows)
    os.makedirs(a.out, exist_ok=True)
    tag = f"{a.scheme}_a{int(round(a.alpha * 100)):02d}"
    df.to_csv(os.path.join(a.out, f"metrics_{tag}.csv"), index=False)
    with open(os.path.join(a.out, f"ktuning_{tag}.json"), "w") as fh:
        json.dump(ks, fh, indent=1)
    summ = df.groupby("method")[["cov", "cov_q95", "cov_q99", "relwidth", "relwidth_q95", "winkler"]].median()
    print(summ.loc[METHODS].round(3).to_string())


if __name__ == "__main__":
    main()
