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
