## Point skill pub
median NSE 0.657 | median KGE 0.613 | NSE<0: 5.0% | n=558

        nse    kge
fold              
F1    0.643  0.600
F2    0.676  0.640
F3    0.669  0.607
F4    0.646  0.616
F5    0.642  0.616

## Intervals pub alpha=0.1
         Coverage  Coverage Q95+  Coverage Q99+  Missed above Q95+  Regime gap  Rel. width  Rel. width Q95+  Winkler (median)  Winkler (mean)  Basins under-covered (%)
method                                                                                                                                                                 
QR          0.661          0.625          0.590              0.334       0.108       1.009            6.117             3.119           4.013                    82.079
SCP         0.875          0.238          0.109              0.610       0.814       1.254            1.612             4.389           5.676                    21.505
CQR         0.877          0.670          0.612              0.298       0.149       1.341            6.484             2.724           3.550                    24.731
CQR-r       0.879          0.799          0.762              0.199       0.084       1.817           10.751             2.786           3.348                    24.194
RC-CQR      0.876          0.759          0.710              0.231       0.009       1.664            9.168             2.765           3.358                    24.552
DW-CQR      0.890          0.806          0.768              0.194       0.085       1.870           11.037             2.864           3.353                    24.014
DRC-CQR     0.887          0.763          0.712              0.233       0.014       1.624            8.652             2.762           3.271                    24.194

## Intervals pub alpha=0.02
         Coverage  Coverage Q95+  Coverage Q99+  Missed above Q95+  Regime gap  Rel. width  Rel. width Q95+  Winkler (median)  Winkler (mean)  Basins under-covered (%)
method                                                                                                                                                                 
QR          0.835          0.812          0.778              0.172       0.069       1.712           10.087             5.803           8.874                    59.677
SCP         0.974          0.661          0.394              0.289       0.471       4.007            6.142             8.812          14.662                     5.914
CQR         0.977          0.868          0.809              0.126       0.068       2.520           11.078             4.371           6.484                     8.244
CQR-r       0.977          0.936          0.915              0.064       0.019       3.357           18.963             4.363           5.671                     8.602
RC-CQR      0.977          0.921          0.887              0.079       0.004       3.132           16.167             4.252           5.674                     8.781
DW-CQR      0.999          0.993          0.988              0.007       0.001       9.152           51.560             9.330          13.325                     0.358
DRC-CQR     0.999          0.989          0.978              0.011       0.002       7.330           33.077             7.677          11.216                     0.538

## Point skill region
median NSE 0.577 | median KGE 0.540 | NSE<0: 7.9% | n=558

                                nse    kge
fold                                      
R1_Northeast                  0.619  0.598
R2_Southeast                  0.565  0.514
R3_GreatLakes_Ohio_Tennessee  0.634  0.571
R4_Mississippi_Missouri       0.551  0.552
R5_SouthCentral_Southwest     0.394  0.174
R6_PacificNW_California       0.628  0.618

## Intervals region alpha=0.1
         Coverage  Coverage Q95+  Coverage Q99+  Missed above Q95+  Regime gap  Rel. width  Rel. width Q95+  Winkler (median)  Winkler (mean)  Basins under-covered (%)
method                                                                                                                                                                 
QR          0.582          0.573          0.510              0.379       0.133       1.079            6.072             3.892           5.047                    89.247
SCP         0.876          0.295          0.128              0.571       0.762       1.697            2.309             4.790           6.412                    18.817
CQR         0.879          0.640          0.543              0.326       0.198       1.634            6.890             3.232           4.410                    24.194
CQR-r       0.879          0.808          0.765              0.192       0.110       2.388           13.078             3.328           4.102                    27.419
RC-CQR      0.871          0.739          0.675              0.257       0.023       2.016           10.365             3.196           4.038                    28.136
DW-CQR      0.891          0.829          0.786              0.171       0.108       2.512           13.638             3.547           4.441                    23.477
DRC-CQR     0.880          0.749          0.676              0.249       0.030       2.044           10.607             3.312           4.288                    26.344

## Intervals region alpha=0.02
         Coverage  Coverage Q95+  Coverage Q99+  Missed above Q95+  Regime gap  Rel. width  Rel. width Q95+  Winkler (median)  Winkler (mean)  Basins under-covered (%)
method                                                                                                                                                                 
QR          0.773          0.759          0.706              0.221       0.107       1.848           10.182             7.578          12.097                    76.165
SCP         0.970          0.763          0.545              0.204       0.325       7.249           10.315            11.260          17.672                     7.527
CQR         0.975          0.852          0.763              0.141       0.081       3.066           12.038             5.233           8.208                     9.319
CQR-r       0.978          0.948          0.934              0.052       0.016       5.274           28.799             6.153           8.083                     8.781
RC-CQR      0.973          0.912          0.881              0.088       0.008       4.078           20.166             5.159           7.658                    11.290
DW-CQR      0.996          0.993          0.989              0.007       0.003      11.758           64.916            11.986        1122.434                     0.896
DRC-CQR     0.995          0.987          0.976              0.013       0.003       9.500           39.847             9.822         411.703                     1.254

## Paired Wilcoxon signed-rank tests across basins (alpha 0.1)
pub winkler DRC-CQR vs CQR-r: median diff -0.0838, DRC-CQR better in 62.9% basins, p=2.39e-07
pub cov_q95 DRC-CQR vs CQR-r: median diff -0.0436, DRC-CQR better in 21.1% basins, p=1.31e-32
pub relwidth DRC-CQR vs CQR-r: median diff -0.2889, DRC-CQR better in 72.4% basins, p=1.46e-15
pub winkler DRC-CQR vs CQR: median diff -0.0455, DRC-CQR better in 62.0% basins, p=8.19e-08
pub cov_q95 DRC-CQR vs CQR: median diff 0.0650, DRC-CQR better in 95.2% basins, p=4.02e-78
pub relwidth DRC-CQR vs CQR: median diff 0.1797, DRC-CQR better in 26.5% basins, p=1.41e-34
pub winkler DRC-CQR vs RC-CQR: median diff -0.0267, DRC-CQR better in 56.1% basins, p=9.99e-04
pub cov_q95 DRC-CQR vs RC-CQR: median diff -0.0163, DRC-CQR better in 31.4% basins, p=2.35e-05
pub relwidth DRC-CQR vs RC-CQR: median diff -0.1193, DRC-CQR better in 61.3% basins, p=4.02e-02
pub winkler DW-CQR vs CQR-r: median diff -0.0056, DW-CQR better in 51.6% basins, p=9.64e-01
pub cov_q95 DW-CQR vs CQR-r: median diff -0.0027, DW-CQR better in 42.1% basins, p=3.51e-01
pub relwidth DW-CQR vs CQR-r: median diff -0.0598, DW-CQR better in 54.5% basins, p=8.88e-02
pub winkler CQR-r vs CQR: median diff 0.0096, CQR-r better in 49.8% basins, p=4.18e-02
pub cov_q95 CQR-r vs CQR: median diff 0.1257, CQR-r better in 96.1% basins, p=9.47e-84
pub relwidth CQR-r vs CQR: median diff 0.4753, CQR-r better in 12.7% basins, p=6.20e-53
region winkler DRC-CQR vs CQR-r: median diff -0.0912, DRC-CQR better in 58.1% basins, p=2.96e-02
region cov_q95 DRC-CQR vs CQR-r: median diff -0.0542, DRC-CQR better in 15.6% basins, p=6.02e-46
region relwidth DRC-CQR vs CQR-r: median diff -0.3894, DRC-CQR better in 78.7% basins, p=1.07e-21
region winkler DRC-CQR vs CQR: median diff 0.0179, DRC-CQR better in 49.5% basins, p=8.11e-01
region cov_q95 DRC-CQR vs CQR: median diff 0.0919, DRC-CQR better in 93.9% basins, p=7.77e-74
region relwidth DRC-CQR vs CQR: median diff 0.3425, DRC-CQR better in 21.7% basins, p=1.81e-34
region winkler DRC-CQR vs RC-CQR: median diff 0.0294, DRC-CQR better in 45.9% basins, p=2.68e-04
region cov_q95 DRC-CQR vs RC-CQR: median diff -0.0054, DRC-CQR better in 40.9% basins, p=2.68e-01
region relwidth DRC-CQR vs RC-CQR: median diff -0.0209, DRC-CQR better in 51.6% basins, p=8.89e-03
region winkler DW-CQR vs CQR-r: median diff 0.0273, DW-CQR better in 44.6% basins, p=1.73e-05
region cov_q95 DW-CQR vs CQR-r: median diff 0.0000, DW-CQR better in 48.7% basins, p=1.10e-04
region relwidth DW-CQR vs CQR-r: median diff 0.0954, DW-CQR better in 41.2% basins, p=1.83e-11
region winkler CQR-r vs CQR: median diff 0.1087, CQR-r better in 44.4% basins, p=5.24e-01
region cov_q95 CQR-r vs CQR: median diff 0.1676, CQR-r better in 94.3% basins, p=1.50e-79
region relwidth CQR-r vs CQR: median diff 0.7170, CQR-r better in 14.9% basins, p=9.87e-41

## Region x method coverage Q95+ (alpha 0.1)
method                          CQR  CQR-r  DRC-CQR     QR  RC-CQR
fold                                                              
R1_Northeast                  0.674  0.875    0.755  0.623   0.800
R2_Southeast                  0.653  0.814    0.758  0.606   0.761
R3_GreatLakes_Ohio_Tennessee  0.637  0.838    0.711  0.583   0.760
R4_Mississippi_Missouri       0.635  0.763    0.713  0.530   0.683
R5_SouthCentral_Southwest     0.570  0.670    0.684  0.455   0.593
R6_PacificNW_California       0.673  0.895    0.866  0.647   0.842

## Region x method coverage overall (alpha 0.1)
method                          CQR  CQR-r  DRC-CQR     QR  RC-CQR
fold                                                              
R1_Northeast                  0.940  0.952    0.949  0.679   0.951
R2_Southeast                  0.871  0.785    0.763  0.474   0.778
R3_GreatLakes_Ohio_Tennessee  0.901  0.896    0.839  0.607   0.893
R4_Mississippi_Missouri       0.942  0.930    0.941  0.619   0.917
R5_SouthCentral_Southwest     0.920  0.836    0.870  0.625   0.821
R6_PacificNW_California       0.715  0.873    0.903  0.485   0.864

