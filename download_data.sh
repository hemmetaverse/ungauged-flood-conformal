#!/bin/zsh
# Download CAMELS-US (Newman et al., 2014/2015; Addor et al., 2017; CC-BY-4.0) from its Zenodo mirror
# and extract only the Daymet basin-mean forcing and USGS streamflow needed here.
# Usage: ./download_data.sh /path/to/camels_us      (about 3.4 GB download, about 0.8 GB extracted)
set -e
DIR=${1:-data/camels_us}
mkdir -p "$DIR" && cd "$DIR"
BASE="https://zenodo.org/api/records/15529996/files"
for f in clim geol hydro name soil topo vege; do
  curl -fL -o camels_$f.txt "$BASE/camels_$f.txt/content"
done
curl -fL -C - -o basin_timeseries.zip "$BASE/basin_timeseries_v1p2_metForcing_obsFlow.zip/content"
unzip -q -o basin_timeseries.zip 'basin_dataset_public_v1p2/basin_mean_forcing/daymet/*' 'basin_dataset_public_v1p2/usgs_streamflow/*'
echo "CAMELS-US ready in $(pwd)"
