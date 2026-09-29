"""Render BæoRemote screens from the firmware's layout values (fonts, sizes,
positions and colours match tt/assemble.py / tt/body.yaml / tt/tail.yaml).
Renders, not captures: the ESP has no screen-grab path."""
import math, random
from PIL import Image, ImageDraw, ImageFilter, ImageFont

F = '/home/bae/rotary-build/.esphome/font/'
def font(fam, w, s): return ImageFont.truetype(f'{F}{fam}@{w}@False@v1.ttf', s)
S = 480

def text(d, cx, cy, s, f, fill, track=0, anchor_mid=True):
    # draw on a transparent layer and composite, so text opacity blends like LVGL's
    base = d._image; ov = Image.new('RGBA', base.size); od = ImageDraw.Draw(ov)
    w = sum(f.getlength(c) for c in s) + track * (len(s) - 1)
    x = cx - w / 2
    for c in s:
        od.text((x, cy), c, font=f, fill=fill, anchor='lm')
        x += f.getlength(c) + track
    base.alpha_composite(ov)

def blend(d, fn):
    base = d._image; ov = Image.new('RGBA', base.size); fn(ImageDraw.Draw(ov)); base.alpha_composite(ov)

def wrap(s, f, width):
    out, line = [], ''
    for word in s.split():
        t = (line + ' ' + word).strip()
        if f.getlength(t) <= width: line = t
        else: out.append(line); line = word
    out.append(line); return out

def art():
    random.seed(7)
    im = Image.new('RGB', (24, 24))
    px = im.load()
    blobs = [(random.uniform(0, 24), random.uniform(0, 24), random.choice([(46, 196, 182), (231, 29, 54), (255, 159, 28), (90, 60, 200), (20, 90, 140)])) for _ in range(7)]
    for y in range(24):
        for x in range(24):
            acc = [10, 12, 20]; tw = 0.2
            for bx, by, c in blobs:
                w = math.exp(-((x - bx) ** 2 + (y - by) ** 2) / 30)
                acc = [a + ci * w for a, ci in zip(acc, c)]; tw += w
            px[x, y] = tuple(int(min(255, a / tw * 1.1)) for a in acc)
    return im.resize((S, S), Image.BICUBIC).filter(ImageFilter.GaussianBlur(10))

def vignette(base):
    ov = Image.new('RGBA', (S, S)); p = ov.load()
    for y in range(S):
        for x in range(S):
            r = math.hypot(x - 240, y - 240)
            if r >= 222:
                v = max(3, 7 + int(max(0, 224 - r) * 3) + int(-(y - 240) / r * 5)); p[x, y] = (v, v, v + 1, 255)
            else:
                q = r / 222; a = 0.46 + 0.44 * q * q
                rx, ry = (x - 150) / 200, (y - 20) / 120; g = 1 - (rx * rx + ry * ry)
                if g > 0:
                    gl = g * 0.08; w = int(255 * gl / (a + gl)); p[x, y] = (w, w, w, int((a + gl) * 255))
                else: p[x, y] = (5, 5, 6, int(a * 255))
    return Image.alpha_composite(base, ov)

def arc(d, dia, width, frac, color):
    b = (240 - dia / 2, 240 - dia / 2, 240 + dia / 2, 240 + dia / 2)
    d.arc(b, -90, -90 + 360 * frac, fill=color, width=width)

def round_mask(im):
    out = Image.new('RGBA', (S + 40, S + 40), (0, 0, 0, 0))
    m = Image.new('L', (S * 4, S * 4)); ImageDraw.Draw(m).ellipse((0, 0, S * 4 - 1, S * 4 - 1), fill=255)
    m = m.resize((S, S), Image.LANCZOS)
    ring = ImageDraw.Draw(out); ring.ellipse((2, 2, S + 37, S + 37), fill=(18, 18, 20, 255))
    out.paste(im.convert('RGB'), (20, 20), m)
    return out

def nocturne(title, artist, clock='16:10', vol=None):
    base = Image.new('RGBA', (S, S), (5, 5, 6, 255))
    a = art().convert('RGBA'); a.putalpha(235)
    base = Image.alpha_composite(base, a); base = vignette(base)
    ov = Image.new('RGBA', (S, S)); d = ImageDraw.Draw(ov)
    v = 0.38 if vol is None else vol / 100
    arc(d, 462, 12, v, (233, 237, 242, 36)); arc(d, 462, 2, 1, (255, 255, 255, 31)); arc(d, 462, 3 if vol else 2, v, (242, 244, 247, 255))
    base = Image.alpha_composite(base, ov); d = ImageDraw.Draw(base)
    text(d, 240, 70 + 26, clock, font('Syne', 500, 40), (233, 237, 242, 191), 3)
    if vol is not None:
        text(d, 240, 240, str(vol), font('Manrope', 300, 104), (246, 246, 244, 255), -2)
    else:
        ft = font('Syne', 400, 32); lines = wrap(title, ft, 350); lh = 38
        fa = font('Syne', 700, 18)
        h = len(lines) * lh + 6 + 22; y = 240 - h / 2 + lh / 2
        for ln in lines: text(d, 240, y, ln, ft, (246, 246, 244, 255)); y += lh
        text(d, 240, y - lh / 2 + 6 + 11, artist.upper(), fa, (233, 237, 242, 191), 4)
    text(d, 240, 240 + 122, 'BÆOREMOTE', font('Syne', 700, 22), (233, 237, 242, 179), 7)
    return round_mask(base)

def night(title, artist, clock='02:14'):
    im = Image.new('RGBA', (S, S)); p = im.load()
    n0, n1, n2 = (0x0E, 0x0A, 0x08), (0x07, 0x05, 0x04), (0x03, 0x02, 0x02)
    for y in range(S):
        for x in range(S):
            r = math.hypot(x - 240, y - 240)
            if r >= 215:
                t = (r - 215) / 25; lit = -((x - 240) * 0.5 + (y - 240) * 0.85) / r
                c = [a + (b - a) * t + lit * 5 for a, b in zip((0x2A, 0x2A, 0x2E), (0x0B, 0x0B, 0x0C))]
                if r < 216.5: c = [v * 0.55 for v in c]
            else:
                t = min(1, r / 304)
                c = [a + (b - a) * (t / 0.6) for a, b in zip(n0, n1)] if t < 0.6 else [a + (b - a) * ((t - 0.6) / 0.4) for a, b in zip(n1, n2)]
            p[x, y] = tuple(int(max(0, min(255, v))) for v in c) + (255,)
    d = ImageDraw.Draw(im)
    text(d, 240, 240 - 112, title, font('Manrope', 400, 20), (0xA5, 0x64, 0x44, 255))
    text(d, 240, 240 - 86, artist.upper(), font('Manrope', 700, 14), (0xA5, 0x64, 0x44, 255), 3)
    text(d, 240, 240, clock, font('Manrope', 300, 104), (0xB8, 0x70, 0x4A, 255), -2)
    text(d, 240, 240 + 120, 'BÆOREMOTE', font('Syne', 700, 22), (0xA5, 0x64, 0x44, 255), 7)
    return round_mask(im)

def playlists():
    im = Image.new('RGBA', (S, S)); d = ImageDraw.Draw(im)
    for y in range(S):
        t = y / S; c = tuple(int(a + (b - a) * t) for a, b in zip((0x2A, 0x2B, 0x2F), (0x0B, 0x0B, 0x0D)))
        d.line([(0, y), (S, y)], fill=c + (255,))
    text(d, 240, 240 - 150, 'PLAYLISTS', font('Syne', 700, 18), (0xD6, 0xD8, 0xDC, 255), 5)
    blend(d, lambda o: o.ellipse((212, 16, 268, 72), fill=(0x1B, 0x1C, 0x1F, 255), outline=(0xC9, 0xCB, 0xCF, 77)))
    d.line([(233, 37), (247, 51)], fill=(0xD6, 0xD8, 0xDC), width=3); d.line([(247, 37), (233, 51)], fill=(0xD6, 0xD8, 0xDC), width=3)
    disc = Image.open('/home/bae/baeoremote/tt/pl_disc_140.png').convert('RGBA')
    def icon(n, h): i = Image.open(f'/home/bae/baeoremote/{n}').convert('RGBA'); i.thumbnail((h * 2, h)); return i
    for x, n, sc, op in ((-150, 'icon_alb_w.png', 0.72, 0.4), (150, 'icon_house_w.png', 0.72, 0.4), (0, 'icon_disco_w.png', 1.0, 1.0)):
        dz = disc.resize((int(140 * sc), int(140 * sc)), Image.LANCZOS); ic = icon(n, int(44 * sc))
        layer = Image.new('RGBA', (S, S))
        layer.alpha_composite(dz, (240 + x - dz.width // 2, 224 - dz.height // 2))
        layer.alpha_composite(ic, (240 + x - ic.width // 2, 224 - ic.height // 2))
        if op < 1: layer.putalpha(layer.getchannel('A').point(lambda a: int(a * op)))
        im = Image.alpha_composite(im, layer)
    d = ImageDraw.Draw(im)
    text(d, 240, 240 + 84, 'Disco', font('Syne', 400, 40), (0xF2, 0xF2, 0xF0, 255))
    for i in range(7):
        x = 240 - 48 + 16 * i; blend(d, lambda o, x=x, i=i: o.ellipse((x - 4, 240 + 120, x + 4, 240 + 128), fill=(0xD6, 0xD8, 0xDC, 255 if i == 0 else 51)))
    blend(d, lambda o: o.rounded_rectangle((125, 240 + 156, 355, 240 + 196), radius=20, fill=(0x1B, 0x1C, 0x1F, 255), outline=(0xC9, 0xCB, 0xCF, 77)))
    text(d, 240, 240 + 176, 'UNGROUP ALL ROOMS', font('Syne', 700, 18), (0xD6, 0xD8, 0xDC, 255), 2)
    return round_mask(im)

def albums():
    im = playlists_bg(); d = ImageDraw.Draw(im)
    text(d, 240, 240 - 150, 'ALBUMS', font('Syne', 700, 18), (0xD6, 0xD8, 0xDC, 255), 5)
    blend(d, lambda o: o.ellipse((212, 16, 268, 72), fill=(0x1B, 0x1C, 0x1F, 255), outline=(0xC9, 0xCB, 0xCF, 77)))
    d.line([(244, 36), (236, 44)], fill=(0xD6, 0xD8, 0xDC), width=3); d.line([(236, 44), (244, 52)], fill=(0xD6, 0xD8, 0xDC), width=3)
    f20 = font('Manrope', 400, 20)
    for y, s, o in ((-128, 'Ministry of Sound: Sessions Four', 56), (-88, 'Ministry of Sound: Sessions One', 122), (88, 'Ministry of Sound: Sessions Seven', 122), (128, 'Ministry of Sound: Sessions Three', 56)):
        text(d, 240, 240 + y, s, f20, (0xF2, 0xF2, 0xF0, o))
    ft = font('Syne', 400, 32)
    for i, ln in enumerate(wrap('Ministry of Sound: Sessions Six', ft, 360)): text(d, 240, 240 - 30 + i * 38, ln, ft, (0xF2, 0xF2, 0xF0, 255))
    text(d, 240, 240 + 36, 'John Course', f20, (0xD6, 0xD8, 0xDC, 179))
    text(d, 240, 240 + 168, '5 / 39', font('Syne', 600, 13), (0xD6, 0xD8, 0xDC, 140), 2)
    return round_mask(im)

def playlists_bg():
    im = Image.new('RGBA', (S, S)); d = ImageDraw.Draw(im)
    for y in range(S):
        t = y / S; d.line([(0, y), (S, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip((0x2A, 0x2B, 0x2F), (0x0B, 0x0B, 0x0D))) + (255,))
    return im

out = '/home/bae/baeoremote/docs/screens/'
shots = [('now-playing.png', nocturne('See The Way', 'The Chainsmokers')),
         ('volume.png', nocturne('', '', vol=38)),
         ('night.png', night('See The Way', 'The Chainsmokers')),
         ('playlists.png', playlists()),
         ('albums.png', albums())]
for n, im in shots: im.save(out + n)
sheet = Image.new('RGBA', (len(shots) * 540 + 20, 560), (246, 245, 241, 255))
for i, (n, im) in enumerate(shots): sheet.alpha_composite(im, (20 + i * 540, 20))
sheet.save(out + 'overview.png')
print('done')
