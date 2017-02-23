# -*- coding: utf-8 -*-
__author__ = 'AminHP'

# python imports
import os
import shutil
import zipfile

# flask imports
from flask import jsonify, request, g, send_file
from werkzeug.exceptions import RequestEntityTooLarge

# project imports
from project import app
from project.extensions import db, auth
from project.models.contest import Problem, Contest, ContestDateTimeException
from project.models.team import Team
from project.models.user import User
from project.forms.problem import UploadProblemBody, UploadTestCase


@app.api_route('', methods=['POST'])
@app.api_validate('contest.create_schema')
@auth.authenticate
def create():
    """
    Create Contest
    ---
    tags:
      - contest
    parameters:
      - name: body
        in: body
        description: Contest information
        required: true
        schema:
          id: ContestCreation
          required:
            - name
            - starts_at
            - ends_at
          properties:
            name:
              type: string
              pattern: ^[a-zA-Z0-9_]+$
              example: babyknight
              maxLength: 32
            starts_at:
              type: integer
              description: Contest starts_at (utc timestamp)
            ends_at:
              type: integer
              description: Contest ends_at (utc timestamp)
      - name: Access-Token
        in: header
        type: string
        required: true
        description: Token of current user
    responses:
      201:
        description: Successfully created
        schema:
          $ref: "#/definitions/api_1_contest_info_get_ContestInfo"
      400:
        description: Bad request
      401:
        description: Token is invalid or has expired
      406:
        description: EndTime must be greater than StartTime and StartTime must be greater than CreationTime
      409:
        description: Contest already exists
    """

    json = request.json
    try:
        obj = Contest()
        obj.owner = User.objects().get(id=g.user_id)
        obj.populate(json)
        obj.save()
        return jsonify(obj.to_json()), 201

    except db.NotUniqueError:
        return jsonify(error="Contest already exists"), 409
    except ContestDateTimeException:
        return jsonify(
            error="EndTime must be greater than StartTime and StartTime must be greater than CreationTime"
        ), 406


@app.api_route('<string:cid>', methods=['GET'])
@auth.authenticate
def info(cid):
    """
    Get Contest Info
    ---
    tags:
      - contest
    parameters:
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
        description: Contest information
        schema:
          id: ContestInfo
          type: object
          properties:
            id:
              type: string
              description: Contest id
            name:
              type: string
              description: Contest name
            owner:
              description: Owner info
              schema:
                  id: ContestOwnerInfo
                  type: object
                  properties:
                    id:
                      type: string
                      description: Owner id
                    username:
                      type: string
                      description: Owner username
            created_at:
              type: integer
              description: Contest created_at (utc timestamp)
            starts_at:
              type: integer
              description: Contest starts_at (utc timestamp)
            ends_at:
              type: integer
              description: Contest ends_at (utc timestamp)
      401:
        description: Token is invalid or has expired
      404:
        description: Contest does not exist
    """

    try:
        obj = Contest.objects().get(pk=cid)
        return jsonify(obj.to_json()), 200
    except (db.DoesNotExist, db.ValidationError):
        return jsonify(errors='Contest does not exist'), 404


@app.api_route('<string:cid>', methods=['PUT'])
@app.api_validate('contest.edit_schema')
@auth.authenticate
def edit(cid):
    """
    Edit Contest
    ---
    tags:
      - contest
    parameters:
      - name: cid
        in: path
        type: string
        required: true
        description: Id of contest
      - name: body
        in: body
        description: Contest information
        required: true
        schema:
          id: ContestEdition
          properties:
            name:
              type: string
              pattern: ^[a-zA-Z0-9_]+$
              example: babyknight
              maxLength: 32
            starts_at:
              type: integer
              description: Contest starts_at (utc timestamp)
            ends_at:
              type: integer
              description: Contest ends_at (utc timestamp)
      - name: Access-Token
        in: header
        type: string
        required: true
        description: Token of current user
    responses:
      200:
        description: Successfully edited
        schema:
          $ref: "#/definitions/api_1_contest_info_get_ContestInfo"
      400:
        description: Bad request
      401:
        description: Token is invalid or has expired
      403:
        description: You aren't owner of the contest
      404:
        description: Contest does not exist
      406:
        description: EndTime must be greater than StartTime and StartTime must be greater than CreationTime
      409:
        description: Contest name already exists
    """

    json = request.json
    try:
        obj = Contest.objects().get(pk=cid)
        if str(obj.owner.pk) != g.user_id:
            return jsonify(errors="You aren't owner of the contest"), 403

        obj.populate(json)
        obj.save()
        return jsonify(obj.to_json()), 200

    except db.NotUniqueError:
        return jsonify(error="Contest name already exists"), 409
    except (db.DoesNotExist, db.ValidationError):
        return jsonify(errors='Contest does not exist'), 404
    except ContestDateTimeException:
        return jsonify(
            error="EndTime must be greater than StartTime and StartTime must be greater than CreationTime"
        ), 406



@app.api_route('<string:cid>/team', methods=['PATCH'])
@app.api_validate('contest.team_join_schema')
@auth.authenticate
def team_join(cid):
    """
    Team Join
    ---
    tags:
      - contest
    parameters:
      - name: cid
        in: path
        type: string
        required: true
        description: Id of contest
      - name: body
        in: body
        description: Team Identification
        required: true
        schema:
          id: TeamIdentification
          properties:
            team_id:
              type: string
      - name: Access-Token
        in: header
        type: string
        required: true
        description: Token of current user
    responses:
      200:
        description: Join request sent
      400:
        description: Bad request
      401:
        description: Token is invalid or has expired
      403:
        description: You aren't owner of the team
      404:
        description: Contest or Team does not exist
      409:
        description: You are already accepted
    """

    json = request.json
    try:
        obj = Contest.objects().get(pk=cid)
        team_obj = Team.objects().get(pk=json['team_id'])

        if str(team_obj.owner.pk) != g.user_id:
            return jsonify(errors="You aren't owner of the team"), 403

        if team_obj in obj.accepted_teams:
            return jsonify(errors='You are already accepted'), 409

        obj.update(add_to_set__pending_teams=team_obj)
        return '', 200
    except (db.DoesNotExist, db.ValidationError):
        return jsonify(errors='Contest or Team does not exist'), 404


@app.api_route('<string:cid>/team', methods=['DELETE'])
@app.api_validate('contest.team_unjoin_schema')
@auth.authenticate
def team_unjoin(cid):
    """
    Team Unjoin
    ---
    tags:
      - contest
    parameters:
      - name: cid
        in: path
        type: string
        required: true
        description: Id of contest
      - name: body
        in: body
        description: Team Identification
        required: true
        schema:
          $ref: "#/definitions/api_1_contest_team_join_patch_TeamIdentification"
      - name: Access-Token
        in: header
        type: string
        required: true
        description: Token of current user
    responses:
      200:
        description: Successfully unjoined
      400:
        description: Bad request
      401:
        description: Token is invalid or has expired
      403:
        description: You aren't owner of the team
      404:
        description: Contest or Team does not exist
    """

    json = request.json
    try:
        obj = Contest.objects().get(pk=cid)
        team_obj = Team.objects().get(pk=json['team_id'])

        if str(team_obj.owner.pk) != g.user_id:
            return jsonify(errors="You aren't owner of the team"), 403

        obj.update(pull__pending_teams=team_obj, pull__accepted_teams=team_obj)
        return '', 200
    except (db.DoesNotExist, db.ValidationError):
        return jsonify(errors='Contest or Team does not exist'), 404


@app.api_route('<string:cid>/team', methods=['GET'])
@auth.authenticate
def team_list(cid):
    """
    Team Get List
    ---
    tags:
      - contest
    parameters:
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
        description: List of teams
        schema:
          id: ContestTeamsList
          type: object
          properties:
            pending_teams:
              type: array
              items:
                schema:
                  id: TeamAbsInfo
                  type: object
                  properties:
                    id:
                      type: string
                      description: Team id
                    name:
                      type: string
                      description: Team name
                    owner:
                      schema:
                        $ref: "#/definitions/api_1_user_info_get_UserInfo"
            accepted_teams:
              type: array
              items:
                schema:
                  $ref: "#/definitions/api_1_contest_team_list_get_TeamAbsInfo"
      401:
        description: Token is invalid or has expired
      403:
        description: You aren't owner of the contest
      404:
        description: Contest does not exist
    """

    try:
        obj = Contest.objects().get(pk=cid)
        if str(obj.owner.pk) != g.user_id:
            return jsonify(errors="You aren't owner of the contest"), 403

        return jsonify(obj.to_json_teams()), 200
    except (db.DoesNotExist, db.ValidationError):
        return jsonify(errors='Contest does not exist'), 404


@app.api_route('<string:cid>/team/<string:tid>', methods=['PATCH'])
@auth.authenticate
def team_accept(cid, tid):
    """
    Team Accept
    ---
    tags:
      - contest
    parameters:
      - name: cid
        in: path
        type: string
        required: true
        description: Id of contest
      - name: tid
        in: path
        type: string
        required: true
        description: Id of team
      - name: Access-Token
        in: header
        type: string
        required: true
        description: Token of current user
    responses:
      200:
        description: Team Accepted
      401:
        description: Token is invalid or has expired
      403:
        description: You aren't owner of the contest
      404:
        description: Contest or Team does not exist
      406:
        description: The team did not request to join
    """

    try:
        obj = Contest.objects().get(pk=cid)
        if str(obj.owner.pk) != g.user_id:
            return jsonify(errors="You aren't owner of the contest"), 403

        team_obj = Team.objects().get(pk=tid)
        if not team_obj in obj.pending_teams:
            return jsonify(errors="The team did not request to join"), 406

        obj.update(pull__pending_teams=team_obj, add_to_set__accepted_teams=team_obj)
        return '', 200
    except (db.DoesNotExist, db.ValidationError):
        return jsonify(errors='Contest or Team does not exist'), 404


@app.api_route('<string:cid>/team/<string:tid>', methods=['DELETE'])
@auth.authenticate
def team_reject(cid, tid):
    """
    Team Reject
    ---
    tags:
      - contest
    parameters:
      - name: cid
        in: path
        type: string
        required: true
        description: Id of contest
      - name: tid
        in: path
        type: string
        required: true
        description: Id of team
      - name: Access-Token
        in: header
        type: string
        required: true
        description: Token of current user
    responses:
      200:
        description: Team Rejected
      401:
        description: Token is invalid or has expired
      403:
        description: You aren't owner of the contest
      404:
        description: Contest or Team does not exist
      406:
        description: The team did not request to join
    """

    try:
        obj = Contest.objects().get(pk=cid)
        if str(obj.owner.pk) != g.user_id:
            return jsonify(errors="You aren't owner of the contest"), 403

        team_obj = Team.objects().get(pk=tid)
        if not team_obj in obj.pending_teams:
            return jsonify(errors="The team did not request to join"), 406

        obj.update(pull__pending_teams=team_obj)
        return '', 200
    except (db.DoesNotExist, db.ValidationError):
        return jsonify(errors='Contest or Team does not exist'), 404



@app.api_route('<string:cid>/problem', methods=['POST'])
@app.api_validate('contest.problem_create_schema')
@auth.authenticate
def problem_create(cid):
    """
    Problem Create
    ---
    tags:
      - contest
    parameters:
      - name: cid
        in: path
        type: string
        required: true
        description: Id of contest
      - name: body
        in: body
        description: Problem information
        required: true
        schema:
          id: ProblemCreation
          required:
            - title
            - time_limit
            - space_limit
          properties:
            title:
              type: string
              example: babyknight
              maxLength: 32
            time_limit:
              type: number
              minimum: 0.1
              maximum: 10
              description: Problem time limit (seconds)
            space_limit:
              type: integer
              minimum: 16
              maximum: 256
              description: Problem space limit (mega bytes)
      - name: Access-Token
        in: header
        type: string
        required: true
        description: Token of current user
    responses:
      201:
        description: Successfully created
        schema:
          $ref: "#/definitions/api_1_contest_problem_info_get_ProblemInfo"
      400:
        description: Bad request
      401:
        description: Token is invalid or has expired
      403:
        description: You aren't owner of the contest
      404:
        description: Contest does not exist
    """

    json = request.json
    try:
        obj = Contest.objects().get(pk=cid)
        if str(obj.owner.pk) != g.user_id:
            return jsonify(errors="You aren't owner of the contest"), 403

        problem_obj = Problem()
        problem_obj.populate(json)
        problem_obj.save()
        obj.update(push__problems=problem_obj)
        return jsonify(problem_obj.to_json()), 201

    except (db.DoesNotExist, db.ValidationError):
        return jsonify(errors='Contest does not exist'), 404


@app.api_route('<string:cid>/problem/<string:pid>', methods=['GET'])
@auth.authenticate
def problem_info(cid, pid):
    """
    Problem Get Info
    ---
    tags:
      - contest
    parameters:
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
        description: Problem information
        schema:
          id: ProblemInfo
          type: object
          properties:
            id:
              type: string
              description: Problem id
            title:
              type: string
              description: Problem title
            time_limit:
              type: number
              description: Problem time limit (seconds)
            space_limit:
              type: integer
              description: Problem space limit (mega bytes)
      401:
        description: Token is invalid or has expired
      403:
        description: You aren't owner of the contest
      404:
        description: Contest or problem does not exist
    """

    try:
        obj = Contest.objects().get(pk=cid)
        if str(obj.owner.pk) != g.user_id:
            return jsonify(errors="You aren't owner of the contest"), 403

        problem_obj = Problem.objects().get(pk=pid)
        return jsonify(problem_obj.to_json()), 200
    except (db.DoesNotExist, db.ValidationError):
        return jsonify(errors='Contest or problem does not exist'), 404


@app.api_route('<string:cid>/problem', methods=['GET'])
@auth.authenticate
def problem_list(cid):
    """
    Problem Get List
    ---
    tags:
      - contest
    parameters:
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
        description: List of problems
        schema:
          id: ContestProblemsList
          type: object
          properties:
            problems:
              type: array
              items:
                schema:
                  id: ProblemAbsInfo
                  type: object
                  properties:
                    id:
                      type: string
                      description: Problem id
                    title:
                      type: string
                      description: Problem title
      401:
        description: Token is invalid or has expired
      403:
        description: You aren't owner of the contest
      404:
        description: Contest does not exist
    """

    try:
        obj = Contest.objects().get(pk=cid)
        if str(obj.owner.pk) != g.user_id:
            return jsonify(errors="You aren't owner of the contest"), 403

        return jsonify(obj.to_json_problems()), 200
    except (db.DoesNotExist, db.ValidationError):
        return jsonify(errors='Contest does not exist'), 404


@app.api_route('<string:cid>/problem/<string:pid>', methods=['PUT'])
@app.api_validate('contest.problem_edit_schema')
@auth.authenticate
def problem_edit(cid, pid):
    """
    Problem Edit
    ---
    tags:
      - contest
    parameters:
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
      - name: body
        in: body
        description: Problem information
        required: true
        schema:
          id: ProblemEdition
          properties:
            title:
              type: string
              example: babyknight
              maxLength: 32
            time_limit:
              type: number
              minimum: 0.1
              maximum: 10
              description: Problem time limit (seconds)
            space_limit:
              type: integer
              minimum: 16
              maximum: 256
              description: Problem space limit (mega bytes)
      - name: Access-Token
        in: header
        type: string
        required: true
        description: Token of current user
    responses:
      200:
        description: Successfully edited
        schema:
          $ref: "#/definitions/api_1_contest_problem_info_get_ProblemInfo"
      400:
        description: Bad request
      401:
        description: Token is invalid or has expired
      403:
        description: You aren't owner of the contest
      404:
        description: Contest or problem does not exist
    """

    json = request.json
    try:
        obj = Contest.objects().get(pk=cid)
        if str(obj.owner.pk) != g.user_id:
            return jsonify(errors="You aren't owner of the contest"), 403

        problem_obj = Problem.objects().get(pk=pid)
        problem_obj.populate(json)
        problem_obj.save()
        return jsonify(problem_obj.to_json()), 200

    except (db.DoesNotExist, db.ValidationError):
        return jsonify(errors='Contest does not exist'), 404


@app.api_route('<string:cid>/problem', methods=['PATCH'])
@app.api_validate('contest.problem_change_order_schema')
@auth.authenticate
def problem_change_order(cid):
    """
    Problem Change Order
    ---
    tags:
      - contest
    parameters:
      - name: cid
        in: path
        type: string
        required: true
        description: Id of contest
      - name: body
        in: body
        description: Problems order
        required: true
        schema:
          id: ProblemsOrder
          required:
          - order
          properties:
            order:
              type: array
              items:
                type: integer
                description: order number
      - name: Access-Token
        in: header
        type: string
        required: true
        description: Token of current user
    responses:
      200:
        description: List of problems
        schema:
          $ref: "#/definitions/api_1_contest_problem_list_get_ContestProblemsList"
      400:
        description: Bad request
      401:
        description: Token is invalid or has expired
      403:
        description: You aren't owner of the contest
      404:
        description: Contest does not exist
      406:
        description: Bad order format
    """

    json = request.json
    try:
        obj = Contest.objects().get(pk=cid)
        if str(obj.owner.pk) != g.user_id:
            return jsonify(errors="You aren't owner of the contest"), 403

        if len(list(set(json['order']))) != len(json['order']) or \
            len(json['order']) != len(obj.problems):
            return jsonify(errors="Bad order format"), 406

        new_problems = []
        for i in json['order']:
            new_problems.append(obj.problems[i])
        obj.problems = new_problems
        obj.save()

        return jsonify(obj.to_json_problems()), 200
    except IndexError:
        return jsonify(errors="Bad order format"), 406
    except (db.DoesNotExist, db.ValidationError):
        return jsonify(errors='Contest does not exist'), 404


@app.api_route('<string:cid>/problem/<string:pid>', methods=['DELETE'])
@auth.authenticate
def problem_delete(cid, pid):
    """
    Problem Delete
    ---
    tags:
      - contest
    parameters:
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
        description: List of problems
        schema:
          $ref: "#/definitions/api_1_contest_problem_list_get_ContestProblemsList"
      401:
        description: Token is invalid or has expired
      403:
        description: You aren't owner of the contest
      404:
        description: Contest or problem does not exist
    """

    try:
        obj = Contest.objects().get(pk=cid)
        if str(obj.owner.pk) != g.user_id:
            return jsonify(errors="You aren't owner of the contest"), 403

        problem_obj = Problem.objects().get(pk=pid)
        problem_obj.delete()
        obj.reload()
        return jsonify(obj.to_json_problems()), 200
    except (db.DoesNotExist, db.ValidationError):
        return jsonify(errors='Contest or problem does not exist'), 404


@app.api_route('<string:cid>/problem/<string:pid>/body', methods=['POST'])
@auth.authenticate
def problem_upload_body(cid, pid):
    """
    Problem Upload Body File
    ---
    tags:
      - contest
    parameters:
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
      - name: body
        in: formData
        type: file
        required: true
        description: Problem body file (pdf) (max size is 4mb)
      - name: Access-Token
        in: header
        type: string
        required: true
        description: Token of current user
    responses:
      200:
        description: Successfully uploaded
      400:
        description: Bad file
      401:
        description: Token is invalid or has expired
      403:
        description: You aren't owner of the contest
      404:
        description: Contest or problem does not exist
      413:
        description: Request entity too large. (max is 4mg)
    """

    try:
        obj = Contest.objects().get(pk=cid)
        if str(obj.owner.pk) != g.user_id:
            return jsonify(errors="You aren't owner of the contest"), 403

        form = UploadProblemBody()
        if not form.validate():
            return jsonify(errors="Bad file"), 400

        problem_obj = Problem.objects().get(pk=pid)
        file_obj = form.body.data
        file_obj.save(problem_obj.body_addr)

        return "", 200
    except RequestEntityTooLarge:
        return jsonify(errors='Request entity too large. (max is 4mg)'), 413
    except (db.DoesNotExist, db.ValidationError):
        return jsonify(errors='Contest or problem does not exist'), 404


@app.api_route('<string:cid>/problem/<string:pid>/testcase', methods=['POST'])
@auth.authenticate
def problem_upload_testcase(cid, pid):
    """
    Problem Upload Testcase File
    ---
    tags:
      - contest
    parameters:
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
      - name: testcase
        in: formData
        type: file
        required: true
        description: Problem testcase file (zip) (max size is 4mb)
      - name: Access-Token
        in: header
        type: string
        required: true
        description: Token of current user
    responses:
      200:
        description: Successfully uploaded
      400:
        description: Bad file
      401:
        description: Token is invalid or has expired
      403:
        description: You aren't owner of the contest
      404:
        description: Contest or problem does not exist
      413:
        description: Request entity too large. (max is 4mg)
    """

    try:
        obj = Contest.objects().get(pk=cid)
        if str(obj.owner.pk) != g.user_id:
            return jsonify(errors="You aren't owner of the contest"), 403

        form = UploadTestCase()
        if not form.validate():
            return jsonify(errors="Bad file"), 400

        problem_obj = Problem.objects().get(pk=pid)
        if os.path.exists(problem_obj.testcase_dir):
            shutil.rmtree(problem_obj.testcase_dir)

        file_obj = form.testcase.data
        with zipfile.ZipFile(file_obj) as zf:
            zf.extractall(problem_obj.testcase_dir)

        return "", 200
    except RequestEntityTooLarge:
        return jsonify(errors='Request entity too large. (max is 4mg)'), 413
    except (db.DoesNotExist, db.ValidationError):
        return jsonify(errors='Contest or problem does not exist'), 404


@app.api_route('<string:cid>/problem/<string:pid>/body', methods=['GET'])
@auth.authenticate
def problem_download_body(cid, pid):
    """
    Problem Download Body File
    ---
    tags:
      - contest
    parameters:
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
        description: Problem body file
      401:
        description: Token is invalid or has expired
      403:
        description: You aren't owner of the contest
      404:
        description: Contest or problem does not exist
    """

    try:
        obj = Contest.objects().get(pk=cid)
        if str(obj.owner.pk) != g.user_id:
            return jsonify(errors="You aren't owner of the contest"), 403

        problem_obj = Problem.objects().get(pk=pid)
        return send_file(problem_obj.body_addr)

    except (db.DoesNotExist, db.ValidationError):
        return jsonify(errors='Contest or problem does not exist'), 404
