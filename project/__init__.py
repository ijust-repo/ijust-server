# -*- coding: utf-8 -*-
__author__ = 'AminHP'

from application import create_app

app = create_app()

from project.controllers import *
