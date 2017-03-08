# -*- coding: utf-8 -*-
__author__ = ['SALAR', 'AminHP']

# python imports
import docker
import os
import imp

# project imports
from .types import JudgementStatusType


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SCRIPTS_DIR = os.path.join(BASE_DIR, 'scripts')


def run(code_path, prog_lang, testcase_dir, time_limit, space_limit):
    prog_lang = prog_lang.lower()
    pl_script_dir = os.path.join(SCRIPTS_DIR, prog_lang)
    input_dir = os.path.join(testcase_dir, 'inputs')
    output_dir = os.path.join(testcase_dir, 'outputs')
    log_dir = "%s.log" % code_path

    config_file = os.path.join(pl_script_dir, 'config.py')
    config_mod = imp.load_source('plconfig', config_file)

    time_limit = float(time_limit * config_mod.TIME_LIMIT_FACTOR)
    space_limit = "%sMB" % (space_limit + 0) # TODO(AminHP): We must calculate os space usage

    run_in_container(code_path, pl_script_dir, input_dir, log_dir, time_limit, space_limit)
    return check_result(log_dir, output_dir)


def run_in_container(code_path, pl_script_dir, input_dir, log_dir, time_limit, space_limit):
    code_filename = os.path.basename(code_path)

    volumes = {
        code_path: { 
            'bind': "/etc/data/%s" % code_filename,
            'mode': 'ro'
        },
        pl_script_dir: {
            'bind': "/etc/data/plscript",
            'mode': 'rw'
        },
        input_dir: {
            'bind': "/etc/data/inputs",
            'mode': 'ro'
        },
        log_dir: {
            'bind': "/etc/data/%s.log" % code_filename,
            'mode': 'rw'
        }
    }

    env = {
        "CODE_PATH": volumes[code_path]["bind"],
        "PL_SCRIPT_DIR": volumes[pl_script_dir]["bind"],
        "TESTCASE_DIR": volumes[input_dir]["bind"],
        "LOG_DIR": volumes[log_dir]["bind"],
        "TIME_LIMIT": time_limit
    }

    client = docker.from_env()
    try:
        client.containers.run(
            image = "ijudge",
            remove = True, 
            stdout = True,
            stderr = True,
            mem_limit = space_limit,
            mem_swappiness = 0,
            volumes = volumes,
            environment = env
        )
    except docker.errors.ContainerError:
        pass


def check_result(log_dir, output_dir):
    compile_error_fp = os.path.join(log_dir, "compile.err")
    if os.stat(compile_error_fp).st_size != 0:
        return JudgementStatusType.CompileError

    for testcase in sorted([tc for tc in os.listdir(output_dir)]):
        desired_output_fp = os.path.join(output_dir, testcase)
        code_output_fp = "%s.out" % os.path.join(log_dir, testcase)
        code_error_fp = "%s.err" % os.path.join(log_dir, testcase)
        code_stat_fp = "%s.stt" % os.path.join(log_dir, testcase)

        if os.stat(code_error_fp).st_size != 0:
            return JudgementStatusType.RuntimeError

        with open(code_stat_fp) as stat_file:
            line = stat_file.readline()
            running_time = float(line)
            if running_time == -1:
                return JudgementStatusType.TimeExceeded

        if not os.path.exists(code_output_fp):
            return JudgementStatusType.RuntimeError

        with open(code_output_fp) as output_file, \
             open(desired_output_fp) as desired_output_file:

            output = output_file.read()
            desired_output = desired_output_file.read()

            output = output[:-1] if output[-1] == '\n' else output
            desired_output = desired_output.strip()

            if output != desired_output:
                return JudgementStatusType.WrongAnswer

    return JudgementStatusType.Accepted
