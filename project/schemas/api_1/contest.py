# -*- coding: utf-8 -*-
__author__ = 'AminHP'

from good import Schema, All, Any, Required, Optional, Length, Match, Default


create_schema = Schema({
    Required('name'): All(unicode, Match(r'^[a-zA-Z0-9_]+$'), Length(max=32)),
    Required('starts_at'): int,
    Required('ends_at'): int
})


edit_schema = create_schema



team_join_schema = Schema({
    Required('team_id'): unicode
})


team_unjoin_schema = team_join_schema
