# Source me:  source setup.sh      (bash; JLab ifarm, AlmaLinux 9)
# HPSMC_DEV = the dev area that holds hps-mc/install, hps-java, sw, py27, pybin
: ${HPSMC_DEV:=/work/hallb/hps/ekhan/hpsmc-dev}
# 1. SLIC + Geant4 10.3.1 from the farm (this puts the OLD /group/hps/bin first on PATH, so source it before hps-mc)
source /group/hps/bin/slic-env.sh > /dev/null
export GDML_SCHEMA_DIR=/group/hps/share          # SLIC cannot download lcdd.xsd; use the local schemas
# 2. our hps-mc install (puts its bin first on PATH, wins over /group/hps/bin)
source $HPSMC_DEV/hps-mc/install/bin/hps-mc-env.sh
# 3. python2 for MG5 (ap, WAB); only a python2 symlink, so python3 is untouched
export PATH=$HPSMC_DEV/pybin:$PATH
# 4. Java 8 (hps-java is built and run with 8) and detector cache
export JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk
export PATH=$JAVA_HOME/bin:$PATH
export JAVA_TOOL_OPTIONS="-Dorg.lcsim.cacheDir=$HPSMC_DEV/sw -Xmx3g"
export HPS_JAVA_BIN_JAR=$HPSMC_DEV/hps-java/distribution/target/hps-distribution-5.3.1-SNAPSHOT-bin.jar
export LCIO_BIN_JAR=/group/hps/hps_soft/hps-lcio/target/lcio-2.7.4-SNAPSHOT-bin.jar
# 5. make_mini_dst (Maurik's build) needs ROOT 6.30 libs only while it runs: use mini_dst, in a subshell
mini_dst() ( export ROOTSYS=/u/home/holtrop/root
             export LD_LIBRARY_PATH=$ROOTSYS/lib:/home/holtrop/lib:/home/hps/lib:$LD_LIBRARY_PATH
             /home/holtrop/bin/make_mini_dst -a "$@" )
