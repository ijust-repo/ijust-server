# -*- coding: utf-8 -*-
__author__ = 'AminHP'

# python imports
import os
from enum import Enum

# project imports
from project import app
from project.extensions import db
from project.modules.datetime import utcnowts
from project.modules.fields import IntEnumField


class SubmissionStatusType(Enum):
    Pending = 0
    CompileError = 1
    RestrictedFunction = 2
    TimeExceeded = 3
    SpaceExceeded = 4
    RuntimeError = 5
    WrongAnswer = 6
    ExtensionError = 7
    Accepted = 8


class ProgrammingLanguageType(Enum):
    Cpp = 0
    Python = 1
    Java = 2


class Submission(db.Document):
    filename = db.StringField(required=True)
    prog_lang = IntEnumField(enum=ProgrammingLanguageType, required=True)
    submitted_at = db.IntField(required=True, default=lambda: utcnowts())

    contest = db.ReferenceField('Contest', required=True)
    problem = db.ReferenceField('Problem', required=True)
    team = db.ReferenceField('Team', required=True)
    user = db.ReferenceField('User', required=True)

    status = IntEnumField(enum=SubmissionStatusType, required=True, default=SubmissionStatusType.Pending)
    reason = db.StringField()


    @property
    def code_addr(self):
        return os.path.join(
            app.config['SUBMISSION_DIR'],
            str(self.contest.pk),
            str(self.problem.pk),
            str(self.team.pk),
            str(self.submitted_at),
            self.filename
        )


    @property
    def code(self):
        with open(self.code_addr, 'r') as f:
            return f.read()


    def populate(self, json):
        self.filename = json['filename']
        self.prog_lang = json['prog_lang']
