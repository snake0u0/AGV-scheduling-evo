# DeroussiNorre travel times - provenance

9x9 asymmetric travel-time matrix (index 0 = LU depot, 1..8 = M1..M8), row = from, col = to.

Transcribed 2026-07-31 from **TABLE 5 "Layout and the travel times"** of
`fjspt_instances_deroussinorre2010-1.pdf`, downloaded from the dataset page named by
Han et al. (2024):
https://fastmanufacturingproject.wordpress.com/2019/04/11/fjspt-instances/
(direct file: .../wp-content/uploads/2019/04/fjspt_instances_deroussinorre2010-1.pdf)

The same PDF's TABLE 4 lists the job sets; it matches `DeroussiNorre/fjsp*.txt` exactly
(verified on fjsp1: J1 = M1;M2(16) M3;M4(32) M7;M8(24)).

NOTE: these instances have **8 machines**, not 4. Earlier sessions assumed 4 machines and
a 5x5 matrix, which is why all 8 reconstruction hypotheses failed. The flexibility-2
structure comes from machines being paired (M1;M2), (M3;M4), (M5;M6), (M7;M8) - not from
there being only 4 of them.

This matrix is NOT the same as `BerterottiereTravelTimes/layout8.txt`, which belongs to the
Dauzere-Peres & Paulli instances. Do not interchange them.
