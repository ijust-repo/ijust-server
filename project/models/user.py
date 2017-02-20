# -*- coding: utf-8 -*-
__author__ = 'AminHP'

# python imports
from passlib.apps import custom_app_context as pwd_context

# project imports
from project.extensions import db


class User(db.Document):
    username = db.StringField(required=True, unique=True)
    email = db.StringField(required=True, unique=True)
    password = db.StringField(required=True)
    #teams = db.ListField(ReferenceField('Team'))


    def hash_password(self, password):
        password = password.encode('utf-8')
        self.password = pwd_context.encrypt(password)


    def verify_password(self, password):
        password = password.encode('utf-8')
        return pwd_context.verify(password, self.password)


    def change_password(self, old_password, new_password):
        if self.verify_password(old_password):
            self.hash_password(new_password)
            return True
        return False


    def to_json(self):
        return dict(
            id = str(self.pk),
            username = self.username,
            email = self.email
        )
