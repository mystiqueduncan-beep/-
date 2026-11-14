"""Keep Google Fonts requests limited to the characters used by the resume homepages.

Run without arguments after editing the page, or use --check in CI.
"""
import argparse
import re
import string
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, unquote


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
    # Japanese editorial sublabels use the page's system-Japanese font stack,
    # not the Google Fonts Chinese subset. Keep its downloaded glyph set lean.
    font_source = re.sub(
        r'<(?:span|p) class="(?:sec-title-jp|mobile-section-jp)" lang="ja">[^<>]*</(?:span|p)>',
        '', source
    )
    parser.feed(font_source)
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
    for name in ('mobile.html', 'index.html'):
        page = Path(__file__).resolve().parents[1] / name
        original = page.read_text(encoding='utf-8')
        updated = subset_page(original)
        if options.check:
            # Deleting approved sections can leave harmless extra characters in
            # the existing Google Fonts URL. Require complete glyph coverage
            # without forcing a URL rewrite solely to remove unused glyphs.
            pattern = r'&text=([^"<>]*)'
            actual = re.findall(pattern, original)
            required = re.findall(pattern, updated)
            if len(actual) != 2 or len(required) != 2:
                raise SystemExit(name + ': two font subset links required')
            for have, need in zip(actual, required):
                missing = set(unquote(need)) - set(unquote(have))
                if missing:
                    raise SystemExit(name + ': missing font glyphs ' + repr(''.join(sorted(missing))))
            print(f'{name}: font subset covers page text and accessibility labels.')
        else:
            page.write_text(updated, encoding='utf-8')
