# -*- coding: utf-8 -*-
__author__ = 'AminHP'

# python imports
from time import time

# project imports
from project.extensions import db


class ContestDateTimeException(db.ValidationError):
    pass


class Contest(db.Document):
    name = db.StringField(required=True, unique=True)
    owner = db.ReferenceField('User', required=True)
    created_on = db.IntField(required=True, default=lambda: int(time()))
    starts_on = db.IntField(required=True)
    ends_on = db.IntField(required=True)


    def populate(self, json):
        if 'name' in json:
            self.name = json['name']
        if 'starts_on' in json:
            self.starts_on = json['starts_on']
        if 'ends_on' in json:
            self.ends_on = json['ends_on']


    def save(self):
        if not (self.created_on < self.starts_on < self.ends_on):
            raise ContestDateTimeException()
        super(Contest, self).save()


    def to_json(self):
        return dict(
            id = str(self.pk),
            name = self.name,
            owner = self.owner.to_json_abs(),
            created_on = self.created_on,
            starts_on = self.starts_on,
            ends_on = self.ends_on
        )
