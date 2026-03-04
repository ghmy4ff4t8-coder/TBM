
#-------------------------------------------------------------------------------
#   Copyright (c) 2022 DOIDO Technologies
#   Version  : 2.7.0  (Umbrel 1.x compatible fork)
#   Location : github - forked & updated for Umbrel OS 1.x compatibility
#   Changes  :
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

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import time
import datetime
import numpy as np

# ---------------------------------------------------------------------------
# Use the bundled st7735_tbm driver instead of pimoroni/st7735-python.
# This driver is a direct port of the doido-technologies original library
# (v0.0.4.doidotech) with RPi.GPIO replaced by gpiod + spidev.
# It uses the correct MADCTL=0xC8, offset_left=0, offset_top=0 values
# for the TBM 1.8" 128x160 panel.
# ---------------------------------------------------------------------------
from st7735_tbm import ST7735

import urllib.request as urlreq
import certifi
import ssl
import json
import socket
import pathlib
import subprocess
import sys
from connections import test_tor, tor_request
import os
basedir = os.path.abspath(os.path.dirname(__file__))
import configparser
import requests

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
    invert=False
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

# Bitcoin RPC credentials (Umbrel defaults)
BITCOIN_RPC_USER = "umbrel"
BITCOIN_RPC_PASS = "moneyprintergobrrr"
BITCOIN_RPC_HOST = "127.0.0.1"
BITCOIN_RPC_PORT = 8332

# Bitcoin container names to try (Umbrel 1.x uses these)
BITCOIN_CONTAINER_NAMES = [
    "bitcoin_bitcoind_1",
    "bitcoin-bitcoind-1",
    "bitcoind",
]

# LND container names to try
LND_CONTAINER_NAMES = [
    "lightning_lnd_1",
    "lightning-lnd-1",
    "lnd",
]


# ---------------------------------------------------------------------------
# Pillow compatibility helper
# Pillow 10.0.0 removed draw.textsize(). Use draw.textbbox() instead.
# ---------------------------------------------------------------------------
def get_text_size(draw_obj, text, font):
    """Returns (width, height) of the rendered text. Pillow 10+ compatible."""
    try:
        bbox = draw_obj.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    except AttributeError:
        return draw_obj.textsize(text, font=font)


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


def display_icon(image, image_path, position, icon_size):
    picimage = Image.open(image_path).convert('RGBA')
    picimage = picimage.resize((icon_size, icon_size), Image.BICUBIC)
    rotated = picimage.rotate(270, expand=1)
    image.paste(rotated, position, rotated)


def draw_left_justified_text(image, text, xposition, yPosition,
                              angle, font, fill=(255, 255, 255)):
    tmp_draw = ImageDraw.Draw(image)
    width, height = get_text_size(tmp_draw, text, font=font)
    textimage = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    ImageDraw.Draw(textimage).text((0, 0), text, font=font, fill=fill)
    rotated = textimage.rotate(angle, expand=1)
    image.paste(rotated, (xposition, yPosition), rotated)


def draw_right_justified_text(image, text, xposition, yPosition,
                               angle, font, fill=(255, 255, 255)):
    tmp_draw = ImageDraw.Draw(image)
    width, height = get_text_size(tmp_draw, text, font=font)
    textimage = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    ImageDraw.Draw(textimage).text((0, 0), text, font=font, fill=fill)
    rotated = textimage.rotate(angle, expand=1)
    H = 160
    image.paste(rotated, (xposition, int((H - width) - yPosition)), rotated)


def draw_centered_text(image, text, xposition, angle, font,
                       fill=(255, 255, 255)):
    tmp_draw = ImageDraw.Draw(image)
    width, height = get_text_size(tmp_draw, text, font=font)
    textimage = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    ImageDraw.Draw(textimage).text((0, 0), text, font=font, fill=fill)
    rotated = textimage.rotate(angle, expand=1)
    H = 160
    image.paste(rotated, (xposition, int((H - width) / 2)), rotated)


def place_value(number):
    return "{:,}".format(number)


# ---------------------------------------------------------------------------
# Data-fetching helpers
# ---------------------------------------------------------------------------
def get_block_count():
    try:
        url = "https://blockchain.info/q/getblockcount"
        return tor_request(url).text
    except Exception as err:
        print("Error while getting current block:", str(err))
        return ""


def get_btc_price(currency):
    try:
        url = ("https://api.coingecko.com/api/v3/simple/price"
               "?ids=bitcoin&vs_currencies=" + currency)
        data = json.loads(tor_request(url).text)
        return int(data['bitcoin'][currency.lower()])
    except Exception as err:
        print("Error getting price from CoinGecko:", str(err))
        try:
            url = f"https://api.coinbase.com/v2/prices/BTC-{currency}/spot"
            data = requests.get(url, timeout=10).json()
            return int(float(data['data']['amount']))
        except Exception as err2:
            print("Error getting price from Coinbase:", str(err2))
            return ""


def get_recommended_fees():
    try:
        url = mempool_url + "/api/v1/fees/recommended"
        return json.loads(tor_request(url).text)
    except Exception as e:
        print("Error getting recommended fees;", str(e))
        return ""


def get_next_block_info():
    try:
        url = mempool_url + "/api/v1/fees/mempool-blocks"
        return json.loads(tor_request(url).text)[0]
    except Exception as e:
        print("Error getting next block info;", str(e))
        return ""


def get_unconfirmed_txs():
    try:
        url = mempool_url + "/api/mempool"
        return str(json.loads(tor_request(url).text)['count'])
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


def load_config(quiet=False):
    config_file = os.path.join(basedir, 'config.ini')
    CONFIG = configparser.ConfigParser()
    if quiet:
        CONFIG.read(config_file)
        return CONFIG
    if os.path.isfile(config_file):
        CONFIG.read(config_file)
        return CONFIG
    print("LCD app requires config.ini to run")


def check_umbrel_and_mempool():
    config = load_config(True)
    try:
        url = config['UMBREL']['url']
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
        draw_left_justified_text(screen_buffer, newPrice, font_x, 30, 270, price_font)

        cur_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 12)
        draw_right_justified_text(screen_buffer, currency, get_inverted_x(1, 12), 4, 270, cur_font)

        sat_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 14)
        draw_left_justified_text(screen_buffer, "SATS / " + currency,
                                 get_inverted_x(111, 14), 39, 270, sat_font)

        sat_val = str(int(100_000_000 / price)) if price else "0"
        n2 = len(sat_val)
        sf = int(200 / n2) if n2 > 4 else 50
        sat_font2 = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", sf)
        fx2 = get_corrected_x_position(50, sf, 24)
        draw_left_justified_text(screen_buffer, sat_val, fx2, 30, 270, sat_font2)
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
    draw_right_justified_text(screen_buffer, temperature, 3, 3, 270, temp_font)


def display_block_count_text():
    try:
        display_background_image('Block_HeightBG.png')
        block_x_pos = 72
        btc_current_block = get_block_count()
        font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 40)
        draw_centered_text(screen_buffer, btc_current_block,
                           get_inverted_x(block_x_pos, 40), 270, font)
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

    draw_left_justified_text(screen_buffer, str(low), low_x, 9, 270,
                             ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", low_fs))
    draw_left_justified_text(screen_buffer, str(high), high_x, 88, 270,
                             ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", high_fs))

    txs = int(next_block_dict['nTx'])
    txs_fs = int(112 / len(str(txs))) if len(str(txs)) > 4 else 28
    draw_left_justified_text(screen_buffer, str(txs), 43, 67, 270,
                             ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", txs_fs))

    u_n = len(unconfirmed_txs)
    u_fs = int(120 / u_n) if u_n > 5 else 24
    draw_left_justified_text(screen_buffer, unconfirmed_txs, 7, 64, 270,
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
                       get_inverted_x(16, 30), 270, time_font)
    draw_centered_text(screen_buffer, now.strftime('%A'),
                       get_inverted_x(59, 26), 270, day_font)
    draw_centered_text(screen_buffer, now.strftime('%B %d'),
                       get_inverted_x(91, 22), 270, month_font)


def draw_screen5():
    display_background_image('network.png')

    conn = get_connection_count()
    conn_str = str(conn)
    n = len(conn_str)
    conn_y = 23 if n == 2 else (27 if n == 1 else 19)
    conn_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 15)
    draw_left_justified_text(screen_buffer, conn_str, 68, conn_y, 270, conn_font)

    mem = get_mempool_info()
    mem_val, mem_unit = mem.split()[0], mem.split()[1]
    n = len(mem_val)
    mem_y = 101 if n == 2 else (108 if n == 1 else 98)
    mem_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 15)
    draw_left_justified_text(screen_buffer, mem_val, 68, mem_y, 270, mem_font)
    unit_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 9)
    draw_left_justified_text(screen_buffer, mem_unit, 55, 105, 270, unit_font)
    draw_left_justified_text(screen_buffer, "Peers", 55, 22, 270, unit_font)

    hr = get_network_hash_ps()
    hr_val, hr_unit = hr.split()[0], hr.split()[1]
    n = len(hr_val)
    hr_y = 23 if n == 2 else (27 if n == 1 else 19)
    hr_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 15)
    draw_left_justified_text(screen_buffer, hr_val, 22, hr_y, 270, hr_font)
    hr_unit_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 9)
    draw_left_justified_text(screen_buffer, hr_unit, 8, 22, 270, hr_unit_font)

    bs = get_blockchain_size()
    bs_val, bs_unit = bs.split()[0], bs.split()[1]
    n = len(bs_val)
    bs_y = 101 if n == 2 else (108 if n == 1 else 98)
    bs_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 15)
    draw_left_justified_text(screen_buffer, bs_val, 22, bs_y, 270, bs_font)
    bs_unit_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 9)
    draw_left_justified_text(screen_buffer, bs_unit, 8, 105, 270, bs_unit_font)


def draw_screen6():
    display_background_image('payment_channels.png')
    result = get_lnd_info()
    if not result:
        return
    connections, active_channels = result

    n = len(str(connections))
    conn_y = 23 if n == 2 else (27 if n == 1 else 19)
    conn_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 15)
    draw_left_justified_text(screen_buffer, str(connections), 68, conn_y, 270, conn_font)

    n = len(str(active_channels))
    ch_y = 101 if n == 2 else (108 if n == 1 else 98)
    ch_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 15)
    draw_left_justified_text(screen_buffer, str(active_channels), 68, ch_y, 270, ch_font)

    label_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 9)
    draw_left_justified_text(screen_buffer, "Channels", 55, 98, 270, label_font)
    draw_left_justified_text(screen_buffer, "Peers", 55, 22, 270, label_font)

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
    draw_left_justified_text(screen_buffer, send_val, 22, send_y, 270, send_font)

    n = len(recv_val)
    recv_y_map = {1: 108, 2: 101, 3: 98, 4: 93, 5: 90}
    recv_y = recv_y_map.get(n, 90)
    recv_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 15)
    draw_left_justified_text(screen_buffer, recv_val, 22, recv_y, 270, recv_font)

    btc_font = ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 10)
    draw_left_justified_text(screen_buffer, recv_unit, 8, 100, 270, btc_font)
    draw_left_justified_text(screen_buffer, send_unit, 8, 22, 270, btc_font)


def draw_screen7():
    display_background_image('storage.png')
    storage_info = get_disk_storage_info()
    if not storage_info:
        return

    used_space, disk_capacity, available_space, used_pct = (
        storage_info[1], storage_info[0], storage_info[2], storage_info[3])

    draw_left_justified_text(screen_buffer, used_space, 59, 7, 270,
                             ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 20))
    draw_left_justified_text(screen_buffer, "Used out of " + disk_capacity, 44, 7, 270,
                             ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 11))
    draw_right_justified_text(screen_buffer, available_space + " available", 13, 11, 270,
                              ImageFont.truetype(poppins_fonts_path + "Poppins-Bold.ttf", 11))

    # Progress bar drawn directly on screen_buffer
    draw_sb = ImageDraw.Draw(screen_buffer)
    x, y, w, h = 29, 7, 2, 140
    inner_h = int((used_pct * h) / 100) + y
    draw_sb.rectangle((x, y, x + w, y + h), outline=(255, 255, 255), fill=(255, 255, 255))
    draw_sb.rectangle((x, y, x + w, inner_h), outline=(0, 160, 0), fill=(0, 160, 0))


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------
print('Running Umbrel LCD script Version 2.7.0 (Umbrel 1.x compatible)')

# Display umbrel logo for 60 seconds on startup
display_background_image('umbrel_logo.png')
lcd_display(screen_buffer)
time.sleep(60)

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
            time.sleep(60)
    except Exception as e:
        print("Error showing screen1;", str(e))

    try:
        if "Screen2" in userScreenChoices:
            draw_screen2()
            lcd_display(screen_buffer)
            time.sleep(30)
    except Exception as e:
        print("Error showing screen2;", str(e))

    try:
        if "Screen3" in userScreenChoices:
            draw_screen3()
            lcd_display(screen_buffer)
            time.sleep(30)
    except Exception as e:
        print("Error showing screen3;", str(e))

    try:
        if "Screen4" in userScreenChoices:
            draw_screen4()
            lcd_display(screen_buffer)
            time.sleep(30)
    except Exception as e:
        print("Error showing screen4;", str(e))

    try:
        if "Screen5" in userScreenChoices:
            draw_screen5()
            lcd_display(screen_buffer)
            time.sleep(30)
    except Exception as e:
        print("Error showing screen5;", str(e))

    try:
        if "Screen6" in userScreenChoices:
            draw_screen6()
            lcd_display(screen_buffer)
            time.sleep(30)
    except Exception as e:
        print("Error showing screen6;", str(e))

    try:
        if "Screen7" in userScreenChoices:
            draw_screen7()
            lcd_display(screen_buffer)
            time.sleep(30)
    except Exception as e:
        print("Error showing screen7;", str(e))
