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
            - starts_on
            - ends_on
          properties:
            name:
              type: string
              pattern: ^[a-zA-Z0-9_]+$
              example: babyknight
              maxLength: 32
            starts_on:
              type: integer
              description: Contest starts_on (utc timestamp)
            ends_on:
              type: integer
              description: Contest ends_on (utc timestamp)
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
            created_on:
              type: integer
              description: Contest created_on (utc timestamp)
            starts_on:
              type: integer
              description: Contest starts_on (utc timestamp)
            ends_on:
              type: integer
              description: Contest ends_on (utc timestamp)
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
            starts_on:
              type: integer
              description: Contest starts_on (utc timestamp)
            ends_on:
              type: integer
              description: Contest ends_on (utc timestamp)
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
        description: You are'nt owner of the contest
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
            return jsonify(errors="You are'nt owner of the contest"), 403

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
