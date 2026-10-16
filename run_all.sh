#!/bin/zsh
# Usage: CAMELS_DIR=/path/to/camels_us ./run_all.sh [seeds...]
set -e
cd "$(dirname "$0")"
DATA=$CAMELS_DIR/camels_sel.npz
OUT=${OUT:-results}
SEEDS=(${@:-0})
for s in $SEEDS; do
  for k in 0 1 2 3 4; do
    [ -f $OUT/preds/pub_F$((k+1))_s$s.npz ] || python3 train.py --data $DATA --scheme pub --fold $k --seed $s --out $OUT/preds
  done
  for k in 0 1 2 3 4 5; do
    ls $OUT/preds/region_R$((k+1))_*_s$s.npz >/dev/null 2>&1 || python3 train.py --data $DATA --scheme region --fold $k --seed $s --out $OUT/preds
  done
done
for sch in pub region; do
  for a in 0.1 0.02; do python3 conformal.py --data $DATA --preds $OUT/preds --scheme $sch --alpha $a --out $OUT; done
done
