# -*- coding: utf-8 -*-
__author__ = 'AminHP'

# flask imports
from flask import jsonify, request, g

# project imports
from project import app
from project.extensions import db, auth
from project.models.contest import Contest, ContestDateTimeException
from project.models.team import Team
from project.models.user import User


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
    Contest Info
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
        description: Id of Contest
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
        description: Id of Contest
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
        description: Id of Contest
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
    Team List
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
        description: Id of Contest
      - name: tid
        in: path
        type: string
        required: true
        description: Id of Team
      - name: Access-Token
        in: header
        type: string
        required: true
        description: Token of current user
    responses:
      200:
        description: Team Accepted
      400:
        description: Bad request
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
        description: Id of Contest
      - name: tid
        in: path
        type: string
        required: true
        description: Id of Team
      - name: Access-Token
        in: header
        type: string
        required: true
        description: Token of current user
    responses:
      200:
        description: Team Rejected
      400:
        description: Bad request
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
    pass


@app.api_route('<string:cid>/problem/<string:pid>', methods=['PUT'])
@app.api_validate('contest.problem_edit_schema')
@auth.authenticate
def problem_edit(cid, pid):
    pass


@app.api_route('<string:cid>/problem', methods=['PATCH'])
@app.api_validate('contest.problem_change_order_schema')
@auth.authenticate
def problem_change_order(cid):
    pass


@app.api_route('<string:cid>/problem', methods=['GET'])
@auth.authenticate
def problem_list(cid):
    pass


@app.api_route('<string:cid>/problem/<string:pid>', methods=['GET'])
@auth.authenticate
def problem_info(cid, pid):
    pass
