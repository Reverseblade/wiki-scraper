# -*- coding: utf-8 -*-

import sys

from WikiReader import WikiReader


def main():

    keyword = None
    # keyword = "プログラミング言語"

    for i, arg in enumerate(sys.argv):
        if i is 0:
            continue
        if i > 1:
            break
        keyword = arg

    reader = WikiReader(keyword)
    content = reader.get_content()
    print(content)


if __name__ == '__main__':
    main()
