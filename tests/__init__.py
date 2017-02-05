# -*- coding: utf-8 -*-

class MockSettings(object):
    def __init__(self, **kwargs):
        [self.__setattr__(key, val) for key, val in kwargs.items()]
