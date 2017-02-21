# -*- coding: utf-8 -*-
__author__ = 'AminHP'

from good import Schema, All, Required, Length, Match, Email


signup_schema = Schema({
    Required('username'): All(unicode, Match(r'^[a-zA-Z0-9_]+$'), Length(max=32)),
    Required('email'): Email(),
    Required('password'): All(unicode, Length(min=3, max=32))
})


login_schema = Schema({
    Required('login'): unicode,
    Required('password'): unicode
})
