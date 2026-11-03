"""!
@file tritrig_pulser_gen_to_recon_job.py

Tritrig generation -> SLIC, then 2021 pulser-data overlay -> readout -> recon.

Generation half is tritrig_gen_to_recon_job.py (MG5 -> lhe_v1 -> AddMother -> BeamCoords -> SLIC).
Overlay half is the same as ap_pulser_gen_to_recon_job.py / the group's run-14272 production
(python/jobs/signal_pulser_overlay_to_recon_job.py):
  ExtractEventsWithHitAtHodoEcal (>=1 hodo hit, no spacing)
  -> Overlay.lcsim (each MC event gets the next pulser-data event)
  -> FilterBunches (no cuts, 250 empty bunches between events)
  -> readout (PhysicsRun2021TrigSinglesWithPulserDataMerging) -> recon.

Job param **pulser_file**: pulser-data LCIO file (run 14272, v9_14272), read in place.
It must have more events than pass the hodo/ecal filter.
"""
from hpsmc.generators import MG5, StdHepConverter
from hpsmc.tools import (SLIC, JobManager, FilterBunches, BeamCoords, AddMother,
                         ExtractEventsWithHitAtHodoEcal)

job.description = 'tritrig gen to recon with 2021 pulser-data overlay'

## Per-job random seed. hps-mc only passes the job-param seed to MG5; SLIC and BeamCoords
## default to seed 1, which would give every parallel job the same random streams.
seed = job.params['seed'] if 'seed' in job.params else 1

if 'pulser_file' not in job.params:
    raise Exception("Missing required job parameter pulser_file")
pulser_file = job.params['pulser_file']

## Generate tritrig in MG5
mg = MG5(name='tritrig')

## Convert LHE output to stdhep
stdhep_cnv = StdHepConverter()

## Add mother particle to tag trident particles
mom = AddMother()

## Rotate events into beam coords
rot = BeamCoords(seed=seed)

## Simulate events in SLIC
sim = SLIC(seed=seed)

## Keep events with >=1 hodoscope hit (and ECal hits); no spacing yet
filter_events = ExtractEventsWithHitAtHodoEcal(inputs=sim.output_files(), outputs=["tritrig_filt.slcio"],
                                               event_interval=0, num_hodo_hits=1)

## Overlay each MC event with one pulser-data event
overlay = JobManager(steering='overlay', inputs=filter_events.output_files(),
                     overlay_file=pulser_file, outputs=["tritrig_pulser.slcio"],
                     ignore_job_params=['nevents'])

## Insert 250 empty bunches between overlaid events
space_overlay = FilterBunches(inputs=overlay.output_files(), outputs=["tritrig_pulser_spaced.slcio"],
                              filter_no_cuts=True, filter_event_interval=250)

## Readout with pulser-data merging, singles2 + singles3 triggers
readout = JobManager(steering='readout', inputs=space_overlay.output_files(),
                     outputs=["tritrig_pulser_readout.slcio"], ignore_job_params=['nevents'])

## Run physics reconstruction
recon = JobManager(steering='recon', inputs=readout.output_files(),
                   outputs=["tritrig_pulser_recon.slcio"], ignore_job_params=['nevents'])

## Set persistency tags for output files
## One tag per step output (make_jobs.py "keep_outputs" chooses which ones are copied out):
job.ptag('lhe', 'tritrig_unweighted_events.lhe.gz')            # MadGraph events
job.ptag('conv', 'tritrig_unweighted_events.stdhep')           # after lhe_v1 (EGS5 target transport)
job.ptag('mom', 'tritrig_unweighted_events_mom.stdhep')        # after AddMother
job.ptag('rot', 'tritrig_unweighted_events_mom_rot.stdhep')    # after BeamCoords = SLIC input
job.ptag('sim', 'tritrig_unweighted_events_mom_rot.slcio')     # SLIC output
job.ptag('filt', 'tritrig_filt.slcio')                         # after ExtractEventsWithHitAtHodoEcal
job.ptag('overlay', 'tritrig_pulser.slcio')                    # MC + pulser data merged
job.ptag('spaced', 'tritrig_pulser_spaced.slcio')              # after FilterBunches spacing
job.ptag('readout', 'tritrig_pulser_readout.slcio')
job.ptag('recon', 'tritrig_pulser_recon.slcio')

job.add([mg, stdhep_cnv, mom, rot, sim, filter_events, overlay, space_overlay, readout, recon])
