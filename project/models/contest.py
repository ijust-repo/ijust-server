# -*- coding: utf-8 -*-
__author__ = 'AminHP'

# python imports
import os
import shutil
from time import time

# project imports
from project import app
from project.extensions import db


class Problem(db.Document):
    title = db.StringField(required=True)
    time_limit = db.FloatField(required=True)
    space_limit = db.IntField(required=True)

    @property
    def body_addr(self):
        return os.path.join(app.config['PROBLEM_DIR'], str(self.pk))

    @property
    def testcase_dir(self):
        return os.path.join(app.config['TESTCASE_DIR'], str(self.pk))

    def delete(self):
        if os.path.exists(self.body_file):
            os.remove(self.body_file)
        if os.path.exists(self.testcase_dir):
            shutil.rmtree(self.testcase_dir)
        super(Problem, self).delete()


    def populate(self, json):
        if 'title' in json:
            self.title = json['title']
        if 'time_limit' in json:
            self.time_limit = json['time_limit']
        if 'space_limit' in json:
            self.space_limit = json['space_limit']


    def to_json(self):
        return dict(
            id = str(self.pk),
            title = self.title,
            time_limit = self.time_limit,
            space_limit = self.space_limit
        )


    def to_json_abs(self):
        return dict(
            id = str(self.pk),
            title = self.title
        )



class Contest(db.Document):
    name = db.StringField(required=True, unique=True)
    owner = db.ReferenceField('User', required=True)
    created_at = db.IntField(required=True, default=lambda: int(time()))
    starts_at = db.IntField(required=True)
    ends_at = db.IntField(required=True)
    pending_teams = db.ListField(db.ReferenceField('Team', reverse_delete_rule=db.PULL))
    accepted_teams = db.ListField(db.ReferenceField('Team', reverse_delete_rule=db.PULL))
    problems = db.ListField(db.ReferenceField('Problem', reverse_delete_rule=db.PULL))


    def populate(self, json):
        if 'name' in json:
            self.name = json['name']
        if 'starts_at' in json:
            self.starts_at = json['starts_at']
        if 'ends_at' in json:
            self.ends_at = json['ends_at']


    def save(self):
        if not (self.created_at < self.starts_at < self.ends_at):
            raise ContestDateTimeException()
        super(Contest, self).save()


    def to_json(self):
        return dict(
            id = str(self.pk),
            name = self.name,
            owner = self.owner.to_json_abs(),
            created_at = self.created_at,
            starts_at = self.starts_at,
            ends_at = self.ends_at
        )


    def to_json_teams(self):
        return dict(
            pending_teams = [team.to_json_abs() for team in self.pending_teams],
            accepted_teams = [team.to_json_abs() for team in self.accepted_teams]
        )


    def to_json_problems(self):
        return dict(
            problems = [prob.to_json_abs() for prob in self.problems]
        )


class ContestDateTimeException(db.ValidationError):
    pass
