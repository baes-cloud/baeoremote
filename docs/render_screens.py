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

def wordmark(d, cy, fill):
    # BÆO in Syne Bold + SOUND in Syne Regular, tracked 7, centred as one line
    fb, fr = font('Syne', 700, 22), font('Syne', 400, 22)
    w = lambda s, f: sum(f.getlength(c) for c in s) + 7 * (len(s) - 1)
    wb, wr = w('BÆO', fb), w('SOUND', fr); x0 = 240 - (wb + 7 + wr) / 2
    text(d, x0 + wb / 2, cy, 'BÆO', fb, fill, 7); text(d, x0 + wb + 7 + wr / 2, cy, 'SOUND', fr, fill, 7)

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

def nocturne(title, artist, clock='16:10', vol=None, room='CLUB', prog=0.42):
    base = Image.new('RGBA', (S, S), (5, 5, 6, 255))
    a = art().convert('RGBA'); a.putalpha(235)
    base = Image.alpha_composite(base, a); base = vignette(base)
    ov = Image.new('RGBA', (S, S)); d = ImageDraw.Draw(ov)
    v = 0.38 if vol is None else vol / 100
    arc(d, 462, 12, v, (233, 237, 242, 36)); arc(d, 462, 2, 1, (255, 255, 255, 31)); arc(d, 462, 3 if vol else 2, v, (242, 244, 247, 255))
    if prog is not None: arc(d, 432, 1, 1, (255, 255, 255, 15)); arc(d, 432, 1, prog, (233, 237, 242, 97))
    base = Image.alpha_composite(base, ov); d = ImageDraw.Draw(base)
    text(d, 240, 70 + 26, clock, font('Syne', 500, 40), (233, 237, 242, 191), 3)
    text(d, 240, 124 + 11, room, font('Syne', 700, 18), (233, 237, 242, 115), 4)
    if vol is not None:
        text(d, 240, 240, str(vol), font('Manrope', 300, 104), (246, 246, 244, 255), -2)
    else:
        ft = font('Syne', 400, 32); lines = wrap(title, ft, 350); lh = 38
        fa = font('Syne', 700, 18)
        h = len(lines) * lh + 6 + 22; y = 240 - h / 2 + lh / 2
        for ln in lines: text(d, 240, y, ln, ft, (246, 246, 244, 255)); y += lh
        text(d, 240, y - lh / 2 + 6 + 11, artist.upper(), fa, (233, 237, 242, 191), 4)
    wordmark(d, 240 + 122, (233, 237, 242, 179))
    return round_mask(base)

def lp_disc(d, cover, sc, opa, shadow):
    SS = 3; D = d * SS
    im = Image.new('RGBA', (D + 120, D + 120)); dr = ImageDraw.Draw(im); o = 60
    if shadow:
        sh = Image.new('RGBA', im.size); ImageDraw.Draw(sh).ellipse((o, o + 18, o + D, o + D + 18), fill=(0, 0, 0, 140))
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(40))); dr = ImageDraw.Draw(im)
    dr.ellipse((o, o, o + D, o + D), fill=(11, 11, 12, 255), outline=(52, 52, 58, 255), width=SS)
    ov = Image.new('RGBA', im.size); od = ImageDraw.Draw(ov); c = o + D / 2
    r = d - 10
    while r > d * 0.6:
        R = r * SS / 2; od.ellipse((c - R, c - R, c + R, c + R), outline=(255, 255, 255, 18), width=SS); r -= 12
    for a0 in (205, 25):
        R = (d - 8) * SS / 2; w = int(d * 0.16) * SS
        od.arc((c - R, c - R, c + R, c + R), a0 - 90 + 90, a0 + 40, fill=(255, 255, 255, 15), width=w)
    im = Image.alpha_composite(im, ov)
    cv = Image.open('/home/bae/baeoremote/tt/covers/' + cover).convert('RGBA'); n = int(100 * sc * SS)
    cv = cv.resize((n, n), Image.LANCZOS); im.alpha_composite(cv, (int(c - n / 2), int(c - n / 2)))
    h = max(4, int(d * 0.035)) // 2 * 2 * SS / 2; ImageDraw.Draw(im).ellipse((c - h, c - h, c + h, c + h), fill=(11, 11, 12, 255), outline=(85, 85, 92, 255), width=SS)
    im = im.resize((im.width // SS, im.height // SS), Image.LANCZOS)
    if opa < 1: im.putalpha(im.getchannel('A').point(lambda a: int(a * opa)))
    return im

def picker(room='CLUB', sel=0):
    covers = ['pdm_london.png', 'pdm_paradise.png', 'dfp_love.png', 'dfp_boiler.png', 'gayfm.png']
    base = Image.new('RGBA', (S, S), (5, 5, 6, 255))
    a = art().convert('RGBA'); a.putalpha(120)
    base = Image.alpha_composite(base, a); base = vignette(base)
    ov = Image.new('RGBA', (S, S)); d = ImageDraw.Draw(ov)
    arc(d, 462, 2, 1, (255, 255, 255, 31)); arc(d, 462, 2, 0.38, (242, 244, 247, 255))
    base = Image.alpha_composite(base, ov)
    for x, dd, sc, op, sh, i in ((-152, 108, 0.58, 0.45, False, (sel + 4) % 5), (152, 108, 0.58, 0.45, False, (sel + 1) % 5), (0, 176, 1.0, 1.0, True, sel)):
        im = lp_disc(dd, covers[i], sc, op, sh); base.alpha_composite(im, (240 + x - im.width // 2, 244 - im.height // 2))
    d = ImageDraw.Draw(base)
    text(d, 240, 70 + 26, '18:05', font('Syne', 500, 40), (233, 237, 242, 191), 3)
    text(d, 240, 124 + 11, 'PLAY IN ' + room, font('Syne', 700, 18), (233, 237, 242, 115), 4)
    wordmark(d, 240 + 122, (233, 237, 242, 179))
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
    wordmark(d, 240 + 120, (0xA5, 0x64, 0x44, 255))
    return round_mask(im)

out = '/home/bae/baeoremote/docs/screens/'
shots = [('now-playing.png', nocturne('See The Way', 'The Chainsmokers')),
         ('volume.png', nocturne('', '', vol=38)),
         ('grouped.png', nocturne('Lady (Hear Me Tonight)', 'Let go to stop all', room='CLUB + LIVING ROOM', prog=0.71)),
         ('bedroom.png', nocturne('Teardrop', 'Massive Attack', clock='22:41', room='BEDROOM', prog=0.18)),
         ('pick.png', picker()),
         ('pick-gayfm.png', picker('BEDROOM', 4)),
         ('night.png', night('See The Way', 'The Chainsmokers'))]
for n, im in shots: im.save(out + n)
sheet = Image.new('RGBA', (len(shots) * 540 + 20, 560), (246, 245, 241, 255))
for i, (n, im) in enumerate(shots): sheet.alpha_composite(im, (20 + i * 540, 20))
sheet.save(out + 'overview.png')
print('done')
