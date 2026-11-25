#!/usr/bin/env python3
"""THE WORLD - front page for Wednesday, 25 November 2026.

Draws a broadsheet newspaper front page (1024x1024 PNG) summing up the
world news of 25 November 2026, using only the Python standard library.

Everything is drawn by hand in this file: a small built-in 5x7 bitmap font
(defined below), rectangle / line / circle primitives on a raw RGB buffer,
and a hand-written PNG encoder (zlib + struct). No fonts, no files, no
network, no randomness, no timestamps - the output is byte-identical on
every run.

Run:  MAKEFUN_OUTPUT_DIR=out python3 main.py   (writes out/entry.png)
"""

import os
import struct
import zlib

W = 1024
H = 1024

PAPER = (247, 243, 232)   # off-white broadsheet paper
INK = (18, 18, 18)        # black ink
GREY = (74, 74, 74)       # deck / secondary text
RED = (176, 32, 32)       # single red accent
SKY = (198, 220, 231)     # scene sky
SKY2 = (214, 230, 238)    # scene sky, lighter band
SEA = (44, 92, 120)       # scene sea
SEA2 = (34, 74, 98)       # scene sea, darker band
SUN = (242, 214, 130)     # pale sun
HULL = (34, 38, 43)       # ship hull
BLAST = (232, 116, 40)    # explosion orange
SMOKE = (120, 120, 118)   # smoke grey
WAVE = (235, 244, 248)    # wave foam

# ---------------------------------------------------------------------------
# 5x7 bitmap font. Each glyph is 7 rows of 5 characters; '#' is ink.
# Only capitals, digits and the punctuation used by the headlines are needed
# because every string in this page is written in capitals.
# ---------------------------------------------------------------------------
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "01100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "+": ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
}

CHAR_W = 6  # glyph advance in font units (5 px glyph + 1 px gap)


class Canvas:
    """A plain RGB pixel buffer with tiny drawing primitives."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(w * h * 3)
        self.clip = None
        self.fill_rect(0, 0, w, h, bg)

    def set_clip(self, rect):
        """Restrict drawing to rect (x, y, w, h); None removes the clip."""
        if rect is None:
            self.clip = None
        else:
            x, y, w, h = rect
            self.clip = (x, y, x + w, y + h)

    def set(self, x, y, color):
        if self.clip is not None:
            cx0, cy0, cx1, cy1 = self.clip
            if not (cx0 <= x < cx1 and cy0 <= y < cy1):
                return
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = color[0]
            self.px[i + 1] = color[1]
            self.px[i + 2] = color[2]

    def fill_rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if self.clip is not None:
            cx0, cy0, cx1, cy1 = self.clip
            x0 = max(x0, cx0)
            y0 = max(y0, cy0)
            x1 = min(x1, cx1)
            y1 = min(y1, cy1)
        r, g, b = color
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.px[i] = r
                self.px[i + 1] = g
                self.px[i + 2] = b

    def hline(self, x, y, w, color, thick=1):
        self.fill_rect(x, y, w, thick, color)

    def vline(self, x, y, h, color, thick=1):
        self.fill_rect(x, y, thick, h, color)

    def frame(self, x, y, w, h, color, thick=1):
        self.hline(x, y, w, color, thick)
        self.hline(x, y + h - thick, w, color, thick)
        self.vline(x, y, h, color, thick)
        self.vline(x + w - thick, y, h, color, thick)

    def line(self, x0, y0, x1, y1, color):
        # Bresenham line, deterministic.
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            self.set(x, y, color)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def disc(self, cx, cy, r, color):
        # Filled circle.
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) * (xx - cx) + (yy - cy) * (yy - cy) <= r * r:
                    self.set(xx, yy, color)

    def ring(self, cx, cy, r, color):
        # Thin circle outline.
        for deg in range(0, 360, 2):
            import math
            a = math.radians(deg)
            self.set(cx + int(r * math.cos(a)), cy + int(r * math.sin(a)), color)

    # -- text ---------------------------------------------------------------
    def text_width(self, text, scale):
        return len(text) * CHAR_W * scale - scale

    def text(self, x, y, text, scale, color):
        cx = x
        for ch in text:
            glyph = FONT.get(ch, FONT[" "])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "1":
                        self.fill_rect(
                            cx + col * scale, y + row * scale, scale, scale, color
                        )
            cx += CHAR_W * scale
        return cx

    def text_centered(self, y, text, scale, color):
        x = (self.w - self.text_width(text, scale)) // 2
        self.text(x, y, text, scale, color)

    def wrap(self, text, max_width, scale):
        """Greedy word wrap; returns a list of lines fitting max_width."""
        limit = max_width // (CHAR_W * scale)
        lines = []
        for para in text.split("\n"):
            words = para.split(" ")
            cur = ""
            for word in words:
                trial = word if not cur else cur + " " + word
                if len(trial) <= limit:
                    cur = trial
                else:
                    if cur:
                        lines.append(cur)
                    cur = word
            if cur:
                lines.append(cur)
        return lines

    def paragraph(self, x, y, text, max_width, scale, color, line_h=None):
        """Draw wrapped text; returns the y just below the last line."""
        if line_h is None:
            line_h = 7 * scale + 4
        for line in self.wrap(text, max_width, scale):
            self.text(x, y, line, scale, color)
            y += line_h
        return y


# ---------------------------------------------------------------------------
# The scene: a cargo ship at sea under a drone, Gulf of Finland.
# ---------------------------------------------------------------------------
def draw_scene(cv, x, y, w, h):
    # Clip everything to the panel so no motif can spill onto the text.
    cv.set_clip((x, y, w, h))
    horizon = y + int(h * 0.58)
    cv.fill_rect(x, y, w, horizon - y, SKY)
    cv.fill_rect(x, y + int(h * 0.30), w, horizon - (y + int(h * 0.30)), SKY2)
    cv.fill_rect(x, horizon, w, y + h - horizon, SEA)
    cv.fill_rect(x, horizon + 34, w, y + h - (horizon + 34), SEA2)
    # Pale sun, upper right.
    cv.disc(x + w - 110, y + 34, 24, SUN)
    cv.ring(x + w - 110, y + 34, 30, (240, 226, 170))
    # Birds.
    for bx, by in ((x + 120, y + 26), (x + 170, y + 40), (x + 210, y + 22)):
        cv.line(bx - 8, by, bx, by - 5, INK)
        cv.line(bx, by - 5, bx + 8, by, INK)
    # Drone: small quadcopter high above the ship, left of centre.
    dx, dy = x + 250, y + 18
    cv.fill_rect(dx - 14, dy, 28, 7, INK)
    cv.fill_rect(dx - 4, dy + 7, 8, 6, INK)
    cv.hline(dx - 30, dy - 3, 60, INK, 2)
    cv.fill_rect(dx - 34, dy - 6, 12, 3, INK)
    cv.fill_rect(dx + 22, dy - 6, 12, 3, INK)
    cv.line(dx - 10, dy + 13, dx - 16, dy + 24, INK)
    cv.line(dx + 10, dy + 13, dx + 16, dy + 24, INK)
    # Smoke plume rising from the ship's mid-deck, kept inside the panel.
    sx = x + 470
    for i, (ox, oy, r) in enumerate(((0, 0, 14), (-12, -10, 11), (9, -16, 12),
                                     (-3, -24, 9), (10, -30, 8))):
        cv.disc(sx + ox, horizon - 52 + oy, r, SMOKE)
    # Explosion burst at the bow, above the deck.
    ex, ey = x + 725, horizon - 26
    for r, col in ((26, BLAST), (18, (240, 160, 60)), (10, (250, 220, 120))):
        cv.disc(ex, ey, r, col)
    for ang in range(0, 360, 30):
        import math
        a = math.radians(ang)
        cv.line(ex, ey, ex + int(42 * math.cos(a)), ey + int(42 * math.sin(a)), BLAST)
    # Containers stacked on deck.
    cont_y = horizon - 52
    cont_cols = [(176, 60, 48), (52, 110, 160), (200, 170, 60), (60, 130, 90)]
    for i in range(4):
        cx = x + 330 + i * 62
        cv.fill_rect(cx, cont_y, 58, 26, cont_cols[i % 4])
        cv.frame(cx, cont_y, 58, 26, INK, 1)
        cv.fill_rect(cx, cont_y + 26, 58, 26, cont_cols[(i + 2) % 4])
        cv.frame(cx, cont_y + 26, 58, 26, INK, 1)
    # Funnel with a red band, standing on the deck behind the containers.
    cv.fill_rect(x + 600, horizon - 64, 30, 64, INK)
    cv.fill_rect(x + 600, horizon - 56, 30, 8, RED)
    # Hull: long dark hull with a raked bow.
    hull_y = horizon
    cv.fill_rect(x + 300, hull_y, 420, 30, HULL)
    cv.line(x + 720, hull_y, x + 760, hull_y + 30, HULL)
    cv.line(x + 720, hull_y + 1, x + 758, hull_y + 30, HULL)
    cv.fill_rect(x + 720, hull_y, 40, 30, HULL)
    cv.hline(x + 300, hull_y + 30, 460, RED, 3)
    # Portholes.
    for px in range(x + 320, x + 700, 34):
        cv.disc(px, hull_y + 14, 4, (220, 225, 228))
    # Waves.
    for wy in (horizon + 30, horizon + 48):
        for wx in range(x + 20, x + w - 60, 90):
            cv.hline(wx, wy, 52, WAVE, 2)
            cv.hline(wx + 12, wy + 5, 28, WAVE, 2)
    cv.set_clip(None)


# ---------------------------------------------------------------------------
# PNG encoder (zlib + struct only). Deterministic: fixed compression level,
# no ancillary chunks, no timestamps.
# ---------------------------------------------------------------------------
def chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def encode_png(cv):
    raw = bytearray()
    for yy in range(cv.h):
        raw.append(0)  # filter: none
        start = yy * cv.w * 3
        raw += cv.px[start:start + cv.w * 3]
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    return png


# ---------------------------------------------------------------------------
# Page layout. All story text below is the verified news of 25 Nov 2026.
# ---------------------------------------------------------------------------
def build_page():
    cv = Canvas(W, H, PAPER)
    M = 28                      # margin
    CW = W - 2 * M              # content width = 968

    # Masthead.
    cv.text_centered(22, "THE WORLD", 12, INK)
    cv.hline(M, 118, CW, RED, 3)
    cv.text_centered(130, "WEDNESDAY, 25 NOVEMBER 2026", 3, INK)
    cv.hline(M, 160, CW, INK, 2)
    cv.hline(M, 166, CW, RED, 5)

    # Lead kicker + headline + deck.
    cv.text(M, 182, "LEAD STORY - THE GULF OF FINLAND", 2, RED)
    y = 206
    for line in ("UKRAINE DRONE STRIKE HITS",
                 "RUSSIAN CARGO SHIP IN THE",
                 "GULF OF FINLAND"):
        cv.text(M, y, line, 4, INK)
        y += 34
    y = cv.paragraph(
        M, 314,
        "ZELENSKIY CONFIRMS SATURDAY STRIKE. NORWAY URGES CAUTION AS "
        "BALTIC TENSIONS RISE AFTER THE ATTACK.",
        CW, 2, GREY)

    # Scene panel.
    scene_y = 352
    scene_h = 158
    draw_scene(cv, M, scene_y, CW, scene_h)
    cv.frame(M, scene_y, CW, scene_h, INK, 2)
    cv.paragraph(
        M, scene_y + scene_h + 10,
        "A DRONE STRIKE ON A RUSSIAN CARGO SHIP IN THE GULF OF FINLAND.",
        CW, 2, GREY)

    # Rule above the columns.
    cv.hline(M, 552, CW, INK, 2)

    # Two columns.
    left_x = M
    right_x = M + 496
    col_w = 472
    cv.vline(M + 484, 566, 316, INK, 1)

    def section_header(x, y, title):
        cv.text(x, y, title, 2, RED)
        cv.hline(x, y + 18, col_w, RED, 2)
        return y + 28

    def story(x, y, headline, deck):
        y = cv.paragraph(x, y, headline, col_w, 2, INK, 18)
        if deck:
            y = cv.paragraph(x, y, deck, col_w, 2, GREY, 18)
        return y + 10

    # LEFT: WORLD.
    y = section_header(left_x, 566, "WORLD")
    y = story(left_x, y,
              "UKRAINE SINKS RUSSIAN NAVAL VESSEL IN LIBYAN PORT",
              "SUNDAY SINKING PUTS LIBYA FROZEN CONFLICT AT RISK")
    y = story(left_x, y,
              "IRAN NAVY SAYS THREE TANKERS HIT BY MINES IN HORMUZ",
              "CLAIM RAISES FEARS FOR GULF SHIPPING")
    y = story(left_x, y,
              "HOUTHIS PUSH TO WITHIN 60 KM OF ADEN",
              "DRONE ATTACK ON RIYADH TOWER HURTS 11")
    y = story(left_x, y,
              "NATO TO SEND EARLY-WARNING JETS TO POLAND",
              "MISSILES LANDED IN POLAND IN ATTACK")
    y = story(left_x, y,
              "SARKOZY CASE ORDERED TO TRIAL",
              "EX-PRESIDENT AND WIFE CARLA BRUNI")

    # RIGHT: MARKETS, LAW AND TECH, SPORT.
    y = section_header(right_x, 566, "MARKETS")
    y = story(right_x, y,
              "SENSEX SLUMPS 1,484 POINTS",
              "NIFTY FALLS BELOW 25,400")
    y = story(right_x, y,
              "ANTHROPIC SHARES SLIDE BELOW $83 IPO PRICE",
              "SHARES TUMBLE BELOW LISTING PRICE")
    y = section_header(right_x, y, "LAW AND TECH")
    y = story(right_x, y,
              "HUAWEI CONVICTED IN US TRIAL OVER IRAN BUSINESS",
              "GUILTY ON TRADE SECRETS")
    y = story(right_x, y,
              "TRUMP GIVES GIULIANI MEDAL OF FREEDOM",
              "HIGHEST CIVILIAN HONOUR")
    y = section_header(right_x, y, "SPORT")
    y = story(right_x, y,
              "ENGLAND BEAT AUSTRALIA BY 8 WICKETS IN 2ND T20I",
              "CHASING 185 - FRASER-MCGURK 27 OFF 13")

    # ALSO TODAY strip.
    strip_y = 890
    cv.hline(M, strip_y, CW, RED, 3)
    cv.text(M, strip_y + 12, "ALSO TODAY", 2, RED)
    cv.paragraph(
        M, strip_y + 34,
        "CIA AND ODNI HIT BY CYBER BREACH - 5.6 QUAKE HITS NEPAL - "
        "BJP AND AKALI DAL REUNITE FOR 2027 PUNJAB POLLS - NEPAL PM "
        "SHAH ENDS INDIA VISIT - 25 NOV IS THE DAY AGAINST VIOLENCE "
        "AGAINST WOMEN - GTA 6 OUT SINCE 19 NOV",
        CW, 2, INK)

    # Footer: the day, named again.
    cv.hline(M, 990, CW, INK, 2)
    cv.text_centered(996, "THE WORLD - WEDNESDAY, 25 NOVEMBER 2026", 2, INK)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    cv = build_page()
    data = encode_png(cv)
    with open(os.path.join(out_dir, "entry.png"), "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
