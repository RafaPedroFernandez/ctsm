"""
gen_mksurfdata_jobscript_multi.py generates a jobscript for running the
mksurfdata executable to generate many fsurdat files at once. For detailed
instructions, see README.
"""
import os
import sys
import argparse

from ctsm.path_utils import path_to_ctsm_root
from ctsm.toolchain.gen_mksurfdata_namelist import main as main_nml
from ctsm.utils import abort

valid_scenarios = [
    "global-present",
    "global-present-low-res",
    "global-present-nldas",
    "global-hist-4x5",
    "crop-tropics-present",
    "crop",
    "crop-global-present",
    "crop-global-present-low-res",
    "crop-global-present-ne16np4",
    "crop-global-present-ne120np4",
    "crop-global-present-0.125",
    "crop-global-1850",
    "crop-global-1850-low-res",
    "crop-global-1850-ne16np4",
    "crop-global-1850-ne120np4",
    "crop-global-hist",
    "crop-global-future",
    "crop-global-SSP1-2.6",
    "crop-global-SSP3-7.0",
    "crop-global-SSP5-3.4",
    "crop-global-SSP2-4.5",
    "crop-global-SSP2-4.5-low-res",
    "crop-global-SSP2-4.5-hi-res",
    "crop-global-SSP1-1.9",
    "crop-global-SSP4-3.4",
    "crop-global-SSP4-6.0",
    "crop-global-SSP5-8.5",
    "crop-global-SSP5-8.5-other",
]


def get_parser():
    """
    Get parser object for this script.
    """
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.print_usage = parser.print_help

    parser.add_argument(
        "-v",
        "--verbose",
        help="ncrease output verbosity",
        action="store_true",
    )
    parser.add_argument(
        "--account",
        help="""account number (default P93300606)""",
        action="store",
        dest="account",
        required=False,
        default="P93300606",
    )
    parser.add_argument(
        "--bld-path",
        help="""Path to build directory for mksurfdata_esmf""",
        action="store",
        dest="bld_path",
        default=os.path.join(path_to_ctsm_root(), "tools", "mksurfdata_esmf", "tool_bld"),
    )
    parser.add_argument(
        "--number-of-nodes",
        help="""number of cheyenne nodes requested (required)""",
        action="store",
        dest="number_of_nodes",
        required=True,
    )
    parser.add_argument(
        "--tasks-per-node",
        help="""number of mpi tasks per node for cheyenne requested (default is 12)""",
        action="store",
        dest="tasks_per_node",
        required=False,
        default="12",
    )
    parser.add_argument(
        "--walltime",
        help="""Wallclock time for job submission default is 12:00:00)""",
        action="store",
        dest="walltime",
        required=False,
        default="12:00:00",
    )
    parser.add_argument(
        "--queue",
        help="""Queue to submit to)""",
        action="store",
        dest="queue",
        required=False,
        default="regular",
    )
    parser.add_argument(
        "--scenario",
        help="""scenario""",
        choices=valid_scenarios,
        action="store",
        dest="scenario",
        required=True,
    )
    parser.add_argument(
        "--jobscript-file",
        help="""output jobscript file to be submitted on cheyenne
                [default: %(default)s]""",
        action="store",
        dest="jobscript_file",
        required=False,
        default="mksurfdata_jobscript_multi",
    )
    return parser


def main():
    """
    See docstring at the top.
    """
    # --------------------------
    # Obtain input args
    # --------------------------
    args = get_parser().parse_args()
    scenario = args.scenario
    jobscript_file = args.jobscript_file
    number_of_nodes = args.number_of_nodes
    tasks_per_node = args.tasks_per_node
    account = args.account
    walltime = args.walltime
    queue = args.queue

    # --------------------------
    # Determine target list
    # --------------------------
    target_list = []
    if scenario == "crop":
        target_list = ["crop-global-present", "crop-global-1850", "crop-global-hist"]
    elif scenario == "crop-global-future":
        target_list = [
            "crop-global-SSP1-2.6",
            "crop-global-SSP3-7.0",
            "crop-global-SSP5-3.4",
            "crop-global-SSP2-4.5",
            "crop-global-SSP1-1.9",
            "crop-global-SSP4-3.4",
            "crop-global-SSP4-6.0",
            "crop-global-SSP5-8.5",
            "crop-global-SSP5-8.5-other",
        ]
    elif scenario == "tropics":
        target_list = ["crop-tropics-present"]
    else:
        target_list = [scenario]

    # --------------------------
    # Error checking
    # --------------------------
    for scenario_list in target_list:
        if scenario_list not in valid_scenarios:
            abort("Input scenario is NOT in valid_scenarios")
    # --------------------------
    # Determine resolution sets that are referenced in commands
    # --------------------------
    resolution_dict = {
        "standard_res_no_crop": ["0.9x1.25", "1.9x2.5"],
        "low_res_no_crop": ["10x15"],
        "low_res_all": ["10x15", "ne3np4.pg3"],
        "hi_res_all": ["ne120np4.pg3"],
        "standard_res": ["0.9x1.25", "1.9x2.5", "C96", "ne30np4.pg3", "mpasa120"],
        "low_res": ["10x15", "4x5", "ne3np4.pg3", "ne5np4.pg3", "C24", "mpasa480"],
        "4x5_res": ["10x15", "4x5", "C24", "mpasa480"],
        "nldas_res": ["0.125nldas2"],
        "5x5_amazon_res": ["5x5_amazon"],
        "ne16np4_res": ["C48", "ne16np4"],
        "ne120np4_res": [
            "ne120np4.pg3",
            "ne0np4.ARCTICGRIS.ne30x8",
            "ne0np4.ARCTIC.ne30x4",
            "ne0np4CONUS.ne30x8",
        ],
    }

    # --------------------------
    # Determine commands for each target list
    # --------------------------
    dataset_dict = {
        "global-present": (
            "--start-year 2000 --end-year 2000 --nocrop --vic                  --res",
            "standard_res_no_crop",
        ),
        "global-present-low-res": (
            "--start-year 2000 --end-year 2000 --nocrop --vic                  --res",
            "low_res_no_crop",
        ),
        "global-present-nldas": (
            "--start-year 2000 --end-year 2000 --nocrop --vic                  --res",
            "nldas_res",
        ),
        "global-hist-4x5": (
            "--start-year 1850 --end-year 2015 --nocrop                        --res",
            "4x5_res",
        ),
        "crop-tropics-present": (
            "--start-year 2000 --end-year 2000                                 --res",
            "5x5_amazon_res",
        ),
        "crop-global-present": (
            "--start-year 2000 --end-year 2000                                 --res",
            "standard_res",
        ),
        "crop-global-present-low-res": (
            "--start-year 2000 --end-year 2000                                 --res",
            "low_res",
        ),
        "crop-global-present-ne16np4": (
            "--start-year 2000 --end-year 2000                                 --res",
            "ne16np4_res",
        ),
        "crop-global-present-ne120np4": (
            "--start-year 2000 --end-year 2000                                 --res",
            "ne120np4_res",
        ),
        "crop-global-present-0.125": (
            "--start-year 2000 --end-year 2000 --hirespft                      --res",
            "nldas_res",
        ),
        "crop-global-1850": (
            "--start-year 1850 --end-year 1850                                 --res",
            "standard_res",
        ),
        "crop-global-1850-low-res": (
            "--start-year 1850 --end-year 1850                                 --res",
            "low_res",
        ),
        "crop-global-1850-ne16np4": (
            "--start-year 1850 --end-year 1850                                 --res",
            "ne16np4_res",
        ),
        "crop-global-1850-ne120np4": (
            "--start-year 1850 --end-year 1850                                 --res",
            "ne120np4_res",
        ),
        "crop-global-hist": (
            "--start-year 1850 --end-year 2015 --nosurfdata                    --res",
            "standard_res",
        ),
        "crop-global-SSP1-1.9": (
            "--start-year 1850 --end-year 2100 --nosurfdata --ssp-rcp SSP1-1.9 --res",
            "standard_res",
        ),
        "crop-global-SSP1-2.6": (
            "--start-year 1850 --end-year 2100 --nosurfdata --ssp-rcp SSP1-2.6 --res",
            "standard_res",
        ),
        "crop-global-SSP2-4.5": (
            "--start-year 1850 --end-year 2100 --nosurfdata --ssp-rcp SSP2-4.5 --res",
            "standard_res",
        ),
        "crop-global-SSP2-4.5-low-res": (
            "--start-year 1850 --end-year 2100 --nosurfdata --ssp-rcp SSP2-4.5 --res",
            "low_res_all",
        ),
        "crop-global-SSP2-4.5-hi-res": (
            "--start-year 1850 --end-year 2100 --nosurfdata --ssp-rcp SSP2-4.5 --res",
            "hi_res_all",
        ),
        "crop-global-SSP3-7.0": (
            "--start-year 1850 --end-year 2100 --nosurfdata --ssp-rcp SSP3-7.0 --res",
            "standard_res",
        ),
        "crop-global-SSP4-3.4": (
            "--start-year 1850 --end-year 2100 --nosurfdata --ssp-rcp SSP4-3.4 --res",
            "standard_res",
        ),
        "crop-global-SSP4-6.0": (
            "--start-year 1850 --end-year 2100 --nosurfdata --ssp-rcp SSP4-6.0 --res",
            "standard_res",
        ),
        "crop-global-SSP5-3.4": (
            "--start-year 1850 --end-year 2100 --nosurfdata --ssp-rcp SSP5-3.4 --res",
            "standard_res",
        ),
        "crop-global-SSP5-8.5": (
            "--start-year 1850 --end-year 2100 --nosurfdata --ssp-rcp SSP5-8.5 --res",
            "standard_res",
        ),
    }

    # --------------------------
    # TODO Here, reuse code from gen_mksurfdata_jobscript_single
    # that's found in the section titled "Obtain mpirun command ..."
    # --------------------------

    # --------------------------
    # Make sure files exist or exit
    # --------------------------
    if not os.path.exists(args.bld_path):
        print(
            args.bld_path
            + " directory does NOT exist -- build mksurdata_esmf before running this script -- using ./gen_mksurfdata_build.sh"
        )
        sys.exit(1)

    env_specific_script = os.path.join(args.bld_path, ".env_mach_specific.sh")
    if not os.path.exists(env_specific_script):
        print(env_specific_script + " does NOT exist")
        sys.exit(1)
    mksurfdata = os.path.join(args.bld_path, "mksurfdata")
    if not os.path.exists(mksurfdata):
        print(mksurfdata + " does NOT exist")
        sys.exit(1)
    # --------------------------
    # Write run script
    # --------------------------
    with open(jobscript_file, "w", encoding="utf-8") as runfile:

        runfile.write("#!/bin/bash \n")
        runfile.write(f"#PBS -A {account} \n")
        runfile.write(f"#PBS -N mksrf_{scenario} \n")
        runfile.write("#PBS -j oe \n")
        runfile.write("#PBS -k eod \n")
        runfile.write("#PBS -S /bin/bash \n")
        runfile.write(f"#PBS -q {queue} \n")
        runfile.write(f"#PBS -l walltime={walltime} \n")
        runfile.write(
            f"#PBS -l select={number_of_nodes}:ncpus={tasks_per_node}:mpiprocs={tasks_per_node}:mem=109GB \n"
        )
        runfile.write(
            f"# This is a batch script to run a set of resolutions for mksurfdata_esmf {scenario} \n"
        )
        runfile.write(
            "# NOTE: THIS SCRIPT IS AUTOMATICALLY GENERATED SO IN GENERAL YOU SHOULD NOT EDIT it!!\n\n"
        )
        runfile.write("\n")

        n_p = int(tasks_per_node) * int(number_of_nodes)

        # Run env_mach_specific.sh to control the machine dependent
        # environment including the paths to compilers and libraries
        # external to cime such as netcdf
        runfile.write(". " + env_specific_script + "\n")
        check = "if [ $? != 0 ]; then echo 'Error running env_specific_script'; exit -4; fi"
        runfile.write(f"{check} \n")
        for target in target_list:
            res_set = dataset_dict[target][1]
            if res_set not in resolution_dict:
                abort(f"Resolution is not in the resolution_dict: {res_set}")
            for res in resolution_dict[res_set]:
                namelist = f"{scenario}_{res}.namelist"
                command = os.path.join(os.getcwd(), "gen_mksurfdata_namelist")
                command = command + " " + dataset_dict[target][0] + " " + res
                command = command + " --silent"
                command = command + f" --namelist {namelist}"
                print(f"command is {command}")
                sys.argv = [x for x in command.split(" ") if x]
                main_nml()
                print(f"generated namelist {namelist}")
                output = f'time mpiexec_mpt -p "%g:" -np {n_p} {mksurfdata} < {namelist}'
                runfile.write(f"{output} \n")
                check = f"if [ $? != 0 ]; then echo 'Error running resolution {res}'; exit -4; fi"
                runfile.write(f"{check} \n")
                runfile.write(f"echo Successfully ran resolution {res}\n")

        runfile.write(f"echo Successfully ran {jobscript_file}\n")

    print(f"echo Successfully created jobscript {jobscript_file}\n")
