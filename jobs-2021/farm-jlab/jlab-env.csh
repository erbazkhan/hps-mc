# tcsh environment for hps-mc jobs on the JLab farm (swif2 wrapper sources this after hps-mc-env.csh).
# Mirrors farm-jlab/setup.sh. ROOT is not needed here: MiniDST is run separately for now.
setenv HPSMC_DEV /work/hallb/hps/ekhan/hpsmc-dev
# SLIC + Geant4 10.3.1 (same values slic-env.sh sets)
set g4d = /group/hps/share/Geant4-10.3.1/data
setenv G4ABLADATA ${g4d}/G4ABLA3.0
setenv G4ENSDFSTATEDATA ${g4d}/G4ENSDFSTATE2.1
setenv G4LEDATA ${g4d}/G4EMLOW6.50
setenv G4LEVELGAMMADATA ${g4d}/PhotonEvaporation4.3.2
setenv G4NEUTRONHPDATA ${g4d}/G4NDL4.5
setenv G4NEUTRONXSDATA ${g4d}/G4NEUTRONXS1.4
setenv G4PIIDATA ${g4d}/G4PII1.3
setenv G4RADIOACTIVEDATA ${g4d}/RadioactiveDecay5.1.1
setenv G4REALSURFACEDATA ${g4d}/RealSurface1.0
setenv G4SAIDXSDATA ${g4d}/G4SAIDDATA1.1
unset g4d
if ($?LD_LIBRARY_PATH) then
    setenv LD_LIBRARY_PATH /group/hps/lib64:/group/hps/lib:${LD_LIBRARY_PATH}
else
    setenv LD_LIBRARY_PATH /group/hps/lib64:/group/hps/lib
endif
setenv PATH ${PATH}:/group/hps/bin
setenv GDML_SCHEMA_DIR /group/hps/share
# python2 for MG5 (link only), Java 8, detector cache, jars
setenv PATH ${HPSMC_DEV}/pybin:${PATH}
setenv JAVA_HOME /usr/lib/jvm/java-1.8.0-openjdk
setenv PATH ${JAVA_HOME}/bin:${PATH}
setenv JAVA_TOOL_OPTIONS "-Dorg.lcsim.cacheDir=${HPSMC_DEV}/sw -Xmx3g -Djava.io.tmpdir=${HPSMC_DEV}/tmp"
setenv HPS_JAVA_BIN_JAR ${HPSMC_DEV}/hps-java/distribution/target/hps-distribution-5.3.1-SNAPSHOT-bin.jar
setenv LCIO_BIN_JAR /group/hps/hps_soft/hps-lcio/target/lcio-2.7.4-SNAPSHOT-bin.jar
