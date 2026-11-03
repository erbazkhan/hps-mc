"""!
@file ap_gen_to_recon_job.py

A-prime generation (displaced decay) through SLIC, filter bunching,
readout, and recon. Extends the stock ap_gen_to_slic_job.py with the
same filter_bunches -> readout -> recon tail used for tritrig/WAB.
No HPSTR/ana step (not built on this cluster).

ASSUMPTION (unverified): reuses PhysicsRun2019TrigSingles.lcsim for
readout, same as tritrig, since no dedicated pair-trigger steering
file has been confirmed to exist for this run/config. If this comes
back with zero triggers, check for a dedicated pair-trigger steering
before assuming it's a pure statistics/acceptance issue.
"""
from hpsmc.generators import MG5, StdHepConverter
from hpsmc.tools import DisplaceTime, Unzip, BeamCoords, AddMotherFullTruth, SLIC, FilterBunches, JobManager


class DisplaceFlatZ(DisplaceTime):
    """! DisplaceTime with the A' decay z drawn uniformly in [0, zmax] mm from the production point
    (option -u of stdhep_lhe_tridents_displacetime, added 2026-10-04). Gives a flat true decay-z
    distribution; analyses reweight it to any c*tau."""

    def __init__(self, zmax, **kwargs):
        self.zmax = zmax
        DisplaceTime.__init__(self, **kwargs)

    def cmd_args(self):
        return DisplaceTime.cmd_args(self) + ["-u", str(self.zmax)]

job.description = 'ap gen to recon (testing -- no HPSTR/ana step)'

## Per-job random seed. hps-mc only passes the job-param seed to MG5; SLIC, BeamCoords and
## DisplaceTime default to seed 1, which would give every parallel job the same random streams.
seed = job.params['seed'] if 'seed' in job.params else 1

if 'nevents' in job.params:
    nevents = job.params['nevents']
else:
    nevents = 10000

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
        ## (DisplaceUni only handles SIMP rho_D 625 / iDM, so it left every A' prompt.)
        cnv = DisplaceTime(seed=seed, inputs=["ap_unweighted_events.lhe"])
    else:
        logger.error("Missing parameter ctau")
elif ap_decay_dist == "flat_z":
    ## Flat decay z: uniform in [0, decay_z_max] mm downstream of the production point (default 150 mm).
    zmax = job.params['decay_z_max'] if 'decay_z_max' in job.params else 150.0
    cnv = DisplaceFlatZ(zmax, seed=seed, inputs=["ap_unweighted_events.lhe"])
else:
    logger.error("Invalid ap decay distribution: ap_decay_dist = %s" % ap_decay_dist)

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

## insert empty bunches expected by pile-up simulation
filter_bunches = FilterBunches()

## Run simulated events in readout to generate triggers
## ignore job param nevents so readout sees ALL filtered bunches (no -n)
readout = JobManager(steering='readout', ignore_job_params=['nevents'])

## Run physics reconstruction
recon = JobManager(steering='recon', ignore_job_params=['nevents'])

## Set persistency tags for output files
job.ptag('lhe', 'ap_unweighted_events.lhe.gz')
job.ptag('sim', 'ap.slcio')
job.ptag('readout', 'ap_filt_readout.slcio')
job.ptag('recon', 'ap_filt_readout_recon.slcio')

job.add([c for c in [mg, unzip, cnv, mom, rot, slic, filter_bunches, readout, recon] if c is not None])
