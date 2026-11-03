"""!
@file wab_pulser_gen_to_recon_job.py

WAB (wide-angle bremsstrahlung, MG5 process `e- N > e- a N`) generation -> SLIC, then 2021 pulser-data
overlay -> readout -> recon. Same overlay/readout/recon chain as tritrig_pulser_gen_to_recon_job.py.

Generation as in the stock python/jobs/wab_gen_mg5_job.py: MG5(name="WAB") -> StdHepConverter (lhe_v1, EGS5
transport through the target) -> BeamCoords -> SLIC. No AddMother label (the stock WAB job has none).

Job param **pulser_file**: one pulser-data piece (run 14272, v9_14272), read in place; it must have more events
than pass the hodo/ecal filter.
"""
from hpsmc.generators import MG5, StdHepConverter
from hpsmc.tools import SLIC, JobManager, FilterBunches, BeamCoords, ExtractEventsWithHitAtHodoEcal

job.description = 'WAB gen to recon with 2021 pulser-data overlay'

## Per-job random seed: hps-mc only passes the job-param seed to MG5 (and EGS5); SLIC and BeamCoords
## default to seed 1, which would give every parallel job the same random streams.
seed = job.params['seed'] if 'seed' in job.params else 1

if 'pulser_file' not in job.params:
    raise Exception("Missing required job parameter pulser_file")
pulser_file = job.params['pulser_file']

## Generate WAB events in MG5 (unweighted events are the first output)
mg = MG5(name='WAB', event_types=['unweighted'])   # WAB writes no weighted-events file

## Convert LHE output to stdhep (EGS5 lhe_v1: transport through the target)
cnv = StdHepConverter()

## Rotate events into beam coords (beam spot, rotation, target position from the job params)
rot = BeamCoords(seed=seed)

## Simulate events in SLIC
sim = SLIC(seed=seed)

## Keep events with >=1 hodoscope hit (and ECal hits); no spacing yet
filter_events = ExtractEventsWithHitAtHodoEcal(inputs=sim.output_files(), outputs=["wab_filt.slcio"],
                                               event_interval=0, num_hodo_hits=1)

## Overlay each MC event with one pulser-data event
overlay = JobManager(steering='overlay', inputs=filter_events.output_files(),
                     overlay_file=pulser_file, outputs=["wab_pulser.slcio"],
                     ignore_job_params=['nevents'])

## Insert 250 empty bunches between overlaid events
space_overlay = FilterBunches(inputs=overlay.output_files(), outputs=["wab_pulser_spaced.slcio"],
                              filter_no_cuts=True, filter_event_interval=250)

## Readout with pulser-data merging, singles2 + singles3 triggers
readout = JobManager(steering='readout', inputs=space_overlay.output_files(),
                     outputs=["wab_pulser_readout.slcio"], ignore_job_params=['nevents'])

## Run physics reconstruction
recon = JobManager(steering='recon', inputs=readout.output_files(),
                   outputs=["wab_pulser_recon.slcio"], ignore_job_params=['nevents'])

## One tag per step output (make_jobs.py "keep_outputs" chooses which ones are copied out):
job.ptag('lhe', 'WAB_unweighted_events.lhe.gz')       # MadGraph events
job.ptag('conv', 'WAB_unweighted_events.stdhep')               # after lhe_v1 (EGS5 target transport)
job.ptag('rot', 'WAB_unweighted_events_rot.stdhep')                # after BeamCoords = SLIC input
job.ptag('sim', 'WAB_unweighted_events_rot.slcio')                # SLIC output
job.ptag('filt', 'wab_filt.slcio')                    # after ExtractEventsWithHitAtHodoEcal
job.ptag('overlay', 'wab_pulser.slcio')               # MC + pulser data merged
job.ptag('spaced', 'wab_pulser_spaced.slcio')         # after FilterBunches spacing
job.ptag('readout', 'wab_pulser_readout.slcio')
job.ptag('recon', 'wab_pulser_recon.slcio')

job.add([mg, cnv, rot, sim, filter_events, overlay, space_overlay, readout, recon])
