# -*- coding: utf-8 -*-
__author__ = 'AminHP'

# python imports
import os

# flask imports
from flask import jsonify, request, g, send_file, abort

# project imports
from project import app
from project.extensions import db, auth
from project.modules.datetime import utcnowts
from project.models.submission import Submission
from project.models.contest import Problem, Contest
from project.models.team import Team
from project.models.user import User
from project.forms.submission import UploadCode
from project.extensions import celery


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
        description: You aren't owner or member of the team
      404:
        description: Contest or problem or team does not exist
      406:
        description: Contest has not started or has been finished
      413:
        description: Request entity too large. (max is 4mg)
      415:
        description: Supported file type is only text/plain
    """

    try:
        form = UploadCode()
        if not form.validate():
            return abort(400, "Bad request")

        if not form.validate_file():
            return abort(415, "Supported file type is only text/plain")

        json = form.to_json()
        code = form.code.data

        problem_obj = Problem.objects.get(pk=json['problem_id'])
        team_obj = Team.objects.get(pk=json['team_id'])
        contest_obj = Contest.objects.get(pk=json['contest_id'], accepted_teams=team_obj, problems=problem_obj)
        user_obj = User.objects.get(pk=g.user_id)

        if not team_obj.is_user_in_team(user_obj):
            return abort(403, "You aren't owner or member of the team")

        now = utcnowts()
        if now < contest_obj.starts_at or now > contest_obj.ends_at:
            return abort(406, "Contest has not started or has been finished")

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

        check_code.delay(str(obj.pk))

        return "", 201
    except (db.DoesNotExist, db.ValidationError):
        return abort(404, "Contest or problem or team does not exist")


@app.api_route('team/<string:tid>/contest/<string:cid>/', methods=['GET'])
@auth.authenticate
def list(tid, cid):
    """
    Get All The Team Submissions in a Contest
    ---
    tags:
      - submission
    parameters:
      - name: tid
        in: path
        type: string
        required: true
        description: Id of team
      - name: cid
        in: path
        type: string
        required: true
        description: Id of contest
      - name: Access-Token
        in: header
        type: string
        required: true
        description: Token of current user
    responses:
      200:
        description: Submissions list
        schema:
          id: SubmissionList
          type: object
          properties:
            id:
              type: string
              description: Submission id
            filename:
              type: string
              description: The code file name
            prog_lang:
              type: string
              description: Programming language
            submitted_at:
              type: integer
              description: Submission submitted_at (utc timestamp)
            problem:
              schema:
                $ref: "#/definitions/api_1_contest_problem_list_get_ProblemAbsInfo"
            user:
              description: The member who submitted the code
              schema:
                $ref: "#/definitions/api_1_team_info_get_UserAbsInfo"
            status:
              type: string
              description: Submission status
            reason:
              type: string
              description: Error reason (is null when status is Pending or Accepted)
      400:
        description: Bad request
      401:
        description: Token is invalid or has expired
      403:
        description: You aren't owner or member of the team
      404:
        description: Team or contest does not exist
    """

    try:
        team_obj = Team.objects.get(pk=tid)
        contest_obj = Contest.objects.get(pk=cid, accepted_teams=team_obj)
        user_obj = User.objects.get(pk=g.user_id)

        if not team_obj.is_user_in_team(user_obj):
            return abort(403, "You aren't owner or member of the team")

        submissions = Submission.objects.filter(
            contest=contest_obj,
            team=team_obj).order_by('-submitted_at')

        submissions = [s.to_json() for s in submissions]

        return jsonify(submissions=submissions), 200
    except (db.DoesNotExist, db.ValidationError):
        return abort(404, "Team or contest does not exist")


@app.api_route('team/<string:tid>/contest/<string:cid>/problem/<string:pid>', methods=['GET'])
@auth.authenticate
def list_problem(tid, cid, pid):
    """
    Get All The Team Submissions in a Contest for a Problem
    ---
    tags:
      - submission
    parameters:
      - name: tid
        in: path
        type: string
        required: true
        description: Id of team
      - name: cid
        in: path
        type: string
        required: true
        description: Id of contest
      - name: pid
        in: path
        type: string
        required: true
        description: Id of problem
      - name: Access-Token
        in: header
        type: string
        required: true
        description: Token of current user
    responses:
      200:
        description: Submissions list
        schema:
          $ref: "#/definitions/api_1_submission_list_get_SubmissionList"
      400:
        description: Bad request
      401:
        description: Token is invalid or has expired
      403:
        description: You aren't owner or member of the team
      404:
        description: Team or contest or problem does not exist
    """

    try:
        team_obj = Team.objects.get(pk=tid)
        problem_obj = Problem.objects.get(pk=pid)
        contest_obj = Contest.objects.get(pk=cid, accepted_teams=team_obj, problems=problem_obj)
        user_obj = User.objects.get(pk=g.user_id)

        if not team_obj.is_user_in_team(user_obj):
            return abort(403, "You aren't owner or member of the team")

        submissions = Submission.objects.filter(
            contest=contest_obj,
            team=team_obj,
            problem=problem_obj).order_by('-submitted_at')

        submissions = [s.to_json() for s in submissions]

        return jsonify(submissions=submissions), 200
    except (db.DoesNotExist, db.ValidationError):
        return abort(404, "Team or contest or problem does not exist")


@app.api_route('<string:sid>/code', methods=['GET'])
@auth.authenticate
def download_code(sid):
    """
    Download Code File
    ---
    tags:
      - submission
    parameters:
      - name: sid
        in: path
        type: string
        required: true
        description: Id of submission
      - name: Access-Token
        in: header
        type: string
        required: true
        description: Token of current user
    responses:
      200:
        description: Code file
      401:
        description: Token is invalid or has expired
      403:
        description: You aren't owner or member of the team
      404:
        description: Submission does not exist
    """

    try:
        obj = Submission.objects.get(pk=sid)
        user_obj = User.objects.get(pk=g.user_id)

        if not obj.team.is_user_in_team(user_obj):
            return abort(403, "You aren't owner or member of the team")

        return send_file(obj.code_addr)
    except (db.DoesNotExist, db.ValidationError):
        return abort(404, "Submission does not exist")



@celery.task()
def check_code(sid):
    obj = Submission.objects.get(pk=sid)
    # check submitted code here
