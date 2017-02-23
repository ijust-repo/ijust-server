# -*- coding: utf-8 -*-
__author__ = 'AminHP'

# flask imports
from flask import jsonify, request, g, redirect, url_for

# project imports
from project import app
from project.extensions import db, auth
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
              pattern: ^[a-zA-Z0-9_]+$
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
        schema:
          $ref: "#/definitions/api_1_user_info_get_UserInfo"
      400:
        description: Bad request
      409:
        description: Email or username already exists
    """

    json = request.json
    try:
        obj = User()
        obj.populate(json)
        obj.hash_password(json['password'])
        obj.save()
        return jsonify(obj.to_json()), 201
    except db.NotUniqueError:
        return jsonify(error="Email or username already exists"), 409


@app.api_route('login', methods=['POST'])
@app.api_validate('user.login_schema')
def login():
    """
    Login
    ---
    tags:
      - user
    parameters:
      - name: body
        in: body
        description: username/email and password for login
        required: true
        schema:
          id: UserLogin
          required:
            - login
            - password
          properties:
            login:
              type: string
              example: babyknight
              description: Username or Email
            password:
              type: string
              example: baby123
    responses:
      200:
        description: Successfully logged in
        schema:
          type: object
          properties:
            token:
              type: string
              description: Generated RESTful token
      400:
        description: Bad request
      404:
        description: User does not exist
      406:
        description: Wrong password
    """

    json = request.json
    login = json['login']
    password = json['password']

    try:
        if '@' in login:
            obj = User.objects().get(email=login)
        else:
            obj = User.objects().get(username=login)

        if obj.verify_password(password):
            token = auth.generate_token(obj.pk)
            return jsonify(token=token), 200
        else:
            return jsonify(errors='Wrong password'), 406

    except db.DoesNotExist:
        return jsonify(errors='User does not exist'), 404


@app.api_route('logout', methods=['POST'])
@auth.authenticate
def logout():
    """
    Logout
    ---
    tags:
      - user
    parameters:
      - name: Access-Token
        in: header
        type: string
        required: true
        description: Token of current user
    responses:
      200:
        description: Successfully logged out
      401:
        description: Token is invalid or has expired
    """

    auth.expire_token()
    return '', 200


@app.api_route('<string:uid>', methods=['GET'])
@auth.authenticate
def info(uid):
    """
    User Info
    ---
    tags:
      - user
    parameters:
      - name: uid
        in: path
        type: string
        required: true
        description: Id of user
      - name: Access-Token
        in: header
        type: string
        required: true
        description: Token of current user
    responses:
      200:
        description: User information
        schema:
          id: UserInfo
          type: object
          properties:
            id:
              type: string
              description: User id
            username:
              type: string
              description: Username
            email:
              type: string
              description: Email
      401:
        description: Token is invalid or has expired
      404:
        description: User does not exist
    """

    try:
        obj = User.objects().get(pk=uid)
        return jsonify(obj.to_json()), 200
    except (db.DoesNotExist, db.ValidationError):
        return jsonify(errors='User does not exist'), 404


@app.api_route('', methods=['GET'])
@auth.authenticate
def myinfo():
    """
    Current User Info
    ---
    tags:
      - user
    parameters:
      - name: Access-Token
        in: header
        type: string
        required: true
        description: Token of current user
    responses:
      200:
        description: Currnt user information
        schema:
          $ref: "#/definitions/api_1_user_info_get_UserInfo"
      401:
        description: Token is invalid or has expired
      404:
        description: User does not exist
    """

    return redirect(url_for('api_1.user.info', uid=g.user_id))
