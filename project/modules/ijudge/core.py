# -*- coding: utf-8 -*-
__author__ = ['SALAR', 'AminHP']

import docker
import os


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SCRIPTS_DIR = os.path.join(BASE_DIR, 'scripts')


def run(code_path, prog_lang, testcase_dir, time_limit, space_limit):
    prog_lang = prog_lang.lower()
    pl_script_dir = os.path.join(SCRIPTS_DIR, prog_lang)
    config_file = os.path.join(pl_script_dir, 'config.py')
    log_dir = "%s.log" % code_path
    config_mod = __import__(config_file)

    time_limit = float(time_limit * config_mod.TIME_LIMIT_FACTOR)
    space_limit = "%sMB" % (space_limit + 0) # TODO(AminHP): We must calculate os space usage

    run_core(code_path, pl_script_dir, testcase_dir, log_dir, time_limit, space_limit)


def run_core(code_path, pl_script_dir, testcase_dir, log_dir, time_limit, space_limit):
    client = docker.from_env()
    code_filename = os.path.basename(code_path)

    volumes = {
        code_path: { 
            "bind": "/etc/data/%s" % code_filename,
            "mode": 'ro'
        },
        pl_script_dir: {
            "bind": "/etc/data/plscript",
        }
        testcase_dir: {
            "bind": "/etc/data/inputs",
            "mode": 'ro'
        },
        log_dir: {
            "bind": "/etc/data/%s.log" % code_filename,
            "mode": 'rw'
        }
    }

    env = {
        "CODE_PATH": volumes[code_path]["bind"],
        "PL_SCRIPT_DIR": volumes[pl_script_dir]["bind"],
        "TESTCASE_DIR": volumes[testcase_dir]["bind"],
        "LOG_DIR": volumes[log_dir]["bind"],
        "TIME_LIMIT": time_limit
    }

    client.containers.run(  
        image = "ijudge",
        remove = True, 
        stdout = True,
        stderr = True,
        mem_limit = SPACE_LIMIT,
        mem_swappiness = 0,
        volumes = volumes,
        environment = env
    )
