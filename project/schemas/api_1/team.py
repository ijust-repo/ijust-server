# -*- coding: utf-8 -*-
__author__ = 'AminHP'

from good import Schema, All, Any, Required, Optional, Length, Match, Default


create_schema = Schema({
    Required('name'): All(unicode, Match(r'^[a-zA-Z0-9_]+$'), Length(max=32)),
    Required('members'): Any(All(list, Length(max=2)), Default([]))
})


edit_schema = Schema({
    Optional('name'): All(unicode, Match(r'^[a-zA-Z0-9_]+$'), Length(max=32)),
    Optional('members'): All(list, Length(max=2))
})
