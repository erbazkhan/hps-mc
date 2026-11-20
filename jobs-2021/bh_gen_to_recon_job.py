"""!
@file bh_gen_to_recon_job.py

Pure Bethe-Heitler tridents, 2021, no pulser overlay:
MG5(name='BH') -> StdHepConverter (lhe_v1) -> AddMother -> BeamCoords -> SLIC
-> FilterBunches (default ECal-energy cut, 250 empty bunches between events) -> readout -> recon -> MiniDST.

Same chain as tritrig_gen_to_recon_job.py with the MG5 process 'BH' (generators/madgraph5/src/BH, the process
with the dsample.f fix; not HPS_soCalledBH). AddMother is kept as in the BH+pulser production
(production/jobscripts/bh_pulser_gen_to_recon_job.py): the BH final state is e+e-e- like tritrig.
"""
from hpsmc.generators import MG5, StdHepConverter
from hpsmc.tools import SLIC, JobManager, FilterBunches, BeamCoords, AddMother, ProcessMiniDst

job.description = 'BH gen to recon, 2021, no pulser'

## Per-job random seed. hps-mc only passes the job-param seed to MG5; SLIC and BeamCoords
## default to seed 1, which would give every parallel job the same random streams.
seed = job.params['seed'] if 'seed' in job.params else 1

## Generate BH in MG5
mg = MG5(name='BH')

## Convert LHE output to stdhep
cnv = StdHepConverter()

## Add mother particle to tag trident particles
mom = AddMother()

## Rotate events into beam coords
rot = BeamCoords(seed=seed)

## Simulate events in SLIC
sim = SLIC(seed=seed)

## Keep events with ECal energy and insert the empty bunches expected by the pile-up simulation
filter_bunches = FilterBunches(inputs=['BH_unweighted_events_mom_rot.slcio'], outputs=['bh_filt.slcio'])

## Readout (singles triggers)
readout = JobManager(steering='readout', inputs=filter_bunches.output_files(),
                     outputs=['bh_readout.slcio'], ignore_job_params=['nevents'])

## Physics reconstruction
recon = JobManager(steering='recon', inputs=readout.output_files(),
                   outputs=['bh_recon.slcio'], ignore_job_params=['nevents'])

## MiniDST from the recon file (make_mini_dst from [ProcessMiniDst] minidst_install_dir in .hpsmc)
mdst = ProcessMiniDst(inputs=['bh_recon.slcio'], outputs=['bh_recon_minidst.root'], minidst_args=['-a'])

## One tag per step output (make_jobs.py "keep_outputs" chooses which ones are copied out):
job.ptag('lhe', 'BH_unweighted_events.lhe.gz')          # MadGraph events
job.ptag('conv', 'BH_unweighted_events.stdhep')         # after lhe_v1 (EGS5 target transport)
job.ptag('mom', 'BH_unweighted_events_mom.stdhep')      # after AddMother
job.ptag('rot', 'BH_unweighted_events_mom_rot.stdhep')  # after BeamCoords = SLIC input
job.ptag('sim', 'BH_unweighted_events_mom_rot.slcio')   # SLIC output
job.ptag('filt', 'bh_filt.slcio')                       # after FilterBunches
job.ptag('readout', 'bh_readout.slcio')
job.ptag('recon', 'bh_recon.slcio')
job.ptag('minidst', 'bh_recon_minidst.root')

job.add([mg, cnv, mom, rot, sim, filter_bunches, readout, recon, mdst])
