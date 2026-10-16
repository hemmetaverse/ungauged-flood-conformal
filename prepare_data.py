"""Build an in-memory CAMELS-US tensor archive (Daymet lumped forcing + USGS streamflow + static attributes).

Basin selection follows Newman et al. (2017) / Kratzert et al. (2019): area < 2000 km2 and
<10% discrepancy between GAGES-II and geospatial-fabric areas, (558 basins with the attribute files used here).
"""
import glob
import os
import sys

import numpy as np
import pandas as pd

DATA = sys.argv[1] if len(sys.argv) > 1 else os.environ["CAMELS_DIR"]
ROOT = os.path.join(DATA, "basin_dataset_public_v1p2")
OUT = os.path.join(DATA, "camels_sel.npz")

START, END = "1988-10-01", "2008-09-30"  # 1-yr warm-up before 1989-10-01 test start
DYN = ["prcp(mm/day)", "srad(W/m2)", "tmax(C)", "tmin(C)", "vp(Pa)"]

# Static attributes used by Kratzert et al. (2019); no discharge-derived signatures (ungauged setting).
STATIC = ["p_mean", "pet_mean", "aridity", "p_seasonality", "frac_snow", "high_prec_freq",
          "high_prec_dur", "low_prec_freq", "low_prec_dur", "elev_mean", "slope_mean", "area_gages2",
          "frac_forest", "lai_max", "lai_diff", "gvf_max", "gvf_diff", "soil_depth_pelletier",
          "soil_depth_statsgo", "soil_porosity", "soil_conductivity", "max_water_content", "sand_frac",
          "silt_frac", "clay_frac", "carbonate_rocks_frac", "geol_permeability"]


def load_attributes():
    dfs = []
    for name in ["clim", "geol", "hydro", "name", "soil", "topo", "vege"]:
        df = pd.read_csv(os.path.join(DATA, f"camels_{name}.txt"), sep=";", dtype={"gauge_id": str})
        dfs.append(df.set_index("gauge_id"))
    att = pd.concat(dfs, axis=1)
    return att.loc[:, ~att.columns.duplicated()]


def main():
    att = load_attributes()
    discrepancy = (att.area_gages2 - att.area_geospa_fabric).abs() / att.area_gages2
    sel = att[(att.area_gages2 < 2000) & (discrepancy < 0.10)].copy()
    dates = pd.date_range(START, END, freq="D")

    X, Q, keep, areas = [], [], [], []
    for gid in sel.index:
        huc = sel.loc[gid, "huc_02"]
        huc = f"{int(huc):02d}"
        ff = glob.glob(os.path.join(ROOT, "basin_mean_forcing", "daymet", huc, f"{gid}_lump_cida_forcing_leap.txt"))
        qf = glob.glob(os.path.join(ROOT, "usgs_streamflow", huc, f"{gid}_streamflow_qc.txt"))
        if not ff or not qf:
            continue
        with open(ff[0]) as fh:
            lines = fh.readlines()
        area_m2 = float(lines[2])
        f = pd.read_csv(ff[0], sep=r"\s+", skiprows=3)
        f.index = pd.to_datetime(dict(year=f.Year, month=f.Mnth, day=f.Day))
        f = f.reindex(dates)
        q = pd.read_csv(qf[0], sep=r"\s+", header=None, names=["id", "y", "m", "d", "q", "flag"],
                        dtype={"id": str})
        q.index = pd.to_datetime(dict(year=q.y, month=q.m, day=q.d))
        q = q.q.reindex(dates).astype(float)
        q[q < 0] = np.nan
        q_mm = q * 0.0283168466 * 86400 * 1000 / area_m2  # cfs -> mm/day
        if f[DYN].isna().any().any():
            continue
        X.append(f[DYN].values.astype(np.float32))
        Q.append(q_mm.values.astype(np.float32))
        keep.append(gid)
        areas.append(area_m2 / 1e6)

    sel = sel.loc[keep]
    S = sel[STATIC].astype(float).values.astype(np.float32)
    np.savez_compressed(OUT, X=np.stack(X), Q=np.stack(Q), S=S, gauges=np.array(keep),
                        huc=sel.huc_02.astype(int).values, dates=dates.values.astype("datetime64[D]"),
                        static_names=np.array(STATIC), area=np.array(areas),
                        lat=sel.gauge_lat.values, lon=sel.gauge_lon.values)
    meta = sel[["huc_02", "gauge_name", "gauge_lat", "gauge_lon", "area_gages2", "aridity", "frac_snow",
                "p_mean", "q_mean", "baseflow_index", "high_q_freq"]]
    meta.to_csv(os.path.join(DATA, "camels_sel_meta.csv"))
    print(f"saved {len(keep)} basins, {len(dates)} days -> {OUT}")
    print("missing-Q fraction:", np.isnan(np.stack(Q)).mean().round(4))


if __name__ == "__main__":
    main()
