
#-------------------------------------------------------------------------------
#   Copyright (c) 2022 DOIDO Technologies
#   Version  : 2.15.0 (Umbrel 1.x compatible fork)
#   Location : github - forked & updated for Umbrel OS 1.x compatibility
#   Changes  :
#    # v2.15.0: Changed display_background_image() from rotate(90) to rotate(270).
#           Background PNG files are designed for rotate(270) orientation.
#           All screen text coordinates recalibrated for rotate(270) coordinate system.
#           Screens updated: Bitcoin Price, Block Height, Transactions,
#           Network, Payment Channels, Storage, Date/Time.
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
    """Load a background image, rotate 270°, paste into screen_buffer.
    Background PNG files are designed for rotate(270) orientation.
    Text is drawn with angle=90 which matches this coordinate system.
    """
    global screen_buffer, draw
    image_path = images_path + image_name
    picimage = Image.open(image_path).convert('RGBA')
    picimage = picimage.resize((160, 128), Image.BICUBIC)
    rotated = picimage.rotate(270, expand=1)           # → 128×160
    screen_buffer = Image.new('RGB', (WIDTH, HEIGHT))
    screen_buffer.paste(rotated, (0, 0), rotated)
    draw = ImageDraw.Draw(screen_buffer)


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
        # Screen1@288x.png layout (128x160 after rotate 270):
        #   Left half (x=0~63):  SAT price area
        #     Satoshi icon: x=27~54
        #     SAT value:    x=27~54 (below icon)
        #     SATS/USD label: x=1~26
        #   Right half (x=64~127): BTC price area
        #     Bitcoin icon: x=80~107
        #     Price value:  x=64~79 (below icon)
        #     Currency label: right-justified
        display_icon(screen_buffer, images_path + 'bitcoin_seeklogo.png', (80, 2), 27)
        display_icon(screen_buffer, images_path + 'Satoshi_regular_elipse.png', (27, 2), 27)

        price = get_btc_price(currency)
        newPrice = str(price)
        n = len(newPrice)
        font_size = int(195 / n) if n else 12

        # BTC price in right half (x=64~79)
        # Ensure font size doesn't exceed safe zone
        safe_font_size = min(font_size, 32)
        font_x = get_corrected_x_position(39, safe_font_size, 64)
        price_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", safe_font_size)
        draw_left_justified_text(screen_buffer, newPrice, font_x, 30, 90, price_font)

        # Currency label: right-justified in right half
        cur_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 12)
        draw_right_justified_text(screen_buffer, currency, 64, 4, 90, cur_font)

        # SATS/USD label in left half (x=1~26)
        sat_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 14)
        draw_left_justified_text(screen_buffer, "SATS / " + currency,
                                 1, 39, 90, sat_font)

        # SAT value in left half (x=27~54)
        sat_val = str(int(100_000_000 / price)) if price else "0"
        n2 = len(sat_val)
        sf = int(200 / n2) if n2 > 4 else 50
        safe_sf = min(sf, 40)
        sat_font2 = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", safe_sf)
        fx2 = get_corrected_x_position(50, safe_sf, 27)
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
    try:
        display_background_image('Block_HeightBG.png')
        # Block_HeightBG layout (128x160 after rotate 270):
        #   Block icon (hexagon): x=23~121 (occupies most of the screen)
        #   Empty space: x=1~22 (left strip, 22px wide)
        # Numbers go in left strip: x=1~22, centered vertically
        btc_current_block = get_block_count()
        n = len(str(btc_current_block))
        # 6 digits: font 18, 7 digits: font 14
        fs = 18 if n <= 6 else (14 if n == 7 else 12)
        font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", fs)
        # Place in left strip (x=1), centered vertically on y-axis
        draw_centered_text(screen_buffer, btc_current_block, 1, 90, font)
    except Exception as e:
        print("Error creating block count text;", str(e))


def draw_screen1(currency):
    display_price_text(currency)
    display_temperature()


def draw_screen2():
    fees_dict = get_recommended_fees()
    next_block_dict = get_next_block_info()
    unconfirmed_txs = get_unconfirmed_txs()
    display_background_image('TxsBG.png')
    high = int(fees_dict['fastestFee'])
    low = int(fees_dict['hourFee'])
    def fee_font_size(n):
        return int(86 / n) if n > 2 else 43
    low_fs = fee_font_size(len(str(low)))
    high_fs = fee_font_size(len(str(high)))
    low_x = 90 if len(str(low)) == 3 else 85
    high_x = 90 if len(str(high)) == 3 else 85
    draw_left_justified_text(screen_buffer, str(low), low_x, 9, 90,
                             ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", low_fs))
    draw_left_justified_text(screen_buffer, str(high), high_x, 88, 90,
                             ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", high_fs))
    txs = int(next_block_dict['nTx'])
    txs_fs = int(112 / len(str(txs))) if len(str(txs)) > 4 else 28
    draw_left_justified_text(screen_buffer, str(txs), 43, 67, 90,
                             ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", txs_fs))
    u_n = len(unconfirmed_txs)
    u_fs = int(120 / u_n) if u_n > 5 else 24
    draw_left_justified_text(screen_buffer, unconfirmed_txs, 7, 64, 90,
                             ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", u_fs))


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
    display_background_image('network.png')

    # network.png layout (128x160 after rotate 270):
    #   "Network" label:      x=108~119 (rightmost)
    #   "Connections" label:  x=86~94,  y=80~159 (right-mid, bottom half)
    #   "Mempool" label:      x=86~94,  y=0~79   (right-mid, top half)
    #   "Blockchain" label:   x=24~47,  y=0~79   (left-mid, top half)
    #   "Hashrate" label:     x=24~47,  y=80~159 (left-mid, bottom half)
    #
    #   Numbers go in the EMPTY space to the LEFT of each label:
    #   Pixel analysis (rot270): labels x=24~47, x=86~94, x=108~119
    #   Empty space: x=48~85 (38px)
    #   Row 1 (x=65~85, 21px): Connections (top) + Mempool (bottom)
    #   Row 2 (x=48~64, 17px): Blockchain (top) + Hashrate (bottom)
    #   y=0~79 (upper half), y=80~159 (lower half)

    conn = get_connection_count()
    conn_str = str(conn)
    n = len(conn_str)
    conn_y = 23 if n == 2 else (27 if n == 1 else 19)
    conn_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 15)
    draw_left_justified_text(screen_buffer, conn_str, 68, conn_y, 90, conn_font)
    mem = get_mempool_info()
    mem_val, mem_unit = mem.split()[0], mem.split()[1]
    n = len(mem_val)
    mem_y = 101 if n == 2 else (108 if n == 1 else 98)
    mem_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 15)
    draw_left_justified_text(screen_buffer, mem_val, 68, mem_y, 90, mem_font)
    unit_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 9)
    draw_left_justified_text(screen_buffer, mem_unit, 55, 105, 90, unit_font)
    draw_left_justified_text(screen_buffer, "Peers", 55, 22, 90, unit_font)
    hr = get_network_hash_ps()
    hr_val, hr_unit = hr.split()[0], hr.split()[1]
    n = len(hr_val)
    hr_y = 23 if n == 2 else (27 if n == 1 else 19)
    hr_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 15)
    draw_left_justified_text(screen_buffer, hr_val, 22, hr_y, 90, hr_font)
    hr_unit_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 9)
    draw_left_justified_text(screen_buffer, hr_unit, 8, 22, 90, hr_unit_font)
    bs = get_blockchain_size()
    bs_val, bs_unit = bs.split()[0], bs.split()[1]
    n = len(bs_val)
    bs_y = 101 if n == 2 else (108 if n == 1 else 98)
    bs_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 15)
    draw_left_justified_text(screen_buffer, bs_val, 22, bs_y, 90, bs_font)
    bs_unit_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 9)
    draw_left_justified_text(screen_buffer, bs_unit, 8, 105, 90, bs_unit_font)


def draw_screen6():
    display_background_image('payment_channels.png')
    result = get_lnd_info()
    if not result:
        return
    connections, active_channels = result

    # payment_channels.png layout (128x160 after rotate 270):
    #   "Payment Channels" label: x=111~121 (rightmost)
    #   "Connections" label:      x=88~96,  y=80~159 (right-mid, bottom half)
    #   "Active" label:           x=88~96,  y=0~79   (right-mid, top half)
    #   "Max Receive" label:      x=24~48,  y=0~79   (left-mid, top half)
    #   "Max Send" label:         x=24~48,  y=80~159 (left-mid, bottom half)
    #
    #   Numbers go in the EMPTY space between labels:
    #   Pixel analysis (rot270): labels x=24~48, x=88~96, x=111~121
    #   Empty space: x=49~87 (39px)
    #   Row 1 (x=67~87, 21px): Connections (top) + Active (bottom)
    #   Row 2 (x=49~66, 18px): Max Receive (top) + Max Send (bottom)
    #   y=0~79 (upper half), y=80~159 (lower half)

    n = len(str(connections))
    conn_y = 23 if n == 2 else (27 if n == 1 else 19)
    conn_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 15)
    draw_left_justified_text(screen_buffer, str(connections), 68, conn_y, 90, conn_font)
    n = len(str(active_channels))
    ch_y = 101 if n == 2 else (108 if n == 1 else 98)
    ch_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 15)
    draw_left_justified_text(screen_buffer, str(active_channels), 68, ch_y, 90, ch_font)
    label_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 9)
    draw_left_justified_text(screen_buffer, "Channels", 55, 98, 90, label_font)
    draw_left_justified_text(screen_buffer, "Peers", 55, 22, 90, label_font)
    bal = get_lnd_channel_balance()
    if not bal:
        return
    max_send, max_receive = bal
    send_val, send_unit = max_send.split()[0], max_send.split()[1]
    recv_val, recv_unit = max_receive.split()[0], max_receive.split()[1]
    n = len(send_val)
    send_y_map = {1: 27, 2: 23, 3: 19, 4: 15, 5: 10}
    send_y = send_y_map.get(n, 6)
    send_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 15)
    draw_left_justified_text(screen_buffer, send_val, 22, send_y, 90, send_font)
    n = len(recv_val)
    recv_y_map = {1: 108, 2: 101, 3: 98, 4: 93, 5: 90}
    recv_y = recv_y_map.get(n, 90)
    recv_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 15)
    draw_left_justified_text(screen_buffer, recv_val, 22, recv_y, 90, recv_font)
    btc_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 10)
    draw_left_justified_text(screen_buffer, recv_unit, 8, 100, 90, btc_font)
    draw_left_justified_text(screen_buffer, send_unit, 8, 22, 90, btc_font)


def draw_screen7():
    display_background_image('storage.png')
    storage_info = get_disk_storage_info()
    if not storage_info:
        return

    used_space, disk_capacity, available_space, used_pct = (
        storage_info[1], storage_info[0], storage_info[2], storage_info[3])

    # storage.png layout (128x160 after rotate 270):
    #   Storage icon:     x=80~120, y=100~140
    #   "Storage" label:  x=100~120, y=10~60
    #   Safe space for text: x=5~60
    #
    #   Layout plan (x = row position from left, y = horizontal position):
    #   Row 1 (x=10~30):  Used space large text (e.g. "929.1 GB")
    #   Row 2 (x=35~45):  "Used out of 2TB" small text
    #   Row 3 (x=50~60):  "1.5TB available" small text
    #   Progress bar (x=65~77): moved to avoid icon overlap

    draw_left_justified_text(screen_buffer, used_space, 59, 7, 90,
                             ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 20))
    draw_left_justified_text(screen_buffer, "Used out of " + disk_capacity, 44, 7, 90,
                             ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 11))
    draw_right_justified_text(screen_buffer, available_space + " available", 13, 11, 90,
                              ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 11))
    draw_sb = ImageDraw.Draw(screen_buffer)
    x, y, w, h = 29, 7, 2, 140
    inner_h = int((used_pct * h) / 100) + y
    draw_sb.rectangle((x, y, x + w, y + h), outline=(255, 255, 255), fill=(255, 255, 255))
    draw_sb.rectangle((x, y, x + w, inner_h), outline=(0, 160, 0), fill=(0, 160, 0))


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
