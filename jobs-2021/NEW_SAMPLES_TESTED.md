# New 2021 job scripts: WAB pure, BH pure, BH + pulser (tested 2026-11-19 on endeavour)

| Script | Example json | Chain |
|---|---|---|
| `wab_gen_to_recon_job.py` | `examples/wab_pure_job_0001.json` | MG5 `WAB` -> lhe_v1 -> BeamCoords -> SLIC -> FilterBunches -> readout `PhysicsRun2021TrigMultiSingles` -> recon -> MiniDST |
| `bh_gen_to_recon_job.py` | `examples/bh_pure_job_0001.json` | MG5 `BH` -> lhe_v1 -> AddMother -> BeamCoords -> SLIC -> FilterBunches -> readout `PhysicsRun2021TrigMultiSingles` -> recon -> MiniDST |
| `bh_pulser_gen_to_recon_job.py` | `examples/bh_pulser_job_0001.json` | MG5 `BH` -> lhe_v1 -> AddMother -> BeamCoords -> SLIC -> ExtractEventsWithHitAtHodoEcal -> Overlay -> FilterBunches(250) -> readout `PhysicsRun2021TrigSinglesWithPulserDataMerging` -> recon -> MiniDST |

Common to all three: run 14272, 3.74 GeV (`run_params` 3pt74), detector `HPS_Run2021Pass1_v9_14272`, target z -1.1 mm,
beam sigma 0.055/0.045 mm, beam_rot_y 0.0305, bunches 10000 (same as `examples/tritrig_pulser_job_0001.json`),
recon `PhysicsRun2021MCRecon_KF_WithSpacing_pass5_physics_HitSmear_HitKill_14272.lcsim`, conditions
`jdbc:sqlite:/net/home/erbaz/ws/hps_conditions_11102025_moller_5.db`. The job seed goes to MG5, BeamCoords and SLIC.
`ignore_job_params=['nevents']` is set on overlay, readout and recon. Every step has a ptag. The last step is ProcessMiniDst with `minidst_args=['-a']`.

Decisions to be aware of:
- WAB pure has no AddMother, as in `wab_pulser_gen_to_recon_job.py` and the stock `wab_gen_mg5_job.py`.
- BH pure and BH + pulser keep AddMother, as in the 987k-event BH + pulser production
  (`production/jobscripts/bh_pulser_gen_to_recon_job.py`).
- The pure samples use FilterBunches with its default ECal-energy cut, like `tritrig_gen_to_recon_job.py`.
- MG5 `BH` maps to `generators/madgraph5/src/BH` (the process with the dsample.f fix), not `HPS_soCalledBH`.

## Test results (one job each)

| | WAB pure | BH pure | BH + pulser |
|---|---|---|---|
| seed | 9100001 | 9200001 | 9300001 |
| nevents | 100000 | 10000 | 10000 |
| MG5 cross-section (pb) | 8.262e+10 +- 2.589e+10 | 4.029e+09 +- 9.048e+06 | 4.030e+09 +- 9.493e+06 |
| SLIC events | 100000 | 10000 | 10000 |
| after filter | 19965 (FilterBunches ECal cut, 20.0%) | 1119 (FilterBunches ECal cut, 11.2%) | 1740 (hodo+ecal filter, 17.4%) |
| after overlay | - | - | 1740 |
| after spacing (incl. empty bunches) | 4,991,250 (= 19965 x 250) | 279,750 (= 1119 x 250) | 435,000 (= 1740 x 250) |
| triggers ("Wrote N triggers") | 56 | 233 | 224 |
| recon events (anajob) | 56 | 233 | 224 |
| MiniDST entries / branches | 56 / 192 | 233 / 192 | 224 / 192 |
| MiniDST / generated | 0.056% | 2.33% | 2.24% |
| job wall time | 48.7 min | 7.3 min | 9.3 min |
| max RSS | 2.0 GB | 1.5 GB | 1.6 GB |

Time per step (s):

| step | WAB pure | BH pure | BH + pulser |
|---|---|---|---|
| MG5 | 1370.0 | 277.5 | 375.9 |
| lhe_v1 | 6.4 | 2.4 | 1.6 |
| add_mother | - | 0.7 | 0.5 |
| beam_coords | 4.0 | 0.5 | 0.4 |
| slic | 649.2 | 60.2 | 53.1 |
| filter (hodo/ecal) | - | - | 3.1 |
| overlay | - | - | 12.0 |
| filter_bunches | 291.0 | 19.7 | 28.3 |
| readout | 588.1 | 52.3 | 59.3 |
| recon | 2.4 | 4.3 | 18.6 |
| make_mini_dst | 0.7 | 15.0 | 0.6 |

All three jobs ran in parallel on endeavour, so the MG5 times are a little inflated (wall-clock times).

Cross-checks against earlier samples:
- **WAB:** cross-section 8.262e10 pb vs. the production mean of 8.240e10 pb (`wab_pulser_run14272/MC_INFO.md`).
  The per-job uncertainty is 31% (production jobs: ~15% at 500k events).
- **BH:** cross-section 4.03e9 pb vs. 4.007e9 pb (Nov 9 test) and 4.02e9 pb (BH + pulser pilot).
- **BH + pulser yield:** 2.24% vs. 2.23% in production.
- **BH pure:** 233 MiniDST entries per 10k vs. 226 in the Nov 9 test.

**MG5 log check** (all exit codes were 0):
- `job.log` has no compile or make errors. The only "Error" line is WAB's `Error: no DISPLAY environment variable specified`, which is harmless.
- In the channel logs (`scratch/<proc>/SubProcesses/*/G*/*log.txt`):
  - `Error opening grid` is the normal first-iteration message.
  - `Error in matrix element` appears 61 times (WAB), 4 times (BH) and once (BH + pulser). This is a runtime message from MG5's own generated `auto_dsig1.f`. It is printed when the matrix element at a phase-space point is not positive, and that point gets weight 0. It is not a compile error.
  - I could not compare these counts with production because production keeps no channel logs. **Guess:** these are rare numerically bad points near the collinear edge; the cross-sections agree with production.

**SLIC:**
- Every SLIC run returns rc -6 (`free(): invalid pointer` at exit) after printing `return code: 0 => okay`. This is the known exit crash after a clean finish.
- No segfault. The sim files hold all nevents.

## Commands

```bash
cd ~/hps-mc && git fetch fork && git reset --keep fork/jobscripts-2021          # -> 452ab9e9
cp install/lib/python/hpsmc/tools.py install/lib/python/hpsmc/tools.py.bak_20261119
cp python/hpsmc/tools.py install/lib/python/hpsmc/tools.py                      # fixed ProcessMiniDst
```

Test dirs: `~/hps-mc/testruns/newsamples_2021/{wab,bh,bh_pulser}`.
- Each holds a copy of the job script, a `job.json` (the example json, but with only lhe/recon/minidst outputs), a `.hpsmc` and a `run.sh`.
- `.hpsmc` = `testruns/bh_2021_test/.hpsmc` (sqlite DB for JobManager/FilterBunches/ExtractEventsWithHitAtHodoEcal) plus:

```
[ProcessMiniDst]
minidst_install_dir = <dir with bin/make_mini_dst>
```

`run.sh`:
```bash
cd $(dirname $0)
export JAVA_TOOL_OPTIONS="-Dorg.lcsim.cacheDir=/net/home/erbaz/ws -Xmx3g"
/usr/bin/time -v hps-mc-job run -d $PWD/scratch $PWD/<name>_gen_to_recon_job.py job.json > job.log 2>&1
```

Counts: the `Read N events, wrote M` lines in job.log (filters), `Wrote N triggers` (readout), `anajob <file> | grep -c EVENT:`
(LCIO files), and ROOT `MiniDST->GetEntries()` / `GetListOfBranches()->GetEntries()`.

## Things that needed attention

1. **make_mini_dst on endeavour needs a wrapper.**
   - Maurik's production binary (`/net/home/maurik/hps-analysis/build/MiniDst/bin/make_mini_dst`) must run in a clean
     environment with ROOT 6.40.05. With the job's ROOT it fails with a libRIO undefined symbol (see CLAUDE.md item 99).
   - `~/hps-analysis` was deleted on Nov 9, so there is no own install.
   - The test pointed `minidst_install_dir` at a wrapper directory whose `bin/make_mini_dst` runs:
     ```bash
     env -i HOME=$HOME PATH=/usr/bin:/bin bash -c "source /net/data/endeavour2/Tools/root-6.40.05-gcc11.5.0/bin/thisroot.sh; \
       export LD_LIBRARY_PATH=/net/home/maurik/AlmaLinux/lib:\$LD_LIBRARY_PATH; cd <cwd>; \
       exec /net/home/maurik/hps-analysis/build/MiniDst/bin/make_mini_dst <args>"
     ```
   - This is the same idea as `farm-jlab/minidst/bin/make_mini_dst`. The wrapper was a session scratch file and is not committed. For
     endeavour production it should be kept somewhere permanent, for example next to `production/run_one.sh`.
2. **`lcio_event_counter` undercounts.**
   - It reported 231 recon events for BH pure, while anajob, the MiniDST and "Wrote 233 triggers" all give 233.
   - For BH + pulser it reported 218 vs. 224.
   - In spaced files it counts only non-empty events.
   - Use anajob (or the MiniDST) for bookkeeping. Earlier numbers taken with `lcio_event_counter` may be a few events low (not checked).
3. **Pulser piece reuse.** Every pulser piece is already allocated (`pulser_pieces/allocations.txt`). The BH + pulser test and its
   example json reuse `p234/pulser_234.003.slcio` (the tritrig_pulser_beamspot job 0001 piece). This is fine for a test. A new
   production needs fresh pulser data.
4. No changes were needed in hps-mc itself. The fixed ProcessMiniDst works inside the job for all three samples.
