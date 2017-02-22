# -*- coding: utf-8 -*-
__author__ = 'AminHP'

# project imports
from project.extensions import db


class Team(db.Document):
    name = db.StringField(required=True, unique=True)
    owner = db.ReferenceField('User', required=True)
    members = db.ListField(db.ReferenceField('User'))


    def populate(self, json):
        from project.models.user import User

        if 'name' in json:
            self.name = json['name']
        if 'members' in json:
            members = filter(lambda un: un != self.owner.username, json['members'])
            members = [User.objects().get(username=username) for username in members]

            for m in (self.members or []):
                m.update(pull__teams=self)

            self.members = members
            for user in self.members:
                user.teams.append(self)
                user.save()


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
