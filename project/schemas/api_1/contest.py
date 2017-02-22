# -*- coding: utf-8 -*-
__author__ = 'AminHP'

from good import Schema, All, Any, Required, Optional, Length, Match, Default


create_schema = Schema({
    Required('name'): All(unicode, Match(r'^[a-zA-Z0-9_]+$'), Length(max=32)),
    Required('starts_on'): int,
    Required('ends_on'): int
})


edit_schema = create_schema
