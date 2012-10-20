# coding: utf-8
import os
import logging
import argparse
import itertools
import hashlib

import sqlsoup
from models import Page


class RedmineWikiExport(object):
    def __init__(self, project_identifier, **config):
        self.project_identifier = project_identifier
        self.config = config
        self.counter = itertools.count()

    def get_db(self):
        return sqlsoup.SQLSoup('mysql://root@localhost/redmine?charset=utf8')

    def get_output_dir(self):
        return os.path.join('output', os.path.dirname(__file__))

    def get_project(self, identifier):
        "プロジェクトを取得"
        logging.debug("get_project:identifier=%s" % identifier)
        db = self.get_db()
        return db.projects.filter(db.projects.identifier==identifier).one()

    def get_wiki(self, project_id):
        "プロジェクトのwikiを取得"
        logging.debug("get_wiki:project_id=%s" % project_id)
        db = self.get_db()
        return db.wikis.filter(db.wikis.project_id==project_id).one()

    def get_wiki_pages(self, wiki_id):
        "wikiページを取得"
        logging.debug("get_wiki_pages:wiki_id=%s" % wiki_id)
        db = self.get_db()
        return db.wiki_pages.filter(db.wiki_pages.wiki_id==wiki_id)

    def get_wiki_content(self, page_id):
        "wikiのコンテンツを取得"
        db = self.get_db()
        return db.wiki_contents.filter(db.wiki_contents.page_id==page_id).one()

    def save_to_file(self, filepath, content):
        "ファイルに書き出し"
        with open(filepath, 'wb') as f:
            f.write(content.encode('utf-8'))

    def get_filename(self, title):
        try:
            name = str(title)
        except UnicodeEncodeError:
            name = hashlib.md5(title.encode('utf-8')).hexdigest()
        return "%s.rst" % name

    def toc_tree(self, pages):
        toctree = """.. toctree::
   :maxdepth: 2

"""
        if len(pages) == 1:
            return ""
        for page in pages:
            if not page.is_start_page:
                toctree += "   %s\n" % os.path.splitext(page.filename)[0]
        return toctree

    def run(self):
        # db接続
        # ページ全部取得
        # rst出力
        # sphinxプロジェクト作成
        # wikiインデックスにtoctree埋め込む
        db = self.get_db()
        project = self.get_project(self.project_identifier)
        wiki = self.get_wiki(project.id)
        wiki_pages = self.get_wiki_pages(wiki.id)
        pages = []
        for wiki_page in wiki_pages:
            page = Page(
                filename=self.get_filename(wiki_page.title),
                title=wiki_page.title,
                content=self.get_wiki_content(wiki_page.id).text,
                is_start_page=wiki_page.title==wiki.start_page)
            pages.append(page)
        output_dir = self.get_output_dir()
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        for page in pages:
            # indexページならtoctreeを埋め込む
            if page.is_start_page:
                page.content += '\n\n' + self.toc_tree(pages)
            self.save_to_file(os.path.join(output_dir, page.filename), page.content)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('project_identifier')
    args = parser.parse_args()
    # TODO: 設定ファイル読み込み
    rwe = RedmineWikiExport(args.project_identifier)
    rwe.run()


if __name__ == '__main__':
    main()
