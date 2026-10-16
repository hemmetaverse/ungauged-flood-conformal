# Gauge-free conformal calibration for ungauged flood forecasting

Code and results for the manuscript *"Transferable Uncertainty for Flood-Relevant Streamflow Prediction in Ungauged Basins: Gauge-Free Conformal Calibration of a Regional Deep Learning Model"* by Hemant Palivela (manuscript under review).

The question the code answers: can a regional deep-learning streamflow model produce prediction intervals for **ungauged** basins that stay calibrated, especially on flood days, when **no discharge from the target basin** is available for calibration and the target may differ from the training basins?

## Method in brief

1. **Regional quantile LSTM.** A single-layer LSTM (128 units) reads 365 days of Daymet forcing plus 27 static CAMELS attributes (no discharge-derived signatures). It outputs 11 quantiles and is trained with a basin-weighted pinball loss.
2. **Out-of-fold donor scores.** Basins are split into folds. Each model is trained with one fold withheld, so every basin gets predictions from a model that never saw it. A target basin is calibrated only on *other* basins' out-of-fold predictions from 1999–2008, and evaluated on 1989–1999.
3. **Conformal calibration with basins as the exchangeable unit.** Each donor basin carries equal weight, with a finite-sample level of (1 − α)(1 + 1/n_eff).
4. **Seven methods compared.**

| Method | Score | Conditioning |
|---|---|---|
| QR | none (raw quantiles) | — |
| SCP | \|y − median\| / simulated mean flow | — |
| CQR | max(l − y, y − h) | — |
| CQR-r | max(l − y, y − h) / (h − l + δ) | — |
| RC-CQR | as CQR-r | Mondrian over five simulated-flow regimes |
| DW-CQR | as CQR-r | k nearest donors in attribute space |
| **DRC-CQR** (proposed) | as CQR-r | regimes + donor neighbourhood |

The regime and the donor neighbourhood are both computed **without target discharge**. The neighbourhood size k is tuned by leave-one-donor-out on donors only, and sizes that cannot give a finite threshold at the requested α are excluded.

## Evaluation schemes

- `pub`: 5-fold random basin holdout (prediction in ungauged basins).
- `region`: leave-one-macro-region-out over six HUC-02 groups (geographic distribution shift).

Nominal coverage is 90% (α = 0.1) and 98% (α = 0.02). The metrics are per-basin coverage overall and on days above the observed 95th and 99th percentiles, regime coverage, relative width, Winkler interval score, and NSE/KGE of the median.

## Repository layout

| File | Purpose |
|---|---|
| `download_data.sh` | Downloads CAMELS-US from Zenodo and extracts the Daymet forcing and USGS streamflow |
| `prepare_data.py` | Selects basins (area < 2000 km², < 10% area discrepancy: 558 basins) and writes `camels_sel.npz` |
| `train.py` | Trains one quantile-LSTM fold model and writes out-of-fold predictions |
| `conformal.py` | Gauge-free calibration (all seven methods), k tuning and per-basin metrics |
| `figures.py` | Tables (`tables.md`, including Wilcoxon tests) and Figures 1–7 |
| `run_all.sh` | Runs every fold for the given seeds, then calibration at α = 0.1 and 0.02 |
| `results/` | Seed-0 metrics, k-tuning logs, tables, figures and per-model training logs |
| `results_seed1/` | The same for the independent seed-1 robustness run |

Model predictions (`results*/preds/*.npz`, about 270 MB per seed) are not tracked; `run_all.sh` regenerates them.

## Reproducing the results

```bash
pip install -r requirements.txt
./download_data.sh data/camels_us
python3 prepare_data.py data/camels_us
CAMELS_DIR=data/camels_us ./run_all.sh 0          # seed 0 -> results/
CAMELS_DIR=data/camels_us OUT=results_seed1 ./run_all.sh 1
python3 figures.py --data data/camels_us/camels_sel.npz --meta data/camels_us/camels_sel_meta.csv --res results
```

Training uses CUDA or Apple-silicon MPS when available, and CPU otherwise. On an Apple M5, each fold model (12,000 iterations, batch 256) takes about 9.5 minutes, so the 11 models of one seed take about 1¾ hours. Calibration takes about 1 minute per scheme and α.

## Main results (seed 0; seed 1 reproduces them)

At nominal 90%, mean per-basin coverage:

| Method | PUB: all days | PUB: days ≥ Q95 | Region: all days | Region: days ≥ Q95 |
|---|---|---|---|---|
| QR | 0.661 | 0.625 | 0.582 | 0.573 |
| SCP | 0.875 | 0.238 | 0.876 | 0.295 |
| CQR | 0.877 | 0.670 | 0.879 | 0.640 |
| CQR-r | 0.879 | 0.799 | 0.879 | 0.808 |
| RC-CQR | 0.876 | 0.759 | 0.871 | 0.739 |
| DW-CQR | 0.890 | 0.806 | 0.891 | 0.829 |
| DRC-CQR | 0.887 | 0.763 | 0.880 | 0.749 |

- Raw quantiles are strongly overconfident in unseen basins. Gauge-free calibration restores mean coverage to 87–89%.
- Width-normalized scores more than triple flood-day coverage compared with split conformal prediction.
- Regime conditioning equalizes coverage across simulated-flow regimes (a gap of 0.01–0.03), and DRC-CQR gives the best mean Winkler score under random holdout. The trade-off is lower coverage of observed flood days.
- Donor weighting helps mainly in arid basins, and makes 98% intervals uninformative.

Full tables are in [`results/tables.md`](results/tables.md).

## Data

CAMELS-US: Newman, A. (2014), *A large-sample watershed-scale hydrometeorological dataset for the contiguous USA*, UCAR/NCAR, https://doi.org/10.5065/D6MW2F4D (CC-BY-4.0). Please also cite Newman et al. (2015, *HESS* 19, 209–223) and Addor et al. (2017, *HESS* 21, 5293–5313). The data are not redistributed here.

## Citation

If you use this code, please cite the repository and, once it is published, the article:

```
Palivela, H. (2026). Gauge-free conformal calibration for ungauged flood forecasting [Computer software].
https://github.com/hemmetaverse/ungauged-flood-conformal
```

## License

MIT; see [LICENSE](LICENSE).
