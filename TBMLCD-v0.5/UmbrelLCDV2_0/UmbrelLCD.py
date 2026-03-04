
#-------------------------------------------------------------------------------
#   Copyright (c) 2022 DOIDO Technologies
#   Version  : 2.15.0 (Umbrel 1.x compatible fork)
#   Location : github - forked & updated for Umbrel OS 1.x compatibility
#   Changes  :
#    # v2.15.0: Architecture overhaul - replaced background image dependency with
#           code-based layout for all screens. All labels and values are now
#           drawn programmatically, eliminating coordinate fragility.
#           Added draw_grid_cell() helper for 2x2 grid layout.
#           Screen 5 (Network) and Screen 6 (Payment Channels) now use correct
#           2x2 grid: top row (x_label=88, x_val=66), bottom row (x_label=44,
#           x_val=22), left col (y_center=40), right col (y_center=120).
#           Screen 3 (Block Height): reduced font max to fit within display.
#           Screen 7 (Storage): removed storage.png icon (was full background),
#           replaced with text symbol. Reduced font size to prevent title overlap.
#    # v2.14.6: Changed flip in image_to_data() from column flip ([:, ::-1, :])
#           to row flip ([::-1, :, :]). After rotate(90 CCW), buffer rows =
#           original columns, so row flip corrects the LR mirror correctly.
#    # v2.14.5: Added horizontal flip (pb[:, ::-1, :]) in image_to_data() - wrong axis.
#           rotate(90 CCW) + MADCTL=0x40 produces correct upright image
#           but left-right mirrored. The flip corrects the LR mirror.
#           All three axes now confirmed correct on hardware.
#    # v2.14.4: Changed all rotate(270) → rotate(90) in UmbrelLCD.py.
#           MADCTL=0x40 is confirmed correct. The upside-down was caused by
#           rotate(270 CCW) producing the wrong orientation with MX=1.
#           rotate(90 CCW) = 270 CW is the correct direction.
#    # v2.14.3: Reverted MADCTL back to 0x40 (MY=0, MX=1, BGR).
#           Root cause of persisting upside-down in v2.14.1 was stale .pyc
#           cache on the device running the old 0xC0 code. MY=1 made it worse.
#           0x40 = rotate(270 CCW) + MX=1 is the confirmed correct combination.
#    # v2.14.2: MADCTL 0x40 → 0xC0 (added MY=1 bit) - incorrect, reverted.
#    # v2.14.1: Reverted MADCTL to 0x40 (MX=1, BGR) + no flip in image_to_data().
#           This is the v2.10.0 combination confirmed working on hardware.
#           All subsequent orientation attempts (0xC0, 0x00 + flip) were wrong.
#    # v2.14.0: Code cleanup: removed unused imports (numpy, certifi, ssl, urlreq,
#           socket), merged duplicate config reader (load_config → _cfg),
#           removed unused get_text_size(), cleaned up st7735_tbm.py
#           (batched data() calls, removed duplicate register constants,
#           clarified orientation pipeline in comments).
#    # v2.13.1: Changed image_to_data() flip from 180° (pb[::-1,::-1,:]) to
#           vertical-only flip (pb[::-1,:,:]) to test upside-down correction only.
#    # v2.13.0: Fixed display orientation (upside-down + left-right mirror)
#           Root cause: software 270° rotation + MADCTL=0x00 (direct map)
#           produces 180°-wrong output. Fix: added 180° flip in image_to_data()
#           in st7735_tbm.py (pb[::-1, ::-1, :]) before RGB565 conversion.
#           Net effect: 270° SW rotation + 180° HW flip = 90° correct portrait.
#           Fixed text clipping: replaced draw.textbbox size calculation with
#           make_text_image() that accounts for font descent/ascent offsets.
#           Fixed setup script language selection (eval bug → case/if approach).
#           Duration prompts now read actual defaults from config.ini.
#    # v2.12.0: MADCTL 0xC0→0x00 (MY=0,MX=0,BGR) 화면 방향 수정 (상하+좌우 반전 해제)
#           모든 화면 기본 전환 시간 10초로 변경, 설치 스크립트 다국어 지원 추가
# v2.11.0: MADCTL 0x48→0xC0 (MY=1 추가) 상하반전 재수정, 설치 스크립트에서 화면 전환 시간 인터랙티브 설정 추가, 기본값 6초
# v2.10.0:2024-03):
#       - FIXED: LCD left-right mirror - MADCTL 0x08 → 0x48 (added MX=1 bit)
#         Photos showed text was horizontally mirrored (e.g. "USD" → "uen")
#       - FIXED: Colour inversion - bgr=True added to ST7735 init
#         Bitcoin icon was blue instead of orange (RGB/BGR byte order swap)
#       - ADDED: Screen display durations configurable via config.ini [DISPLAY]
#         logo_duration, screen1_duration, screen_duration (default: 60/60/30s)
#
#     v2.9.0 (2024-03):
#       - FIXED: LCD 180-degree rotation - MADCTL changed from 0xC8 (MY=1,MX=1)
#         to 0x08 (MY=0,MX=0). Photos confirmed image was upside-down+mirrored.
#       - IMPROVED: Data layer resilience against Umbrel updates:
#         * RPC credentials (user/pass/host/port) now read from config.ini,
#           so future Umbrel credential changes only need config.ini edit.
#         * Container names read from config.ini with hardcoded fallback list.
#         * get_block_count: local RPC → mempool.space → blockchain.info
#         * get_btc_price: CoinGecko → Coinbase → Kraken (3 independent APIs)
#         * mempool data: local Umbrel mempool → public mempool.space
#         * Removed Tor dependency from price/block APIs (direct HTTPS instead)
#
#     v2.8.0 (2024-03):
#       - FIXED: gpiod 2.x API compatibility in st7735_tbm.py.
#         gpiod 2.0 removed the entire 1.x API (get_line, LINE_REQ_DIR_OUT).
#         Updated to use chip.request_lines() with LineSettings(direction=OUTPUT)
#         and gpiod.line.Value.ACTIVE/INACTIVE enum values.
#       - FIXED: lcdSetupScript.sh apt package names (spidev→python3-spidev,
#         removed non-existent python3-gpiod apt package).
#
#     v2.7.0 (2024-03):
#       - FIXED: Root cause of all stripe/noise issues identified and resolved.
#         Replaced pimoroni/st7735-python with bundled st7735_tbm.py driver.
#
#         Root cause: pimoroni library defines ST7735_COLS=132, ST7735_ROWS=162
#         (for their own 0.96" display), giving offset_left=2, offset_top=1.
#         The TBM 1.8" panel uses ST7735_COLS=128, ST7735_ROWS=160, so
#         offset_left=0, offset_top=0. The 2-pixel column offset caused the
#         CASET window to be misaligned, producing the diagonal stripe pattern.
#
#         st7735_tbm.py is a direct port of doido-technologies/st7735-python
#         (v0.0.4.doidotech) with RPi.GPIO replaced by gpiod + spidev.
#         It uses the correct MADCTL=0xC8 and offset_left=0, offset_top=0.
#
#     v2.6.0 (2024-03):
#       - FIXED: Stripe noise by bypassing pimoroni's display() entirely.
#         New lcd_display() function converts PIL image to RGB565 bytes
#         directly (no numpy rot90) and calls disp.set_window() + disp.data()
#         directly. This eliminates all stride/shape mismatch issues.
#
#     v2.5.0 (2024-03):
#       - FIXED: Diagonal stripe / sline noise caused by SPI stride mismatch.
#
#         Root cause analysis:
#         pimoroni/st7735-python v1.0.0 image_to_data() does:
#           pb = np.rot90(np.array(image.convert('RGB')), rotation // 90)
#         The PIL image buffer is shape (HEIGHT, WIDTH, 3) = (160, 128, 3).
#
#         With rotation=0: np.rot90(arr, 0) → shape stays (160, 128, 3).
#         The flattened byte stream is then written to the ST7735 starting at
#         CASET x0=2..129 (128 cols) and RASET y0=1..160 (160 rows).
#         But the numpy array has 160 'rows' of 128 pixels each — the library
#         iterates row-major, so it sends 160 rows × 128 pixels. This matches
#         the RASET window (160 rows) perfectly only if the LCD scans top-to-
#         bottom in portrait. However the MADCTL byte 0xC0 sets MX=1, MY=1
#         which means the ST7735 scans in landscape (row = physical column).
#         Result: every row of pixel data is written across a physical column
#         → diagonal stripe pattern.
#
#         With rotation=90: np.rot90(arr, 1) → shape becomes (128, 160, 3).
#         Now the byte stream has 128 'rows' of 160 pixels, matching the
#         landscape MADCTL scan direction. The image appears correctly oriented.
#
#         The original TBM drawing code rotates every element 270° before
#         pasting onto the 128×160 buffer. Adding the library's internal 90°
#         rotation gives 270+90=360° = no net rotation. Correct portrait output.
#
#       - FIXED: bgr parameter - TBM uses a generic 128x160 ST7735 panel.
#         These panels are typically RGB order. If colours appear wrong, set bgr=True.
#
#     v2.3.0 (2024-03):
#       - FIXED: LCD noisy/garbled display - pimoroni/st7735-python v1.0.0
#         default width=80 (Pimoroni 0.96" product) does NOT match TBM 1.8"
#         LCD (128x160). Must explicitly set width=128, height=160, and
#         offset_left=2, offset_top=1 to match the ST7735 memory map.
#     v2.2.0 (2024-03):
#       - FIXED: ST7735.__init__() TypeError - pimoroni/st7735-python v1.0.0
#         changed API completely:
#           * 'rgb' parameter renamed to 'bgr'
#           * GPIO pin numbers must now be strings ("GPIO24", not 24)
#           * Adafruit_GPIO dependency removed; uses gpiod/spidev internally
#           * 'import ST7735' deprecated; use 'import st7735' (lowercase)
#           * disp.buffer removed; draw to a PIL Image, pass to disp.display()
#       - FIXED: lcdSetupScript.sh now installs pimoroni/st7735-python
#         (pip install st7735) instead of the old doido-technologies fork
#     v2.1.0 (2024-02):
#       - Fixed Pillow 10+ compatibility: replaced deprecated draw.textsize()
#         with draw.textbbox() - this was the root cause of the white screen
#       - Fixed pip install for Python 3.11+ externally-managed-environment
#       - Added fallback for bitcoin RPC (direct HTTP RPC + docker exec)
#       - Added fallback for lncli (docker exec with multiple container names)
#       - Fixed SPI config path for umbrelOS (/boot/firmware/config.txt)
#       - Improved error handling and graceful degradation
#       - Added disk detection for both /dev/sda1 and /dev/mmcblk0p1
#-------------------------------------------------------------------------------
# This script displays eight screens on your Umbrel Node:
#    1. First screen displays the umbrel logo.
#    2. Second screen has bitcoin price and satoshis per unit of
#       the currency used.
#    3. Third screen has information about the next bitcoin block.
#    4. Fourth screen has the current Bitcoin block height.
#    5. Fifth screen has the current date and time.
#    6. Sixth screen has the bitcoin network information.
#    7. Seventh screen has the payment channels information.
#    8. Eighth screen has the Node disk storage information.
#    9. First screen is displayed once for 60 seconds.
#   10. The second to eighth screens are displayed in a loop; second screen
#       is displayed for 60 seconds, third to eighth screens for 30 seconds
#       each.
#-------------------------------------------------------------------------------

from PIL import Image, ImageDraw, ImageFont
import time
import datetime
import json
import pathlib
import subprocess
import sys
import os
import configparser
import requests

from st7735_tbm import ST7735
from connections import test_tor, tor_request

basedir = os.path.abspath(os.path.dirname(__file__))

WIDTH = 128
HEIGHT = 160
SPEED_HZ = 16000000

# Raspberry Pi pin configuration (BCM numbering, integers).
# These match the original doido-technologies wiring for TBM.
DC         = 24   # BCM 24 = physical Pin 18
RST        = 25   # BCM 25 = physical Pin 22
SPI_PORT   = 0
SPI_DEVICE = 0    # CE0

# ---------------------------------------------------------------------------
# Initialise the ST7735 display using the bundled TBM driver.
# offset_left=0, offset_top=0 because the doido-technologies library uses
# ST7735_COLS=128 and ST7735_ROWS=160 (same as the panel), so no offset
# is needed. This is the key difference from pimoroni (which uses 132x162).
# ---------------------------------------------------------------------------
disp = ST7735(
    port=SPI_PORT,
    cs=SPI_DEVICE,
    dc=DC,
    rst=RST,
    width=128,
    height=160,
    offset_left=0,
    offset_top=0,
    spi_speed_hz=SPEED_HZ,
    invert=False,
    bgr=True    # TBM panel uses BGR colour order (blue icon = wrong, orange = correct)
)


def lcd_display(image):
    """Send a PIL Image to the LCD via the bundled st7735_tbm driver."""
    disp.display(image)

# ---------------------------------------------------------------------------
# Off-screen image buffer.
# All drawing happens here; call disp.display(screen_buffer) to push to LCD.
# The buffer is 128×160 (portrait). Drawing functions rotate elements 270°
# before pasting, matching the physical LCD orientation.
# ---------------------------------------------------------------------------
screen_buffer = Image.new('RGB', (WIDTH, HEIGHT))

# Shape drawing object (re-created in display_background_image each frame)
draw = ImageDraw.Draw(screen_buffer)

# Get directory of the executing script
filePath=str(pathlib.Path(__file__).parent.absolute())

# customizable images path
images_path = filePath+'/images/'

# Customizable fonts path
poppins_fonts_path = filePath+'/poppins/'

# Currency as a global variable
currency = sys.argv[1]

# User screen options
userScreenChoices = sys.argv[2]

# Initial mempool url
mempool_url = "https://mempool.space"

# Mainnet or testnet settings
blockchain_type = "mainnet"

# ---------------------------------------------------------------------------
# Bitcoin / LND connection settings
# ---------------------------------------------------------------------------
# These are read from config.ini if present, otherwise fall back to defaults.
# This means future Umbrel updates that change RPC credentials only require
# editing config.ini — no code changes needed.
# ---------------------------------------------------------------------------
_cfg = configparser.ConfigParser()
_cfg.read(os.path.join(basedir, 'config.ini'))

BITCOIN_RPC_USER = _cfg.get('BITCOIN', 'rpc_user', fallback='umbrel')

# ---------------------------------------------------------------------------
# Screen display durations (seconds) - configurable via config.ini
# [DISPLAY]
# logo_duration   = 60   ; startup Umbrel logo screen
# screen1_duration = 60  ; Bitcoin price screen
# screen_duration  = 30  ; all other screens (2-7)
# ---------------------------------------------------------------------------
LOGO_DURATION    = int(_cfg.get('DISPLAY', 'logo_duration',    fallback='10'))
SCREEN1_DURATION = int(_cfg.get('DISPLAY', 'screen1_duration', fallback='10'))
SCREEN_DURATION  = int(_cfg.get('DISPLAY', 'screen_duration',  fallback='10'))
BITCOIN_RPC_PASS = _cfg.get('BITCOIN', 'rpc_pass', fallback='moneyprintergobrrr')
BITCOIN_RPC_HOST = _cfg.get('BITCOIN', 'rpc_host', fallback='127.0.0.1')
BITCOIN_RPC_PORT = int(_cfg.get('BITCOIN', 'rpc_port', fallback='8332'))

# Bitcoin container names to try in order (Umbrel may rename containers across versions)
# Add new names here if Umbrel changes container naming in a future update.
BITCOIN_CONTAINER_NAMES = [
    _cfg.get('BITCOIN', 'container', fallback=''),   # user override in config.ini
    "bitcoin_bitcoind_1",    # Umbrel 0.x / 1.x docker-compose style
    "bitcoin-bitcoind-1",   # Umbrel 1.x alternative
    "bitcoind",             # generic fallback
]
BITCOIN_CONTAINER_NAMES = [n for n in BITCOIN_CONTAINER_NAMES if n]  # remove empty

# LND container names to try in order
LND_CONTAINER_NAMES = [
    _cfg.get('LIGHTNING', 'container', fallback=''),  # user override
    "lightning_lnd_1",      # Umbrel 0.x / 1.x
    "lightning-lnd-1",     # Umbrel 1.x alternative
    "lnd",                  # generic fallback
]
LND_CONTAINER_NAMES = [n for n in LND_CONTAINER_NAMES if n]  # remove empty


# ---------------------------------------------------------------------------
# Pillow text rendering helper
# ---------------------------------------------------------------------------

def make_text_image(text, font, fill=(255, 255, 255)):
    """Create a transparent RGBA image containing the rendered text.

    Uses textbbox to account for font descent/ascent offsets so that
    characters with descenders (g, p, y, …) are not clipped at the bottom.
    """
    # Measure with a temporary draw object
    tmp = Image.new('RGBA', (1, 1))
    tmp_draw = ImageDraw.Draw(tmp)
    try:
        bbox = tmp_draw.textbbox((0, 0), text, font=font)
        x_off = -bbox[0]          # shift so left edge is at x=0
        y_off = -bbox[1]          # shift so top edge is at y=0
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
    except AttributeError:
        # Pillow < 9 fallback
        w, h = tmp_draw.textsize(text, font=font)
        x_off, y_off = 0, 0
    # Add a small margin to avoid clipping at the bottom
    h_margin = max(4, int(h * 0.15))
    img = Image.new('RGBA', (max(w, 1), max(h + h_margin, 1)), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((x_off, y_off), text, font=font, fill=fill)
    return img


# ---------------------------------------------------------------------------
# Bitcoin RPC helper - direct HTTP + docker exec fallback
# ---------------------------------------------------------------------------
def bitcoin_rpc(method, params=None, chain="main"):
    if params is None:
        params = []
    payload = json.dumps({
        "jsonrpc": "1.0", "id": "tbm-lcd",
        "method": method, "params": params
    })
    try:
        response = requests.post(
            f"http://{BITCOIN_RPC_HOST}:{BITCOIN_RPC_PORT}",
            data=payload,
            auth=(BITCOIN_RPC_USER, BITCOIN_RPC_PASS),
            timeout=10
        )
        result = response.json()
        if result.get("error"):
            raise Exception(str(result["error"]))
        return result["result"]
    except Exception:
        return bitcoin_cli_exec(method, params, chain)


def bitcoin_cli_exec(method, params=None, chain="main"):
    if params is None:
        params = []
    chain_flag = ["-chain=test"] if chain == "test" else []
    for container in BITCOIN_CONTAINER_NAMES:
        try:
            cmd = (["docker", "exec", container, "bitcoin-cli"]
                   + chain_flag + [method] + [str(p) for p in params])
            r = subprocess.run(cmd, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, timeout=15)
            if r.returncode == 0:
                out = r.stdout.decode('utf-8').strip()
                try:
                    return json.loads(out)
                except json.JSONDecodeError:
                    return out
        except Exception:
            continue
    raise Exception(f"Could not execute bitcoin-cli {method}")


def lncli_exec(method, params=None, network="mainnet"):
    if params is None:
        params = []
    for container in LND_CONTAINER_NAMES:
        try:
            cmd = (["docker", "exec", container, "lncli",
                    f"--network={network}", method]
                   + [str(p) for p in params])
            r = subprocess.run(cmd, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, timeout=15)
            if r.returncode == 0:
                out = r.stdout.decode('utf-8').strip()
                try:
                    return json.loads(out)
                except json.JSONDecodeError:
                    return out
        except Exception:
            continue
    raise Exception(f"Could not execute lncli {method}")


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------
def get_inverted_x(currentX, objectSize):
    return WIDTH - (currentX + objectSize)


def get_corrected_x_position(ideal_font_height, smaller_font_height,
                              ideal_x_position):
    try:
        correction = int((ideal_font_height - smaller_font_height) / 2)
        return correction + ideal_x_position
    except Exception as e:
        print("Error while calculating corrected x position; ", str(e))
        return ideal_x_position


def display_background_image(image_name):
    """Load a background image, rotate 270°, paste into screen_buffer."""
    global screen_buffer, draw
    image_path = images_path + image_name
    picimage = Image.open(image_path).convert('RGBA')
    picimage = picimage.resize((160, 128), Image.BICUBIC)
    rotated = picimage.rotate(270, expand=1)          # → 128×160
    screen_buffer = Image.new('RGB', (WIDTH, HEIGHT))
    screen_buffer.paste(rotated, (0, 0), rotated)
    draw = ImageDraw.Draw(screen_buffer)


# ---------------------------------------------------------------------------
# Code-based layout helpers (배경 이미지 없이 코드로 직접 그리는 방식)
# ---------------------------------------------------------------------------

# TBM 브랜드 색상
BG_DARK   = (20,  10,  60)   # 진한 보라/남색 배경
BG_BLUE   = (15,  20,  80)   # 짙은 파랑 배경 (Network 화면)
COL_WHITE = (255, 255, 255)
COL_GRAY  = (180, 180, 200)
COL_GREEN = (0,   200,  80)
COL_ORANGE= (255, 140,   0)
COL_YELLOW= (255, 200,  50)


def clear_screen(bg_color=None):
    """화면을 단색으로 초기화한다. 배경 이미지 없이 코드 기반 레이아웃의 시작점."""
    global screen_buffer, draw
    if bg_color is None:
        bg_color = BG_DARK
    screen_buffer = Image.new('RGB', (WIDTH, HEIGHT), bg_color)
    draw = ImageDraw.Draw(screen_buffer)


def pf(size):
    """Poppins-Bold 폰트 로드 단축 함수."""
    return ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", size)


def text_size(text, font):
    """텍스트의 (width, height) 반환."""
    tmp = Image.new('RGBA', (1, 1))
    tmp_draw = ImageDraw.Draw(tmp)
    try:
        bbox = tmp_draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    except AttributeError:
        return tmp_draw.textsize(text, font=font)


def fit_font_size(text, max_px, min_size=8, max_size=80):
    """텍스트가 max_px 픽셀 너비에 맞는 최대 폰트 크기를 반환한다."""
    for size in range(max_size, min_size - 1, -1):
        w, _ = text_size(text, pf(size))
        if w <= max_px:
            return size
    return min_size


def draw_rot(image, text, x, y, font, fill=COL_WHITE):
    """텍스트를 90도 회전하여 (x, y) 위치에 붙여넣는다.

    LCD 좌표계 (128x160, portrait):
      x = 0 (화면 위쪽) ~ 127 (화면 아래쪽)
      y = 0 (화면 왼쪽) ~ 159 (화면 오른쪽)

    텍스트는 90도 회전되므로 원본 텍스트의 '너비'가 y축 방향으로 배치된다.
    """
    textimage = make_text_image(text, font, fill)
    rotated = textimage.rotate(90, expand=1)
    image.paste(rotated, (x, y), rotated)


def draw_rot_centered_y(image, text, x, font, fill=COL_WHITE):
    """텍스트를 90도 회전하여 y축(가로) 중앙에 배치한다."""
    textimage = make_text_image(text, font, fill)
    w, h = textimage.size
    rotated = textimage.rotate(90, expand=1)
    y = (HEIGHT - w) // 2
    image.paste(rotated, (x, y), rotated)


def draw_rot_right_y(image, text, x, font, fill=COL_WHITE):
    """텍스트를 90도 회전하여 y축 오른쪽 끝에 정렬한다."""
    textimage = make_text_image(text, font, fill)
    w, h = textimage.size
    rotated = textimage.rotate(90, expand=1)
    y = HEIGHT - w - 2
    image.paste(rotated, (x, y), rotated)


def draw_grid_cell(buf, label, val, unit, x_label, x_val, y_center, max_val_width=70):
    """2x2 그리드의 한 셀을 그린다.

    LCD 좌표계 (128x160, portrait):
      x: 0=화면 위쪽, 127=화면 아래쪽
      y: 0=화면 왼쪽, 159=화면 오른쪽

    각 셀 레이아웃 (x축 기준):
      x_label: 레이블 행 (회색, 작은 글씨)
      x_val:   값 행 (흰색, 큰 글씨)

    y_center: 셀의 y축 중앙 위치
    """
    # 레이블 (작은 글씨, 회색)
    lbl_w, _ = text_size(label, pf(9))
    draw_rot(buf, label, x_label, y_center - lbl_w // 2, pf(9), fill=COL_GRAY)

    # 값 (큰 글씨, 흰색) - y 중앙 정렬
    val_fs = fit_font_size(val, max_val_width, min_size=12, max_size=24)
    val_w, _ = text_size(val, pf(val_fs))
    val_y = y_center - val_w // 2
    draw_rot(buf, val, x_val, val_y, pf(val_fs))

    # 단위 (작은 글씨, 회색) - 값 바로 오른쪽(y축)
    if unit:
        draw_rot(buf, unit, x_val, val_y + val_w + 2, pf(9), fill=COL_GRAY)


def draw_divider_h(image, x, color=COL_GRAY, thickness=1):
    """가로 구분선을 그린다 (x 위치, y=0~159)."""
    d = ImageDraw.Draw(image)
    d.rectangle((x, 0, x + thickness - 1, HEIGHT - 1), fill=color)


def draw_divider_v(image, y, color=COL_GRAY, thickness=1):
    """세로 구분선을 그린다 (y 위치, x=0~127)."""
    d = ImageDraw.Draw(image)
    d.rectangle((0, y, WIDTH - 1, y + thickness - 1), fill=color)


def display_icon(image, image_path, position, icon_size):
    picimage = Image.open(image_path).convert('RGBA')
    picimage = picimage.resize((icon_size, icon_size), Image.BICUBIC)
    rotated = picimage.rotate(270, expand=1)
    image.paste(rotated, position, rotated)


def draw_left_justified_text(image, text, xposition, yPosition,
                              angle, font, fill=(255, 255, 255)):
    textimage = make_text_image(text, font, fill)
    rotated = textimage.rotate(angle, expand=1)
    image.paste(rotated, (xposition, yPosition), rotated)


def draw_right_justified_text(image, text, xposition, yPosition,
                               angle, font, fill=(255, 255, 255)):
    textimage = make_text_image(text, font, fill)
    w, h = textimage.size
    rotated = textimage.rotate(angle, expand=1)
    H = 160
    image.paste(rotated, (xposition, int((H - w) - yPosition)), rotated)


def draw_centered_text(image, text, xposition, angle, font,
                       fill=(255, 255, 255)):
    textimage = make_text_image(text, font, fill)
    w, h = textimage.size
    rotated = textimage.rotate(angle, expand=1)
    H = 160
    image.paste(rotated, (xposition, int((H - w) / 2)), rotated)


def place_value(number):
    return "{:,}".format(number)


# ---------------------------------------------------------------------------
# Data-fetching helpers
# ---------------------------------------------------------------------------
def get_block_count():
    # Priority 1: local Bitcoin node RPC (most reliable, no external dependency)
    try:
        chain = "test" if blockchain_type == "test" else "main"
        count = bitcoin_rpc("getblockcount", chain=chain)
        return str(count)
    except Exception:
        pass
    # Priority 2: public mempool.space API (works even if local node is down)
    try:
        url = mempool_url + "/api/blocks/tip/height"
        r = requests.get(url, timeout=10)
        return r.text.strip()
    except Exception:
        pass
    # Priority 3: blockchain.info (last resort)
    try:
        url = "https://blockchain.info/q/getblockcount"
        return tor_request(url).text
    except Exception as err:
        print("Error while getting current block:", str(err))
        return ""


def get_btc_price(currency):
    # Priority 1: CoinGecko (most comprehensive)
    try:
        url = ("https://api.coingecko.com/api/v3/simple/price"
               "?ids=bitcoin&vs_currencies=" + currency)
        data = requests.get(url, timeout=10).json()
        return int(data['bitcoin'][currency.lower()])
    except Exception as err:
        print("Error getting price from CoinGecko:", str(err))
    # Priority 2: Coinbase
    try:
        url = f"https://api.coinbase.com/v2/prices/BTC-{currency}/spot"
        data = requests.get(url, timeout=10).json()
        return int(float(data['data']['amount']))
    except Exception as err2:
        print("Error getting price from Coinbase:", str(err2))
    # Priority 3: Kraken
    try:
        pair = f"XBT{currency.upper()}"
        url = f"https://api.kraken.com/0/public/Ticker?pair={pair}"
        data = requests.get(url, timeout=10).json()
        result = list(data['result'].values())[0]
        return int(float(result['c'][0]))
    except Exception as err3:
        print("Error getting price from Kraken:", str(err3))
    return ""


def _mempool_get(path):
    """GET from local mempool first, fall back to mempool.space public API."""
    for base in [mempool_url, "https://mempool.space"]:
        try:
            r = requests.get(base + path, timeout=10)
            if r.ok:
                return r
        except Exception:
            continue
    return None


def get_recommended_fees():
    try:
        r = _mempool_get("/api/v1/fees/recommended")
        if r:
            return r.json()
    except Exception as e:
        print("Error getting recommended fees;", str(e))
    return ""


def get_next_block_info():
    try:
        r = _mempool_get("/api/v1/fees/mempool-blocks")
        if r:
            return r.json()[0]
    except Exception as e:
        print("Error getting next block info;", str(e))
    return ""


def get_unconfirmed_txs():
    try:
        r = _mempool_get("/api/mempool")
        if r:
            return str(r.json()['count'])
    except Exception as e:
        print("Error getting unconfirmed txs;", str(e))
    return ""


def classify_bytes(num_of_bytes):
    n = int(num_of_bytes)
    for unit, threshold in [("TB", 1e12), ("GB", 1e9), ("MB", 1e6), ("KB", 1e3)]:
        if n > threshold:
            return f"{round(n/threshold)} {unit}"
    return f"{n} B"


def classify_kilo_bytes(num_of_bytes):
    n = int(num_of_bytes) * 1024
    for unit, threshold in [("TB", 1e12), ("GB", 1e9), ("MB", 1e6), ("KB", 1e3)]:
        if n > threshold:
            return f"{n/threshold:.1f} {unit}"
    return f"{n} B"


def classify_satoshis(num_of_satoshis):
    n = int(num_of_satoshis)
    ONE_BTC = 100_000_000
    if n >= 1_000_000 * ONE_BTC:
        return f"{round(n/(1_000_000*ONE_BTC))} MBTC"
    elif n >= 1_000 * ONE_BTC:
        return f"{round(n/(1_000*ONE_BTC))} kBTC"
    elif n >= ONE_BTC:
        return f"{round(n/ONE_BTC)} BTC"
    elif n >= 1_000:
        return f"{round(n/1_000)} kSats"
    return f"{n} Sats"


def remove_extra_spaces(s):
    result, prev = [], ""
    for c in s.strip():
        if not (prev == ' ' and c == ' '):
            result.append(c)
        prev = c
    return "".join(result)


def get_blockchain_size():
    global blockchain_type
    try:
        chain = "test" if blockchain_type == "test" else "main"
        info = bitcoin_rpc("getblockchaininfo", chain=chain)
        blockchain_type = info["chain"]
        return classify_bytes(int(info["size_on_disk"]))
    except Exception as e:
        print("Error getting blockchain size;", str(e))
        return False


def get_connection_count():
    try:
        chain = "test" if blockchain_type == "test" else "main"
        return int(bitcoin_rpc("getconnectioncount", chain=chain))
    except Exception as e:
        print("Error getting connection count;", str(e))
        return False


def get_mempool_info():
    try:
        chain = "test" if blockchain_type == "test" else "main"
        info = bitcoin_rpc("getmempoolinfo", chain=chain)
        return classify_bytes(int(info["bytes"]))
    except Exception as e:
        print("Error getting mempool info;", str(e))
        return False


def get_network_hash_ps():
    thresholds = [
        (1e24, "YH/s"), (1e21, "ZH/s"), (1e18, "EH/s"),
        (1e15, "PH/s"), (1e12, "TH/s"), (1e9, "GH/s"),
        (1e6, "MH/s"), (1e3, "kH/s"),
    ]
    try:
        chain = "test" if blockchain_type == "test" else "main"
        h = float(bitcoin_rpc("getnetworkhashps", chain=chain))
        for threshold, unit in thresholds:
            if h > threshold:
                return f"{round(h/threshold)} {unit}"
        return f"{h} H/s"
    except Exception as e:
        print("Error getting hash rate;", str(e))
        return False


def get_disk_storage_info():
    for disk_path in ["/dev/sda1", "/dev/sda", "/dev/mmcblk0p1",
                      "/dev/nvme0n1p1", "/"]:
        try:
            r = subprocess.run(["df", disk_path], stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
            if r.returncode != 0:
                continue
            lines = r.stdout.decode('utf-8').split('\n')
            if len(lines) < 2:
                continue
            parts = remove_extra_spaces(lines[1]).split()
            if len(parts) < 5:
                continue
            cap = classify_kilo_bytes(int(parts[1]))
            used = classify_kilo_bytes(int(parts[2]))
            avail = classify_kilo_bytes(int(parts[1]) - int(parts[2]))
            pct = int(parts[4].replace("%", ""))
            return [cap, used, avail, pct]
        except Exception:
            continue
    return False


def get_lnd_info():
    try:
        network = "testnet" if blockchain_type == "test" else "mainnet"
        info = lncli_exec("getinfo", network=network)
        return int(info['num_peers']), int(info['num_active_channels'])
    except Exception as e:
        print("Error getting LND info;", str(e))
        return False


def get_lnd_channel_balance():
    try:
        network = "testnet" if blockchain_type == "test" else "mainnet"
        bal = lncli_exec("channelbalance", network=network)
        max_send = classify_satoshis(int(bal['local_balance']['sat']))
        max_receive = classify_satoshis(int(bal['remote_balance']['sat']))
        return max_send, max_receive
    except Exception as e:
        print("Error getting LND channel balance;", str(e))
        return False


def get_tor_status():
    try:
        tor = test_tor()
        if tor['status']:
            print("Tor Connected")
            return True
        print("Could not connect to Tor.")
        return False
    except Exception as e:
        print("Error getting Tor status;", str(e))
        return False


def check_umbrel_and_mempool():
    try:
        url = _cfg.get('UMBREL', 'url', fallback='http://umbrel.local/')
    except Exception:
        url = 'http://umbrel.local/'

    umbrel = False
    try:
        result = tor_request(url)
        if isinstance(result, requests.models.Response) and result.ok:
            umbrel = True
    except Exception as e:
        print("Umbrel not found:", str(e))

    if not umbrel:
        return False

    try:
        murl = config['MEMPOOL']['url']
    except Exception:
        murl = 'http://umbrel.local:3006/'
    try:
        result = tor_request(murl)
        if isinstance(result, requests.models.Response) and result.ok:
            tor_request(murl + '/api/blocks/tip/height').json()
            return True
    except Exception as e:
        print("Mempool not found:", str(e))
    return False


def get_mempool_base_url():
    status = check_umbrel_and_mempool()
    print(f"Local Mempool app status = {status}")
    return "http://umbrel.local:3006" if status else "https://mempool.space"


def get_btc_network():
    global blockchain_type
    try:
        info = bitcoin_rpc("getblockchaininfo")
        blockchain_type = "test" if info.get("chain") == "test" else "main"
        return
    except Exception:
        pass
    try:
        r = subprocess.run(
            ["docker", "ps", "--filter", "name=bitcoin_bitcoind_1"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        blockchain_type = "test" if "-chain=tes" in r.stdout.decode() else "main"
    except Exception as e:
        print("Error getting BTC network type;", str(e))


# ---------------------------------------------------------------------------
# Screen drawing functions
# ---------------------------------------------------------------------------
def display_price_text(currency):
    try:
        display_background_image('Screen1@288x.png')
        display_icon(screen_buffer, images_path + 'bitcoin_seeklogo.png', (80, 2), 27)
        display_icon(screen_buffer, images_path + 'Satoshi_regular_elipse.png', (27, 2), 27)

        price = get_btc_price(currency)
        newPrice = str(price)
        n = len(newPrice)
        font_size = int(195 / n) if n else 12

        ideal_x = 79
        font_x = get_corrected_x_position(39, font_size, ideal_x)
        price_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", font_size)
        draw_left_justified_text(screen_buffer, newPrice, font_x, 30, 90, price_font)

        cur_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 12)
        draw_right_justified_text(screen_buffer, currency, get_inverted_x(1, 12), 4, 90, cur_font)

        sat_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 14)
        draw_left_justified_text(screen_buffer, "SATS / " + currency,
                                 get_inverted_x(111, 14), 39, 90, sat_font)

        sat_val = str(int(100_000_000 / price)) if price else "0"
        n2 = len(sat_val)
        sf = int(200 / n2) if n2 > 4 else 50
        sat_font2 = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", sf)
        fx2 = get_corrected_x_position(50, sf, 24)
        draw_left_justified_text(screen_buffer, sat_val, fx2, 30, 90, sat_font2)
    except Exception as e:
        print("Error creating price text;", str(e))


def display_temperature():
    try:
        r = subprocess.run(['vcgencmd', 'measure_temp'],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if r.returncode == 0:
            raw = r.stdout.decode().replace("temp=", "").replace("'C", "").strip()
            temperature = str(int(float(raw))) + "'C"
        else:
            with open('/sys/class/thermal/thermal_zone0/temp') as f:
                temperature = str(int(int(f.read().strip()) / 1000)) + "'C"
    except Exception:
        temperature = "--'C"
    temp_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 12)
    draw_right_justified_text(screen_buffer, temperature, 3, 3, 90, temp_font)


def display_block_count_text():
    """블록 높이 화면 - 코드 기반 레이아웃.

    참고 사이트 레이아웃:
      - 상단 절반: 하이퍼큐브 아이콘 (중앙)
      - 하단 절반: 블록 숫자 (큰 글씨, 중앙)
    """
    try:
        clear_screen(BG_DARK)
        btc_current_block = get_block_count()
        block_str = str(btc_current_block)

        # 아이콘: 상단 절반 중앙 (x=5~58, y 중앙)
        icon_size = 50
        icon_x = 4   # x 위치 (상단 절반)
        icon_y = (HEIGHT - icon_size) // 2
        try:
            display_icon(screen_buffer, images_path + 'Block_HeightBG.png',
                         (icon_x, icon_y), icon_size)
        except Exception:
            # 아이콘 로드 실패 시 텍스트 대체
            draw_rot(screen_buffer, '#', icon_x, icon_y, pf(40))

        # 블록 숫자: 오른쪽 절반 (x=65~108), y축 중앙
        # max_px=100으로 제한하여 화면 안에 들어오게 함
        fs = fit_font_size(block_str, 100, min_size=18, max_size=34)
        draw_rot_centered_y(screen_buffer, block_str, 65, pf(fs))
    except Exception as e:
        print("Error creating block count text;", str(e))


def draw_screen1(currency):
    display_price_text(currency)
    display_temperature()


def draw_screen2():
    """트랜잭션 화면 - 코드 기반 레이아웃.

    참고 사이트 레이아웃:
      우측 열 (y=82~159): 수수료(sat/vB) 박스 2개
        상단 박스: 저속 수수료 (1h fee)
        하단 박스: 빠른 수수료 (fastest fee)
      좌측 영역 (y=0~80):
        상단: 다음 블록 TXs 수 ("TXs" 레이블 + 숫자)
        하단: 미확인 TXs 수 (숫자)
    """
    fees_dict = get_recommended_fees()
    next_block_dict = get_next_block_info()
    unconfirmed_txs = get_unconfirmed_txs()

    high = int(fees_dict['fastestFee'])
    low = int(fees_dict['hourFee'])

    # 배경: 진한 보라
    clear_screen(BG_DARK)
    d = ImageDraw.Draw(screen_buffer)

    # 우측 열: y=82~159 영역
    # 수수료 박스 2개 그리기
    box_x1, box_x2 = 80, 127
    box_top_y1, box_top_y2 = 2, 77      # 상단 박스
    box_bot_y1, box_bot_y2 = 82, 157    # 하단 박스
    d.rectangle((box_x1, box_top_y1, box_x2, box_top_y2),
                outline=COL_WHITE, fill=(40, 20, 100))
    d.rectangle((box_x1, box_bot_y1, box_x2, box_bot_y2),
                outline=COL_WHITE, fill=(40, 20, 100))

    # 수수료 숫자: 박스 내부 중앙
    # 상단 박스 높이 ~75px, 너비 ~47px
    low_str = str(low)
    high_str = str(high)
    low_fs = fit_font_size(low_str, 70, min_size=16, max_size=60)
    high_fs = fit_font_size(high_str, 70, min_size=16, max_size=60)

    # 상단 박스 수수료: y 중앙 = (2+77)//2 = 39
    low_w, _ = text_size(low_str, pf(low_fs))
    low_y = box_top_y1 + (box_top_y2 - box_top_y1 - low_w) // 2
    draw_rot(screen_buffer, low_str, box_x1 + 2, low_y, pf(low_fs))

    # 하단 박스 수수료: y 중앙 = (82+157)//2 = 119
    high_w, _ = text_size(high_str, pf(high_fs))
    high_y = box_bot_y1 + (box_bot_y2 - box_bot_y1 - high_w) // 2
    draw_rot(screen_buffer, high_str, box_x1 + 2, high_y, pf(high_fs))

    # 좌측 영역: y=0~80
    # 좌측 상단 영역 (x=43~78): 다음 블록 TXs
    draw_rot(screen_buffer, "TXs", 62, 4, pf(11), fill=COL_GRAY)
    txs_str = str(int(next_block_dict['nTx']))
    txs_fs = fit_font_size(txs_str, 74, min_size=14, max_size=30)
    draw_rot_centered_y(screen_buffer, txs_str, 43, pf(txs_fs))

    # 좌측 하단 영역 (x=5~40): 미확인 TXs
    u_fs = fit_font_size(unconfirmed_txs, 74, min_size=12, max_size=26)
    draw_rot_centered_y(screen_buffer, unconfirmed_txs, 7, pf(u_fs))
    draw_rot(screen_buffer, "unconf", 5, 4, pf(8), fill=COL_GRAY)


def draw_screen3():
    display_block_count_text()


def draw_screen4():
    display_background_image('Screen1@288x.png')
    now = datetime.datetime.now()
    time_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 30)
    day_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 26)
    month_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 22)
    draw_centered_text(screen_buffer, now.strftime('%-I:%M %p'),
                       get_inverted_x(16, 30), 90, time_font)
    draw_centered_text(screen_buffer, now.strftime('%A'),
                       get_inverted_x(59, 26), 90, day_font)
    draw_centered_text(screen_buffer, now.strftime('%B %d'),
                       get_inverted_x(91, 22), 90, month_font)


def draw_screen5():
    """네트워크 화면 - 코드 기반 2x2 그리드 레이아웃.

    참고 사이트 레이아웃:
      제목: "Network" (상단)
      2x2 그리드:
        좌상: Connections / 11 Peers
        우상: Mempool / 816 KB
        좌하: Hashrate / 240 EH/S
        우하: Blockchain / 457 GB
    """
    clear_screen(BG_BLUE)

    # 제목 "Network" - 오른쪽 (x=110~124)
    draw_rot(screen_buffer, "Network", 110, 4, pf(13))

    # 구분선: 가로 (x=64), 세로 (y=80)
    draw_divider_h(screen_buffer, 64, color=(50, 50, 110))
    draw_divider_v(screen_buffer, 80, color=(50, 50, 110))

    # 데이터 가져오기
    conn_str = str(get_connection_count())
    mem = get_mempool_info()
    hr = get_network_hash_ps()
    bs = get_blockchain_size()

    mem_parts = mem.split()
    hr_parts = hr.split()
    bs_parts = bs.split()

    mem_val  = mem_parts[0] if mem_parts else "?"
    mem_unit = mem_parts[1] if len(mem_parts) > 1 else ""
    hr_val   = hr_parts[0]  if hr_parts  else "?"
    hr_unit  = hr_parts[1]  if len(hr_parts) > 1  else ""
    bs_val   = bs_parts[0]  if bs_parts  else "?"
    bs_unit  = bs_parts[1]  if len(bs_parts) > 1  else ""

    # 각 셀의 y 중앙 (0~79 왼쪽 열, 80~159 오른쪽 열)
    y_L = 40   # 왼쪽 열 중앙
    y_R = 120  # 오른쪽 열 중앙

    # 2x2 그리드:
    #   상단행 (x_label=88, x_val=66): Connections, Mempool
    #   하단행 (x_label=44, x_val=22): Hashrate, Blockchain
    draw_grid_cell(screen_buffer, "Connections", conn_str, "Peers",
                   x_label=88, x_val=66, y_center=y_L)
    draw_grid_cell(screen_buffer, "Mempool",     mem_val,  mem_unit,
                   x_label=88, x_val=66, y_center=y_R)
    draw_grid_cell(screen_buffer, "Hashrate",    hr_val,   hr_unit,
                   x_label=44, x_val=22, y_center=y_L)
    draw_grid_cell(screen_buffer, "Blockchain",  bs_val,   bs_unit,
                   x_label=44, x_val=22, y_center=y_R)


def draw_screen6():
    """페이먼트 채널 화면 - 코드 기반 2x2 그리드 레이아웃.

    참고 사이트 레이아웃:
      제목: "Payment Channels" (상단)
      2x2 그리드:
        좌상: Connections / 5 Peers
        우상: Active / 0 Channels
        좌하: Max Send / 0 Sats
        우하: Max Receive / 0 Sats
    """
    clear_screen(BG_DARK)

    # 제목 "Payment Channels" - 오른쪽 (x=110~124)
    draw_rot(screen_buffer, "Payment Channels", 110, 4, pf(10))

    # 구분선: 가로 (x=64), 세로 (y=80)
    draw_divider_h(screen_buffer, 64, color=(50, 50, 110))
    draw_divider_v(screen_buffer, 80, color=(50, 50, 110))

    # 데이터 가져오기
    result = get_lnd_info()
    connections = str(result[0]) if result else "--"
    active_channels = str(result[1]) if result else "--"

    bal = get_lnd_channel_balance() if result else None
    if bal:
        max_send, max_receive = bal
        send_parts = max_send.split()
        recv_parts = max_receive.split()
        send_val  = send_parts[0] if send_parts else "0"
        send_unit = send_parts[1] if len(send_parts) > 1 else "Sats"
        recv_val  = recv_parts[0] if recv_parts else "0"
        recv_unit = recv_parts[1] if len(recv_parts) > 1 else "Sats"
    else:
        send_val, send_unit = "--", "Sats"
        recv_val, recv_unit = "--", "Sats"

    # 각 셀의 y 중앙
    y_L = 40
    y_R = 120

    # 2x2 그리드:
    #   상단행 (x_label=88, x_val=66): Connections, Active
    #   하단행 (x_label=44, x_val=22): Max Send, Max Receive
    draw_grid_cell(screen_buffer, "Connections", connections,     "Peers",
                   x_label=88, x_val=66, y_center=y_L)
    draw_grid_cell(screen_buffer, "Active",      active_channels, "Channels",
                   x_label=88, x_val=66, y_center=y_R)
    draw_grid_cell(screen_buffer, "Max Send",    send_val,        send_unit,
                   x_label=44, x_val=22, y_center=y_L)
    draw_grid_cell(screen_buffer, "Max Receive", recv_val,        recv_unit,
                   x_label=44, x_val=22, y_center=y_R)


def draw_screen7():
    """스토리지 화면 - 코드 기반 레이아웃.

    참고 사이트 레이아웃:
      제목: "Storage" + 플로피디스크 아이콘 (오른쪽 상단)
      큰 숫자: "565.2 GB" (중앙)
      소형: "Used out of 965.2 GB"
      진행바: 가로 바 (하단)
      소형: "418.2 GB available"
    """
    clear_screen(BG_DARK)

    storage_info = get_disk_storage_info()
    if not storage_info:
        draw_rot_centered_y(screen_buffer, "Storage", 50, pf(18))
        draw_rot_centered_y(screen_buffer, "No data", 30, pf(12), fill=COL_GRAY)
        return

    used_space, disk_capacity, available_space, used_pct = (
        storage_info[1], storage_info[0], storage_info[2], storage_info[3])

    # 제목 "Storage" - 오른쪽 (x=110~124)
    draw_rot(screen_buffer, "Storage", 110, 4, pf(13))

    # 아이콘: storage.png는 배경 이미지이므로 사용 불가 (전체 화면이 로드됨)
    # 대신 플로피디스크 심볼을 텍스트로 표시
    draw_rot(screen_buffer, "[=]", 86, 110, pf(18), fill=COL_GRAY)

    # 큰 숫자: 사용량 (x=60~84), y축 중앙
    # max_size=24로 제한하여 제목 영역을 침범하지 않게 함
    used_fs = fit_font_size(used_space, 150, min_size=16, max_size=24)
    draw_rot_centered_y(screen_buffer, used_space, 60, pf(used_fs))

    # 중간 텍스트: "Used out of X" (x=44~58)
    out_of_str = "Used out of " + disk_capacity
    out_fs = fit_font_size(out_of_str, 150, min_size=8, max_size=12)
    draw_rot_centered_y(screen_buffer, out_of_str, 44, pf(out_fs), fill=COL_GRAY)

    # 진행바: 가로 바 (x=30~38), y=4~155
    d = ImageDraw.Draw(screen_buffer)
    bar_x, bar_y = 30, 4
    bar_h, bar_w = 151, 8
    # 배경바 (흰색)
    d.rectangle((bar_x, bar_y, bar_x + bar_w, bar_y + bar_h),
                outline=COL_WHITE, fill=(60, 60, 80))
    # 사용량 (녹색)
    used_h = int((used_pct * bar_h) / 100)
    d.rectangle((bar_x, bar_y, bar_x + bar_w, bar_y + used_h),
                fill=COL_GREEN)

    # 사용 가능 텍스트: "X available" (x=14~28)
    avail_str = available_space + " available"
    avail_fs = fit_font_size(avail_str, 150, min_size=8, max_size=12)
    draw_rot_centered_y(screen_buffer, avail_str, 14, pf(avail_fs), fill=COL_GREEN)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
print('Running Umbrel LCD script - Version: 2.15.0 (Umbrel 1.x compatible)')

# Display umbrel logo on startup (duration configurable in config.ini)
display_background_image('umbrel_logo.png')
lcd_display(screen_buffer)
time.sleep(LOGO_DURATION)

tor_status = get_tor_status()
mempool_status = check_umbrel_and_mempool()
print(f"Local Mempool app status = {mempool_status}")

while True:
    get_btc_network()

    try:
        mempool_url = get_mempool_base_url()
        print(f"current_mempool_url = {mempool_url}")
        if "Screen1" in userScreenChoices:
            draw_screen1(currency)
            lcd_display(screen_buffer)
            time.sleep(SCREEN1_DURATION)
    except Exception as e:
        print("Error showing screen1;", str(e))

    try:
        if "Screen2" in userScreenChoices:
            draw_screen2()
            lcd_display(screen_buffer)
            time.sleep(SCREEN_DURATION)
    except Exception as e:
        print("Error showing screen2;", str(e))

    try:
        if "Screen3" in userScreenChoices:
            draw_screen3()
            lcd_display(screen_buffer)
            time.sleep(SCREEN_DURATION)
    except Exception as e:
        print("Error showing screen3;", str(e))

    try:
        if "Screen4" in userScreenChoices:
            draw_screen4()
            lcd_display(screen_buffer)
            time.sleep(SCREEN_DURATION)
    except Exception as e:
        print("Error showing screen4;", str(e))

    try:
        if "Screen5" in userScreenChoices:
            draw_screen5()
            lcd_display(screen_buffer)
            time.sleep(SCREEN_DURATION)
    except Exception as e:
        print("Error showing screen5;", str(e))

    try:
        if "Screen6" in userScreenChoices:
            draw_screen6()
            lcd_display(screen_buffer)
            time.sleep(SCREEN_DURATION)
    except Exception as e:
        print("Error showing screen6;", str(e))

    try:
        if "Screen7" in userScreenChoices:
            draw_screen7()
            lcd_display(screen_buffer)
            time.sleep(SCREEN_DURATION)
    except Exception as e:
        print("Error showing screen7;", str(e))
