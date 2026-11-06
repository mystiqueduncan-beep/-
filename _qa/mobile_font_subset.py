"""Keep Google Fonts requests limited to the characters used by mobile.html.

Run without arguments after editing the page, or use --check in CI.
"""
import argparse
import re
import string
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote


class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hidden = 0
        self.parts = [string.printable]

    def handle_starttag(self, tag, attrs):
        if tag in ('style', 'script'):
            self.hidden += 1
        for name, value in attrs:
            if name in ('alt', 'title', 'aria-label') and value:
                self.parts.append(value)

    def handle_endtag(self, tag):
        if tag in ('style', 'script'):
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def subset_page(source):
    parser = VisibleText()
    parser.feed(source)
    parser.parts.extend(re.findall(r'content:\s*[\"\']([^\"\']*)[\"\']', source))
    characters = ''.join(sorted(set(''.join(parser.parts))))
    characters = ''.join(c for c in characters if c.isprintable())
    pattern = r'(https://fonts\.googleapis\.com/css2\?[^\"<>]*?&display=swap)(?:&text=[^\"<>]*)?'
    updated, count = re.subn(pattern, lambda m: m[1] + '&text=' + quote(characters, safe=''), source)
    if count != 2:
        raise ValueError('Expected stylesheet and no-JavaScript font links')
    return updated


if __name__ == '__main__':
    arguments = argparse.ArgumentParser()
    arguments.add_argument('--check', action='store_true')
    options = arguments.parse_args()
    page = Path(__file__).resolve().parents[1] / 'mobile.html'
    original = page.read_text(encoding='utf-8')
    updated = subset_page(original)
    if options.check:
        if updated != original:
            raise SystemExit('Run python3 _qa/mobile_font_subset.py to include updated text')
        print('Mobile font subset covers page text and accessibility labels.')
    else:
        page.write_text(updated, encoding='utf-8')
