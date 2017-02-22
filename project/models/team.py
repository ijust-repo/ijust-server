# -*- coding: utf-8 -*-
__author__ = 'AminHP'

# project imports
from project.extensions import db


class Team(db.Document):
    name = db.StringField(required=True, unique=True)
    owner = db.ReferenceField('User', required=True)
    members = db.ListField(db.ReferenceField('User'))
    #contests = db.ListField(db.ReferenceField('Contest'))
    #pending_contests = db.ListField(db.ReferenceField('Contest'))
    #rejected_contests = db.ListField(db.ReferenceField('Contest'))


    def to_json(self):
        return dict(
            id = str(self.pk),
            name = self.name,
            owner = self.owner.to_json_abs(),
            members = [user.to_json_abs() for user in self.members]
        )


    def to_json_abs(self):
        return dict(
            id = str(self.pk),
            name = self.name
        )
