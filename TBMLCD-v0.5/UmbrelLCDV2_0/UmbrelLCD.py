
#-------------------------------------------------------------------------------
#   Copyright (c) 2022 DOIDO Technologies
#   Version  : 2.32.0 (Umbrel 1.x compatible fork)
#   Location : github - forked & updated for Umbrel OS 1.x compatibility
#   Changes  :
#    v2.32.0 (2024-03-07)
#    - Screen1: Widened the gap between SATS/USD and temperature to 8 spaces for better readability.
#    - Config: Increased default dissolve steps to 8 for a smoother transition effect.
#
#    v2.31.0 (2024-03-05)
#    - Umbrel 1.x Compatibility: Major overhaul to support changes in Umbrel OS 1.x.
#      - Added fallback logic to find correct Docker container names (e.g., `bitcoin_bitcoind_1`, `lnd_lnd_1`).
#      - Implemented direct HTTP RPC calls to `bitcoind` and `lncli` as a more robust alternative to `docker exec`.
#    - Pillow 10+ Compatibility: Replaced the deprecated `draw.textsize()` with a backward-compatible function using `draw.textbbox()`.
#    - Systemd Service: Explicitly added `/usr/local/bin` to the `PATH` in the service file to ensure Docker commands are found.
#    - Installation Script: Added `--break-system-packages` flag to `pip` commands to comply with Python 3.11+ system package protection.
#    























#         160, 3).
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

from setup_wizard import run_wizard
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


# Previous frame buffer for dissolve effect
_prev_buffer = None

def lcd_display_dissolve(image, steps=8):
    """Display image with a dissolve (cross-fade) transition from the previous frame.
    steps: number of blend frames (6 = ~0.3s on RPi at typical SPI speed).
    """
    global _prev_buffer
    if _prev_buffer is None:
        # First call: no previous frame, just display directly
        disp.display(image)
        _prev_buffer = image.copy()
        return
    prev = _prev_buffer.convert('RGBA')
    curr = image.convert('RGBA')
    for i in range(1, steps + 1):
        alpha = int(255 * i / steps)
        blended = Image.blend(prev, curr, alpha / 255.0).convert('RGB')
        disp.display(blended)
    _prev_buffer = image.copy()

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

# ---------------------------------------------------------------------------
# Interactive setup wizard
# Reads config.ini, shows current settings, prompts user (10s timeout),
# and returns effective settings for this run.
# ---------------------------------------------------------------------------
_config_path = os.path.join(basedir, 'config.ini')
_wizard_settings = run_wizard(_config_path)

# Currency as a global variable (from wizard / config.ini)
currency = _wizard_settings['currency']

# User screen options (from wizard / config.ini)
userScreenChoices = _wizard_settings['screens']

# Temperature unit (from wizard / config.ini)
TEMP_UNIT = _wizard_settings['temp_unit']  # 'C' or 'F'

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
# Duration settings: wizard result takes priority over config.ini
LOGO_DURATION    = _wizard_settings['logo_duration']
SCREEN1_DURATION = _wizard_settings['screen_duration']
SCREEN_DURATION  = _wizard_settings['screen_duration']
BITCOIN_RPC_PASS = _cfg.get('BITCOIN', 'rpc_pass', fallback='moneyprintergobrrr')
BITCOIN_RPC_HOST = _cfg.get('BITCOIN', 'rpc_host', fallback='127.0.0.1')
BITCOIN_RPC_PORT = int(_cfg.get('BITCOIN', 'rpc_port', fallback='8332'))

# Bitcoin container names to try in order (Umbrel may rename containers across versions)
# Add new names here if Umbrel changes container naming in a future update.
BITCOIN_CONTAINER_NAMES = [
    _cfg.get('BITCOIN', 'container', fallback=''),   # user override in config.ini
    "bitcoin_app_1",         # Umbrel 1.x confirmed container name
    "bitcoin_bitcoind_1",    # Umbrel 0.x docker-compose style
    "bitcoin-bitcoind-1",   # Umbrel 1.x alternative
    "app_bitcoind_1",        # Umbrel 1.x app store style
    "app-bitcoin-bitcoind-1",  # Umbrel 1.x app store alternative
    "bitcoin-app-bitcoind-1",  # Umbrel 1.x variant
    "bitcoind",             # generic fallback
]
BITCOIN_CONTAINER_NAMES = [n for n in BITCOIN_CONTAINER_NAMES if n]  # remove empty

# LND container names to try in order
LND_CONTAINER_NAMES = [
    _cfg.get('LIGHTNING', 'container', fallback=''),  # user override
    "lightning_app_1",      # Umbrel 1.x confirmed (Bitcoin Lightning Node app)
    "lightning_lnd_1",      # Umbrel 0.x
    "lightning-lnd-1",     # Umbrel 1.x alternative
    "app_lnd_1",            # Umbrel 1.x app store style
    "app-lightning-lnd-1",  # Umbrel 1.x app store alternative
    "lightning-app-lnd-1",  # Umbrel 1.x variant
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
    # h_margin can be overridden per-call via make_text_image_no_margin()
    h_margin = max(4, int(h * 0.15))
    img = Image.new('RGBA', (max(w, 1), max(h + h_margin, 1)), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((x_off, y_off), text, font=font, fill=fill)
    return img


def make_text_image_no_margin(text, font, fill=(255, 255, 255)):
    """Same as make_text_image but with h_margin=0 (text flush to bottom edge)."""
    tmp = Image.new('RGBA', (1, 1))
    tmp_draw = ImageDraw.Draw(tmp)
    try:
        bbox = tmp_draw.textbbox((0, 0), text, font=font)
        x_off = -bbox[0]
        y_off = -bbox[1]
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
    except AttributeError:
        w, h = tmp_draw.textsize(text, font=font)
        x_off, y_off = 0, 0
    img = Image.new('RGBA', (max(w, 1), max(h, 1)), (0, 0, 0, 0))
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
            val = n / threshold
            # Show decimal only if non-zero (e.g. 1 TB not 1.0 TB, but 1.5 TB stays)
            if val == int(val):
                return f"{int(val)} {unit}"
            return f"{val:.1f} {unit}"
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
        # Original TBM design (doidotech/TBM v2.0.1) coordinates preserved exactly.
        # Icons: 27px, BTC at (80,2), SAT at (27,2)
        # BTC price: font_size=int(195/n), x=get_corrected_x_pos(39,fs,79), y=30
        # SAT value: font_size=int(200/n) if n>4 else 50, x=get_corrected_x_pos(50,fs,24), y=30
        # Currency label: 12px, right-justified at get_inverted_x(1,12), y=4
        # SATS/USD label: 14px, left-justified at get_inverted_x(111,14), y=39

        # Icons: 27px. BTC x=75 (center=88), SAT x=33 (center=46) - gap=15px between icons
        display_icon(screen_buffer, images_path + 'bitcoin_seeklogo.png', (75, 2), 27)
        display_icon(screen_buffer, images_path + 'Satoshi_regular_elipse.png', (33, 2), 27)

        price = get_btc_price(currency)
        newPrice = str(price)
        n = len(newPrice)

        # BTC price font size: original formula int(195/n)
        price_font_size = int(195 / n) if n > 0 else 12
        price_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", price_font_size)
        # x: ideal_x=69 centers the number vertically with the BTC icon (center=88)
        price_x = get_corrected_x_position(39, price_font_size, 69)
        draw_left_justified_text(screen_buffer, newPrice, price_x, 36, 270, price_font)

        # Currency label: 12px, right-justified (original TBM design)
        cur_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 12)
        draw_right_justified_text(screen_buffer, currency, get_inverted_x(1, 12), 4, 270, cur_font)

        # SAT value: same formula as BTC price but capped at price_font_size
        sat_val = str(int(100_000_000 / price)) if price else "0"
        n2 = len(sat_val)
        sat_font_size = min(int(195 / n2) if n2 > 0 else 12, price_font_size)
        sat_font2 = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", sat_font_size)
        # x: ideal_x=27 centers the number vertically with the SAT icon (center=46)
        sat_x = get_corrected_x_position(39, sat_font_size, 27)
        draw_left_justified_text(screen_buffer, sat_val, sat_x, 36, 270, sat_font2)

        # SATS/USD + temperature: right-justified, flush to bottom (h_margin=0, x=0)
        temperature = get_temperature()
        sats_msg = "SATS / " + currency + "        " + temperature + " "
        bottom_label_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 12)
        textimage = make_text_image_no_margin(sats_msg, bottom_label_font)
        rotated = textimage.rotate(270, expand=1)
        H = 160
        w, _ = textimage.size
        screen_buffer.paste(rotated, (0, int((H - w) - 4)), rotated)
    except Exception as e:
        print("Error creating price text;", str(e))


def get_temperature():
    """Read CPU temperature and return as string like '51'C' or '124'F'.
    Unit is controlled by the global TEMP_UNIT variable ('C' or 'F').
    Returns '--'C' (or '--'F') on failure.
    """
    unit_suffix = "'F" if TEMP_UNIT == 'F' else "'C"
    try:
        with open('/sys/class/thermal/thermal_zone0/temp') as f:
            celsius = int(int(f.read().strip()) / 1000)
            if TEMP_UNIT == 'F':
                return str(int(celsius * 9 / 5 + 32)) + unit_suffix
            return str(celsius) + unit_suffix
    except Exception:
        pass
    try:
        r = subprocess.run(['vcgencmd', 'measure_temp'],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if r.returncode == 0:
            raw = r.stdout.decode().replace("temp=", "").replace("'C", "").strip()
            celsius = float(raw)
            if TEMP_UNIT == 'F':
                return str(int(celsius * 9 / 5 + 32)) + unit_suffix
            return str(int(celsius)) + unit_suffix
    except Exception:
        pass
    return "--" + unit_suffix


def display_block_count_text():
    try:
        display_background_image('Block_HeightBG.png')
        # Block_HeightBG layout (128x160 after rotate 270):
        #   Block icon: occupies upper portion of screen
        #   Block height number: displayed large at the bottom
        #
        # Original TBM design: block number shown large at bottom of screen,
        # centered horizontally. Moved slightly lower (x=8) to better match original.
        btc_current_block = get_block_count()
        hard_font_size = 40
        block_num_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", hard_font_size)
        draw_centered_text(screen_buffer, btc_current_block, 8, 270, block_num_font)
    except Exception as e:
        print("Error creating block count text;", str(e))


def draw_screen1(currency):
    display_price_text(currency)  # temperature is now included inside display_price_text


def draw_screen2():
    fees_dict = get_recommended_fees()
    next_block_dict = get_next_block_info()
    unconfirmed_txs = get_unconfirmed_txs()
    display_background_image('TxsBG.png')
    # Original TBM design (doidotech/TBM v2.0.1) coordinates preserved exactly.
    high = int(fees_dict['fastestFee'])
    low = int(fees_dict['hourFee'])

    # Calculate font size for low fee (original: font_constant=86)
    low_number_of_chars = len(str(low))
    font_constant = 86
    if low_number_of_chars > 2:
        low_font_size = int(font_constant / low_number_of_chars)
    else:
        low_font_size = 43

    # Calculate font size for high fee
    high_number_of_chars = len(str(high))
    if high_number_of_chars > 2:
        high_font_size = int(font_constant / high_number_of_chars)
    else:
        high_font_size = 43

    # x position depending on digit count (original values)
    low_fee_x = 90 if low_number_of_chars == 3 else 85
    high_fee_x = 90 if high_number_of_chars == 3 else 85

    # Display low and high fees (original y positions: low=9, high=88)
    low_fees_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", low_font_size)
    high_fees_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", high_font_size)
    draw_left_justified_text(screen_buffer, str(low), low_fee_x, 9, 270, low_fees_font)
    draw_left_justified_text(screen_buffer, str(high), high_fee_x, 88, 270, high_fees_font)

    # Next block TX count - right-aligned (y=11 from right edge)
    transactions = int(next_block_dict['nTx'])
    txs_number_of_chars = len(str(transactions))
    font_constant = 112
    if txs_number_of_chars > 4:
        txs_font_size = int(font_constant / txs_number_of_chars)
    else:
        txs_font_size = 28
    txs_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", txs_font_size)
    draw_right_justified_text(screen_buffer, str(transactions), 43, 11, 270, txs_font)

    # Unconfirmed TX count - right-aligned (y=11 from right edge)
    unconfirmed_txs_number_of_chars = len(unconfirmed_txs)
    font_constant = 120
    if unconfirmed_txs_number_of_chars > 5:
        unconfirmed_txs_font_size = int(font_constant / unconfirmed_txs_number_of_chars)
    else:
        unconfirmed_txs_font_size = 24
    unconfirmed_txs_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", unconfirmed_txs_font_size)
    draw_right_justified_text(screen_buffer, unconfirmed_txs, 7, 11, 270, unconfirmed_txs_font)


def draw_screen3():
    display_block_count_text()


def draw_screen4():
    display_background_image('Screen1@288x.png')
    # Timezone: from wizard settings (config.ini [USER] timezone)
    tz_name = _wizard_settings.get('timezone', 'UTC')
    try:
        import pytz
        tz = pytz.timezone(tz_name)
        now = datetime.datetime.now(tz)
    except Exception:
        now = datetime.datetime.now()
    # Order (top to bottom on LCD): Month Day → Day of week → Time
    # After rotate(270): higher x = lower on screen
    # x=82 = top, x=43 = middle, x=15 = bottom (approx)
    month_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 22)
    day_font   = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 26)
    time_font  = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 30)
    # Month Day at top: shift up by 8px for better vertical balance
    draw_centered_text(screen_buffer, now.strftime('%B %d'),
                       get_inverted_x(8, 22), 270, month_font)
    # Day of week in middle
    draw_centered_text(screen_buffer, now.strftime('%A'),
                       get_inverted_x(51, 26), 270, day_font)
    # Time at bottom
    draw_centered_text(screen_buffer, now.strftime('%-I:%M %p'),
                       get_inverted_x(83, 30), 270, time_font)


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

    # Layout: network.png has labels at x=86~94 (Connections/Mempool) and x=24~47 (Hashrate/Blockchain)
    # Data values are placed BELOW the labels (smaller x = higher on screen in rot270 system)
    # x=55~72: data row for top section (below Connections/Mempool labels at x=86~94)
    # x=8~22:  data row for bottom section (below Hashrate/Blockchain labels at x=24~47)
    # Original design: value + unit on SAME line (e.g. "10 Peers", "8 MB")
    # A1 layout: font=11, x_top=62, x_bot=14, y_left=9, y_right=89
    data_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 11)

    # Connections (top-right quadrant, x=62): value + "Peers" on same line
    conn = get_connection_count()
    conn_str = str(conn) if conn is not False else "--"
    draw_left_justified_text(screen_buffer, conn_str + " Peers", 62, 9, 270, data_font)

    # Mempool (bottom-right quadrant, x=62): value + unit on same line
    mem = get_mempool_info()
    if mem and isinstance(mem, str) and len(mem.split()) >= 2:
        mem_val, mem_unit = mem.split()[0], mem.split()[1]
    else:
        mem_val, mem_unit = "--", "MB"
    draw_left_justified_text(screen_buffer, mem_val + " " + mem_unit, 62, 89, 270, data_font)

    # Hashrate (bottom-left quadrant, x=14): value + unit on same line
    hr = get_network_hash_ps()
    if hr and isinstance(hr, str) and len(hr.split()) >= 2:
        hr_val, hr_unit = hr.split()[0], hr.split()[1]
    else:
        hr_val, hr_unit = "--", "EH/s"
    draw_left_justified_text(screen_buffer, hr_val + " " + hr_unit, 14, 9, 270, data_font)

    # Blockchain size (top-left quadrant, x=14): value + unit on same line
    bs = get_blockchain_size()
    if bs and isinstance(bs, str) and len(bs.split()) >= 2:
        bs_val, bs_unit = bs.split()[0], bs.split()[1]
    else:
        bs_val, bs_unit = "--", "GB"
    draw_left_justified_text(screen_buffer, bs_val + " " + bs_unit, 14, 89, 270, data_font)


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

    # Same layout as Screen5 (Network): font=11, x_top=62, x_bot=14, y_left=9, y_right=89
    data_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 11)

    # Connections (top-right quadrant): value + "Peers" on same line
    draw_left_justified_text(screen_buffer, str(connections) + " Peers", 62, 9, 270, data_font)

    # Active channels (bottom-right quadrant): value + "Active" on same line
    draw_left_justified_text(screen_buffer, str(active_channels) + " Active", 62, 89, 270, data_font)

    bal = get_lnd_channel_balance()
    if not bal:
        return
    max_send, max_receive = bal
    send_val, send_unit = max_send.split()[0], max_send.split()[1]
    recv_val, recv_unit = max_receive.split()[0], max_receive.split()[1]

    # Max Send (top-left quadrant): value + unit on same line
    draw_left_justified_text(screen_buffer, send_val + " " + send_unit, 14, 9, 270, data_font)

    # Max Receive (bottom-left quadrant): value + unit on same line
    draw_left_justified_text(screen_buffer, recv_val + " " + recv_unit, 14, 89, 270, data_font)


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

    # Used space: large text
    draw_left_justified_text(screen_buffer, used_space, 59, 7, 270,
                             ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 20))
    # "Used out of X" with a space before disk_capacity for readability
    draw_left_justified_text(screen_buffer, "Used out of " + disk_capacity, 43, 7, 270,
                             ImageFont.truetype(poppins_fonts_path + "Poppins-Regular.ttf", 10))
    # Available space: right-aligned (space already included in classify_kilo_bytes output)
    draw_right_justified_text(screen_buffer, available_space + "  available", 13, 11, 270,
                              ImageFont.truetype(poppins_fonts_path + "Poppins-Regular.ttf", 10))
    # Progress bar
    draw_sb = ImageDraw.Draw(screen_buffer)
    x, y, w, h = 29, 7, 2, 140
    inner_h = int((used_pct * h) / 100) + y
    draw_sb.rectangle((x, y, x + w, y + h), outline=(255, 255, 255), fill=(255, 255, 255))
    draw_sb.rectangle((x, y, x + w, inner_h), outline=(0, 160, 0), fill=(0, 160, 0))


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
print('Running Umbrel LCD script - Version: 2.32.0 (Umbrel 1.x compatible)')
print(f'  Currency: {currency} | Screens: {userScreenChoices} | Temp: {TEMP_UNIT} | TZ: {_wizard_settings["timezone"]}')

# Apply timezone from wizard settings
os.environ['TZ'] = _wizard_settings['timezone']
try:
    time.tzset()
except AttributeError:
    pass  # Windows does not have time.tzset()

# Display umbrel logo on startup (duration configurable in config.ini)
display_background_image('umbrel_logo.png')
lcd_display(screen_buffer)
time.sleep(LOGO_DURATION)
# Prime the dissolve buffer with the logo frame
_prev_buffer = screen_buffer.copy()

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
            lcd_display_dissolve(screen_buffer)
            time.sleep(SCREEN1_DURATION)
    except Exception as e:
        print("Error showing screen1;", str(e))

    try:
        if "Screen2" in userScreenChoices:
            draw_screen2()
            lcd_display_dissolve(screen_buffer)
            time.sleep(SCREEN_DURATION)
    except Exception as e:
        print("Error showing screen2;", str(e))

    try:
        if "Screen3" in userScreenChoices:
            draw_screen3()
            lcd_display_dissolve(screen_buffer)
            time.sleep(SCREEN_DURATION)
    except Exception as e:
        print("Error showing screen3;", str(e))

    try:
        if "Screen4" in userScreenChoices:
            draw_screen4()
            lcd_display_dissolve(screen_buffer)
            time.sleep(SCREEN_DURATION)
    except Exception as e:
        print("Error showing screen4;", str(e))

    try:
        if "Screen5" in userScreenChoices:
            draw_screen5()
            lcd_display_dissolve(screen_buffer)
            time.sleep(SCREEN_DURATION)
    except Exception as e:
        print("Error showing screen5;", str(e))

    try:
        if "Screen6" in userScreenChoices:
            draw_screen6()
            lcd_display_dissolve(screen_buffer)
            time.sleep(SCREEN_DURATION)
    except Exception as e:
        print("Error showing screen6;", str(e))

    try:
        if "Screen7" in userScreenChoices:
            draw_screen7()
            lcd_display_dissolve(screen_buffer)
            time.sleep(SCREEN_DURATION)
    except Exception as e:
        print("Error showing screen7;", str(e))
