"""OFT B1 wiring sheet: Waveshare RP2350-POE-ETH <-> Seeed XIAO ESP32-C5.

GPL-3.0-or-later."""
import sys
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

OUT = sys.argv[1]
W, H = landscape(letter)

INK = HexColor("#1b1f24")
MUTED = HexColor("#5b6570")
LINE = HexColor("#c9d1d9")
PANEL = HexColor("#f4f6f8")
BOARD_RP = HexColor("#1f4e8c")
BOARD_XIAO = HexColor("#22262b")
AMBER = HexColor("#b45309")
AMBER_BG = HexColor("#fdf1dc")
GREEN = HexColor("#1a7f4b")
GREEN_BG = HexColor("#e3f4ea")
PAD = HexColor("#d4a94a")

# signal, colour, colour name, RP label, RP detail, XIAO label, XIAO detail, where, direction, wire note, optional
WIRES = [
    ("5 V power", "#d1242f", "red", "Vsys", "pin 31", "5V", "VBUS pin", "header", ">", "about 4.7 V, from USB or PoE", False),
    ("Ground", "#1b1f24", "black", "G", "pin 8 (any G pin)", "GND", "", "header", "", "", False),
    ("Node link, Timer to Node", "#d9730d", "orange", "4", "pin 6, GP4, UART1 TX", "D7", "GPIO12, UART0 RX", "header", ">", "921600 baud 8N1, 3.3 V", False),
    ("Node link, Node to Timer", "#0969da", "blue", "5", "pin 7, GP5, UART1 RX", "D6", "GPIO11, UART0 TX", "header", "<", "921600 baud 8N1, 3.3 V", False),
    ("SYNC", "#8250df", "purple", "6", "pin 9, GP6, output", "MTMS", "GPIO2, input", "pad", ">", "20 Hz pulse, 0.2 ms wide", False),
    ("Node reset", "#6e7781", "grey", "7", "pin 10, GP7, output", "EN", "chip enable, low = reset", "pad", ">", "optional for first tests", True),
    ("Node boot mode", "#0f8a8a", "teal", "8", "pin 11, GP8, output", "BOOT", "GPIO28, low = download", "pad", ">", "optional for first tests", True),
]

body = ParagraphStyle("body", fontName="Helvetica", fontSize=8.6, leading=11.4, textColor=INK)
small = ParagraphStyle("small", parent=body, fontSize=7.4, leading=9.6, textColor=MUTED)
head = ParagraphStyle("head", parent=body, fontName="Helvetica-Bold", fontSize=9.6, leading=12)


def para(c, text, x, top, width, style=body):
    p = Paragraph(text, style)
    _, h = p.wrapOn(c, width, 1000)
    p.drawOn(c, x, top - h)
    return top - h


def text(c, s, x, y, size=9, bold=False, color=INK, align="l"):
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    c.setFillColor(color)
    {"l": c.drawString, "r": c.drawRightString, "c": c.drawCentredString}[align](x, y, s)


def pill(c, s, x_right, y, fg, bg):
    c.setFont("Helvetica-Bold", 6.8)
    w = c.stringWidth(s, "Helvetica-Bold", 6.8) + 10
    c.setFillColor(bg)
    c.roundRect(x_right - w, y - 3.5, w, 11.5, 5.7, stroke=0, fill=1)
    c.setFillColor(fg)
    c.drawCentredString(x_right - w / 2, y - 0.3, s)


def arrow(c, x, y, d, color):
    c.setFillColor(color)
    p = c.beginPath()
    s = 7 * d
    p.moveTo(x, y); p.lineTo(x - s, y + 5); p.lineTo(x - s, y - 5); p.close()
    c.drawPath(p, stroke=0, fill=1)


def title(c, t, sub, page):
    text(c, t, 36, H - 46, 19, True)
    text(c, sub, 36, H - 62, 9.5, color=MUTED)
    text(c, f"Open FPV Timer, build B1  |  2026-11-09  |  page {page} of 2", W - 36, H - 46, 8, color=MUTED, align="r")
    c.setStrokeColor(LINE); c.setLineWidth(0.8); c.line(36, H - 72, W - 36, H - 72)


# ---------------------------------------------------------------- page 1
def page1(c):
    title(c, "Gate timer wiring", "Waveshare RP2350-POE-ETH (Timer) to Seeed XIAO ESP32-C5 (Node): 7 wires, all logic 3.3 V", 1)

    # system chain
    y = H - 104
    chain = [("PoE switch", 76), ("RP2350-POE-ETH + PoE module", 160), ("XIAO ESP32-C5", 90), ("5.8 GHz antenna", 90)]
    links = ["Ethernet: data + power", "7 wires (below)", "u.FL plug"]
    gap = (W - 72 - sum(w for _, w in chain)) / 3
    x = 36
    for i, (name, w) in enumerate(chain):
        c.setFillColor(PANEL); c.setStrokeColor(LINE); c.setLineWidth(0.8)
        c.roundRect(x, y - 9, w, 24, 5, stroke=1, fill=1)
        text(c, name, x + w / 2, y, 8.6, True, align="c")
        x += w
        if i < 3:
            c.setStrokeColor(MUTED); c.setLineWidth(1.2); c.line(x + 5, y + 3, x + gap - 5, y + 3)
            text(c, links[i], x + gap / 2, y + 8, 7.4, color=MUTED, align="c")
            x += gap

    # the two boards
    top, bot = H - 136, 152
    lx0, lx1, rx0, rx1 = 36, 262, 530, 756
    for x0, x1, col, name, sub in ((lx0, lx1, BOARD_RP, "RP2350-POE-ETH", "Timer"), (rx0, rx1, BOARD_XIAO, "XIAO ESP32-C5", "Node")):
        c.setFillColor(PANEL); c.setStrokeColor(LINE); c.setLineWidth(0.8)
        c.roundRect(x0, bot, x1 - x0, top - bot, 8, stroke=1, fill=1)
        c.setFillColor(col)
        c.roundRect(x0, top - 24, x1 - x0, 24, 8, stroke=0, fill=1)
        c.rect(x0, top - 24, x1 - x0, 10, stroke=0, fill=1)
        text(c, name, x0 + 10, top - 16, 10.5, True, white)
        text(c, sub, x1 - 10, top - 16, 8.5, color=white, align="r")
    text(c, "label printed on the board", lx1 - 12, top - 36, 7, color=MUTED, align="r")
    text(c, "label printed on the board", rx0 + 12, top - 36, 7, color=MUTED)

    step = 39.5
    y0 = top - 62
    for i, (sig, col, cname, rl, rd, xl, xd, where, d, note, opt) in enumerate(WIRES):
        y = y0 - i * step
        col = HexColor(col)
        # wire
        c.setStrokeColor(col); c.setLineWidth(3.2); c.setLineCap(1)
        c.setDash([7, 5] if opt else [])
        a, b = lx1 + 7, rx0 - 7
        c.line(a + (9 if d == "<" else 0), y, b - (9 if d == ">" else 0), y)
        c.setDash([])
        if d == ">": arrow(c, b + 1, y, 1, col)
        if d == "<": arrow(c, a - 1, y, -1, col)
        mid = (lx1 + rx0) / 2
        text(c, sig, mid, y + 6.5, 9.2, True, align="c")
        text(c, f"{cname} wire" + (f"  |  {note}" if note else ""), mid, y - 13, 7.4, color=MUTED, align="c")
        # pin stubs
        for px in (lx1, rx0):
            c.setFillColor(PAD); c.setStrokeColor(INK); c.setLineWidth(0.6)
            c.circle(px, y, 5, stroke=1, fill=1)
        # RP side
        text(c, rl, lx1 - 12, y - 1, 13, True, align="r")
        text(c, rd, lx1 - 12, y - 12, 7.6, color=MUTED, align="r")
        # XIAO side
        text(c, xl, rx0 + 12, y - 1, 13, True)
        if xd: text(c, xd, rx0 + 12, y - 12, 7.6, color=MUTED)
        if where == "header": pill(c, "HEADER PIN", rx1 - 10, y - 1, GREEN, GREEN_BG)
        else: pill(c, "SOLDER PAD ON BACK", rx1 - 10, y - 1, AMBER, AMBER_BG)

    # notes
    ny = 138
    cw = (W - 72 - 2 * 18) / 3
    notes = [
        ("Power from Vsys, not Vbus",
         "Waveshare's schematic feeds Vsys from both USB and the PoE module through diodes. "
         "Vbus is only live while the RP2350 board's own USB-C is plugged in, so a Node powered "
         "from Vbus would be dead on PoE."),
        ("SYNC lands on a back pad",
         "The Node firmware as built listens on GPIO2. On the XIAO that is the MTMS pad on the back, "
         "not header pin D2 (D2 is GPIO25). To use a header pin instead, rebuild with "
         "<font face='Courier'>OFT_SYNC_GPIO</font> set to a free one, for example 8 for D8, and move the wire."),
        ("TX goes to RX",
         "The two data wires cross: the Timer's TX (4) feeds the Node's RX (D7), and the Node's TX (D6) "
         "feeds the Timer's RX (5). The dashed wires only matter once the Timer resets or flashes the Node; "
         "skip them to avoid two of the three solder joints."),
    ]
    for i, (h, t) in enumerate(notes):
        x = 36 + i * (cw + 18)
        yy = para(c, h, x, ny, cw, head)
        para(c, t, x, yy - 2, cw)
    c.showPage()


# ---------------------------------------------------------------- page 2
def pin_row(c, x, y, label, side, hot=None, r=4.6, size=7.6):
    """A header hole at (x, y) with its label on the given side; hot = wire colour."""
    if hot:
        c.setFillColor(hot); c.circle(x, y, r + 3.6, stroke=0, fill=1)
    c.setFillColor(PAD); c.setStrokeColor(INK); c.setLineWidth(0.5)
    c.circle(x, y, r, stroke=1, fill=1)
    c.setFillColor(white); c.circle(x, y, r * 0.42, stroke=0, fill=1)
    dx = (r + 8) * (1 if side == "r" else -1)
    text(c, label, x + dx, y - 2.8, size + (1.6 if hot else 0), bool(hot), hot or MUTED, "l" if side == "r" else "r")


def page2(c):
    title(c, "Where the pins are", "Coloured pins are the ones to wire. Go by the labels printed on the boards: turning a board over swaps left and right.", 2)
    col = {w[3]: HexColor(w[1]) for w in WIRES}
    xcol = {w[5]: HexColor(w[1]) for w in WIRES}
    wire_of = {"G": "Ground", "4": "TX, to D7", "5": "RX, from D6", "6": "SYNC, to MTMS",
               "7": "to EN", "8": "to BOOT"}

    # --- RP2350-POE-ETH
    bx, bw, btop, bbot = 112, 96, H - 118, 118
    text(c, "RP2350-POE-ETH", bx + bw / 2, H - 92, 10.5, True, align="c")
    text(c, "label side, USB-C at the top", bx + bw / 2, H - 104, 7.6, color=MUTED, align="c")
    c.setFillColor(BOARD_RP); c.roundRect(bx, bbot, bw, btop - bbot, 6, stroke=0, fill=1)
    c.setFillColor(HexColor("#aeb6bf")); c.roundRect(bx + bw / 2 - 16, btop - 6, 32, 13, 3, stroke=0, fill=1)   # USB-C
    c.roundRect(bx + bw / 2 - 30, bbot - 9, 60, 50, 3, stroke=0, fill=1)                                        # RJ45
    text(c, "RJ45", bx + bw / 2, bbot + 12, 7.5, True, INK, "c")
    left = ["Vbus", "Vsys", "G", "EN", "3V3", "VREF", "28", "G", "27", "26", "RUN", "22", "G", "15", "14", "13"]      # pins 32..17
    right = ["0", "1", "G", "2", "3", "4", "5", "G", "6", "7", "8", "9", "G", "10", "11", "12"]                    # pins 1..16
    step = 18.6
    py0 = btop - 22
    for i, lab in enumerate(left):
        hot = col["Vsys"] if lab == "Vsys" else None
        s = f"{lab}  ({32 - i})" if not hot else f"{lab}  (pin {32 - i})"
        pin_row(c, bx + 9, py0 - i * step, s, "l", hot)
    for i, lab in enumerate(right):
        n = i + 1
        hot = col.get(lab) if (lab != "G" or n == 8) else None
        if lab == "G" and n == 8: hot = col["G"]
        s = f"({n})  {lab}" if not hot else f"{lab}  (pin {n})  {wire_of['G' if lab == 'G' else lab]}"
        pin_row(c, bx + bw - 9, py0 - i * step, s, "r", hot)

    # --- XIAO front
    fx, fw, ftop, fbot = 404, 92, H - 118, H - 262
    text(c, "XIAO ESP32-C5, front", fx + fw / 2, H - 92, 10.5, True, align="c")
    text(c, "component side, USB-C at the top", fx + fw / 2, H - 104, 7.6, color=MUTED, align="c")
    c.setFillColor(BOARD_XIAO); c.roundRect(fx, fbot, fw, ftop - fbot, 9, stroke=0, fill=1)
    c.setFillColor(HexColor("#aeb6bf")); c.roundRect(fx + fw / 2 - 17, ftop - 22, 34, 30, 3, stroke=0, fill=1)
    c.setFillColor(HexColor("#d8dde2")); c.roundRect(fx + 20, fbot + 34, fw - 40, 58, 3, stroke=0, fill=1)
    text(c, "shield can", fx + fw / 2, fbot + 60, 6.6, color=MUTED, align="c")
    c.setFillColor(PAD); c.circle(fx + fw / 2, fbot + 14, 6, stroke=0, fill=1)
    text(c, "u.FL", fx + fw / 2, fbot + 24, 6.2, color=white, align="c")
    for bx_, lab in ((fx + 24, "R"), (fx + fw - 24, "B")):
        c.setFillColor(HexColor("#8b949e")); c.rect(bx_ - 6, fbot + 8, 12, 12, stroke=0, fill=1)
        text(c, lab, bx_, fbot + 11, 6.4, True, white, "c")
    fl = ["D0", "D1", "D2", "D3", "D4", "D5", "D6"]
    fr = ["5V", "GND", "3V3", "D10", "D9", "D8", "D7"]
    fstep = 18.6
    fy0 = ftop - 18
    names = {"5V": "5 V power", "GND": "Ground", "D7": "from Timer 4", "D6": "to Timer 5"}
    for i, lab in enumerate(fl):
        hot = xcol.get(lab)
        pin_row(c, fx + 7, fy0 - i * fstep, f"{names[lab]}  {lab}" if hot else lab, "l", hot)
    for i, lab in enumerate(fr):
        hot = xcol.get(lab)
        pin_row(c, fx + fw - 7, fy0 - i * fstep, f"{lab}  {names[lab]}" if hot else lab, "r", hot)
    text(c, "R = reset button, B = boot button", fx + fw / 2, fbot - 12, 7, color=MUTED, align="c")

    # --- XIAO back
    kx, kw, ktop, kbot = 404, 92, H - 318, H - 462
    text(c, "XIAO ESP32-C5, back", kx + kw / 2, H - 292, 10.5, True, align="c")
    text(c, "flipped left to right, USB-C still at the top", kx + kw / 2, H - 304, 7.6, color=MUTED, align="c")
    c.setFillColor(BOARD_XIAO); c.roundRect(kx, kbot, kw, ktop - kbot, 9, stroke=0, fill=1)
    c.setFillColor(HexColor("#aeb6bf")); c.roundRect(kx + kw / 2 - 17, ktop - 2, 34, 9, 3, stroke=0, fill=1)
    for i in range(7):
        for px in (kx + 7, kx + kw - 7):
            c.setFillColor(PAD); c.circle(px, ktop - 18 - i * fstep, 3.6, stroke=0, fill=1)
    padl = ["MTDO", "GND", "MTCK", "3V3"]
    padr = ["MTDI", "EN", "MTMS", "BOOT"]
    pnames = {"EN": "from Timer 7", "MTMS": "from Timer 6", "BOOT": "from Timer 8"}
    for i in range(4):
        y = ktop - 22 - i * 19
        for px, lab, side in ((kx + kw / 2 - 9, padl[i], "l"), (kx + kw / 2 + 9, padr[i], "r")):
            hot = xcol.get(lab) if side == "r" else None
            if hot:
                c.setFillColor(hot); c.circle(px, y, 7.4, stroke=0, fill=1)
            c.setFillColor(PAD); c.setStrokeColor(INK); c.setLineWidth(0.5); c.circle(px, y, 4.2, stroke=1, fill=1)
            if side == "l":
                text(c, lab, kx - 8, y - 2.8, 7.6, color=MUTED, align="r")
                c.setStrokeColor(LINE); c.setLineWidth(0.6); c.line(kx - 5, y, px - 6, y)
            else:
                s = f"{lab}  {pnames[lab]}" if hot else lab
                text(c, s, kx + kw + 8, y - 2.8, 9.2 if hot else 7.6, bool(hot), hot or MUTED)
                c.setStrokeColor(hot or LINE); c.setLineWidth(1.2 if hot else 0.6); c.line(px + (8 if hot else 6), y, kx + kw + 5, y)
    text(c, "BAT - / +", kx + kw / 2, kbot + 22, 6.6, color=HexColor("#aeb6bf"), align="c")
    text(c, "8 round pads in two columns between the headers", kx + kw / 2, kbot - 12, 7, color=MUTED, align="c")

    # --- right column: other connections and cautions
    x, w = 606, W - 36 - 606
    y = H - 88
    y = para(c, "Other connections", x, y, w, head)
    for t in (
        "<b>PoE module</b> (in the kit): plug it onto the RP2350 board.",
        "<b>Ethernet</b>: RJ45 to a PoE port on the switch. The module's PoE standard is still to confirm (HBOM).",
        "<b>Antenna</b>: 5.8 GHz u.FL antenna onto the XIAO's u.FL socket.",
        "<b>USB-C, only for flashing</b>: RP2350 board (hold BOOT, copy the .uf2); XIAO (esptool).",
    ):
        y = para(c, t, x, y - 5, w)
    y = para(c, "Before you power it", x, y - 16, w, head)
    for t in (
        "<b>Leave the XIAO's buttons alone</b> once the reset and boot wires are on: the Timer drives both lines high, "
        "and a button press pulls against that output.",
        "<b>XIAO USB joins the 5 V rails.</b> Its 5V pin is wired straight to its USB socket, so a laptop on the XIAO "
        "also feeds Vsys and runs both boards. Unplug PoE first, or lift the red wire.",
        "<b>Power both boards together.</b> A powered board driving the data pins of an unpowered one feeds current "
        "through its protection diodes.",
        "<b>Keep the wires short</b> and bring them through the foil wall between the boards (HBOM box rules).",
        "<b>Not yet run on hardware.</b> Pin choices come from the firmware sources and the vendors' pinout drawings; "
        "check each label on the real boards as you go.",
    ):
        y = para(c, t, x, y - 5, w)

    para(c, "Sources: oft-timer-rp2350/src/board.rs and main.rs; oft-node-c5/firmware/src/proto/oft.h; "
            "oft-spec/hbom-b1-single-pilot.md; Waveshare RP2350-POE-ETH pinout drawing and schematic; "
            "Seeed XIAO ESP32-C5 front and back pinout drawings.", 36, 58, W - 72, small)
    c.showPage()


c = canvas.Canvas(OUT, pagesize=(W, H))
c.setTitle("OFT B1 gate timer wiring")
c.setAuthor("Open FPV Timer")
page1(c)
page2(c)
c.save()
