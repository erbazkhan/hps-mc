"""!
@file wab_gen_to_recon_job.py

Pure WAB (wide-angle bremsstrahlung, MG5 process `e- N > e- a N`), 2021, no pulser overlay:
MG5(name='WAB') -> StdHepConverter (lhe_v1, EGS5 transport through the target) -> BeamCoords -> SLIC
-> FilterBunches (default ECal-energy cut, 250 empty bunches between events) -> readout -> recon -> MiniDST.

Generation is the same as wab_pulser_gen_to_recon_job.py (no AddMother, like the stock wab_gen_mg5_job.py);
the readout/recon half is the same as tritrig_gen_to_recon_job.py (readout PhysicsRun2021TrigMultiSingles).
"""
from hpsmc.generators import MG5, StdHepConverter
from hpsmc.tools import SLIC, JobManager, FilterBunches, BeamCoords, ProcessMiniDst

job.description = 'WAB gen to recon, 2021, no pulser'

## Per-job random seed: hps-mc only passes the job-param seed to MG5 (and EGS5); SLIC and BeamCoords
## default to seed 1, which would give every parallel job the same random streams.
seed = job.params['seed'] if 'seed' in job.params else 1

## Generate WAB events in MG5
mg = MG5(name='WAB', event_types=['unweighted'])   # WAB writes no weighted-events file

## Convert LHE output to stdhep (EGS5 lhe_v1: transport through the target)
cnv = StdHepConverter()

## Rotate events into beam coords (beam spot, rotation, target position from the job params)
rot = BeamCoords(seed=seed)

## Simulate events in SLIC
sim = SLIC(seed=seed)

## Keep events with ECal energy and insert the empty bunches expected by the pile-up simulation
filter_bunches = FilterBunches(inputs=['WAB_unweighted_events_rot.slcio'], outputs=['wab_filt.slcio'])

## Readout (singles triggers)
readout = JobManager(steering='readout', inputs=filter_bunches.output_files(),
                     outputs=['wab_readout.slcio'], ignore_job_params=['nevents'])

## Physics reconstruction
recon = JobManager(steering='recon', inputs=readout.output_files(),
                   outputs=['wab_recon.slcio'], ignore_job_params=['nevents'])

## MiniDST from the recon file (make_mini_dst from [ProcessMiniDst] minidst_install_dir in .hpsmc)
mdst = ProcessMiniDst(inputs=['wab_recon.slcio'], outputs=['wab_recon_minidst.root'], minidst_args=['-a'])

## One tag per step output (make_jobs.py "keep_outputs" chooses which ones are copied out):
job.ptag('lhe', 'WAB_unweighted_events.lhe.gz')        # MadGraph events
job.ptag('conv', 'WAB_unweighted_events.stdhep')       # after lhe_v1 (EGS5 target transport)
job.ptag('rot', 'WAB_unweighted_events_rot.stdhep')    # after BeamCoords = SLIC input
job.ptag('sim', 'WAB_unweighted_events_rot.slcio')     # SLIC output
job.ptag('filt', 'wab_filt.slcio')                     # after FilterBunches
job.ptag('readout', 'wab_readout.slcio')
job.ptag('recon', 'wab_recon.slcio')
job.ptag('minidst', 'wab_recon_minidst.root')

job.add([mg, cnv, rot, sim, filter_bunches, readout, recon, mdst])
