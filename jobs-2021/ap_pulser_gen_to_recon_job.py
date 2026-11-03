"""!
@file ap_pulser_gen_to_recon_job.py

A-prime generation -> SLIC, then 2021 pulser-data overlay -> readout -> recon.

Generation half is the same as testruns/ap_gen_to_recon/ap_gen_to_recon_job.py
(MG5 -> DisplaceTime -> BeamCoords -> SLIC).
Overlay half follows python/jobs/signal_pulser_overlay_to_recon_job.py, as used
by the group's run-14272 production (MC_test/run_signal_pulser/job_14272.json.tmpl):
  ExtractEventsWithHitAtHodoEcal (>=1 hodo hit, no spacing)
  -> Overlay.lcsim (each MC event gets the next pulser-data event)
  -> FilterBunches (no cuts, 250 empty bunches between events)
  -> readout (PhysicsRun2021TrigSinglesWithPulserDataMerging) -> recon.

Job param **pulser_file**: pulser-data LCIO file (run 14272, v9_14272), read in
place (not copied). It must have more events than pass the hodo/ecal filter.
"""
from hpsmc.generators import MG5, StdHepConverter
from hpsmc.tools import (DisplaceTime, Unzip, BeamCoords, AddMotherFullTruth, SLIC,
                         ExtractEventsWithHitAtHodoEcal, FilterBunches, JobManager)


class DisplaceFlatZ(DisplaceTime):
    """! DisplaceTime with the A' decay z drawn uniformly in [0, zmax] mm from the production point
    (option -u of stdhep_lhe_tridents_displacetime, added 2026-10-04). Gives a flat true decay-z
    distribution; analyses reweight it to any c*tau."""

    def __init__(self, zmax, **kwargs):
        self.zmax = zmax
        DisplaceTime.__init__(self, **kwargs)

    def cmd_args(self):
        return DisplaceTime.cmd_args(self) + ["-u", str(self.zmax)]

job.description = 'ap gen to recon with 2021 pulser-data overlay'

## Per-job random seed. hps-mc only passes the job-param seed to MG5; SLIC, BeamCoords and
## DisplaceTime default to seed 1, which would give every parallel job the same random streams.
seed = job.params['seed'] if 'seed' in job.params else 1

if 'nevents' in job.params:
    nevents = job.params['nevents']
else:
    nevents = 10000

if 'pulser_file' not in job.params:
    raise Exception("Missing required job parameter pulser_file")
pulser_file = job.params['pulser_file']

## Generate A' in MG5
mg = MG5(name='ap', event_types=['unweighted'])

if 'ap_decay_dist' in job.params:
    ap_decay_dist = job.params['ap_decay_dist']
else:
    ap_decay_dist = "lhe_uniform"

## Unzip the LHE events to a local file
unzip = Unzip(inputs=["ap_unweighted_events.lhe.gz"], outputs=["ap_unweighted_events.lhe"])

if ap_decay_dist == "lhe_uniform":
    cnv = StdHepConverter(name="lhe_uniform", inputs=["ap_unweighted_events.lhe"])
elif ap_decay_dist == "lhe_prompt":
    cnv = StdHepConverter(name="lhe_prompt", inputs=["ap_unweighted_events.lhe"])
elif ap_decay_dist == "displace_time":
    if 'ctau' in job.params:
        ## DisplaceTime handles the A' (PDG 622): exponential proper decay length, mean ctau [mm].
        cnv = DisplaceTime(seed=seed, inputs=["ap_unweighted_events.lhe"])
    else:
        raise Exception("Missing parameter ctau")
elif ap_decay_dist == "flat_z":
    ## Flat decay z: uniform in [0, decay_z_max] mm downstream of the production point (default 150 mm).
    zmax = job.params['decay_z_max'] if 'decay_z_max' in job.params else 150.0
    cnv = DisplaceFlatZ(zmax, seed=seed, inputs=["ap_unweighted_events.lhe"])
else:
    raise Exception("Invalid ap decay distribution: ap_decay_dist = %s" % ap_decay_dist)

## Truth label: only for lhe_uniform. The EGS5 lhe_uniform converter drops MG5's A' and makes the
## recoil e- the mother of the e+e-; AddMotherFullTruth then adds ONE PDG-622 stand-in (mother of
## the e+e-, vertex = decay point) + a 623 placeholder (mother of the recoil e-) and fixes that.
## flat_z / displace_time keep MG5's real A' (with its e+e- daughters), so they get no label
## (a label there would duplicate the A', seen 2026-10-05).
if ap_decay_dist == "lhe_uniform":
    mom = AddMotherFullTruth(inputs=["ap_unweighted_events.stdhep", unzip.output_files()[0]], outputs=["ap_mom.stdhep"])
    rot_input = mom.output_files()
else:
    mom = None
    rot_input = ["ap_unweighted_events.stdhep"]

rot = BeamCoords(seed=seed, inputs=rot_input, outputs=["ap_rot.stdhep"])

## Simulate signal events
slic = SLIC(seed=seed, nevents=nevents + 1, inputs=rot.output_files(), outputs=["ap.slcio"])

## Keep events with >=1 hodoscope hit (and ECal hits); no spacing yet
filter_events = ExtractEventsWithHitAtHodoEcal(inputs=slic.output_files(), outputs=["ap_filt.slcio"],
                                               event_interval=0, num_hodo_hits=1)

## Overlay each MC event with one pulser-data event
overlay = JobManager(steering='overlay', inputs=filter_events.output_files(),
                     overlay_file=pulser_file, outputs=["ap_pulser.slcio"],
                     ignore_job_params=['nevents'])

## Insert 250 empty bunches between overlaid events
space_overlay = FilterBunches(inputs=overlay.output_files(), outputs=["ap_pulser_spaced.slcio"],
                              filter_no_cuts=True, filter_event_interval=250)

## Readout with pulser-data merging, singles2 + singles3 triggers
readout = JobManager(steering='readout', inputs=space_overlay.output_files(),
                     outputs=["ap_pulser_readout.slcio"], ignore_job_params=['nevents'])

## Run physics reconstruction
recon = JobManager(steering='recon', inputs=readout.output_files(),
                   outputs=["ap_pulser_recon.slcio"], ignore_job_params=['nevents'])

## Set persistency tags for output files
## One tag per step output (make_jobs.py "keep_outputs" chooses which ones are copied out):
job.ptag('lhe', 'ap_unweighted_events.lhe.gz')        # MadGraph events
job.ptag('conv', 'ap_unweighted_events.stdhep')       # after the decay step (lhe_uniform / displacement)
if mom is not None:
    job.ptag('mom', 'ap_mom.stdhep')                  # after AddMotherFullTruth
job.ptag('rot', 'ap_rot.stdhep')                      # after BeamCoords = SLIC input
job.ptag('sim', 'ap.slcio')                           # SLIC output
job.ptag('filt', 'ap_filt.slcio')                     # after ExtractEventsWithHitAtHodoEcal
job.ptag('overlay', 'ap_pulser.slcio')                # MC + pulser data merged
job.ptag('spaced', 'ap_pulser_spaced.slcio')          # after FilterBunches spacing
job.ptag('readout', 'ap_pulser_readout.slcio')
job.ptag('recon', 'ap_pulser_recon.slcio')

job.add([c for c in [mg, unzip, cnv, mom, rot, slic, filter_events, overlay, space_overlay, readout, recon] if c is not None])
