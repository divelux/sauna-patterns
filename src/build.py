#!/usr/bin/env python3
"""Builds the Sauna Patterns set: seamless tiles as SVG (240 x 240 units) and PNG (1024 px), patterns.css, demo.html, preview.png.

Seamless by construction: every element is drawn at its position and again shifted by one tile in each direction
wherever it crosses an edge (see wrap()). check_seams() then verifies it on the rendered pixels.

Needs: pip install resvg-py fonttools pillow numpy
License: artwork CC BY 4.0, code MIT - DIVELUX, https://diveluxsaunahat.com
"""
import io
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gfxlib as g

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = g.PAL
S = 240


def f(v):
    return ('%.1f' % v).rstrip('0').rstrip('.')


def wrap(items):
    """items: (markup, cx, cy, radius). Returns markup with the copies needed so the tile repeats without seams."""
    out = []
    for m, cx, cy, r in items:
        for dx in (-S, 0, S):
            for dy in (-S, 0, S):
                x, y = cx + dx, cy + dy
                if x + r < 0 or x - r > S or y + r < 0 or y - r > S:
                    continue
                out.append(m if (dx, dy) == (0, 0) else f'<g transform="translate({dx} {dy})">{m}</g>')
    return ''.join(out)


def tdist(a, b):
    dx = abs(a[0] - b[0]); dy = abs(a[1] - b[1])
    dx = min(dx, S - dx); dy = min(dy, S - dy)
    return math.hypot(dx, dy)


def scatter(rnd, n_try, rmin, rmax, gap):
    """Random circles on the torus that do not touch."""
    pts = []
    for _ in range(n_try):
        c = (rnd.uniform(0, S), rnd.uniform(0, S), rnd.uniform(rmin, rmax))
        if all(tdist(c, q) > c[2] + q[2] + gap for q in pts):
            pts.append(c)
    return pts


def stroke(d, c, w, extra=''):
    return f'<path d="{d}" fill="none" stroke="{c}" stroke-width="{f(w)}" stroke-linecap="round" stroke-linejoin="round"{extra}/>'


def wisp_d(x, y, h, amp, n=2):
    seg = h / n
    d = f'M{f(x)} {f(y + h / 2)}'
    for i in range(n):
        y0 = y + h / 2 - i * seg
        d += f' C{f(x + amp)} {f(y0 - seg * .33)} {f(x - amp)} {f(y0 - seg * .66)} {f(x)} {f(y0 - seg)}'
    return d


# line icons from the Sauna & Banya Icon Set (24 px grid)
ICON = {
    'sauna-hat': 'M5.5 16.5c1.2-3.2.8-11 6.5-11s5.3 7.8 6.5 11M4.5 16.5h15a1.5 1.5 0 0 1 0 3h-15a1.5 1.5 0 0 1 0-3zM12 5.5c-1.6-.8-1.7-2.8-.5-3 1.2-.2 1.7 1.5.5 3zM12 5.5c1.3 3 1.8 6.5 1.8 11',
    'bucket-hat': 'M7.5 13.2c.2-4.3 1.2-7.7 4.5-7.700s4.3 3.4 4.5 7.700M2.5 17.2c2-2.6 5-4 9.5-4s7.5 1.4 9.5 4c-2.6 1.4-6 2.1-9.5 2.100s-6.9-.700-9.5-2.100z',
    'sauna-stove': 'M5.5 11.5h13a1 1 0 0 1 1 1V18a1 1 0 0 1-1 1h-13a1 1 0 0 1-1-1v-5.500a1 1 0 0 1 1-1zM7 19v2M17 19v2M5.5 11.500a2.3 2.3 0 0 1 4.3-1.1 2.6 2.6 0 0 1 4.6-.200 2.3 2.3 0 0 1 4.1 1.300M8.7 8.200a2.2 2.2 0 0 1 3.8-1.1 2.1 2.1 0 0 1 3.2 1.300M8 14.300h8M8 16.500h8',
    'bucket-ladle': 'M4 10h12l-1.2 10.500H5.200zM4.4 13.500h11.200M4.8 17.200h10.400M12.5 10 20 3.500M7 10c.300-1.6 1.2-2.5 2.5-2.5',
    'birch-whisk': 'M3 21.500l5.2-5.200M6.6 15.100l2.8 2.800M8.2 16.300c-2.3-3.2-1.5-6.3.800-7.3.200-3 3-4.7 5.5-3.7 2.5-1.5 5.3.500 4.8 3.2 2 2 1 5.2-1.5 5.7-1 2.5-4 3-5.5 1.5-1.5.800-3 .700-4.1.600zM9.5 15 16 8.500M12.7 11.800V8.500M14.5 10H18',
    'thermometer': 'M14 14.800V5a2 2 0 0 0-4 0v9.800a4 4 0 1 0 4 0zM12 9v9.300M17 6h2.500M17 9.500h2.500M17 13h2.5',
    'sand-timer': 'M6 3h12M6 21h12M7.5 3v3c0 2.5 4.5 3.5 4.5 6s-4.5 3.5-4.5 6v3M16.5 3v3c0 2.5-4.5 3.5-4.5 6s4.5 3.5 4.5 6v3M10 18.500h4M12 14.500v1',
    'steam': 'M7 21c-2-2.5 2-4.5 0-7s2-4.5 0-7M12 18c-2-2.5 2-4.5 0-7s2-4.5 0-7M17 21c-2-2.5 2-4.5 0-7s2-4.5 0-7',
}


def icon(name, cx, cy, size, color, rot=0, sw=1.5):
    k = size / 24
    return (f'<g transform="translate({f(cx)} {f(cy)}) rotate({f(rot)}) scale({f(k)}) translate(-12 -12)">'
            + stroke(ICON[name], color, sw) + '</g>')


# ---------------------------------------------------------------- patterns: return (background color, [items])
def steam():
    items = []
    for i in range(4):
        for j in range(2):
            x = 30 + 60 * i
            y = 60 + 120 * j + (60 if i % 2 else 0)
            amp = 9 if (i + j) % 2 else -9
            items.append((stroke(wisp_d(x, y % S, 76, amp), P['white'], 7), x, y % S, 46))
            x2, y2 = x + 30, (y + 60) % S
            items.append((stroke(wisp_d(x2, y2, 40, -amp * .7), P['line'], 5), x2, y2, 28))
    return SPOT, items


def stones():
    rnd = random.Random(11)
    cols = [P['stone1'], P['stone2'], P['stone3'], P['felt2'], P['stone1'], P['stone2']]
    items = []
    for k, (x, y, r) in enumerate(scatter(rnd, 3000, 13, 27, 5)):
        rot = rnd.uniform(-40, 40)
        m = f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="{f(r)}" ry="{f(r * rnd.uniform(.68, .86))}" fill="{cols[k % len(cols)]}" transform="rotate({f(rot)} {f(x)} {f(y)})"/>'
        items.append((m, x, y, r + 1))
    return P['ink'], items


def planks():
    rnd = random.Random(5)
    shades = ['#ecd6b2', '#e7cfa6', '#efdcbc', '#e3c898', '#ecd6b2', '#e9d2ac']
    items = []
    w = S / 6
    for i in range(6):
        x = i * w
        items.append((f'<rect x="{f(x)}" y="-1" width="{f(w)}" height="{S + 2}" fill="{shades[i]}"/>', x + w / 2, S / 2, 0))
        # grain: gentle vertical lines that close on themselves across the tile edge
        for gx in (x + 9, x + 21, x + 31):
            a = rnd.uniform(1, 3) * rnd.choice((-1, 1))
            ph = rnd.uniform(0, S)
            pts = ' '.join(f'{f(gx + a * math.sin(2 * math.pi * (yy + ph) / S))} {yy}' for yy in range(-12, S + 13, 12))
            items.append((stroke('M' + pts, P['wood2'], 1.4, ' opacity=".8"'), gx, S / 2, 0))
        # board end joint and a knot
        jy = (37 + i * 97) % S
        items.append((stroke(f'M{f(x)} {jy}h{f(w)}', P['wood3'], 1.6), x + w / 2, jy, w))
        if i % 2 == 0:
            ky = (jy + 110) % S
            items.append((f'<ellipse cx="{f(x + w / 2 + 3)}" cy="{ky}" rx="4" ry="6.5" fill="{P["wood3"]}"/>'
                          f'<ellipse cx="{f(x + w / 2 + 3)}" cy="{ky}" rx="8" ry="12" fill="none" stroke="{P["wood2"]}" stroke-width="1.4"/>', x + w / 2, ky, 14))
    for i in range(6):
        items.append((stroke(f'M{f(i * w)} -2V{S + 2}', P['wood3'], 1.6), i * w, S / 2, 1))
    return '#ecd6b2', items


def hats():
    items = []
    spots = [(60, 60, 'sauna-hat', -10), (180, 60, 'bucket-hat', 8), (0, 180, 'bucket-hat', -8), (120, 180, 'sauna-hat', 10)]
    for x, y, name, rot in spots:
        items.append((icon(name, x, y, 62, P['ink'], rot), x, y, 46))
    for x, y in ((120, 60), (0, 60), (60, 180), (180, 180)):
        items.append((f'<circle cx="{x}" cy="{y}" r="3.2" fill="{P["ember"]}"/>', x, y, 4))
    for x, y in ((60, 120), (180, 120), (0, 0), (120, 0)):
        items.append((stroke(wisp_d(x, y, 30, 5), P['felt2'], 3), x, y, 18))
    return P['paper'], items


def leaves():
    rnd = random.Random(23)
    items = []
    greens = [(P['leaf'], P['leaf2']), (P['leaf2'], '#3f5a35'), ('#8aa871', P['leaf']), (P['leaf'], P['leaf2'])]
    cells = [(i, j) for j in range(6) for i in range(6)]
    for k, (i, j) in enumerate(cells):                      # jittered grid: even density, no rows or columns
        x = (20 + 40 * i + (20 if j % 2 else 0) + rnd.uniform(-8, 8)) % S
        y = (20 + 40 * j + rnd.uniform(-8, 8)) % S
        r = rnd.uniform(15, 19)
        rot = rnd.uniform(0, 360)
        c, v = greens[rnd.randrange(4)]
        k2 = r / 34
        m = (f'<g transform="translate({f(x)} {f(y)}) rotate({f(rot)}) scale({f(k2)})">'
             f'<path d="M0 -34C20 -22 22 10 0 34C-22 10 -20 -22 0 -34z" fill="{c}"/>'
             f'<path d="M0 -22V34M0 -6l9-9M0 8l10-10M0 -4l-9-9M0 10l-10-10" fill="none" stroke="{v}" stroke-width="2.2" stroke-linecap="round"/></g>')
        items.append((m, x, y, r + 1))
    return P['paper'], items


def drops():
    items = []
    for i in range(4):
        for j in range(4):
            x = 30 + 60 * i
            y = 36 + 60 * j + (30 if i % 2 else 0)
            big = (i + 2 * j) % 4 == 0
            s = 1.25 if big else .8
            c = P['water2'] if big else P['water']
            m = (f'<g transform="translate({x} {y % S}) scale({s})"><path d="M0 -15c9 11 14 18 14 25a14 14 0 0 1-28 0c0-7 5-14 14-25z" fill="{c}"/>'
                 f'<path d="M-7 10a7 7 0 0 0 5 6.5" fill="none" stroke="#ffffff" stroke-width="2.4" stroke-linecap="round" opacity=".85"/></g>')
            items.append((m, x, y % S, 30))
    return SPOT, items


def snow():
    rnd = random.Random(4)
    items = []
    for k, (x, y, r) in enumerate(scatter(rnd, 3000, 9, 24, 7)):
        arms = []
        for a6 in range(6):
            a = math.radians(60 * a6 + (k * 17) % 60)
            tip = (r * math.cos(a), r * math.sin(a))
            mid = (r * .6 * math.cos(a), r * .6 * math.sin(a))
            br = r * .3
            l = (mid[0] + br * math.cos(a - math.radians(50)), mid[1] + br * math.sin(a - math.radians(50)))
            rr = (mid[0] + br * math.cos(a + math.radians(50)), mid[1] + br * math.sin(a + math.radians(50)))
            arms.append(f'M0 0 {f(tip[0])} {f(tip[1])}' + (f'M{f(l[0])} {f(l[1])} {f(mid[0])} {f(mid[1])} {f(rr[0])} {f(rr[1])}' if r > 13 else ''))
        c = P['paper'] if k % 3 == 0 else P['water']
        m = f'<g transform="translate({f(x)} {f(y)})">' + stroke(''.join(arms), c, 2.2 if r > 13 else 1.8) + '</g>'
        items.append((m, x, y, r + 2))
    return '#22303a', items


def kit():
    names = ['sauna-hat', 'sauna-stove', 'bucket-ladle', 'birch-whisk', 'thermometer', 'sand-timer', 'steam', 'bucket-hat']
    items = []
    for j in range(4):
        for i in range(4):
            x = 30 + 60 * i
            y = 30 + 60 * j
            name = names[(i + j * 3) % 8]
            items.append((icon(name, x, y, 30, P['wood2']), x, y, 22))
            items.append((f'<circle cx="{(x + 30) % S}" cy="{(y + 30) % S}" r="1.8" fill="{P["wood4"]}"/>', (x + 30) % S, (y + 30) % S, 3))
    return P['night'], items


SPOT = P['paper2']
PATTERNS = [
    ('steam', 'Steam', steam, 'white steam wisps on warm paper'),
    ('stones', 'Sauna stones', stones, 'stove stones on dark ink'),
    ('planks', 'Wood planks', planks, 'light sauna boards with grain and knots'),
    ('hats', 'Sauna hats', hats, 'bell and bucket hats with ember dots'),
    ('leaves', 'Birch leaves', leaves, 'whisk leaves in two greens'),
    ('drops', 'Water drops', drops, 'water drops on warm paper'),
    ('snow', 'Snowflakes', snow, 'cold plunge snowflakes on a deep blue-grey'),
    ('kit', 'Sauna kit', kit, 'line icons on a dark wood-brown'),
]


def tile_svg(title, bg, items, n=1):
    """n=1: the tile itself. n>1: an n x n sheet built with <pattern>, used for the seam test and previews."""
    body = f'<rect width="{S}" height="{S}" fill="{bg}"/>' + wrap(items)
    if n == 1:
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{S}" height="{S}" viewBox="0 0 {S} {S}">'
                f'<title>{title}</title><clipPath id="t"><rect width="{S}" height="{S}"/></clipPath><g clip-path="url(#t)">{body}</g></svg>\n')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{S * n}" height="{S * n}" viewBox="0 0 {S * n} {S * n}">'
            f'<defs><pattern id="p" width="{S}" height="{S}" patternUnits="userSpaceOnUse">{body}</pattern></defs>'
            f'<rect width="{S * n}" height="{S * n}" fill="url(#p)"/></svg>')


TOUCH_OK = 4   # of 1024 pixels per edge


def check_seams(name, png_bytes):
    """Edge test on the rendered pixels. A shape that is cut off at a tile edge shows up as a hard jump between the
    last and the first pixel column (or row) at a place where the picture is flat on both sides of the seam.
    Counts such pixels. A seamless tile has none, or a handful where a round shape only touches the edge (TOUCH_OK)"""
    import numpy as np
    from PIL import Image
    a = np.asarray(Image.open(io.BytesIO(png_bytes)).convert('RGB')).astype(float)
    res = {}
    for axis, label in ((1, 'x'), (0, 'y')):
        b = a if axis == 1 else a.transpose(1, 0, 2)
        seam = np.abs(b[:, 0] - b[:, -1]).max(axis=1)            # jump across the wrap-around seam
        flat = np.maximum(np.abs(b[:, 1] - b[:, 0]).max(axis=1), np.abs(b[:, -1] - b[:, -2]).max(axis=1))
        cut = int(((seam > 40) & (flat < 12)).sum())
        res[label] = (cut, float(seam.mean()))
    ok = all(cut <= TOUCH_OK for cut, _ in res.values())
    print(f'  seam {name:8} hard-cut pixels  x: {res["x"][0]:4d}  y: {res["y"][0]:4d}   mean jump x {res["x"][1]:.2f}  y {res["y"][1]:.2f}   {"OK" if ok else "FAIL"}')
    return ok


def main():
    for d in ('svg', 'png'):
        os.makedirs(os.path.join(ROOT, d), exist_ok=True)
    css = ['/*! Sauna Patterns | artwork CC BY 4.0, CSS MIT | DIVELUX - https://diveluxsaunahat.com */',
           '/* Usage: <div class="sauna-pattern sauna-pattern-steam"></div>. Change the size with --sauna-tile. */',
           '.sauna-pattern { background-repeat: repeat; background-size: var(--sauna-tile, 240px) var(--sauna-tile, 240px); }']
    cells, all_ok = [], True
    for name, title, fn, note in PATTERNS:
        bg, items = fn()
        svg = tile_svg(title, bg, items)
        open(os.path.join(ROOT, 'svg', name + '.svg'), 'w', encoding='utf-8').write(svg)
        data = g.render(svg, os.path.join(ROOT, 'png', name + '-1024.png'), width=1024)
        all_ok &= check_seams(name, data)
        css.append(f'.sauna-pattern-{name} {{ background-color: {bg}; background-image: url("svg/{name}.svg"); }}')
        sheet = tile_svg(title, bg, items, 3)
        inner = sheet[sheet.index('<defs>'):sheet.rindex('</svg>')].replace('id="p"', f'id="p-{name}"').replace('url(#p)', f'url(#p-{name})')
        cells.append((f'<svg x="16" y="16" width="336" height="336" viewBox="0 0 {S * 3} {S * 3}">{inner}</svg>', f'{name} — {note}'))
    open(os.path.join(ROOT, 'patterns.css'), 'w').write('\n'.join(css) + '\n')
    sheet = g.contact_sheet(cells, 4, 368, 404, 'Sauna Patterns', f'{len(cells)} seamless tiles · SVG + PNG 1024 px + CSS · each shown tiled 3 x 3 · free under CC BY 4.0',
                            grid_lines=False, label_size=13)
    g.render(sheet, os.path.join(ROOT, 'preview.png'))
    demo = ['<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">',
            '<title>Sauna Patterns — demo</title><link rel="stylesheet" href="patterns.css">',
            '<style>body{margin:0;background:#f6f3ee;color:#1b1512;font:16px/1.5 Inter,system-ui,sans-serif}main{max-width:1120px;margin:0 auto;padding:40px 24px}',
            'h1{font-size:36px;line-height:1.1;margin:0 0 8px}p{color:#6f655c;margin:0 0 24px}.g{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:20px}',
            '.sw{height:300px;border-radius:6px}figure{margin:0}figcaption{font-size:14px;color:#6f655c;margin-top:6px}code{font-size:13px}a{color:inherit}</style></head><body><main>',
            '<h1>Sauna Patterns</h1><p>Seamless tiles as CSS backgrounds. Each swatch is one class.</p><div class="g">']
    for name, title, fn, note in PATTERNS:
        demo.append(f'<figure><div class="sw sauna-pattern sauna-pattern-{name}" style="--sauna-tile:160px"></div><figcaption>{title} — <code>sauna-pattern-{name}</code></figcaption></figure>')
    demo.append('</div><p style="margin-top:32px">Patterns by DIVELUX, makers of handmade wool sauna hats — <a href="https://diveluxsaunahat.com">diveluxsaunahat.com</a>. CC BY 4.0.</p></main></body></html>')
    open(os.path.join(ROOT, 'demo.html'), 'w', encoding='utf-8').write('\n'.join(demo) + '\n')
    print(len(cells), 'patterns', 'ALL SEAMS OK' if all_ok else 'SEAM PROBLEMS')
    return 0 if all_ok else 1


if __name__ == '__main__':
    sys.exit(main())
