# -*- coding: utf-8 -*-

import json
import re
import urllib
from urllib.request import urlopen

from bs4 import BeautifulSoup

##############################
# WikiReader Class
##############################


class WikiReader:

    def __init__(self, keyword=None):
        """
        initialize
        :param keyword:
        """

        self.api_base = "https://ja.wikipedia.org/w/api.php"

        self.keyword = keyword
        self.title = None

        if self.keyword is None:
            # set random keyword
            self.keyword = self.get_random_keyword()

        self.keyword.replace(" ", "_")
        self.keyword = self.conv_to_ascii(self.keyword)

    def get_content(self):
        """
        :return:
        """
        content = ''
        json_data = self.get_content_json(self.keyword)

        is_content = False

        if "error" in json_data.keys():
            return None

        self.title = json_data['parse']['title']

        html = json_data['parse']['text']['*']
        bs_obj = BeautifulSoup(html, "html.parser")

        try:
            p_elements = bs_obj.findAll(["p"])
        except Exception:
            return None
        else:
            redirect_text_count = bs_obj.findAll("ul", {"class": "redirectText"})
            if len(redirect_text_count) > 0:
                redirect_text = bs_obj.findAll("ul", {"class": "redirectText"})[0].get_text()
                self.keyword = self.conv_to_ascii(redirect_text)
                return self.get_content()

            content_starter_regex = "^([^\x00-\x7F]|[\x00-\x7F])+は、"
            for p in p_elements:

                if re.findall(content_starter_regex, self.normalize(p.get_text())):
                    is_content = True

                if is_content:
                    text = p.get_text()

                    # （2018年6月現在）目次の前に空のパラグラフがある場合が多いので、コンテンツの区切りとして利用している
                    if text is not '':
                        content += text
                    else:
                        break

            content = self.format_content(content)

            return content

    def get_content_json(self, keyword: str):
        query_string = "?format=json&action=parse&section=0&prop=text&page=" + keyword
        url = urlopen(self.api_base + query_string.replace(' ', '+'))
        return json.load(url)

    def get_random_keyword(self):
        """
        :return:
        """
        query_string = "?action=query&format=json&list=random&rnnamespace=0&rnlimit=1"
        url = urlopen(self.api_base + query_string)
        json_data = json.load(url)
        random_keyword = json_data['query']['random'][0]['title']
        return random_keyword

    def format_content(self, content):
        """
        本文の整形
        :param content:
        :return:
        """

        content = self.normalize(content)

        exclude_list = [
            u"この記事には複数の問題があります。改善やノートページでの議論にご協力ください。",
            u"引用エラー: ",
            u"「注」という名前のグループの",
            u"タグがありません",
            u"\\n。",
        ]

        content = self.exclude(content, exclude_list)

        # 最後の文に問題があれば除去する
        if self.check_last_sentence_error(content) is False:
            content = self.remove_last_sentence(content)

        # &はエラーになるので除去
        content = content.replace("&", "")

        return content

    def normalize(self, content):
        return re.sub(r'（[^（）]*）|\([^\(\)]*\)|\[[^\[\]]*\]|<.+>', "", content)

    def conv_to_ascii(self, url):
        regex = r'[^\x00-\x7F]'
        match_all = re.findall(regex, url)
        for m in match_all:
            url = url.replace(m, urllib.parse.quote_plus(m, encoding="utf-8"))
        return url

    def exclude(self, content, exclude_list):
        """
        除外テキストの置換処理
        :param content:
        :param exclude_list:
        :return:
        """
        for exclude_item in exclude_list:
            content = content.replace(exclude_item, "")
        return content


    def check_last_sentence_error(self, content):
        """
        不完全な文章などが含まれていないかチェック
        :param content:
        :return:
        """

        if content[-1:] != u"。" or content[-4:] == u"を参照。" or content[-3:] == u"を参照":
            return False
        else:
            return True

    def remove_last_sentence(self, content):
        """
        句点を元に最後の文を判断し削除
        :param content:
        :return:
        """

        content_array = content.split(u"。")
        new_content = ""

        sentence_limit = len(content_array) - 1
        sentence_count = 1

        for content_item in content_array:
            if sentence_count <= sentence_limit:
                new_content += content_item + u"。"
            else:
                break

            sentence_count += 1

        return new_content
