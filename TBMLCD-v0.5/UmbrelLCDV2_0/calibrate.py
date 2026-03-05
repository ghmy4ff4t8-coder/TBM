#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# calibrate.py  –  TBM LCD Coordinate Calibration Tool
#
# Usage:
#   sudo python3 calibrate.py
#
# This script displays each background image on the LCD with x-coordinate
# markers overlaid. Take a photo of each screen and send it to identify
# exactly where each x position appears on the physical display.
#
# Each screen shows:
#   - The background image (rotated the same way as UmbrelLCD.py)
#   - Horizontal lines at x=20, 40, 60, 80, 100, 120 with x labels
#   - Sample data text at candidate positions
#
# Press Ctrl+C to stop.
# ---------------------------------------------------------------------------

from PIL import Image, ImageDraw, ImageFont
import time
import pathlib
import os
import sys

from st7735_tbm import ST7735

basedir = os.path.abspath(os.path.dirname(__file__))

WIDTH  = 128
HEIGHT = 160

DC         = 24
RST        = 25
SPI_PORT   = 0
SPI_DEVICE = 0

disp = ST7735(
    port=SPI_PORT, cs=SPI_DEVICE, dc=DC, rst=RST,
    width=128, height=160,
    offset_left=0, offset_top=0,
    spi_speed_hz=16000000,
    invert=False, bgr=True
)

filePath     = str(pathlib.Path(__file__).parent.absolute())
images_path  = filePath + '/images/'
fonts_path   = filePath + '/poppins/'

def load_font(size):
    try:
        return ImageFont.truetype(fonts_path + "Poppins-Bold.ttf", size)
    except Exception:
        return ImageFont.load_default()

def make_text_image(text, font, fill=(255, 255, 255)):
    tmp = Image.new('RGBA', (1, 1))
    tmp_draw = ImageDraw.Draw(tmp)
    try:
        bbox = tmp_draw.textbbox((0, 0), text, font=font)
        x_off, y_off = -bbox[0], -bbox[1]
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
    except AttributeError:
        w, h = tmp_draw.textsize(text, font=font)
        x_off, y_off = 0, 0
    h_margin = max(4, int(h * 0.15))
    img = Image.new('RGBA', (max(w, 1), max(h + h_margin, 1)), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((x_off, y_off), text, font=font, fill=fill)
    return img

def put_text(buf, text, x, y, font, fill=(255, 255, 255)):
    """Draw text rotated 90° at position (x, y) in the buffer."""
    ti = make_text_image(text, font, fill)
    rotated = ti.rotate(90, expand=True)
    buf.paste(rotated, (x, y), rotated)

def load_bg(image_name, rotate_deg=90):
    """Load background image, resize to 160x128, rotate, return 128x160 image."""
    path = images_path + image_name
    img = Image.open(path).convert('RGBA')
    img = img.resize((160, 128), Image.BICUBIC)
    rotated = img.rotate(rotate_deg, expand=True)   # → 128×160
    buf = Image.new('RGB', (WIDTH, HEIGHT))
    buf.paste(rotated, (0, 0), rotated)
    return buf

def draw_grid(buf, x_marks, color=(255, 255, 0)):
    """Draw horizontal lines at each x position with x label."""
    d = ImageDraw.Draw(buf)
    label_font = load_font(8)
    for x in x_marks:
        if 0 <= x < WIDTH:
            # Draw a horizontal line across the full width at this x
            d.line([(x, 0), (x, HEIGHT - 1)], fill=color, width=1)
            # Label the x value at the left edge
            label = str(x)
            ti = make_text_image(label, label_font, fill=color)
            rt = ti.rotate(90, expand=True)
            # Paste label slightly to the right of the line
            lx = min(x + 1, WIDTH - rt.size[0] - 1)
            buf.paste(rt, (lx, 2), rt)
    return buf

def show(buf):
    disp.display(buf)

# ---------------------------------------------------------------------------
# Screen definitions: each entry is (title, bg_image, rotate_deg, samples)
# samples = list of (x, y, text, font_size, color)
# ---------------------------------------------------------------------------
SCREENS = [
    {
        "title": "1. Payment Channels",
        "bg": "payment_channels.png",
        "rotate": 90,
        "grid": [20, 40, 60, 80, 87, 100, 107, 120],
        "samples": [
            # Test values at candidate positions
            (87, 10,  "11",      16, (0, 255, 0)),   # Connections top
            (87, 90,  "8",       16, (0, 255, 0)),   # Active bottom
            (107, 10, "500k",    11, (255, 128, 0)), # MaxReceive top
            (107, 90, "300k",    11, (255, 128, 0)), # MaxSend bottom
        ],
    },
    {
        "title": "2. Network",
        "bg": "network.png",
        "rotate": 90,
        "grid": [20, 40, 60, 80, 88, 100, 108, 120],
        "samples": [
            (88, 10,  "11",      16, (0, 255, 0)),   # Connections top
            (88, 90,  "816MB",   12, (0, 255, 0)),   # Mempool bottom
            (108, 10, "457GB",   12, (255, 128, 0)), # Blockchain top
            (108, 90, "240EH",   12, (255, 128, 0)), # Hashrate bottom
        ],
    },
    {
        "title": "3. Block Height",
        "bg": "Block_HeightBG.png",
        "rotate": 90,
        "grid": [5, 20, 40, 60, 67, 80, 100],
        "samples": [
            (67, 30, "939290", 22, (0, 255, 0)),  # block number candidate
        ],
    },
    {
        "title": "4. Storage",
        "bg": "storage.png",
        "rotate": 90,
        "grid": [20, 40, 47, 60, 75, 92, 108],
        "samples": [
            (47, 5,  "929.1GB",        20, (0, 255, 0)),
            (75, 5,  "Used of 2.0TB",  12, (0, 200, 255)),
            (92, 5,  "1.0TB avail",    12, (255, 128, 0)),
        ],
    },
    {
        "title": "5. Transactions",
        "bg": "TxsBG.png",
        "rotate": 90,
        "grid": [5, 20, 30, 50, 65, 72, 90, 110],
        "samples": [
            (5,  5,  "34133", 20, (0, 255, 0)),   # unconfirmed
            (30, 5,  "3876",  20, (0, 200, 255)), # next block txs
            (72, 10, "4",     50, (255, 128, 0)), # fee low
            (72, 100,"1",     50, (255, 0, 128)), # fee high
        ],
    },
    {
        "title": "6. Logo",
        "bg": "umbrel_logo.png",
        "rotate": 90,
        "grid": [],
        "samples": [],
    },
]

# ---------------------------------------------------------------------------
# Main: cycle through each screen, hold for 8 seconds
# ---------------------------------------------------------------------------
print("TBM LCD Calibration Tool")
print("Each screen will display for 8 seconds.")
print("Take a photo of each screen and send it for coordinate analysis.")
print("Press Ctrl+C to stop.\n")

font_label = load_font(9)

while True:
    for screen in SCREENS:
        print(f"Showing: {screen['title']}")

        # Load background
        buf = load_bg(screen["bg"], screen["rotate"])

        # Draw coordinate grid
        draw_grid(buf, screen["grid"])

        # Draw sample text at candidate positions
        for (x, y, text, fs, color) in screen["samples"]:
            put_text(buf, text, x, y, load_font(fs), fill=color)

        # Show on LCD
        show(buf)
        time.sleep(8)
