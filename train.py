"""Train a regional quantile LSTM on donor basins and predict held-out (pseudo-ungauged) basins.

Schemes
  pub    : 5-fold random cross-validation over basins (prediction in ungauged basins, PUB)
  region : leave-one-macro-region-out over HUC-02 groups (geographic distribution shift)

Every held-out basin gets out-of-fold quantile predictions for the full 1989-10-01..2008-09-30
record, so later conformal calibration can use donor scores that are themselves out-of-sample.
"""
import argparse
import json
import os
import time

import numpy as np
import torch
import torch.nn as nn

QUANTILES = [0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.975, 0.99]
SEQ = 365
PRED_LAST = 60  # each window supervises its last 60 days (look-back 306-365 d)
TRAIN = ("1999-10-01", "2008-09-30")
EVAL0 = "1989-10-01"

# HUC-02 macro-regions for the regional-holdout experiment.
REGIONS = {
    "R1_Northeast": [1, 2],
    "R2_Southeast": [3],
    "R3_GreatLakes_Ohio_Tennessee": [4, 5, 6],
    "R4_Mississippi_Missouri": [7, 8, 9, 10],
    "R5_SouthCentral_Southwest": [11, 12, 13, 14, 15, 16],
    "R6_PacificNW_California": [17, 18],
}


def make_folds(d, scheme, n_folds=5, seed=0):
    nb = len(d["gauges"])
    if scheme == "pub":
        perm = np.random.RandomState(seed).permutation(nb)
        return [np.sort(perm[k::n_folds]) for k in range(n_folds)], [f"F{k+1}" for k in range(n_folds)]
    huc = d["huc"]
    folds = [np.where(np.isin(huc, v))[0] for v in REGIONS.values()]
    return folds, list(REGIONS)


class QLSTM(nn.Module):
    def __init__(self, n_in, hidden, n_q, dropout):
        super().__init__()
        self.lstm = nn.LSTM(n_in, hidden, batch_first=True)
        self.drop = nn.Dropout(dropout)
        self.head = nn.Linear(hidden, n_q)
        with torch.no_grad():  # LSTM forget-gate bias init (Kratzert et al., 2019)
            self.lstm.bias_hh_l0[hidden:2 * hidden].fill_(3.0)

    def forward(self, x):
        h, _ = self.lstm(x)
        return self.head(self.drop(h[:, -PRED_LAST:]))  # (batch, PRED_LAST, n_q)


def pinball(pred, y, w, taus):
    mask = ~torch.isnan(y)
    e = torch.nan_to_num(y)[..., None] - pred
    loss = torch.maximum(taus * e, (taus - 1) * e).mean(-1) * w[:, None]
    return (loss * mask).sum() / mask.sum().clamp(min=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--scheme", choices=["pub", "region"], required=True)
    ap.add_argument("--fold", type=int, required=True)
    ap.add_argument("--iters", type=int, default=12000)
    ap.add_argument("--batch", type=int, default=256)
    ap.add_argument("--hidden", type=int, default=128)
    ap.add_argument("--dropout", type=float, default=0.4)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    torch.manual_seed(a.seed)
    np.random.seed(a.seed)
    dev = torch.device("cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu")
    d = dict(np.load(a.data, allow_pickle=True))
    dates = d["dates"].astype("datetime64[D]")
    folds, names = make_folds(d, a.scheme)
    test_idx = folds[a.fold]
    train_idx = np.setdiff1d(np.arange(len(d["gauges"])), test_idx)

    t0 = np.searchsorted(dates, np.datetime64(TRAIN[0]))
    t1 = np.searchsorted(dates, np.datetime64(TRAIN[1])) + 1
    X, Q, S = d["X"], d["Q"], d["S"]

    # Normalisation statistics come from training basins and the training period only.
    xm = X[train_idx, t0:t1].reshape(-1, X.shape[2]).mean(0)
    xs = X[train_idx, t0:t1].reshape(-1, X.shape[2]).std(0)
    sm, ss = S[train_idx].mean(0), S[train_idx].std(0) + 1e-6
    qtr = Q[train_idx, t0:t1]
    qm, qs = np.nanmean(qtr), np.nanstd(qtr)

    Xn = torch.tensor((X - xm) / xs, dtype=torch.float32, device=dev)
    Sn = torch.tensor((S - sm) / ss, dtype=torch.float32, device=dev)
    Qn = torch.tensor((Q - qm) / qs, dtype=torch.float32, device=dev)
    basin_sd = torch.tensor(np.nanstd(Q[:, t0:t1], axis=1) / qs, dtype=torch.float32, device=dev)
    w_basin = 1.0 / (basin_sd + 0.1)  # NSE*-style weighting so large basins do not dominate
    taus = torch.tensor(QUANTILES, device=dev)

    # Training windows: (basin, end day) such that all supervised days lie in the training period
    # and at least one target is observed.
    ends = np.arange(t0 + PRED_LAST - 1, t1)
    obs = ~np.isnan(Q[train_idx, t0:t1])
    cnt = np.concatenate([np.zeros((len(train_idx), 1)), np.cumsum(obs, 1)], 1)
    n_obs = cnt[:, ends - t0 + 1] - cnt[:, ends - t0 + 1 - PRED_LAST]
    bi, ei = np.nonzero(n_obs > 0)
    samp_b = torch.tensor(train_idx[bi], device=dev)
    samp_t = torch.tensor(ends[ei], device=dev)
    ar = torch.arange(-SEQ + 1, 1, device=dev)
    ar_y = torch.arange(-PRED_LAST + 1, 1, device=dev)

    def batch_inputs(b, t):
        idx = t[:, None] + ar[None, :]
        xd = Xn[b[:, None], idx]
        xs_ = Sn[b][:, None, :].expand(-1, SEQ, -1)
        return torch.cat([xd, xs_], dim=2)

    model = QLSTM(X.shape[2] + S.shape[1], a.hidden, len(QUANTILES), a.dropout).to(dev)
    opt = torch.optim.Adam(model.parameters(), lr=a.lr)
    sched = torch.optim.lr_scheduler.MultiStepLR(opt, [int(a.iters * 0.6), int(a.iters * 0.85)], 0.2)

    start = time.time()
    log = []
    model.train()
    for it in range(1, a.iters + 1):
        j = torch.randint(0, len(samp_b), (a.batch,), device=dev)
        b, t = samp_b[j], samp_t[j]
        pred = model(batch_inputs(b, t))
        y = Qn[b[:, None], t[:, None] + ar_y[None, :]]
        loss = pinball(pred, y, w_basin[b], taus)
        opt.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        sched.step()
        if dev.type == "mps" and it % 10 == 0:
            torch.mps.synchronize()  # stop the CPU from queueing unbounded MPS work (memory growth)
        if it % 500 == 0:
            log.append((it, float(loss), time.time() - start))
            print(f"it {it} loss {float(loss):.4f} {time.time() - start:.0f}s", flush=True)

    # Out-of-fold prediction for held-out basins over the whole evaluation record.
    model.eval()
    e0 = np.searchsorted(dates, np.datetime64(EVAL0))
    days = np.arange(e0, len(dates))
    out = np.zeros((len(test_idx), len(days), len(QUANTILES)), dtype=np.float32)
    # Non-overlapping windows; each emits PRED_LAST consecutive days, matching the training look-back.
    win_end = np.arange(e0 + PRED_LAST - 1, len(dates) + PRED_LAST - 1, PRED_LAST)
    win_end = np.minimum(win_end, len(dates) - 1)
    with torch.no_grad():
        for k, b in enumerate(test_idx):
            t = torch.tensor(win_end, device=dev)
            bb = torch.full_like(t, int(b))
            p = model(batch_inputs(bb, t)).cpu().numpy() * qs + qm  # (n_win, PRED_LAST, n_q)
            day_idx = win_end[:, None] + np.arange(-PRED_LAST + 1, 1)[None, :]
            out[k, day_idx.ravel() - e0] = p.reshape(-1, p.shape[-1])
    out = np.maximum(np.sort(out, axis=2), 0.0)  # remove quantile crossing, enforce non-negativity

    os.makedirs(a.out, exist_ok=True)
    tag = f"{a.scheme}_{names[a.fold]}_s{a.seed}"
    np.savez_compressed(os.path.join(a.out, f"{tag}.npz"), pred=out, basins=test_idx,
                        dates=dates[days], quantiles=np.array(QUANTILES))
    with open(os.path.join(a.out, f"{tag}.json"), "w") as fh:
        json.dump(dict(vars(a), n_train=len(train_idx), n_test=len(test_idx), log=log,
                       seconds=time.time() - start), fh, indent=1)
    print("done", tag, f"{time.time() - start:.0f}s")


if __name__ == "__main__":
    main()
