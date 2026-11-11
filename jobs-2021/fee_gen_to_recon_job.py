"""!
Simulation of beam, beam signals in detector (using SLIC), and readout.
The simulation is followed by reconstruction of the events.
"""
from hpsmc.generators import EGS5
from hpsmc.tools import BeamCoords, RandomSample, SLIC, ExtractEventsWithHitAtHodoEcal, JobManager

from hpsmc.tools import ProcessMiniDst

job.description = 'beam from generation to slic'

## Get job input file targets
inputs = list(job.input_files.values())

if 'nevents' in job.params:
    nevents = job.params['nevents']
else:
    nevents = 250000

## Per-job seed for BeamCoords and SLIC (hps-mc only passes it to the generator)
seed = job.params['seed'] if 'seed' in job.params else 1

## Generate beam
egs5 = EGS5(name="beam_v7_%s" % job.params['run_params'])

## Rotate events into beam coordinates
rot = BeamCoords(seed=seed)

## Sample events into new stdhep file
sample = RandomSample()

## Simulate events
slic = SLIC(nevents=nevents + 1, seed=seed)

## Space signal events
space_events = ExtractEventsWithHitAtHodoEcal(event_interval=250, num_hodo_hits=0)

## Run simulated events in readout to generate triggers
readout = JobManager(steering='readout', ignore_job_params=['nevents'])

## Run physics reconstruction
recon = JobManager(steering='recon', ignore_job_params=['nevents'])

## Set persistency tags for output files
job.ptag('sim', 'beam_rot_sampled.slcio')
job.ptag('readout', 'beam_rot_sampled_filt_readout.slcio')
job.ptag('recon', 'beam_rot_sampled_filt_readout_recon.slcio')

## Run the job
## MiniDST from the recon file (make_mini_dst from [ProcessMiniDst] minidst_install_dir in .hpsmc)
mdst = ProcessMiniDst(inputs=['beam_rot_sampled_filt_readout_recon.slcio'], outputs=['beam_rot_sampled_filt_readout_recon_minidst.root'], minidst_args=['-a'])
job.ptag('minidst', 'beam_rot_sampled_filt_readout_recon_minidst.root')

job.add([egs5, rot, sample, slic, space_events, readout, recon, mdst])
