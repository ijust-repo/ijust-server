# -*- coding: utf-8 -*-
__author__ = 'AminHP'

# flask imports
from flask import jsonify, request, g

# project imports
from project import app
from project.extensions import db, auth
from project.models.team import Team
from project.models.user import User


@app.api_route('', methods=['POST'])
@app.api_validate('team.create_schema')
@auth.authenticate
def create():
    """
    Create Team
    ---
    tags:
      - team
    parameters:
      - name: body
        in: body
        description: Team information
        required: true
        schema:
          id: TeamCreation
          required:
            - name
          properties:
            name:
              type: string
              pattern: ^[a-zA-Z0-9_]+$
              example: babyknight
              maxLength: 32
            members:
              type: array
              maxLength: 2
              items:
                type: string
                description: Member username
      - name: Access-Token
        in: header
        type: string
        required: true
        description: Token of current user
    responses:
      201:
        description: Successfully created
        schema:
          $ref: "#/definitions/api_1_team_info_get_TeamInfo"
      400:
        description: Bad request
      401:
        description: Token is invalid or has expired
      404:
        description: Member does not exist
      406:
        description: You can't create more teams
      409:
        description: Team already exists
    """

    json = request.json
    try:
        owner = User.objects().get(id=g.user_id)
        if len(owner.teams) > 5:
            return jsonify(errors="You can't create more teams"), 406

        json['members'] = filter(lambda un: un != owner.username, json['members'])
        obj = Team(name=json['name'])
        obj.owner = owner
        obj.members = [User.objects().get(username=username) for username in json['members']]
        obj.save()

        owner.teams.append(obj)
        owner.save()

        for user in obj.members:
            user.teams.append(obj)
            user.save()
        return jsonify(obj.to_json()), 201

    except db.NotUniqueError:
        return jsonify(error="Team already exists"), 409
    except (db.DoesNotExist, db.ValidationError):
        return jsonify(errors='Member does not exist'), 404


@app.api_route('<string:teamid>', methods=['GET'])
@auth.authenticate
def info(teamid):
    """
    Team Info
    ---
    tags:
      - team
    parameters:
      - name: teamid
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
        description: Team information
        schema:
          id: TeamInfo
          type: object
          properties:
            id:
              type: string
              description: Team id
            name:
              type: string
              description: Team name
            owner:
              description: Owner info
              schema:
                  id: TeamMemberInfo
                  type: object
                  properties:
                    id:
                      type: string
                      description: Member id
                    username:
                      type: string
                      description: Member username
            members:
              type: array
              items:
                schema:
                  $ref: "#/definitions/api_1_team_info_get_TeamMemberInfo"
      401:
        description: Token is invalid or has expired
      404:
        description: Team does not exist
    """

    try:
        obj = Team.objects().get(pk=teamid)
        return jsonify(obj.to_json()), 200
    except (db.DoesNotExist, db.ValidationError):
        return jsonify(errors='Team does not exist'), 404


@app.api_route('<string:teamid>', methods=['PUT'])
@app.api_validate('team.edit_schema')
@auth.authenticate
def edit(teamid):
    """
    Edit Team
    ---
    tags:
      - team
    parameters:
      - name: teamid
        in: path
        type: string
        required: true
        description: Id of team
      - name: body
        in: body
        description: Team information
        required: true
        schema:
          id: TeamEdition
          properties:
            name:
              type: string
              pattern: ^[a-zA-Z0-9_]+$
              example: babyknight
              maxLength: 32
            members:
              type: array
              maxLength: 2
              items:
                type: string
                description: Member username
      - name: Access-Token
        in: header
        type: string
        required: true
        description: Token of current user
    responses:
      200:
        description: Successfully edited
        schema:
          $ref: "#/definitions/api_1_team_info_get_TeamInfo"
      400:
        description: Bad request
      401:
        description: Token is invalid or has expired
      403:
        description: You are'nt owner of the team
      404:
        description: Member does not exist
      409:
        description: Team name already exists
    """

    json = request.json
    try:
        obj = Team.objects().get(pk=teamid)
        if str(obj.owner.pk) != g.user_id:
            return jsonify(errors="You are'nt owner of the team"), 403

        if 'name' in json:
            obj.name = json['name']

        if 'members' in json:
            json['members'] = filter(lambda un: un != obj.owner.username, json['members'])
            new_members = [User.objects().get(username=username) for username in json['members']]

            for m in obj.members:
                m.update(pull__teams=obj)

            obj.members = new_members
            for user in obj.members:
                user.teams.append(obj)
                user.save()

        obj.save()
        return jsonify(obj.to_json()), 200

    except db.NotUniqueError:
        return jsonify(error="Team name already exists"), 409
    except (db.DoesNotExist, db.ValidationError):
        return jsonify(errors='Member does not exist'), 404
