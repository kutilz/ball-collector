"""Diagram skripsi robot pengumpul bola. Semua isi diambil dari naskah
(Skripsi Maul.docx) dan kode repo; tidak ada komponen/nilai tambahan."""
import json
import os
from svgkit import *

OUT = os.path.dirname(os.path.abspath(__file__))
FIGS = {}


def fig(name, w, h):
    def deco(fn):
        FIGS[name] = (w, h, fn)
        return fn
    return deco


def bullets(x, y, w, h, title, items, fill=SURF, stroke=LINE, size=FS_S):
    out = [rect(x, y, w, h, fill, stroke), text(x + w / 2, y + 30, title, FS, 700)]
    for i, s in enumerate(items):
        out.append(text(x + 16, y + 60 + i * size * 1.4, s, size, anchor="start"))
    return "".join(out)


def legend(items, x, y, size=FS_S, gap=36):
    """items: (warna, label, jenis) jenis = 'box' | 'line'"""
    out, cx = [], x
    for color, label, kind in items:
        if kind == "line":
            out.append(f'<line x1="{cx}" y1="{y-6}" x2="{cx+34}" y2="{y-6}" stroke="{color}" stroke-width="4"/>')
            cx += 42
        else:
            out.append(rect(cx, y - 16, 18, 18, color, color, 1, 3))
            cx += 26
        out.append(text(cx, y, label, size, anchor="start"))
        cx += tw(label, size) + gap
    return "".join(out)


# ---------------------------------------------------------------- Gambar 2.1
@fig("g2_1_mecanum", 920, 450)
def mecanum():
    o = []
    panels = [
        ("(a) Maju: v_{x} > 0", ["+", "+", "+", "+"], "maju"),
        ("(b) Menyamping: v_{y} > 0", ["+", "−", "−", "+"], "geser"),
        ("(c) Berputar: ω > 0", ["+", "−", "+", "−"], "putar"),
    ]
    for i, (title, signs, kind) in enumerate(panels):
        cx = 155 + i * 305
        o.append(text(cx, 34, title, FS, 700))
        o.append(text(cx, 88, "depan", FS_S, fill=INK2))
        o.append(f'<path d="M{cx-8},98 L{cx+8},98 L{cx},108 z" fill="{INK2}" transform="rotate(180 {cx} 103)"/>')
        o.append(rect(cx - 65, 118, 130, 200, NEUTRAL_FILL, LINE, 2, 10))
        wheels = [("FL", cx - 101, 132), ("FR", cx + 69, 132), ("RL", cx - 101, 238), ("RR", cx + 69, 238)]
        for (nm, wx, wy), sg in zip(wheels, signs):
            col = BLUE if sg == "+" else RED
            o.append(rect(wx, wy, 32, 72, col, col, 1, 5))
            o.append(text(wx + 16, wy + 45, sg, 28, 700, fill="#ffffff"))
            if nm.endswith("L"):
                o.append(text(wx - 8, wy + 43, nm, FS_S, 700, "end"))
            else:
                o.append(text(wx + 40, wy + 43, nm, FS_S, 700, "start"))
        if kind == "maju":
            o.append(arrow([(cx, 285), (cx, 158)], INK, 3))
        elif kind == "geser":
            o.append(arrow([(cx - 42, 218), (cx + 42, 218)], INK, 3, tail=True))
            o.append(text(cx, 255, "sumbu y", FS_S, fill=INK2))
        else:
            r = 42
            o.append(f'<path d="M {cx - r*0.87:.1f},{218 + r*0.5:.1f} A {r} {r} 0 1 1 {cx + r*0.87:.1f},{218 + r*0.5:.1f}" '
                     f'fill="none" stroke="{INK}" stroke-width="3" marker-end="url(#ah1)"/>')
        o.append(text(cx, 352, "   ·   ".join(f"{n} {s}" for n, s in zip(["FL", "FR", "RL", "RR"], signs)), FS_S))
    o.append(legend([(BLUE, "+  roda berputar maju", "box"), (RED, "−  roda berputar mundur", "box")], 215, 420))
    return "".join(o)


# ---------------------------------------------------------------- Gambar 2.2
@fig("g2_2_kerangka", 920, 720)
def kerangka():
    o = [box(160, 20, 600, 96, "Permasalahan",
             ["Pengumpulan bola pingpong secara manual", "menyita waktu dan tenaga atlet maupun pelatih"])]
    o.append(arrow([(460, 116), (460, 146)]))
    o.append(box(10, 150, 200, 510, "Masukan",
                 ["Arena latihan", "dalam ruangan", "berlantai datar;", "bola pingpong", "tersebar di lantai"], size=FS_S))
    o.append(rect(250, 150, 420, 510, SURF, LINE))
    o.append(text(460, 180, "Proses", FS, 700))
    steps = [
        (ORANGE_T, ORANGE, ["ESP32-CAM mengalirkan citra", "(MJPEG) ke laptop"]),
        (BLUE_T, BLUE, ["Segmentasi warna HSV:", "centroid dan galat posisi bola"]),
        (BLUE_T, BLUE, ["FSM + *P-controller* →", "perintah (v_{x}, v_{y}, ω)"]),
        (AQUA_T, AQUA, ["Arduino Uno: kinematika invers", "Mecanum → PWM → DRV8833 → motor"]),
        (AQUA_T, AQUA, ["Servo menggerakkan", "*gripper* cetak 3D"]),
    ]
    y = 196
    for i, (f, s, b) in enumerate(steps):
        o.append(box(270, y, 380, 62, None, b, f, s, 2, 8, FS_S))
        if i < len(steps) - 1:
            o.append(arrow([(460, y + 62), (460, y + 86)], sw=2))
        y += 88
    o.append(text(460, 632, "Diawasi *watchdog* dan *heartbeat*;", FS_S, fill=INK2))
    o.append(text(460, 652, "YOLOv8 dievaluasi luring sebagai pembanding", FS_S, fill=INK2))
    o.append(box(710, 150, 200, 510, "Keluaran",
                 ["Bola terkumpul", "otomatis ke", "penampung;", "beban kerja", "manual berkurang"], size=FS_S))
    o.append(arrow([(210, 405), (248, 405)]))
    o.append(arrow([(670, 405), (708, 405)]))
    o.append(legend([(BLUE, "laptop (*ground station*)", "box"), (ORANGE, "ESP32-CAM", "box"),
                     (AQUA, "Arduino Uno", "box")], 150, 705))
    return "".join(o)


# ---------------------------------------------------------------- Gambar 3.1
@fig("g3_1_metode", 920, 860)
def metode():
    o = []
    cx, x0, w = 220, 70, 300
    o.append(pill(x0 + 50, 20, 200, 52, "Mulai"))
    steps = ["Analisis kebutuhan", "Perancangan", "Implementasi", "Pengujian", "Evaluasi"]
    desc = [
        ["Kebutuhan fungsional: deteksi bola, navigasi", "mendekati bola, pengumpulan bola. Non-fungsional:",
         "keselamatan, kemudahan kalibrasi, pencatatan data."],
        ["Arsitektur terdistribusi, mekanik sasis & *intake*,", "elektrik & daya, perangkat lunak (deteksi, FSM,",
         "kinematika, komunikasi, dasbor)."],
        ["Fabrikasi cetak 3D, perakitan elektronik, *firmware*", "Arduino & ESP32-CAM, program *ground station*."],
        ["Uji per subsistem (deteksi, navigasi, *intake*),", "dilanjutkan uji sistem terintegrasi."],
        ["Analisis hasil pengujian; iterasi perbaikan", "bila diperlukan."],
    ]
    o.append(arrow([(cx, 72), (cx, 108)]))
    for i, (s, d) in enumerate(zip(steps, desc)):
        y = 110 + i * 100
        o.append(box(x0, y, w, 60, s, [], SURF, LINE))
        h = 26 + len(d) * FS_S * 1.35
        dy = y + 30 - h / 2
        o.append(rect(410, dy, 500, h, NEUTRAL_FILL, NEUTRAL_FILL, 1, 6))
        for j, line in enumerate(d):
            o.append(text(426, dy + 32 + j * FS_S * 1.35, line, FS_S, anchor="start"))
        o.append(f'<line x1="{x0 + w}" y1="{y + 30}" x2="410" y2="{y + 30}" stroke="{MUTED}" stroke-width="1.5" stroke-dasharray="4 4"/>')
        if i < len(steps) - 1:
            o.append(arrow([(cx, y + 60), (cx, y + 98)]))
    o.append(arrow([(cx, 570), (cx, 598)]))
    o.append(diamond(cx, 660, 280, 120, ["Memenuhi", "kebutuhan?"]))
    o.append(arrow([(cx - 140, 660), (30, 660), (30, 240), (x0 - 2, 240)]))
    o.append(tag(40, 604, "Tidak", FS_S, "start"))
    o.append(arrow([(cx, 720), (cx, 768)]))
    o.append(tag(cx + 10, 750, "Ya", FS_S, "start"))
    o.append(pill(x0 + 50, 770, 200, 52, "Selesai"))
    return "".join(o)


# ---------------------------------------------------------------- Gambar 3.2
@fig("g3_2_arsitektur", 920, 900)
def arsitektur():
    o = [rect(20, 20, 880, 230, BLUE_T, BLUE, 2.5, 10),
         text(460, 54, "Laptop — *ground station* (Python)", 21, 700)]
    mods = [("vision", ["segmentasi", "warna HSV"]), ("brain", ["FSM +", "*P-controller*"]),
            ("comms", ["video &", "perintah"]), ("logger", ["pencatatan", "CSV"]),
            ("app", ["Flask +", "Socket.IO"])]
    for i, (t, b) in enumerate(mods):
        o.append(box(40 + i * 170, 76, 156, 100, t, b, SURF, BLUE, 1.5, 8, FS_S, FS))
    o.append(text(460, 214, "Dasbor web (WebSocket): video + *overlay*, kalibrasi HSV, telemetri, kendali manual", FS_S))
    # Wi-Fi
    o.append(lines(95, 300, ["Wi-Fi", "(router/", "hotspot)"], FS_S, fill=INK2))
    o.append(arrow([(250, 370), (250, 252)]))
    o.append(tag(260, 305, "Video MJPEG", FS_S, "start"))
    o.append(tag(260, 326, "(port 81, /stream)", FS_S, "start"))
    o.append(arrow([(460, 252), (460, 370)]))
    o.append(tag(470, 305, "Perintah HTTP GET", FS_S, "start"))
    o.append(tag(470, 326, "(port 80, /cmd)", FS_S, "start"))
    o.append(arrow([(690, 370), (690, 252)], dash="7 5"))
    o.append(tag(700, 305, "Telemetri", FS_S, "start"))
    o.append(tag(700, 326, "(TEL)", FS_S, "start"))
    o.append(box(170, 372, 580, 108, "ESP32-CAM (ESP32 + kamera OV2640)",
                 ["*web server*: aliran MJPEG dan *endpoint* perintah", "meneruskan perintah dari Wi-Fi ke UART"],
                 ORANGE_T, ORANGE, 2.5, 10))
    # UART
    o.append(box(300, 530, 320, 52, None, ["*Logic level converter* 5 V ↔ 3,3 V"], NEUTRAL_FILL, MUTED, 1.5, 6, FS_S))
    o.append(arrow([(380, 482), (380, 528)]))
    o.append(arrow([(380, 584), (380, 638)]))
    o.append(arrow([(540, 638), (540, 584)], dash="7 5"))
    o.append(arrow([(540, 528), (540, 482)], dash="7 5"))
    o.append(tag(290, 562, "UART 115200 baud", FS_S, "end"))
    o.append(tag(370, 618, "CMD / SERVO / COLLECT", FS_S, "end"))
    o.append(tag(550, 618, "TEL", FS_S, "start"))
    o.append(box(170, 640, 580, 110, "Arduino Uno — pengendali tingkat rendah",
                 ["kinematika invers Mecanum, PWM, kendali servo,", "pembacaan IMU, *watchdog* 500 ms"],
                 AQUA_T, AQUA, 2.5, 10))
    per = [(20, 300, "2 × DRV8833", "→ 4 motor DC + roda Mecanum"),
           (340, 240, "Servo MG996R", "*gripper*"),
           (600, 300, "MPU6050", "giroskop sumbu-Z (I²C)")]
    for x, w, t, b in per:
        o.append(box(x, 810, w, 76, t, [b], NEUTRAL_FILL, MUTED, 1.5, 8, FS_S))
    o.append(arrow([(250, 752), (250, 808)]))
    o.append(tag(260, 786, "PWM + arah", FS_S, "start"))
    o.append(arrow([(460, 752), (460, 808)]))
    o.append(tag(470, 786, "sinyal servo", FS_S, "start"))
    o.append(arrow([(690, 752), (690, 808)], tail=True))
    o.append(tag(700, 786, "I²C", FS_S, "start"))
    return "".join(o)


# ---------------------------------------------------------------- Gambar 3.4
@fig("g3_4_daya", 920, 590)
def daya():
    o = []
    o.append(box(20, 200, 170, 110, "Baterai LiPo 2S", ["7,4–8,4 V"], NEUTRAL_FILL, LINE))
    # rel motor
    o.append(arrow([(190, 235), (290, 235), (290, 115), (328, 115)], ORANGE, 3.5))
    o.append(tag(236, 225, "VM", FS_S))
    o.append(box(330, 70, 220, 90, "2 × DRV8833", ["masukan VM"], SURF, ORANGE, 2))
    o.append(arrow([(550, 115), (618, 115)], ORANGE, 3.5))
    o.append(box(620, 70, 280, 90, "4 motor DC Mecanum", ["FL, FR, RL, RR"], SURF, ORANGE, 2))
    o.append(lines(330, 190, ["Kapasitor *bulk* ≥ 470 µF", "pada rel motor"], FS_S, anchor="start", fill=INK2))
    o.append(lines(620, 190, ["Kapasitor keramik 0,1 µF", "di terminal motor"], FS_S, anchor="start", fill=INK2))
    # rel 5 V
    o.append(arrow([(190, 275), (290, 275), (290, 385), (328, 385)], BLUE, 3.5))
    o.append(box(330, 340, 220, 90, "Modul *buck* XL4015", ["penurun tegangan ke 5 V"], SURF, BLUE, 2, 8, FS_S, FS))
    o.append(f'<path d="M550,385 L600,385" stroke="{BLUE}" stroke-width="3.5"/>')
    o.append(f'<path d="M600,318 L600,498" stroke="{BLUE}" stroke-width="3.5"/>')
    o.append(tag(575, 372, "5 V", FS_S))
    for i, t in enumerate(["Arduino Uno", "*Logic level converter*", "Servo MG996R"]):
        y = 290 + i * 90
        o.append(arrow([(600, y + 28), (658, y + 28)], BLUE, 3.5))
        o.append(box(660, y, 240, 56, None, [t], SURF, BLUE, 2, 8, FS_S))
    o.append(lines(20, 380, ["Semua modul memakai", "ground bersama", "(*common ground*)."], FS_S, anchor="start", fill=INK2))
    o.append(legend([(ORANGE, "rel motor (VM)", "line"), (BLUE, "rel logika 5 V", "line")], 220, 566))
    return "".join(o)


# ---------------------------------------------------------------- Gambar 3.5
@fig("g3_5_koneksi", 920, 560)
def koneksi():
    o = [rect(330, 60, 260, 450, AQUA_T, AQUA, 2.5, 10), text(460, 92, "Arduino Uno", FS, 700),
         rect(150, 60, 130, 450, NEUTRAL_FILL, MUTED, 1.5, 8), text(215, 92, "2 × DRV8833", 18, 700)]
    motors = [("FL", "D3", "D4"), ("FR", "D5", "D7"), ("RL", "D6", "D8"), ("RR", "D11", "D12")]
    for i, (m, pwm, dr) in enumerate(motors):
        y1 = 140 + i * 95
        y2 = y1 + 30
        o.append(text(344, y1 + 6, f"{pwm} · PWM {m}", FS_S, anchor="start"))
        o.append(text(344, y2 + 6, f"{dr} · DIR {m}", FS_S, anchor="start"))
        o.append(arrow([(330, y1), (282, y1)]))
        o.append(arrow([(330, y2), (282, y2)]))
        yc = (y1 + y2) / 2
        o.append(text(215, yc + 6, f"kanal {m}", FS_S))
        o.append(arrow([(150, yc), (122, yc)]))
        o.append(box(10, yc - 26, 110, 52, None, [f"Motor {m}"], SURF, LINE, 2, 8, FS_S))
    for y, lab in [(140, "D2 · servo"), (230, "A4 · SDA"), (260, "A5 · SCL"),
                   (325, "D0 · RX"), (355, "D1 · TX"), (450, "D13 · LED")]:
        o.append(text(570, y + 6, lab, FS_S, anchor="end"))
    o.append(arrow([(590, 140), (638, 140)]))
    o.append(box(640, 114, 170, 52, None, ["Servo MG996R"], SURF, LINE, 2, 8, FS_S))
    o.append(arrow([(590, 230), (638, 230)], tail=True))
    o.append(arrow([(590, 260), (638, 260)], tail=True))
    o.append(box(640, 214, 170, 62, None, ["MPU6050 (I²C)"], SURF, LINE, 2, 8, FS_S))
    o.append(arrow([(638, 325), (592, 325)]))
    o.append(arrow([(590, 355), (638, 355)]))
    o.append(box(640, 307, 140, 66, None, ["*Logic level*", "*converter*"], NEUTRAL_FILL, MUTED, 1.5, 8, FS_S))
    o.append(arrow([(780, 340), (798, 340)], tail=True))
    o.append(box(800, 307, 110, 66, None, ["ESP32-", "CAM"], ORANGE_T, ORANGE, 2, 8, FS_S))
    o.append(text(775, 400, "UART 5 V ↔ 3,3 V", FS_S, fill=INK2))
    o.append(arrow([(590, 450), (638, 450)]))
    o.append(box(640, 424, 170, 52, None, ["LED indikator"], SURF, LINE, 2, 8, FS_S))
    o.append(text(10, 545, "Catatan: jalur daya (VM, 5 V) dan ground bersama tidak digambar pada diagram ini.",
                  FS_S, anchor="start", fill=INK2))
    return "".join(o)


# ---------------------------------------------------------------- Gambar 3.6
@fig("g3_6_pipeline", 720, 1090)
def pipeline():
    o, cx, x0, w = [], 300, 80, 440
    o.append(pill(x0, 20, w, 52, "*Frame* MJPEG dari ESP32-CAM"))
    items = [
        (106, ["Ubah ukuran *frame* ke 640 × 480"]),
        (196, ["Konversi ruang warna BGR → HSV"]),
        (286, ["*inRange*: H 5–25, S 100–255, V 100–255", "→ *mask* biner"]),
        (396, ["Erosi 2× lalu dilasi 2× (morfologi)"]),
        (486, ["Cari kontur (*findContours*)"]),
    ]
    prev = 72
    for y, b in items:
        h = 76 if len(b) > 1 else 56
        o.append(arrow([(cx, prev), (cx, y - 2)]))
        o.append(box(x0, y, w, h, None, b, SURF, LINE, 2, 8, FS))
        prev = y + h
    o.append(arrow([(cx, prev), (cx, 559)]))
    o.append(diamond(cx, 626, 360, 132, ["Ada kontur dengan", "luas ≥ 50 px²?"]))
    o.append(arrow([(cx + 180, 626), (538, 626)]))
    o.append(tag(510, 614, "Tidak", FS_S))
    o.append(box(540, 596, 160, 60, None, ["Bola tidak", "terdeteksi"], NEUTRAL_FILL, LINE, 2, 8, FS_S))
    o.append(arrow([(cx, 692), (cx, 723)]))
    o.append(tag(cx + 10, 712, "Ya", FS_S, "start"))
    rest = [(725, ["Pilih kontur dengan luas terbesar"]),
            (815, ["Hitung momen citra: luas M_{00}", "dan centroid (c_{x}, c_{y})"]),
            (925, ["Galat *e*_{x} = c_{x} − x_{tengah}"])]
    prev = None
    for y, b in rest:
        h = 76 if len(b) > 1 else 56
        if prev:
            o.append(arrow([(cx, prev), (cx, y - 2)]))
        o.append(box(x0, y, w, h, None, b, SURF, LINE, 2, 8, FS))
        prev = y + h
    o.append(arrow([(cx, prev), (cx, 1013)]))
    o.append(pill(x0, 1015, w, 52, "Status deteksi, luas, dan e_{x} → FSM"))
    o.append(arrow([(620, 656), (620, 1041), (522, 1041)]))
    return "".join(o)


# ---------------------------------------------------------------- Gambar 3.7
@fig("g3_7_fsm", 920, 600)
def fsm():
    o = []

    def state(x, y, w, h, name, body):
        return box(x, y, w, h, name, body, BLUE_T, BLUE, 2.5, 18, 18, 21)
    o.append(state(40, 390, 200, 130, "IDLE", ["diam, menunggu", "perintah mulai"]))
    o.append(state(300, 90, 220, 110, "SEARCH", ["berputar perlahan", "mencari bola"]))
    o.append(state(660, 90, 240, 110, "APPROACH", ["maju + koreksi arah", "ω = K_{p} · e_{x}"]))
    o.append(state(660, 390, 240, 130, "COLLECT", ["berhenti, buka–tutup", "*gripper*, hitung bola"]))
    o.append(f'<circle cx="140" cy="572" r="10" fill="{INK}"/>')
    o.append(arrow([(140, 562), (140, 522)]))
    o.append(arrow([(140, 390), (140, 145), (298, 145)]))
    o.append(tag(150, 280, "operator menekan Mulai", FS_S, "start"))
    o.append(arrow([(520, 130), (658, 130)]))
    o.append(tag(590, 58, "bola terdeteksi dan", FS_S))
    o.append(tag(590, 78, "luas ≥ 500 px²", FS_S))
    o.append(arrow([(660, 172), (522, 172)]))
    o.append(tag(590, 196, "bola hilang", FS_S))
    o.append(arrow([(780, 200), (780, 388)]))
    o.append(tag(770, 300, "luas ≥ 8000 px²", FS_S, "end"))
    o.append(arrow([(660, 455), (410, 455), (410, 202)]))
    o.append(tag(535, 444, "sekuens selesai", FS_S))
    return "".join(o)


# ---------------------------------------------------------------- Gambar 3.8
@fig("g3_8_protokol", 920, 810)
def protokol():
    o = []
    heads = [(120, 210, "*Ground station*", "(laptop)", BLUE_T, BLUE), (380, 180, "ESP32-CAM", None, ORANGE_T, ORANGE),
             (620, 180, "Arduino Uno", None, AQUA_T, AQUA), (830, 160, "Motor", "(via DRV8833)", NEUTRAL_FILL, MUTED)]
    for cx, w, t, b, f, s in heads:
        o.append(f'<line x1="{cx}" y1="84" x2="{cx}" y2="795" stroke="{MUTED}" stroke-width="1.5" stroke-dasharray="6 5"/>')
        o.append(box(cx - w / 2, 20, w, 64, t, [b] if b else [], f, s, 2, 8, FS_S, 18))
    X = {"L": 120, "E": 380, "A": 620, "M": 830}

    def msg(a, b, y, label, dash=None, bold=False, x_end=None):
        xa, xb = X[a], (x_end if x_end else X[b])
        d = 4 if xb > xa else -4
        r = [arrow([(xa, y), (xb - d, y)], dash=dash)]
        r.append(tag((xa + xb) / 2, y - 9, label, FS_S, weight=700 if bold else 400))
        return "".join(r)
    o.append(msg("E", "L", 130, "aliran MJPEG (port 81, /stream)"))
    # frame loop
    o.append(rect(30, 160, 880, 240, "none", INK2, 1.5, 4))
    o.append(f'<path d="M30,160 L110,160 L110,182 L100,192 L30,192 z" fill="{NEUTRAL_FILL}" stroke="{INK2}" stroke-width="1.5"/>')
    o.append(text(70, 182, "loop", FS_S, 700))
    o.append(tag(122, 182, "[*heartbeat*: dikirim ulang tiap 0,15 s selama perintah gerak aktif]", FS_S, "start", INK2))
    o.append(msg("L", "E", 232, "HTTP GET /cmd (port 80)"))
    o.append(msg("E", "A", 282, "CMD:vx,vy,omega (UART)"))
    o.append(rect(612, 290, 16, 70, AQUA, AQUA, 1, 2))
    o.append(lines(640, 312, ["reset *watchdog*;", "kinematika invers"], FS_S, anchor="start"))
    o.append(msg("A", "M", 378, "PWM + arah"))
    o.append(msg("A", "E", 440, "TEL:heading,vbat", dash="7 5"))
    o.append(msg("E", "L", 480, "telemetri", dash="7 5"))
    o.append(f'<line x1="20" y1="535" x2="900" y2="535" stroke="{INK2}" stroke-width="1.5" stroke-dasharray="10 6"/>')
    o.append(tag(460, 541, "Skenario: koneksi Wi-Fi terputus", FS_S, weight=700))
    o.append(arrow([(120, 600), (290, 600)], head=False))
    o.append(f'<path d="M282,590 L302,610 M302,590 L282,610" stroke="{INK}" stroke-width="3"/>')
    o.append(tag(205, 590, "HTTP GET tidak sampai", FS_S))
    o.append(f'<path d="M608,585 L596,585 L596,715 L608,715" fill="none" stroke="{INK}" stroke-width="2"/>')
    o.append(tag(584, 640, "tidak ada perintah valid", FS_S, "end"))
    o.append(tag(584, 662, "selama 500 ms → *watchdog*", FS_S, "end"))
    o.append(msg("A", "M", 755, "STOP (PWM = 0)", bold=True))
    return "".join(o)


# ---------------------------------------------------------------- Gambar 3.9
@fig("g3_9_lingkar", 720, 1120)
def lingkar():
    o, cx, x0, w = [], 300, 80, 440
    o.append(pill(x0, 20, w, 52, "Mulai (*background task*)"))
    o.append(arrow([(cx, 72), (cx, 104)]))
    o.append(box(x0, 106, w, 56, None, ["Ambil *frame* dari sumber video"]))
    o.append(arrow([(cx, 162), (cx, 194)]))
    o.append(box(x0, 196, w, 56, None, ["Proses deteksi bola (segmentasi HSV)"]))
    o.append(arrow([(cx, 252), (cx, 284)]))
    o.append(diamond(cx, 346, 340, 120, ["Mode otomatis", "aktif?"]))
    o.append(arrow([(cx, 406), (cx, 438)]))
    o.append(tag(cx + 10, 426, "Ya", FS_S, "start"))
    o.append(box(x0, 440, w, 76, None, ["Jalankan FSM → perintah", "(v_{x}, v_{y}, ω) dan servo"]))
    o.append(arrow([(cx, 516), (cx, 548)]))
    o.append(box(x0, 550, w, 76, None, ["Kirim perintah ke robot", "(*thread* pekerja non-pemblokir)"]))
    o.append(f'<path d="M{cx+170},346 L620,346 L620,655 L{cx},655" fill="none" stroke="{LINE}" stroke-width="2"/>')
    o.append(tag(500, 334, "Tidak", FS_S))
    o.append(arrow([(cx, 626), (cx, 668)]))
    o.append(diamond(cx, 725, 340, 110, ["Perekaman CSV", "aktif?"]))
    o.append(arrow([(cx, 780), (cx, 812)]))
    o.append(tag(cx + 10, 800, "Ya", FS_S, "start"))
    o.append(box(x0, 814, w, 56, None, ["Catat baris data ke berkas CSV"]))
    o.append(f'<path d="M{cx+170},725 L620,725 L620,900 L{cx},900" fill="none" stroke="{LINE}" stroke-width="2"/>')
    o.append(tag(500, 713, "Tidak", FS_S))
    o.append(arrow([(cx, 870), (cx, 932)]))
    o.append(box(x0, 934, w, 76, None, ["Hitung FPS dan siarkan telemetri", "ke dasbor (WebSocket)"]))
    o.append(arrow([(cx, 1010), (cx, 1042)]))
    o.append(box(x0, 1044, w, 56, None, ["Jeda ± 30 ms (target ≈ 33 FPS)"]))
    o.append(arrow([(x0, 1072), (36, 1072), (36, 134), (x0 - 2, 134)]))
    return "".join(o)


# ---------------------------------------------------------------- Gambar 3.11
@fig("g3_11_pengujian", 920, 660)
def pengujian():
    o = [text(10, 28, "Tahap 1 — uji per subsistem (isolasi)", 18, 700, "start", INK2)]
    cols = [("Deteksi (*vision*)", ["• *precision*, *recall*, *F1-score*", "• laju deteksi vs jarak", "• laju deteksi vs cahaya",
                                  "• FPS dan latensi *end-to-end*", "• HSV vs YOLOv8"]),
            ("Navigasi", ["• galat posisi berhenti", "• waktu tempuh vs jarak", "• *drift* saat *strafe*",
                          "• *repeatability*"]),
            ("Intake (*gripper*)", ["• keberhasilan cengkeram", "• waktu per bola"])]
    for i, (t, items) in enumerate(cols):
        x = 10 + i * 305
        o.append(bullets(x, 44, 290, 196, t, items))
        o.append(arrow([(x + 145, 240), (x + 145, 298)]))
    o.append(rect(10, 300, 900, 96, SURF, LINE))
    o.append(text(460, 332, "Tahap 2 — uji sistem terintegrasi", FS, 700))
    o.append(text(460, 364, "keberhasilan *clear* lapangan · total waktu *clear* N bola · cakupan · konsumsi daya/*endurance*", FS_S))
    o.append(arrow([(460, 396), (460, 438)]))
    o.append(box(170, 440, 580, 96, "Analisis data",
                 ["rata-rata ± simpangan baku, persentase keberhasilan,", "disajikan dalam tabel dan grafik"], SURF, LINE, 2, 8, FS_S))
    o.append(arrow([(460, 536), (460, 578)]))
    o.append(pill(260, 580, 400, 52, "Pembahasan (Subbab 4.6)"))
    return "".join(o)


if __name__ == "__main__":
    meta = {}
    for name, (w, h, fn) in FIGS.items():
        with open(os.path.join(OUT, name + ".html"), "w", encoding="utf8") as f:
            f.write(page(svg(w, h, fn())))
        meta[name] = [w, h]
    with open(os.path.join(OUT, "meta.json"), "w") as f:
        json.dump(meta, f)
    print("ok", list(meta))
