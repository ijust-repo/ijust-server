# -*- coding: utf-8 -*-
__author__ = 'AminHP'

from .types import JudgementStatusType, ProgrammingLanguageType


def judge(code_path, prog_lang, testcase_dir, time_limit, space_limit):
    return JudgementStatusType.Accepted, ''
