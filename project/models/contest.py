# -*- coding: utf-8 -*-
__author__ = 'AminHP'

# python imports
import os
import shutil

# project imports
from project import app
from project.extensions import db
from project.modules.datetime import utcnowts
from project.models.user import User
from project.models.team import Team


class Problem(db.Document):
    title = db.StringField(required=True)
    time_limit = db.FloatField(required=True)
    space_limit = db.IntField(required=True)

    meta = {
        'collection': 'problems'
    }


    @property
    def body_path(self):
        return os.path.join(app.config['PROBLEM_DIR'], str(self.pk))

    @property
    def testcase_dir(self):
        return os.path.join(app.config['TESTCASE_DIR'], str(self.pk))

    def delete(self):
        if os.path.exists(self.body_path):
            os.remove(self.body_path)
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



class Result(db.Document):
    teams = db.DictField()

    default_team_data = dict(
        problems = {},
        solved_count = 0,
        penalty = 0
    )

    default_problem_data = dict(
        submitted_at = None,
        failed_tries = 0,
        penalty = 0,
        solved = False
    )

    meta = {
        'collection': 'results'
    }


    @staticmethod
    def _make_query_ids(tid, pid):
        tqid = "teams__%s" % tid
        pqid = "teams__%s__problems__%s" % (tid, pid)
        return tqid, pqid


    def _check_existence(self, tid, pid):
        tqid, pqid = self._make_query_ids(tid, pid)

        find_query = {
            'pk': str(self.pk),
            tqid: None
        }
        update_query = {tqid: self.default_team_data}
        Result.objects(**find_query).update(**update_query)

        update_query = {("set__%s" % pqid): self.default_problem_data}
        find_query = {
            'pk': str(self.pk),
            pqid: None
        }
        Result.objects(**find_query).update(**update_query)


    def update_failed_try(self, tid, pid, submitted_at, penalty=20):
        self._check_existence(tid, pid)
        tqid, pqid = self._make_query_ids(tid, pid)

        find_query = {
            'pk': str(self.pk),
            ("%s__solved" % pqid): False
        }
        update_query = {
            ("set__%s__submitted_at" % pqid): submitted_at,
            ("inc__%s__failed_tries" % pqid): 1,
            ("inc__%s__penalty" % pqid): penalty
        }
        Result.objects(**find_query).update(**update_query)


    def update_succeed_try(self, tid, pid, submitted_at, contest_starts_at):
        self._check_existence(tid, pid)
        tqid, pqid = self._make_query_ids(tid, pid)

        find_query = {
            'pk': str(self.pk),
            ("%s__solved"% pqid): False
        }
        update_query = {
            ("set__%s__submitted_at" % pqid): submitted_at,
            ("set__%s__solved" % pqid): True,
            ("inc__%s__penalty" % pqid): (submitted_at - contest_starts_at) // 60,
            ("inc__%s__solved_count" % tqid): 1
        }

        if Result.objects(**find_query).update(**update_query):
            aggregate_query = [
                {
                    "$match": {
                        "_id": self.pk
                    }
                },
                {
                    '$project': {
                        'last_penalty': ('$teams.%s.problems.%s.penalty' % (tid, pid))
                    }
                }
            ]
            aggregate_result = list(Result.objects.aggregate(*aggregate_query))
            last_penalty = aggregate_result[0]['last_penalty']
            update_query = {
                ("inc__%s__penalty" % tqid): last_penalty
            }
            Result.objects(pk=str(self.pk)).update(**update_query)


    def to_json(self, original_problems):
        from copy import deepcopy
        teams = deepcopy(self.teams)
        teams_list = []
        for team_id in teams:
            t = teams[team_id]
            t['team_id'] = team_id
            problems_list = []
            for problem in original_problems:
                p={
                        p['problem_id'] : str(problem.pk)
                        p['title'] : str(problem.title)
                        if str(problem.pk) in t['problems']:
                            p.update(t['problems'][str(problem.pk)])
                        else :
                            p['solved'] : "unknown"
                      }
            problems_list.append(p)
            problems_list.sort(key=lambda c:c["title"])
            t['problems'] = problems_list
            teams_list.append(t)

        teams_list.sort(key=lambda d:d["penalty"])
        teams_list.sort(key=lambda d:d["solved_count"], reverse=True)
        return teams_list



class Contest(db.Document):
    name = db.StringField(required=True, unique=True)
    owner = db.ReferenceField('User', required=True)
    admins = db.ListField(db.ReferenceField('User', reverse_delete_rule=db.PULL))
    created_at = db.IntField(required=True, default=lambda: utcnowts())
    starts_at = db.IntField(required=True)
    ends_at = db.IntField(required=True)
    pending_teams = db.ListField(db.ReferenceField('Team', reverse_delete_rule=db.PULL))
    accepted_teams = db.ListField(db.ReferenceField('Team', reverse_delete_rule=db.PULL))
    problems = db.ListField(db.ReferenceField('Problem', reverse_delete_rule=db.PULL))
    result = db.ReferenceField('Result')

    meta = {
        'collection': 'contests',
        'indexes': [
            '-starts_at',
            'owner',
            'admins',
            'accepted_teams',
            'problems'
        ]
    }


    def create_result(self):
        result_obj = Result()
        result_obj.save()
        self.result = result_obj
        self.save()


    def is_user_in_contest(self, user_obj):
        for team in self.accepted_teams:
            if team.is_user_in_team(user_obj):
                return True
        return False


    def user_joining_status(self, user_obj):
        for team in self.accepted_teams:
            if team.is_user_in_team(user_obj):
                return 2, team
        for team in self.pending_teams:
            if team.is_user_in_team(user_obj):
                return 1, team
        return 0, None


    def populate(self, json):
        if 'name' in json:
            self.name = json['name']
        if 'starts_at' in json:
            self.starts_at = json['starts_at']
        if 'ends_at' in json:
            self.ends_at = json['ends_at']


    def save(self):
        if not (self.created_at < self.starts_at < self.ends_at):
            raise ContestDateTimeError()
        super(Contest, self).save()


    def to_json(self):
        return dict(
            id = str(self.pk),
            name = self.name,
            owner = self.owner.to_json_abs(),
            created_at = self.created_at,
            starts_at = self.starts_at,
            ends_at = self.ends_at,
            is_active = True if self.starts_at <= utcnowts() <= self.ends_at else False,
            teams_num = len(self.accepted_teams)
        )


    def to_json_user(self, user_obj):
        json = self.to_json()
        status, team = self.user_joining_status(user_obj)
        json['joining_status'] = dict(
            status=status,
            team=team.to_json_abs() if team else None
        )
        json['is_owner'] = user_obj == self.owner
        json['is_admin'] = user_obj in self.admins
        return json


    def to_json_admins(self):
        return dict(
            admins = [admin.to_json_abs() for admin in self.admins]
        )


    def to_json_teams(self, category):
        if category == 'pending':
            return dict(
                pending_teams = [team.to_json() for team in self.pending_teams]
            )
        elif category == 'accepted':
            return dict(
                accepted_teams = [team.to_json() for team in self.accepted_teams]
            )
        else:
            return dict(
                pending_teams = [team.to_json() for team in self.pending_teams],
                accepted_teams = [team.to_json() for team in self.accepted_teams]
            )


    def to_json_problems(self):
        return dict(
            problems = [prob.to_json_abs() for prob in self.problems]
        )


    def to_json_result(self):
        return dict(
            result = self.result.to_json(self.problems),
            teams = {str(t.pk): {t.name} for t in self.accepted_teams},
            problems = {str(p.pk): p.title for p in self.problems}
        )



class ContestDateTimeError(db.ValidationError):
    pass
