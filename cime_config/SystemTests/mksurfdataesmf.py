"""
This test passes if mksurfdata_esmf generates an fsurdat (surface dataset)
and the CTSM completes a simulation with this fsurdat file.

We test res = '10x15' because it uses a lower-res topography file instead of
the 1-km topography raw dataset. The 1-km file causes the test to run out of
memory on cheyenne.

Currently casper complains that `git -C` is not a valid option.
I added -C to the `git describe` in gen_mksurfdata_namelist.py for this
system test to work.
"""

import os
import sys
import subprocess
from datetime import datetime
from CIME.SystemTests.system_tests_common import SystemTestsCommon
from CIME.XML.standard_module_setup import *
from CIME.SystemTests.test_utils.user_nl_utils import append_to_user_nl_files

logger = logging.getLogger(__name__)

class MKSURFDATAESMF(SystemTestsCommon):

    def __init__(self, case):
        """
        initialize an object interface to the SMS system test
        """
        SystemTestsCommon.__init__(self, case)

        # Paths and strings needed throughout
        ctsm_root = self._case.get_value('COMP_ROOT_DIR_LND')
        self._tool_path = os.path.join(ctsm_root, 'tools/mksurfdata_esmf')
        time_stamp = datetime.today().strftime("%y%m%d")
        self._res = '10x15'  # see important comment in script's docstring
        self._model_yr = '1850'
        self._fsurdat_out_prefix = os.path.join(self._get_caseroot(), f'surfdata_{self._res}_hist_78pfts_CMIP6_{self._model_yr}_c{time_stamp}.')
        self._TestStatus_log_path = os.path.join(self._get_caseroot(),
            'TestStatus.log')

    def build_phase(self, sharedlib_only=False, model_only=False):
        """
        Build executable that will generate fsurdat
        Generate namelist for generating fsurdat
        SKIP Generate jobscript that runs executable
        Modify user_nl_clm to point to the generated fsurdat
        """
        # These steps need only happen once
        if not os.path.exists(os.path.join(self._get_caseroot(),
            'done_MKSURFDATAESMF_setup.txt')):
            # Paths and strings
            rm_bld_dir = f"rm -rf {self._tool_path}/bld"
            build_script_path = os.path.join(self._tool_path,
                'gen_mksurfdata_build.sh')
            nml_script_path = os.path.join(self._tool_path,
                'gen_mksurfdata_namelist.py')
            gen_mksurfdata_namelist = f'{nml_script_path} --res {self._res} --start-year {self._model_yr} --end-year {self._model_yr}'

            # Build executable
            try:
                subprocess.check_call(rm_bld_dir, shell=True)
            except subprocess.CalledProcessError as e:
                sys.exit(f'{e} ERROR RUNNING {rm_bld_dir}. DETAILS IN {self._TestStatus_log_path}')
            try:
                subprocess.check_call(build_script_path, shell=True)
            except subprocess.CalledProcessError as e:
                sys.exit(f'{e} ERROR RUNNING {build_script_path}. DETAILS IN {self._TestStatus_log_path}')

            # Generate namelist for generating fsurdat
            try:
                subprocess.check_call(gen_mksurfdata_namelist, shell=True)
            except subprocess.CalledProcessError as e:
                sys.exit(f'{e} ERROR RUNNING {gen_mksurfdata_namelist}. DETAILS IN {self._TestStatus_log_path}')

            # Modify user_nl_clm to point to the generated fsurdat
            self._modify_user_nl()
            with open('done_MKSURFDATAESMF_setup.txt', 'w') as fp:
                pass

        self.build_indv(sharedlib_only=sharedlib_only, model_only=model_only)

    def run_phase(self):
        """
        Run executable to generate fsurdat
        Submit CTSM run that uses fsurdat just generated
        """
        # Paths and command strings
        executable_path = os.path.join(self._tool_path, 'bld/mksurfdata')
        machine = self._case.get_value("MACH")
        if machine == 'cheyenne':
            mpiexec_mpt_cmd = f"mpiexec_mpt -np 144 {executable_path} < {self._fsurdat_out_prefix}namelist"
        elif machine == 'casper':
            mpiexec_mpt_cmd = f"mpiexec -np 144 {executable_path} < {self._fsurdat_out_prefix}namelist"

        # Run executable to generate fsurdat
        try:
            subprocess.check_call(mpiexec_mpt_cmd, shell=True)
        except subprocess.CalledProcessError as e:
            sys.exit(f'{e} ERROR RUNNING {mpiexec_mpt_cmd}; details in {self._TestStatus_log_path}')

        # Submit CTSM run that uses fsurdat just generated
        self.run_indv()

    def _modify_user_nl(self):
        """
        Modify user_nl_clm to point to the generated fsurdat
        """
        append_to_user_nl_files(caseroot = self._get_caseroot(),
                                component = "clm",
                                contents = "fsurdat = '{}nc'".format(self._fsurdat_out_prefix))
