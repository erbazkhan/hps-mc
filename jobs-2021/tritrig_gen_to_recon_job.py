"""!
@file tritrig_gen_to_recon_job.py

Tritrig signal generation through SLIC, filter bunching, readout, and recon.
This is tritrig_slic_full_chain_job.py from the hps-mc repo with the final
two HPSTR components (LCIO->ROOT conversion and analysis) removed, since
this build doesn't have hpstr installed (using hps-analysis/MiniDst instead,
which is a separate downstream step to be chained on later).
"""
from hpsmc.generators import MG5, StdHepConverter
from hpsmc.tools import SLIC, JobManager, FilterBunches, BeamCoords, AddMother

job.description = 'tritrig gen to recon (testing -- no HPSTR/ana step)'

## Per-job random seed. hps-mc only passes the job-param seed to MG5; SLIC, BeamCoords and
## DisplaceTime default to seed 1, which would give every parallel job the same random streams.
seed = job.params['seed'] if 'seed' in job.params else 1

## Generate tritrig in MG5
mg = MG5(name='tritrig')

## Convert LHE output to stdhep
stdhep_cnv = StdHepConverter()

## Add mother particle to tag trident particles
mom = AddMother()

## Rotate events into beam coords
rot = BeamCoords(seed=seed)

## generate events in slic
sim = SLIC(seed=seed)

## insert empty bunches expected by pile-up simulation
filter_bunches = FilterBunches()

## Run simulated events in readout to generate triggers
readout = JobManager(steering='readout', ignore_job_params=['nevents'])

## Run physics reconstruction
recon = JobManager(steering='recon', ignore_job_params=['nevents'])

## Set persistency tags for output files
job.ptag('gen', 'tritrig_unweighted_events_mom_rot.stdhep')
job.ptag('sim', 'tritrig_unweighted_events_mom_rot.slcio')
job.ptag('readout', 'tritrig_unweighted_events_mom_rot_filt_readout.slcio')
job.ptag('recon', 'tritrig_unweighted_events_mom_rot_filt_readout_recon.slcio')

## Add job components -- stops at recon, no HPSTR
job.add([mg, stdhep_cnv, mom, rot, sim, filter_bunches, readout, recon])
