# coding: utf-8


class Page(object):
    def __init__(self, **kwargs):
        self.filename = kwargs.get('filename')
        self.title = kwargs.get('title')
        self.content = kwargs.get('content')
        self.is_start_page = kwargs.get('is_start_page')
