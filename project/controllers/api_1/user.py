# -*- coding: utf-8 -*-
__author__ = 'AminHP'

# flask imports
from flask import jsonify, request

# project imports
from project import app
from project.extensions import db
from project.models.user import User


@app.api_route('signup', methods=['POST'])
@app.api_validate('user.signup_schema')
def signup():
    """
    Signup
    ---
    tags:
      - user
    parameters:
      - name: body
        in: body
        description: username, email and password for signup
        required: true
        schema:
          id: UserSignup
          required:
            - username
            - email
            - password
          properties:
            username:
              type: string
              pattern: ^[\w.]+$
              example: babyknight
              maxLength: 32
            email:
              type: string
              example: baby@knight.org
            password:
              type: string
              example: baby123
              minLength: 3
              maxLength: 32
    responses:
      201:
        description: Successfully registered
      400:
        description: Bad request
      409:
        description: Email or username already exists
    """

    json = request.json
    try:
        obj = User(username=json['username'], email=json['email'])
        obj.hash_password(json['password'])
        obj.save()
    except db.NotUniqueError:
        return jsonify(error="Email or username already exists"), 409

    return "", 201
