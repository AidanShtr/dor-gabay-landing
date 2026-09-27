#!/usr/bin/env python3
"""
Build the standalone landing page.

    python3 build.py            -> index.html   (noindex, for the public draft)
    python3 build.py --index    -> index.html   (indexable, once the copy is real)
    python3 build.py --fetch    -> re-download everything into vendor/ first

src/index.html is the editable source: it loads GSAP, ScrollTrigger, Three.js, Lenis and
Heebo from CDNs, so it can be opened and edited directly. This script inlines all of them
into a single file that makes no network requests at all — that file is what gets shipped
and what GitHub Pages serves.
"""
import argparse, base64, io, os, re, sys, urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
VENDOR = os.path.join(ROOT, 'vendor')

LIBS = [
    ('gsap.min.js',          'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js'),
    ('ScrollTrigger.min.js', 'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js'),
    ('three.min.js',         'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js'),
    ('lenis.min.js',         'https://cdn.jsdelivr.net/npm/lenis@1.1.20/dist/lenis.min.js'),
    ('lenis.css',            'https://cdn.jsdelivr.net/npm/lenis@1.1.20/dist/lenis.css'),
]
# only the weights the page actually uses, and only the subsets Hebrew copy needs
FONT_CSS = 'https://fonts.googleapis.com/css2?family=Heebo:wght@400;700;800;900&display=swap'
UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0 Safari/537.36')   # asks Google Fonts for woff2


def get(url, binary=False):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    data = urllib.request.urlopen(req).read()
    return data if binary else data.decode('utf-8')


def fetch_vendor():
    os.makedirs(VENDOR, exist_ok=True)
    for name, url in LIBS:
        io.open(os.path.join(VENDOR, name), 'w', encoding='utf-8').write(get(url))
        print('  fetched', name)

    faces = []
    for block in re.findall(r'@font-face\s*\{[^}]*\}', get(FONT_CSS)):
        rng = re.search(r'unicode-range:\s*([^;]+);', block)
        if not rng:
            continue
        r = rng.group(1)
        if not ('U+0590-05FF' in r or r.strip().startswith('U+0000-00FF')):
            continue                                   # skip latin-ext / math / symbols
        url = re.search(r'url\((https://[^)]+\.woff2)\)', block).group(1)
        b64 = base64.b64encode(get(url, binary=True)).decode()
        block = re.sub(r'url\(https://[^)]+\.woff2\)',
                       'url(data:font/woff2;base64,' + b64 + ')', block)
        faces.append(re.sub(r'\s+', ' ', block).strip())
    io.open(os.path.join(VENDOR, 'heebo-inline.css'), 'w', encoding='utf-8').write('\n'.join(faces))
    print('  fetched heebo-inline.css (%d faces)' % len(faces))


def vendor(name):
    path = os.path.join(VENDOR, name)
    if not os.path.exists(path):
        sys.exit('missing vendor/%s — run: python3 build.py --fetch' % name)
    return io.open(path, encoding='utf-8').read()


def build(noindex=True):
    s = io.open(os.path.join(ROOT, 'src', 'index.html'), encoding='utf-8').read()

    if noindex:                                        # keep the draft out of Google
        s = s.replace('<meta name="viewport"',
                      '<meta name="robots" content="noindex, nofollow">\n<meta name="viewport"', 1)

    s = re.sub(r'<link rel="preconnect"[^>]*>\n', '', s)
    s = re.sub(r'<link href="https://fonts\.googleapis\.com/[^"]*" rel="stylesheet">\n', '', s)
    s = re.sub(r'<link rel="stylesheet" href="https://cdn\.jsdelivr\.net/[^"]*lenis\.css">\n', '', s)
    s = s.replace('<style>\n',
                  '<style>\n/* ---- Heebo: hebrew + latin, weights 400/700/800/900 ---- */\n'
                  + vendor('heebo-inline.css')
                  + '\n\n/* ---- lenis 1.1.20 ---- */\n' + vendor('lenis.css') + '\n\n', 1)

    for name, url in LIBS:
        if not name.endswith('.js'):
            continue
        tag = '<script src="%s"></script>' % url
        if tag not in s:
            sys.exit('source no longer loads %s — update LIBS in build.py' % name)
        code = vendor(name).replace('</script>', '<\\/script>')   # can't end the block early
        s = s.replace(tag, '<script>/* %s */\n%s\n</script>' % (name, code))

    left = re.findall(r'(?:src|href)="(https?://[^"]+)"', s)
    if left:
        sys.exit('page still loads something over the network: %s' % left)

    out = os.path.join(ROOT, 'index.html')
    io.open(out, 'w', encoding='utf-8').write(s)
    print('built index.html  %d KB  noindex=%s' % (len(s.encode()) / 1024, noindex))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--fetch', action='store_true', help='re-download libraries and fonts')
    ap.add_argument('--index', action='store_true', help='allow search engines (drop noindex)')
    a = ap.parse_args()
    if a.fetch:
        fetch_vendor()
    build(noindex=not a.index)
