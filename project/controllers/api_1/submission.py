# -*- coding: utf-8 -*-
__author__ = 'AminHP'

# python imports
import os

# flask imports
from flask import jsonify, request, g, send_file
from werkzeug.exceptions import RequestEntityTooLarge

# project imports
from project import app
from project.extensions import db, auth
from project.modules.datetime import utcnowts
from project.models.submission import Submission
from project.models.contest import Problem, Contest
from project.models.team import Team
from project.models.user import User
from project.forms.submission import UploadCode


@app.api_route('', methods=['POST'])
@auth.authenticate
def create():
    """
    Create Submission
    ---
    tags:
      - submission
    parameters:
      - name: contest_id
        in: formData
        type: string
        required: true
        description: If of contest
      - name: problem_id
        in: formData
        type: string
        required: true
        description: If of problem
      - name: team_id
        in: formData
        type: string
        required: true
        description: If of team
      - name: prog_lang
        in: formData
        type: integer
        required: true
        description: Programming language type (0=Cpp, 1=Python, 2=Java)
      - name: code
        in: formData
        type: file
        required: true
        description: Code file (max size is 4mb)
      - name: Access-Token
        in: header
        type: string
        required: true
        description: Token of current user
    responses:
      201:
        description: Successfully submitted
      400:
        description: Bad request
      401:
        description: Token is invalid or has expired
      403:
        description: You aren't allowed to submit
      404:
        description: Contest or problem or team does not exist
      406:
        description: Contest not started or has been finished
    """

    try:
        form = UploadCode()
        if not form.validate():
            return jsonify(errors="Bad request"), 400

        json = form.to_json()
        code = form.code.data

        contest_obj = Contest.objects().get(pk=json['contest_id'])
        problem_obj = Problem.objects().get(pk=json['problem_id'])
        team_obj = Team.objects().get(pk=json['team_id'])
        user_obj = User.objects().get(pk=g.user_id)

        if (not problem_obj in contest_obj.problems) or \
            (not team_obj in contest_obj.accepted_teams) or \
            (user_obj != team_obj.owner and not user_obj in team_obj.members):
            return jsonify(errors="You aren't allowed to submit"), 403

        now = utcnowts()
        if now < contest_obj.starts_at or now > contest_obj.ends_at:
            return jsonify(errors="Contest not started or has been finished"), 406

        obj = Submission()
        obj.populate(json)
        obj.contest = contest_obj
        obj.problem = problem_obj
        obj.team = team_obj
        obj.user = user_obj
        obj.save()

        file_obj = code
        directory = os.path.dirname(obj.code_addr)
        if not os.path.exists(directory):
            os.makedirs(directory)
        file_obj.save(obj.code_addr)

        return "", 201
    except (db.DoesNotExist, db.ValidationError):
        return jsonify(errors="Contest or problem or team does not exist"), 404
