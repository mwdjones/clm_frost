# This file is for user convenience only and is not used by the model
# Changes to this file will be ignored and overwritten
# Changes to the environment should be made in env_mach_specific.xml
# Run ./case.setup --reset to regenerate this file
source $LMOD_ROOT/lmod/init/sh
module load cesmdev/1.0 ncarenv/23.09
module purge 
module load craype intel/2023.2.1 mkl spherepack/3.2 ncarcompilers/1.0.0 cmake cray-mpich/8.1.27 netcdf-mpi/4.9.2 parallel-netcdf/1.12.3 esmf/8.6.0
export OMP_STACKSIZE=64M
export FI_CXI_RX_MATCH_MODE=hybrid
export FI_MR_CACHE_MONITOR=memhooks
export SPHEREPACK_LIBDIR=/glade/u/apps/cseg/derecho/23.09/spack/opt/spack/linux-sles15-x86_64_v3/oneapi-2023.2.1/spherepack-3.2-lpt2vfttjsz6eccov2g2npicgg53xlf6/lib