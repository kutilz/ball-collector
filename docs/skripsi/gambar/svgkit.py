"""Helper kecil untuk menggambar diagram SVG bergaya seragam (skripsi)."""
import html
import re

FONT = "Liberation Sans, Arial, Helvetica, sans-serif"
INK = "#0b0b0b"
INK2 = "#52514e"
LINE = "#3d3d3a"
MUTED = "#8a8984"
SURF = "#ffffff"
NEUTRAL_FILL = "#f0efec"

# Slot kategorikal 1-3 (tervalidasi all-pairs, mode terang) + tint isi
BLUE, BLUE_T = "#2a78d6", "#e6f0fb"      # laptop / ground station
ORANGE, ORANGE_T = "#eb6834", "#fdece4"  # ESP32-CAM
AQUA, AQUA_T = "#1baf7a", "#e3f5ee"      # Arduino Uno
RED = "#e34948"                           # kutub negatif (divergen)

FS = 20        # ukuran huruf isi
FS_S = 17      # label panah / catatan


def esc(s):
    return html.escape(s, quote=False)


_TOKEN = re.compile(r"(_\{[^}]*\}|\^\{[^}]*\}|\*[^*]+\*)")


def rich(s, size):
    """Markup: _{sub}, ^{sup}, *miring*  -> tspan."""
    out = []
    for part in _TOKEN.split(s):
        if not part:
            continue
        if part.startswith("_{"):
            out.append(f'<tspan baseline-shift="sub" font-size="{size*0.72:.1f}">{esc(part[2:-1])}</tspan>')
        elif part.startswith("^{"):
            out.append(f'<tspan baseline-shift="super" font-size="{size*0.72:.1f}">{esc(part[2:-1])}</tspan>')
        elif part.startswith("*"):
            out.append(f'<tspan font-style="italic">{esc(part[1:-1])}</tspan>')
        else:
            out.append(esc(part))
    return "".join(out)


def plain(s):
    return _TOKEN.sub(lambda m: m.group(0)[2:-1] if m.group(0)[0] in "_^" else m.group(0)[1:-1], s)


def tw(s, size=FS, bold=False):
    """Perkiraan lebar teks (px)."""
    k = 0.56 if bold else 0.53
    return len(plain(s)) * size * k


def text(x, y, s, size=FS, weight=400, anchor="middle", fill=INK, italic=False):
    st = ' font-style="italic"' if italic else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" '
            f'text-anchor="{anchor}" fill="{fill}"{st}>{rich(s, size)}</text>')


def lines(x, y, items, size=FS, weight=400, anchor="middle", fill=INK, lh=1.3):
    """Beberapa baris; y = baseline baris pertama."""
    return "".join(text(x, y + i * size * lh, s, size, weight, anchor, fill) for i, s in enumerate(items))


def rect(x, y, w, h, fill=SURF, stroke=LINE, sw=2, rx=8, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')


def box(x, y, w, h, title=None, body=(), fill=SURF, stroke=LINE, sw=2, rx=8,
        size=FS, title_size=None, dash=None, valign="center"):
    """Kotak dengan judul tebal + baris isi, teks di tengah."""
    ts = title_size or size
    rows = ([(title, ts, 700)] if title else []) + [(b, size, 400) for b in body]
    lh = 1.3
    total = sum(r[1] * lh for r in rows) - (rows[-1][1] * (lh - 1) if rows else 0)
    if valign == "center":
        cy = y + (h - total) / 2 + rows[0][1] * 0.8 if rows else y
    else:
        cy = y + 14 + rows[0][1] * 0.8
    out = [rect(x, y, w, h, fill, stroke, sw, rx, dash)]
    for s, sz, wt in rows:
        out.append(text(x + w / 2, cy, s, sz, wt))
        cy += sz * lh
    return "".join(out)


def pill(x, y, w, h, label, fill=NEUTRAL_FILL, stroke=LINE, size=FS):
    return (rect(x, y, w, h, fill, stroke, 2, h / 2) +
            text(x + w / 2, y + h / 2 + size * 0.35, label, size, 700))


def diamond(cx, cy, w, h, body, fill=SURF, stroke=LINE, size=FS):
    pts = f"{cx},{cy-h/2} {cx+w/2},{cy} {cx},{cy+h/2} {cx-w/2},{cy}"
    n = len(body)
    y0 = cy - (n - 1) * size * 1.25 / 2 + size * 0.35
    return (f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>' +
            "".join(text(cx, y0 + i * size * 1.25, s, size) for i, s in enumerate(body)))


MARKER_COLORS = [LINE, INK, BLUE, ORANGE]


def arrow(pts, color=LINE, sw=2, dash=None, head=True, tail=False):
    marker = "ah%d" % (MARKER_COLORS.index(color) if color in MARKER_COLORS else 0)
    d = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    da = f' stroke-dasharray="{dash}"' if dash else ""
    me = f' marker-end="url(#{marker})"' if head else ""
    ms = f' marker-start="url(#{marker}s)"' if tail else ""
    return (f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}" '
            f'stroke-linejoin="round"{da}{me}{ms}/>')


def tag(x, y, s, size=FS_S, anchor="middle", fill=INK, bg=SURF, weight=400, pad=4):
    """Label panah dengan latar putih agar tidak tertimpa garis."""
    w = tw(s, size, weight >= 600) + 2 * pad
    if anchor == "middle":
        x0 = x - w / 2
    elif anchor == "start":
        x0 = x - pad
    else:
        x0 = x - w + pad
    return (f'<rect x="{x0:.1f}" y="{y - size*0.95:.1f}" width="{w:.1f}" height="{size*1.3:.1f}" fill="{bg}"/>' +
            text(x, y, s, size, weight, anchor, fill))


def svg(w, h, body):
    defs = "<defs>" + "".join(
        f'<marker id="ah{i}" viewBox="0 0 10 10" refX="9" refY="5" markerUnits="userSpaceOnUse" '
        f'markerWidth="15" markerHeight="15" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>'
        f'<marker id="ah{i}s" viewBox="0 0 10 10" refX="1" refY="5" markerUnits="userSpaceOnUse" '
        f'markerWidth="15" markerHeight="15" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>'
        for i, c in enumerate(MARKER_COLORS)) + "</defs>"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'font-family="{FONT}">{defs}<rect width="{w}" height="{h}" fill="{SURF}"/>{body}</svg>')


def page(svgs):
    return ("<!doctype html><html><head><meta charset='utf-8'><style>"
            "body{margin:0;background:#fff}</style></head><body>" + svgs + "</body></html>")
