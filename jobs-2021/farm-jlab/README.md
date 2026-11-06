# hps-mc on the JLab ifarm

Validated chain: MG5 -> SLIC -> FilterBunches -> readout -> recon -> MiniDST (A' 100 MeV, run 14272).
Reference (endeavour) vs ifarm: MG5 xsec 1.059e15 pb both; filter 5563 vs 5545; MiniDST 2742 vs 2748.

## Layout ($HPSMC_DEV)
- hps-mc/install   hps-mc build (branch jobscripts-2021 = jlab-port + job scripts)
- hps-java         commit 4d47d0383, built with Java 8: mvn -q clean install -DskipTests
- py27, pybin      conda python=2.7 (+ pip install six); pybin/ holds only a python2 symlink
- sw               sw/<detector>/ (for SLIC) and sw/.lcsim/detectors/<detector>/ (for hps-java)
- hps-mc/install/share/fieldmap -> /group/hps/share/fieldmap (checked identical to endeavour's for the 2021 map)
- Conditions DB: /work/hallb/hps/mgignac/db/hps_conditions_11102025_moller_5.db (see hpsmc.template)

## Things that bit us
1. Use bash (the login shell is tcsh).
2. MG5 for ap/WAB runs `python2`; it needs the `six` module.
3. SLIC needs GDML_SCHEMA_DIR=/group/hps/share, or it tries to download lcdd.xsd and fails.
4. The detector must exist twice: sw/<name>/ (SLIC) and sw/.lcsim/detectors/<name>/ (hps-java).
5. Source slic-env.sh BEFORE hps-mc-env.sh: /group/hps/bin has an older hps-mc-job.
6. The run directory must be empty: rm -rf scratch before each run (delete_existing is not reliable).
7. Maurik's jars lack the 2021 recon steering; use the jar built from hps-java 4d47d0383.
8. make_mini_dst needs ROOT libs only at run time: use the mini_dst function from setup.sh.
9. Interactive runs first; batch usage (account hallb, partition production) not yet validated.

## Batch (swif2) notes — validated with a 1-job A' test (MiniDST agrees with interactive within 0.6%)
10. `hps-mc-batch swif` runs `hps-mc-env.csh` then `jlab-env.csh` in tcsh. Our `farm-jlab/jlab-env.csh` replaces the generated one (the generated one has an empty ROOT path); link it into `install/bin/`.
11. Submit with `-P hallb` (the default account hallb-pro is rejected for our users) and, for short tests, `-q priority -W 4`.
12. Batch nodes cannot run libraries from /tmp (sqlite-jdbc fails: "failed to map segment"); jlab-env.csh sets `-Djava.io.tmpdir=$HPSMC_DEV/tmp`.
13. Run the submit command once; running it twice created a duplicate job (remove with `swif2 abandon-jobs -workflow <wf> -problems <type>`).
14. Job scripts are found by name under `install/lib/python/jobs/`; the jobstore is a JSON list with a `job_id` per job. MiniDST is not yet inside the job script.
