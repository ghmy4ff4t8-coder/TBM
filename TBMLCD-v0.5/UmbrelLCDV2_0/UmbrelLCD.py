
#-------------------------------------------------------------------------------
#   Copyright (c) 2022 DOIDO Technologies
#   Version  : 2.2.0  (Umbrel 1.x compatible fork)
#   Location : github - forked & updated for Umbrel OS 1.x compatibility
#   Changes  :
#     v2.3.0 (2024-03):
#       - FIXED: LCD noisy/garbled display - pimoroni/st7735-python v1.0.0
#         default width=80 (Pimoroni 0.96" product) does NOT match TBM 1.8"
#         LCD (128x160). Must explicitly set width=128, height=160, and
#         offset_left=2, offset_top=1 to match the ST7735 memory map.
#         Without this, the CASET/RASET window is wrong -> noise/garbage.
#       - FIXED: rotation parameter: pimoroni v1.0.0 default is rotation=90
#         (for landscape). TBM uses portrait (rotation=0) but image_to_data()
#         now applies rotation internally, so set rotation=0 here.
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

# pimoroni/st7735-python v1.0.0 uses lowercase module name
import st7735 as TFT

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
SPEED_HZ = 4000000


# Raspberry Pi configuration.
# pimoroni/st7735-python v1.0.0 requires GPIO pin numbers as strings.
# Use "GPIO24" format (BCM numbering) or "PIN18" format (physical pin numbering).
DC  = "GPIO24"   # physical Pin 18
RST = "GPIO25"   # physical Pin 22
SPI_PORT   = 0
SPI_DEVICE = 0   # CE0 = cs=0

# Create TFT LCD display class.
# pimoroni/st7735-python v1.0.0 API changes:
#   - 'rgb' parameter is now 'bgr' (True = BGR colour order)
#   - 'dc' and 'rst' now accept strings like "GPIO24", not integers
#   - 'cs' is the SPI chip-select number (0 or 1), not a GPIO pin
#   - 'disp.buffer' no longer exists; create your own PIL Image and pass to disp.display(image)
#
# CRITICAL for TBM 1.8" LCD (128x160):
#   - width=128, height=160 MUST be set explicitly.
#     The library default is width=80 (for Pimoroni's own 0.96" display).
#     Using width=80 on a 128-pixel-wide panel causes the CASET address window
#     to be wrong, resulting in a noisy/garbled display.
#   - offset_left=2, offset_top=1 are the correct offsets for the ST7735
#     memory map when driving a 128x160 panel (COLS=132, ROWS=162):
#       offset_left = (132 - 128) // 2 = 2
#       offset_top  = (162 - 160) // 2 = 1
#   - rotation=0 for portrait orientation (TBM mounts the LCD in portrait).
#     image_to_data() in the library applies np.rot90 internally.
#   - bgr=False for this panel (most generic ST7735 128x160 panels are RGB)
disp = TFT.ST7735(
    port=SPI_PORT,
    cs=SPI_DEVICE,
    dc=DC,
    rst=RST,
    width=128,
    height=160,
    rotation=0,
    offset_left=2,
    offset_top=1,
    spi_speed_hz=SPEED_HZ,
    bgr=False,
    invert=False
)

# Initialize display.
disp.begin()

# Create a persistent off-screen image buffer.
# All drawing is done to this buffer; call disp.display(screen_buffer) to push to LCD.
screen_buffer = Image.new('RGB', (WIDTH, HEIGHT))

# Shape drawing object for the persistent buffer (used only for the progress bar in screen7)
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
# This was the PRIMARY cause of the white screen on Umbrel 1.x
# ---------------------------------------------------------------------------
def get_text_size(draw_obj, text, font):
    """
    Returns (width, height) of the rendered text.
    Compatible with both old and new Pillow versions.
    """
    try:
        # Pillow >= 10.0.0
        bbox = draw_obj.textbbox((0, 0), text, font=font)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        return width, height
    except AttributeError:
        # Pillow < 10.0.0 (legacy fallback)
        return draw_obj.textsize(text, font=font)


# ---------------------------------------------------------------------------
# Bitcoin RPC helper - direct HTTP + docker exec fallback
# ---------------------------------------------------------------------------
def bitcoin_rpc(method, params=None, chain="main"):
    """
    Calls bitcoin RPC directly via HTTP. Falls back to docker exec on failure.
    """
    if params is None:
        params = []
    payload = json.dumps({
        "jsonrpc": "1.0",
        "id": "tbm-lcd",
        "method": method,
        "params": params
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
    except Exception as e:
        # Fallback: docker exec
        return bitcoin_cli_exec(method, params, chain)


def bitcoin_cli_exec(method, params=None, chain="main"):
    """
    Executes bitcoin-cli inside the docker container.
    Tries multiple container names for Umbrel 1.x compatibility.
    """
    if params is None:
        params = []

    chain_flag = ["-chain=test"] if chain == "test" else []

    for container in BITCOIN_CONTAINER_NAMES:
        try:
            cmd = ["docker", "exec", container, "bitcoin-cli"] + chain_flag + [method] + [str(p) for p in params]
            response = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)
            if response.returncode == 0:
                output = response.stdout.decode('utf-8').strip()
                try:
                    return json.loads(output)
                except json.JSONDecodeError:
                    return output
        except Exception:
            continue
    raise Exception(f"Could not execute bitcoin-cli {method} via any known container")


def lncli_exec(method, params=None, network="mainnet"):
    """
    Executes lncli inside the docker container.
    Tries multiple container names for Umbrel 1.x compatibility.
    """
    if params is None:
        params = []

    for container in LND_CONTAINER_NAMES:
        try:
            cmd = ["docker", "exec", container, "lncli", f"--network={network}", method] + [str(p) for p in params]
            response = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)
            if response.returncode == 0:
                output = response.stdout.decode('utf-8').strip()
                try:
                    return json.loads(output)
                except json.JSONDecodeError:
                    return output
        except Exception:
            continue
    raise Exception(f"Could not execute lncli {method} via any known container")


# ---------------------------------------------------------------------------
# Define a function to calculate an inverted x co-ordinate.
# ---------------------------------------------------------------------------
def get_inverted_x(currentX, objectSize):
    invertedX = WIDTH - (currentX + objectSize)
    return invertedX

# Define a function to calculate an x position that is
# corrected for smaller font sizes to re-center the text
# vertically inside the original bigger font space
def get_corrected_x_position(ideal_font_height,smaller_font_height,ideal_x_position):
    try:
        smaller_font_x_correction = int((ideal_font_height - smaller_font_height)/2)
        smaller_font_x_position = smaller_font_x_correction + ideal_x_position
        return smaller_font_x_position
    except Exception as e:
        print("Error while calculating corrected x position; ",str(e))
        return ideal_x_position

# Define a function to draw the lcd background image.
# NOTE: draws onto the global screen_buffer
def display_background_image(image_name):
    global screen_buffer, draw
    image_path = images_path+image_name
    position = (0,0)
    picimage = Image.open(image_path)
    # Convert to RGBA
    picimage = picimage.convert('RGBA')
    # Resize the image
    picimage = picimage.resize((160, 128), Image.BICUBIC)
    # Rotate image
    rotated = picimage.rotate(270, expand=1)
    # Create a fresh buffer and paste the background
    screen_buffer = Image.new('RGB', (WIDTH, HEIGHT))
    screen_buffer.paste(rotated, position, rotated)
    # Recreate draw object bound to the new buffer
    draw = ImageDraw.Draw(screen_buffer)

# Define a function to draw an icon.
def display_icon(image, image_path, position,icon_size):
    # Load an image.
    picimage = Image.open(image_path)
    # Convert to RGBA
    picimage = picimage.convert('RGBA')
    # Resize the image
    picimage = picimage.resize((icon_size, icon_size), Image.BICUBIC)
    # Rotate image
    rotated = picimage.rotate(270, expand=1)
    # Paste the image into the screen buffer
    image.paste(rotated, position, rotated)


# Define a function to create left justified text.
def draw_left_justified_text(image, text, xposition, yPosition, angle, font, fill=(255,255,255)):
    # Get rendered font width and height.
    tmp_draw = ImageDraw.Draw(image)
    width, height = get_text_size(tmp_draw, text, font=font)
    # Create a new image with transparent background to store the text.
    textimage = Image.new('RGBA', (width, height), (0,0,0,0))
    # Render the text.
    textdraw = ImageDraw.Draw(textimage)
    textdraw.text((0,0), text, font=font, fill=fill)
    W, H = (128,160)
    # Rotate the text image.
    rotated = textimage.rotate(angle, expand=1)
    # Paste the text into the image, using it as a mask for transparency.
    xCordinate = xposition
    yCordinate = yPosition
    image.paste(rotated, (xCordinate,yCordinate), rotated)

# Define a function to create right justified text.
def draw_right_justified_text(image, text, xposition, yPosition, angle, font, fill=(255,255,255)):
    # Get rendered font width and height.
    tmp_draw = ImageDraw.Draw(image)
    width, height = get_text_size(tmp_draw, text, font=font)
    # Create a new image with transparent background to store the text.
    textimage = Image.new('RGBA', (width, height), (0,0,0,0))
    # Render the text.
    textdraw = ImageDraw.Draw(textimage)
    textdraw.text((0,0), text, font=font, fill=fill)
    W, H = (128,160)
    # Rotate the text image.
    rotated = textimage.rotate(angle, expand=1)
    # Paste the text into the image, using it as a mask for transparency.
    xCordinate = xposition
    yCordinate = int((H-width)-yPosition)
    image.paste(rotated, (xCordinate,yCordinate), rotated)

# Define a function to create centered text.
def draw_centered_text(image, text, xposition, angle, font, fill=(255,255,255)):
    # Get rendered font width and height.
    tmp_draw = ImageDraw.Draw(image)
    width, height = get_text_size(tmp_draw, text, font=font)
    # Create a new image with transparent background to store the text.
    textimage = Image.new('RGBA', (width, height), (0,0,0,0))
    # Render the text.
    textdraw = ImageDraw.Draw(textimage)
    textdraw.text((0,0), text, font=font, fill=fill)
    W, H = (128,160)
    # Rotate the text image.
    rotated = textimage.rotate(angle, expand=1)
    # Paste the text into the image, using it as a mask for transparency.
    xCordinate = xposition
    yCordinate = int((H-width)/2)
    image.paste(rotated, (xCordinate,yCordinate), rotated)

# Define a function to return a comma seperated number
def place_value(number):
    return ("{:,}".format(number))

# Define a function to get current block height in the longest chain
def get_block_count():
    """Gets current block height in the longest chain."""

    try:
        url = "https://blockchain.info/q/getblockcount"
        currentBlock = tor_request(url)
        currentBlockString = currentBlock.text
        return currentBlockString
    except Exception as err:
        print("Error while getting current block: "+ str(err))
        return ""

# Define a function to get bitcoin price
def get_btc_price(currency):
    """Gets bitcoin price."""

    try:
        # Try CoinGecko first
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies="+currency
        currentPrice = tor_request(url)
        coin_prices_dict = json.loads(currentPrice.text)
        bitcoin_price_dict = coin_prices_dict['bitcoin']
        lowercase_currency = currency.lower()
        price = int(bitcoin_price_dict[lowercase_currency])
        return price
    except Exception as err:
        print("Error while getting price from CoinGecko: "+ str(err))
        # Fallback: try Coinbase API
        try:
            url = f"https://api.coinbase.com/v2/prices/BTC-{currency}/spot"
            response = requests.get(url, timeout=10)
            data = response.json()
            price = int(float(data['data']['amount']))
            return price
        except Exception as err2:
            print("Error while getting price from Coinbase: "+ str(err2))
            return ""


# Define a function get the the recommended fees
def get_recommended_fees():
    """Gets the the recommended fees."""

    try:
        url = mempool_url + "/api/v1/fees/recommended"
        json_response = tor_request(url)
        fees_dict = json.loads(json_response.text)
        return fees_dict
    except Exception as e:
        print("Error while getting recommended fees; ",str(e))
        return ""

# Define a function get the the next block info
def get_next_block_info():
    """Gets the the next block info."""

    try:
        url = mempool_url + "/api/v1/fees/mempool-blocks"
        json_response = tor_request(url)
        blocks_dict = json.loads(json_response.text)
        # Use the first block
        next_block_dict = blocks_dict[0]
        return next_block_dict
    except Exception as e:
        print("Error while getting next block info; ",str(e))
        return ""

# Define a function to get the number of unconfirmed transactions
def get_unconfirmed_txs():
    """Gets the number of unconfirmed transactions."""

    try:
        url = mempool_url + "/api/mempool"
        json_response = tor_request(url)
        unconfirmed_dict = json.loads(json_response.text)
        unconfirmed_txs = str(unconfirmed_dict['count'])
        return unconfirmed_txs
    except Exception as e:
        print("Error while getting unconfirmed txs; ",str(e))
        return ""

# Define a function to auto fit price text
def display_price_text(currency):
    try:
        # Display background
        display_background_image('Screen1@288x.png')
        # Display bitcoin icon
        display_icon(screen_buffer, images_path+'bitcoin_seeklogo.png', (80,2),27)
        # Display satoshi icon
        display_icon(screen_buffer, images_path+'Satoshi_regular_elipse.png', (27,2),27)
        # Get the price
        price = get_btc_price(currency)
        newPrice = str(price)
        # Calculate a font size
        number_of_chars = len(newPrice)
        # Check for divide by zero
        if (number_of_chars != 0):
            font_size = int(195/number_of_chars)
        else:
            font_size = 12

        # Display the price
        ideal_font_height = 39
        smaller_font_height = font_size
        ideal_x_position = 79
        font_x_position =  get_corrected_x_position(ideal_font_height,smaller_font_height,ideal_x_position)
        price_font = ImageFont.truetype(poppins_fonts_path+"Poppins-Bold.ttf", font_size)
        draw_left_justified_text(screen_buffer, newPrice, font_x_position,30, 270, price_font, fill=(255,255,255))

        # Display currency
        currency_font_size = 12
        currency_font = ImageFont.truetype(poppins_fonts_path+"Poppins-Bold.ttf", currency_font_size)
        draw_right_justified_text(screen_buffer, currency, get_inverted_x(1,currency_font_size),4, 270, currency_font, fill=(255,255,255))

        # display SAT / USD string
        sat_font_size = 14
        sats_msg = "SATS / "+currency
        sat_font = ImageFont.truetype(poppins_fonts_path+"Poppins-Bold.ttf", sat_font_size)
        draw_left_justified_text(screen_buffer, sats_msg, get_inverted_x(111,sat_font_size),39, 270, sat_font, fill=(255,255,255))

        # Calculate and display SAT/USD value
        if price != 0:
            sat_per_usd_int = int(100000000/price)
        else:
            sat_per_usd_int = 0
        sat_per_usd_str = str(sat_per_usd_int)
        # Calculate a font size
        number_of_chars = len(sat_per_usd_str)
        # Check for divide by zero
        if (number_of_chars > 4):
            sat_font_size = int(200/number_of_chars)
        else:
            sat_font_size = 50
        sat_font = ImageFont.truetype(poppins_fonts_path+"Poppins-Bold.ttf", sat_font_size)
        ideal_font_height = 50
        smaller_font_height = sat_font_size
        ideal_x_position = 24
        font_x_position =  get_corrected_x_position(ideal_font_height,smaller_font_height,ideal_x_position)
        draw_left_justified_text(screen_buffer, sat_per_usd_str, font_x_position,30, 270, sat_font, fill=(255,255,255))
    except Exception as e:
        print("Error while creating price text; ",str(e))

# Define a function to display temperature
def display_temperature():
    try:
        # Try vcgencmd first (Raspberry Pi)
        temp_result = subprocess.run(['vcgencmd', 'measure_temp'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if temp_result.returncode == 0:
            temp_string = temp_result.stdout.decode('utf-8')
            raw_temp = temp_string.replace("temp=","").replace("'C","").strip()
            raw_temp_float = float(raw_temp)
            temperature = str(int(raw_temp_float))+"'C"
        else:
            # Fallback: read from thermal zone (works on both RPi and x86)
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp_milli = int(f.read().strip())
                temperature = str(int(temp_milli/1000))+"'C"
    except Exception:
        temperature = "--'C"

    # display temperature
    temp_font = ImageFont.truetype(poppins_fonts_path+"Poppins-Bold.ttf", 12)
    draw_right_justified_text(screen_buffer, temperature, 3,3, 270, temp_font, fill=(255,255,255))


# Define a function to auto fit block count text
def display_block_count_text():
    try:
        # Display background
        display_background_image('Block_HeightBG.png')
        block_x_pos = 72
        # Get current bitcoin block
        btc_current_block = get_block_count()
        # Display the current block text
        hard_font_size = 40
        block_num_font = ImageFont.truetype(poppins_fonts_path+"Poppins-Bold.ttf", hard_font_size)
        draw_centered_text(screen_buffer, btc_current_block, get_inverted_x(block_x_pos,hard_font_size), 270, block_num_font, fill=(255,255,255))
    except Exception as e:
        print("Error while creating block count text; ",str(e))

def get_tor_status():
    """Checks if tor is running."""

    try:
        tor = test_tor()
        if tor['status']:
            print("Tor Connected")
            return True
        else:
            print("Could not connect to Tor. The LCD application requires Tor to run.")
            return False
    except Exception as e:
        print("Error while getting Tor status; ",str(e))
        return False

def load_config(quiet=False):
    """Loads the config file."""

    # Load Config
    basedir = os.path.abspath(os.path.dirname(__file__))
    config_file = os.path.join(basedir, 'config.ini')
    CONFIG = configparser.ConfigParser()
    if quiet:
        CONFIG.read(config_file)
        return (CONFIG)

    # Check that config file exists
    if os.path.isfile(config_file):
        CONFIG.read(config_file)
        return (CONFIG)
    else:
        print("LCD app requires config.ini to run")

def check_umbrel_and_mempool():
    """Checks for local mempool app."""

    umbrel = False
    mempool = False
    config = load_config(True)
    config_file = os.path.join(basedir, 'config.ini')
    try:
        url = config['UMBREL']['url']
    except Exception:
        url = 'http://umbrel.local/'

    # Test if this url can be reached
    try:
        result = tor_request(url)
        if not isinstance(result, requests.models.Response):
            raise Exception(f'Did not get a return from {url}')
        if not result.ok:
            raise Exception(f'Reached {url} but an error occured.')
        umbrel = True
    except Exception as e:
        print("    Umbrel not found:" + str(e))

    if umbrel:
        # Checking if Mempool.space app is installed
        # Umbrel 1.x mempool port is still 3006
        try:
            url = config['MEMPOOL']['url']
        except Exception:
            url = 'http://umbrel.local:3006/'
        try:
            result = tor_request(url)
            if not isinstance(result, requests.models.Response):
                raise Exception('Did not get a return from mempool url')
            if not result.ok:
                raise Exception('Reached Mempool app but an error occured.')

            block_height = tor_request(url + '/api/blocks/tip/height').json()
            # Found mempool
            mempool = True
        except Exception as e:
            print("Mempool not found:" + str(e))

    if mempool:
        return True
    else:
        return False

def get_mempool_base_url():
    """Determines the mempool base url."""

    mempool_status = check_umbrel_and_mempool()
    print(f"Local Mempool app status = {mempool_status}")

    if mempool_status:
        # return local mempool app url
        return "http://umbrel.local:3006"
    else:
        # return web app mempool url
        return "https://mempool.space"


def classify_bytes(num_of_bytes):
    """Converts number to convenient units of bytes"""

    num_of_bytes = int(num_of_bytes)

    one_terabyte = 1000*1000*1000*1000
    one_gigabyte = 1000*1000*1000
    one_megabyte = 1000*1000
    one_kilobyte = 1000

    if num_of_bytes > one_terabyte:
        return "{0} TB".format(round(num_of_bytes/one_terabyte))
    elif num_of_bytes > one_gigabyte:
        return "{0} GB".format(round(num_of_bytes/one_gigabyte))
    elif num_of_bytes > one_megabyte:
        return "{0} MB".format(round(num_of_bytes/one_megabyte))
    elif num_of_bytes > one_kilobyte:
        return "{0} KB".format(round(num_of_bytes/one_kilobyte))
    else:
        return "{0} B".format(num_of_bytes)


def get_blockchain_size():
    """Gets blockchain size via RPC or docker exec"""

    global blockchain_type
    try:
        chain = "test" if blockchain_type == "test" else "main"
        size_dictionary = bitcoin_rpc("getblockchaininfo", chain=chain)
        size_on_disk = int(size_dictionary["size_on_disk"])
        blockchain_type = size_dictionary["chain"]
        return classify_bytes(size_on_disk)
    except Exception as e:
        print("Error while getting blockchain size; ",str(e))
        return False

def get_connection_count():
    """Gets the number of peers"""
    try:
        chain = "test" if blockchain_type == "test" else "main"
        result = bitcoin_rpc("getconnectioncount", chain=chain)
        return int(result)
    except Exception as e:
        print("Error while getting number of peers; ",str(e))
        return False

def get_mempool_info():
    """Gets mempool number of bytes"""

    try:
        chain = "test" if blockchain_type == "test" else "main"
        mempool_info_dictionary = bitcoin_rpc("getmempoolinfo", chain=chain)
        mempool_bytes = int(mempool_info_dictionary["bytes"])
        return classify_bytes(mempool_bytes)
    except Exception as e:
        print("Error while getting mempool bytes; ",str(e))
        return False

def get_network_hash_ps():
    """Gets the number of network hashes per second"""

    one_kilo_hash = 1000
    one_mega_hash = 1000000
    one_giga_hash = 1000000000
    one_tera_hash = 1000000000000
    one_peta_hash = 1000000000000000
    one_exa_hash = 1000000000000000000
    one_zeta_hash = 1000000000000000000000
    one_yotta_hash = 1000000000000000000000000

    try:
        chain = "test" if blockchain_type == "test" else "main"
        hash_per_second = float(bitcoin_rpc("getnetworkhashps", chain=chain))

        if hash_per_second > one_yotta_hash:
            return "{0} YH/s".format(round(hash_per_second/one_yotta_hash))
        elif hash_per_second > one_zeta_hash:
            return "{0} ZH/s".format(round(hash_per_second/one_zeta_hash))
        elif hash_per_second > one_exa_hash:
            return "{0} EH/s".format(round(hash_per_second/one_exa_hash))
        elif hash_per_second > one_peta_hash:
            return "{0} PH/s".format(round(hash_per_second/one_peta_hash))
        elif hash_per_second > one_tera_hash:
            return "{0} TH/s".format(round(hash_per_second/one_tera_hash))
        elif hash_per_second > one_giga_hash:
            return "{0} GH/s".format(round(hash_per_second/one_giga_hash))
        elif hash_per_second > one_mega_hash:
            return "{0} MH/s".format(round(hash_per_second/one_mega_hash))
        elif hash_per_second > one_kilo_hash:
            return "{0} kH/s".format(round(hash_per_second/one_kilo_hash))
        else:
            return "{0} H/s".format(hash_per_second)
    except Exception as e:
        print("Error while getting hash rate; ",str(e))
        return False

def remove_extra_spaces(the_string):
    """Removes extra spaces in a string"""

    string_list = list(the_string.strip())
    previous_char = ""

    for i in range(len(string_list)):
        if i == 0:
            previous_char = string_list[i]
        else:
            if(previous_char == ' ')and(string_list[i] == ' '):
                string_list[i] = ''
            else:
                previous_char = string_list[i]

    return "".join(string_list)

def classify_kilo_bytes(num_of_bytes):
    """Converts kilobytes to convenient units of bytes"""

    num_of_bytes = int(num_of_bytes)*1024

    one_terabyte = 1000*1000*1000*1000
    one_gigabyte = 1000*1000*1000
    one_megabyte = 1000*1000
    one_kilobyte = 1000

    if num_of_bytes > one_terabyte:
        return "{:.1f} TB".format(num_of_bytes/one_terabyte)
    elif num_of_bytes > one_gigabyte:
        return "{:.1f} GB".format(num_of_bytes/one_gigabyte)
    elif num_of_bytes > one_megabyte:
        return "{:.1f} MB".format(num_of_bytes/one_megabyte)
    elif num_of_bytes > one_kilobyte:
        return "{:.1f} KB".format(num_of_bytes/one_kilobyte)
    else:
        return "{0} B".format(num_of_bytes)

def get_disk_storage_info():
    """Gets information on how the disk is used"""

    # Try common disk paths for Umbrel setups (SSD, NVMe, SD card)
    disk_paths = ["/dev/sda1", "/dev/sda", "/dev/mmcblk0p1", "/dev/nvme0n1p1"]

    for disk_path in disk_paths:
        try:
            command = f"df {disk_path}"
            response = subprocess.run(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if response.returncode != 0:
                continue
            disk_info = response.stdout.decode('utf-8')
            disk_info_array = disk_info.split('\n')
            if len(disk_info_array) < 2:
                continue
            usage_string = disk_info_array[1]
            cleaned_usage_string = remove_extra_spaces(usage_string)
            usage_list = cleaned_usage_string.split()
            if len(usage_list) < 5:
                continue
            disk_capacity = classify_kilo_bytes(int(usage_list[1]))
            used_space = classify_kilo_bytes(int(usage_list[2]))
            available_space = classify_kilo_bytes(int(usage_list[1]) - int(usage_list[2]))
            used_percentage = int(usage_list[4].replace("%",""))
            return [disk_capacity, used_space, available_space, used_percentage]
        except Exception:
            continue

    # Final fallback: use root filesystem
    try:
        command = "df /"
        response = subprocess.run(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        disk_info = response.stdout.decode('utf-8')
        disk_info_array = disk_info.split('\n')
        usage_string = disk_info_array[1]
        cleaned_usage_string = remove_extra_spaces(usage_string)
        usage_list = cleaned_usage_string.split()
        disk_capacity = classify_kilo_bytes(int(usage_list[1]))
        used_space = classify_kilo_bytes(int(usage_list[2]))
        available_space = classify_kilo_bytes(int(usage_list[1]) - int(usage_list[2]))
        used_percentage = int(usage_list[4].replace("%",""))
        return [disk_capacity, used_space, available_space, used_percentage]
    except Exception as e:
        print("Error while getting disk information; ",str(e))
        return False

def get_lnd_info():
    """Gets the lnd connections and active channels"""

    try:
        network = "testnet" if blockchain_type == "test" else "mainnet"
        lnd_info_dictionary = lncli_exec("getinfo", network=network)
        connections = int(lnd_info_dictionary['num_peers'])
        active_channels = int(lnd_info_dictionary['num_active_channels'])
        return connections, active_channels
    except Exception as e:
        print("Error while getting number of lnd peers and active channels; ",str(e))
        return False


def classify_satoshis(num_of_satoshis):
    """
        Converts satoshis to convenient units of
        bitcoin or satoshis
    """

    num_of_satoshis = int(num_of_satoshis)

    one_bitcoin = 100000000
    megaBitcoin = 1000000*one_bitcoin
    kiloBitcoin = 1000*one_bitcoin
    kiloSatoshi = 1000

    if num_of_satoshis >= megaBitcoin:
        return "{0} MBTC".format(round(num_of_satoshis/megaBitcoin))
    elif num_of_satoshis >= kiloBitcoin:
        return "{0} kBTC".format(round(num_of_satoshis/kiloBitcoin))
    elif num_of_satoshis >= one_bitcoin:
        return "{0} BTC".format(round(num_of_satoshis/one_bitcoin))
    elif num_of_satoshis >= kiloSatoshi:
        return "{0} kSats".format(round(num_of_satoshis/kiloSatoshi))
    else:
        return "{0} Sats".format(num_of_satoshis)


def get_lnd_channel_balance():
    """Gets the lnd wallet max send, max receive balance."""

    try:
        network = "testnet" if blockchain_type == "test" else "mainnet"
        channel_balance_dictionary = lncli_exec("channelbalance", network=network)

        local_balance_dict = channel_balance_dictionary['local_balance']
        max_send = classify_satoshis(int(local_balance_dict['sat']))
        remote_balance_dict = channel_balance_dictionary['remote_balance']
        max_receive = classify_satoshis(int(remote_balance_dict['sat']))
        return max_send, max_receive
    except Exception as e:
        print("Error while getting lnd wallet max send and max receive balance; ",str(e))
        return False

def get_btc_network():
    """
        Get's BTC network from bitcoin RPC or docker ps
    """

    try:
        global blockchain_type
        # Try RPC first
        try:
            info = bitcoin_rpc("getblockchaininfo")
            chain = info.get("chain", "main")
            if chain == "test":
                blockchain_type = "test"
            else:
                blockchain_type = "main"
            return
        except Exception:
            pass

        # Fallback: docker ps
        command = ["docker","ps","--filter","name=bitcoin_bitcoind_1"]
        response = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        docker_info = response.stdout.decode('utf-8')

        if "-chain=tes" in docker_info:
            blockchain_type = "test"
        else:
            blockchain_type = "main"
    except Exception as e:
        print("Error while getting BTC network type; ",str(e))


# Define a function to draw Screen1
def draw_screen1(currency):
    # Display current bitcoin price
    display_price_text(currency)
    # Display temperature
    display_temperature()


# Define a function to draw Screen2
def draw_screen2():
    # Get all the data from APIs
    fees_dict = get_recommended_fees()
    next_block_dict = get_next_block_info()
    unconfirmed_txs = get_unconfirmed_txs()

    # Display background
    display_background_image('TxsBG.png')

    # Get the low and high fees
    high = int(fees_dict['fastestFee'])
    low = int(fees_dict['hourFee'])

    # Calculate a font size for the low value
    low_number_of_chars = len(str(low))
    font_constant = 86
    if (low_number_of_chars > 2):
        low_font_size = int(font_constant/low_number_of_chars)
    else:
        low_font_size = 43

    # Calculate a font size for the high value
    high_number_of_chars = len(str(high))
    if (high_number_of_chars > 2):
        high_font_size = int(font_constant/high_number_of_chars)
    else:
        high_font_size = 43

    # Set x position depending on font size
    if low_number_of_chars == 3:
        low_fee_x = 90
    else:
        low_fee_x = 85
    if high_number_of_chars == 3:
        high_fee_x = 90
    else:
        high_fee_x = 85

    # Display the low and high fees
    low_fees_font = ImageFont.truetype(poppins_fonts_path+"Poppins-Bold.ttf", low_font_size)
    high_fees_font = ImageFont.truetype(poppins_fonts_path+"Poppins-Bold.ttf", high_font_size)
    draw_left_justified_text(screen_buffer, str(low), low_fee_x,9, 270, low_fees_font, fill=(255,255,255))
    draw_left_justified_text(screen_buffer, str(high), high_fee_x,88, 270, high_fees_font, fill=(255,255,255))

    # Get the number of transactions
    transactions = int(next_block_dict['nTx'])
    txs_number_of_chars = len(str(transactions))
    font_constant = 112
    if (txs_number_of_chars > 4):
        txs_font_size = int(font_constant/txs_number_of_chars)
    else:
        txs_font_size = 28

    # Display the transactions
    txs_x = 43
    txs_font = ImageFont.truetype(poppins_fonts_path+"Poppins-Bold.ttf", txs_font_size)
    draw_left_justified_text(screen_buffer, str(transactions), txs_x,67, 270, txs_font, fill=(255,255,255))

    # Get the number of unconfirmed transactions
    unconfirmed_txs_number_of_chars = len(unconfirmed_txs)

    font_constant = 120
    if (unconfirmed_txs_number_of_chars > 5):
        unconfirmed_txs_font_size = int(font_constant/unconfirmed_txs_number_of_chars)
    else:
        unconfirmed_txs_font_size = 24

    # Display the number of unconfirmed transactions
    unconfirmed_txs_x = 7
    unconfirmed_txs_font = ImageFont.truetype(poppins_fonts_path+"Poppins-Bold.ttf", unconfirmed_txs_font_size)
    draw_left_justified_text(screen_buffer, unconfirmed_txs, unconfirmed_txs_x,64, 270, unconfirmed_txs_font, fill=(255,255,255))


# Define a function to draw Screen3
def draw_screen3():
    # Display block count
    display_block_count_text()


# Define a function to draw Screen4
def draw_screen4():
    # Display background
    display_background_image('Screen1@288x.png')

    # Get current date and time
    current_date_and_time = datetime.datetime.now()
    #Convert time object to AM/PM format
    time_string = current_date_and_time.strftime('%-I:%M %p')
    # Get the day
    day_string = current_date_and_time.strftime('%A')
    # Get the month
    month_string = current_date_and_time.strftime('%B %d')

    # Display the time
    time_font_size = 30
    time_font = ImageFont.truetype(poppins_fonts_path+"Poppins-Bold.ttf", time_font_size)
    draw_centered_text(screen_buffer, time_string, get_inverted_x(16,time_font_size), 270, time_font, fill=(255,255,255))

    # Display week day
    day_font_size = 26
    day_font = ImageFont.truetype(poppins_fonts_path+"Poppins-Bold.ttf", day_font_size)
    draw_centered_text(screen_buffer, day_string, get_inverted_x(59,day_font_size), 270, day_font, fill=(255,255,255))

    # Display the month
    month_font_size = 22
    month_font = ImageFont.truetype(poppins_fonts_path+"Poppins-Bold.ttf", month_font_size)
    draw_centered_text(screen_buffer, month_string, get_inverted_x(91,month_font_size), 270, month_font, fill=(255,255,255))


def draw_screen5():
    """Displays the bitcoin network information"""

    # Display background
    display_background_image('network.png')

    # connection count
    connection_count = get_connection_count()

    # Display the number of peers
    connection_count_x = 68
    connections_number_of_chars = len(str(connection_count))
    if connections_number_of_chars == 2:
        connection_count_y = 23
    elif connections_number_of_chars == 1:
        connection_count_y = 27
    else:
        connection_count_y = 19

    connection_count_font_size = 15
    connection_count_font = ImageFont.truetype(poppins_fonts_path+"Poppins-Bold.ttf", connection_count_font_size)
    draw_left_justified_text(screen_buffer, str(connection_count), connection_count_x,connection_count_y, 270, connection_count_font, fill=(255,255,255))

    # mempool bytes
    mempool_bytes_data = get_mempool_info()
    mempool_bytes = mempool_bytes_data.split()[0]
    mempool_bytes_units = mempool_bytes_data.split()[1]
    # Display the number of mempool bytes
    mempool_bytes_x = 68
    mempool_bytes_number_of_chars = len(str(mempool_bytes))
    if mempool_bytes_number_of_chars == 2:
        mempool_bytes_y = 101
    elif mempool_bytes_number_of_chars == 1:
        mempool_bytes_y = 108
    else:
        mempool_bytes_y = 98

    mempool_bytes_font_size = 15
    mempool_bytes_font = ImageFont.truetype(poppins_fonts_path+"Poppins-Bold.ttf", mempool_bytes_font_size)
    draw_left_justified_text(screen_buffer, str(mempool_bytes), mempool_bytes_x,mempool_bytes_y, 270, mempool_bytes_font, fill=(255,255,255))

    # Display mempool bytes units
    mempool_units_font_size = 9
    mempool_units_font = ImageFont.truetype(poppins_fonts_path+"Poppins-Bold.ttf", mempool_units_font_size)
    draw_left_justified_text(screen_buffer, mempool_bytes_units, 55,105, 270, mempool_units_font, fill=(255,255,255))
    draw_left_justified_text(screen_buffer, "Peers", 55,22, 270, mempool_units_font, fill=(255,255,255))

    # Hash rate
    network_hash_rate_data = get_network_hash_ps()
    network_hash_rate = network_hash_rate_data.split()[0]
    network_hash_rate_units = network_hash_rate_data.split()[1]
    # Display the value of network hash rate
    network_hash_rate_x = 22
    network_hash_rate_number_of_chars = len(str(network_hash_rate))
    if network_hash_rate_number_of_chars == 2:
        network_hash_rate_y = 23
    elif network_hash_rate_number_of_chars == 1:
        network_hash_rate_y = 27
    else:
        network_hash_rate_y = 19

    network_hash_rate_font_size = 15
    network_hash_rate_font = ImageFont.truetype(poppins_fonts_path+"Poppins-Bold.ttf", network_hash_rate_font_size)
    draw_left_justified_text(screen_buffer, str(network_hash_rate), network_hash_rate_x,network_hash_rate_y, 270, network_hash_rate_font, fill=(255,255,255))

    # Display network hash rate units
    network_hash_rate_units_font_size = 9
    network_hash_rate_units_font = ImageFont.truetype(poppins_fonts_path+"Poppins-Bold.ttf", network_hash_rate_units_font_size)
    draw_left_justified_text(screen_buffer, network_hash_rate_units, 8,22, 270, network_hash_rate_units_font, fill=(255,255,255))

    # Blockchain size
    blockchain_size_data = get_blockchain_size()
    blockchain_size = blockchain_size_data.split()[0]
    blockchain_size_units = blockchain_size_data.split()[1]
    # Display the value of blockchain size
    blockchain_size_x = 22
    blockchain_size_number_of_chars = len(str(blockchain_size))
    if blockchain_size_number_of_chars == 2:
        blockchain_size_y = 101
    elif blockchain_size_number_of_chars == 1:
        blockchain_size_y = 108
    else:
        blockchain_size_y = 98

    blockchain_size_font_size = 15
    blockchain_size_font = ImageFont.truetype(poppins_fonts_path+"Poppins-Bold.ttf", blockchain_size_font_size)
    draw_left_justified_text(screen_buffer, str(blockchain_size), blockchain_size_x,blockchain_size_y, 270, blockchain_size_font, fill=(255,255,255))

    # Display blockchain size units
    blockchain_size_units_font_size = 9
    blockchain_size_units_font = ImageFont.truetype(poppins_fonts_path+"Poppins-Bold.ttf", blockchain_size_units_font_size)
    draw_left_justified_text(screen_buffer, blockchain_size_units, 8,105, 270, blockchain_size_units_font, fill=(255,255,255))

def draw_screen6():
    """Displays the payment channels information"""

    # Display background
    display_background_image('payment_channels.png')

    # lnd connections and active channels
    connections,active_channels = get_lnd_info()

    # Connections
    connection_count = connections
    # Display the number of peers
    connection_count_x = 68
    connections_number_of_chars = len(str(connection_count))
    if connections_number_of_chars == 2:
        connection_count_y = 23
    elif connections_number_of_chars == 1:
        connection_count_y = 27
    else:
        connection_count_y = 19

    connection_count_font_size = 15
    connection_count_font = ImageFont.truetype(poppins_fonts_path+"Poppins-Bold.ttf", connection_count_font_size)
    draw_left_justified_text(screen_buffer, str(connection_count), connection_count_x,connection_count_y, 270, connection_count_font, fill=(255,255,255))

    # Active channels
    active_channels_x = 68
    active_channels_number_of_chars = len(str(active_channels))
    if active_channels_number_of_chars == 2:
        active_channels_y = 101
    elif active_channels_number_of_chars == 1:
        active_channels_y = 108
    else:
        active_channels_y = 98

    active_channels_font_size = 15
    active_channels_font = ImageFont.truetype(poppins_fonts_path+"Poppins-Bold.ttf", active_channels_font_size)
    draw_left_justified_text(screen_buffer, str(active_channels), active_channels_x,active_channels_y, 270, active_channels_font, fill=(255,255,255))

    # Display Connections and active channels units
    connections_units_font_size = 9
    connections_units_font = ImageFont.truetype(poppins_fonts_path+"Poppins-Bold.ttf", connections_units_font_size)
    draw_left_justified_text(screen_buffer, "Channels", 55,98, 270, connections_units_font, fill=(255,255,255))
    draw_left_justified_text(screen_buffer, "Peers", 55,22, 270, connections_units_font, fill=(255,255,255))

    # lnd wallet max send and max receive
    temp_max_send,temp_max_receive = get_lnd_channel_balance()
    max_send = temp_max_send.split()[0]
    max_send_units = temp_max_send.split()[1]
    max_receive = temp_max_receive.split()[0]
    max_receive_units = temp_max_receive.split()[1]

    # Max send
    max_send_x = 22
    max_send_number_of_chars = len(str(max_send))
    if max_send_number_of_chars == 1:
        max_send_y = 27
    elif max_send_number_of_chars == 2:
        max_send_y = 23
    elif max_send_number_of_chars == 3:
        max_send_y = 19
    elif max_send_number_of_chars == 4:
        max_send_y = 15
    elif max_send_number_of_chars == 5:
        max_send_y = 10
    else:
        max_send_y = 6

    max_send_font_size = 15
    max_send_font = ImageFont.truetype(poppins_fonts_path+"Poppins-Bold.ttf", max_send_font_size)
    draw_left_justified_text(screen_buffer, str(max_send), max_send_x,max_send_y, 270, max_send_font, fill=(255,255,255))

    # Max receive
    max_receive_x = 22
    max_receive_number_of_chars = len(str(max_receive))
    if max_receive_number_of_chars == 1:
        max_receive_y = 108
    elif max_receive_number_of_chars == 2:
        max_receive_y = 101
    elif max_receive_number_of_chars == 3:
        max_receive_y = 98
    elif max_receive_number_of_chars == 4:
        max_receive_y = 93
    elif max_receive_number_of_chars == 5:
        max_receive_y = 90
    else:
        max_receive_y = 90

    max_receive_font_size = 15
    max_receive_font = ImageFont.truetype(poppins_fonts_path+"Poppins-Bold.ttf", max_receive_font_size)
    draw_left_justified_text(screen_buffer, str(max_receive), max_receive_x,max_receive_y, 270, max_receive_font, fill=(255,255,255))

    # Display max send and max receive bitcoin units
    bitcoin_units_font_size = 10
    bitcoin_units_font = ImageFont.truetype(poppins_fonts_path+"Poppins-Bold.ttf", bitcoin_units_font_size)
    draw_left_justified_text(screen_buffer, max_receive_units, 8,100, 270, bitcoin_units_font, fill=(255,255,255))
    draw_left_justified_text(screen_buffer, max_send_units, 8,22, 270, bitcoin_units_font, fill=(255,255,255))

def draw_screen7():
    """Displays the disk storage information"""

    # Display background
    display_background_image('storage.png')

    # Disk usage info
    storage_info = get_disk_storage_info()

    # Display used space
    used_space = storage_info[1]
    used_space_font_size = 20
    used_space_font = ImageFont.truetype(poppins_fonts_path+"Poppins-Bold.ttf", used_space_font_size)
    draw_left_justified_text(screen_buffer, used_space, 59,7, 270, used_space_font, fill=(255,255,255))

    # Display space capacity
    disk_capacity = storage_info[0]
    disk_capacity_string = "Used out of "+ disk_capacity
    disk_capacity_font_size = 11
    disk_capacity_font = ImageFont.truetype(poppins_fonts_path+"Poppins-Bold.ttf", disk_capacity_font_size)
    draw_left_justified_text(screen_buffer, disk_capacity_string, 44,7, 270, disk_capacity_font, fill=(255,255,255))

    # Display available space
    available_space = storage_info[2]
    available_space_string = available_space+" available"
    available_space_font_size = 11
    available_space_font = ImageFont.truetype(poppins_fonts_path+"Poppins-Bold.ttf", available_space_font_size)
    draw_right_justified_text(screen_buffer, available_space_string, 13,11, 270, available_space_font, fill=(255,255,255))

    # Progress bar - draw directly onto screen_buffer
    draw_sb = ImageDraw.Draw(screen_buffer)
    width = 2
    height = 140
    x = 29
    y = 7
    used_percentage = int(storage_info[3])
    inner_bar_height = int((used_percentage*height)/100)+y
    draw_sb.rectangle((x, y, width+x, height+y), outline=(255, 255, 255), fill=(255, 255, 255))
    draw_sb.rectangle((x, y, width+x, inner_bar_height), outline=(0, 160, 0), fill=(0, 160, 0))


# ---------------------------------------------------------------------------
# Start the display of images now.
# ---------------------------------------------------------------------------
print('Running Umbrel 1.8 Inch LCD script Version 2.2.0 (Umbrel 1.x compatible)')

# Display umbrel logo first for 60 seconds
display_background_image('umbrel_logo.png')
disp.display(screen_buffer)
time.sleep(60)

# An initial check if Tor is running
tor_status = get_tor_status()

# Initial check for umbrel and mempool
mempool_status = check_umbrel_and_mempool()
print(f"Local Mempool app status = {mempool_status}")

# Display other screens in a loop
while True:
    # Get BTC network; testnet or mainnet
    get_btc_network()

    # First screen 60s
    try:
        # Set mempool url
        mempool_url = get_mempool_base_url()
        print(f"current_mempool_url = {mempool_url}")

        if "Screen1" in userScreenChoices:
            draw_screen1(currency)
            disp.display(screen_buffer)
            time.sleep(60)
    except Exception as e:
            print("Error while showing screen1; ",str(e))

    # Second screen 30s
    try:
        if "Screen2" in userScreenChoices:
            draw_screen2()
            disp.display(screen_buffer)
            time.sleep(30)
    except Exception as e:
        print("Error while showing screen2; ",str(e))

    # Third screen 30s
    try:
        if "Screen3" in userScreenChoices:
            draw_screen3()
            disp.display(screen_buffer)
            time.sleep(30)
    except Exception as e:
        print("Error while showing screen3; ",str(e))

    # Fourth screen 30s
    try:
        if "Screen4" in userScreenChoices:
            draw_screen4()
            disp.display(screen_buffer)
            time.sleep(30)
    except Exception as e:
        print("Error while showing screen4; ",str(e))

    # Fifth screen 30s
    try:
        if "Screen5" in userScreenChoices:
            draw_screen5()
            disp.display(screen_buffer)
            time.sleep(30)
    except Exception as e:
        print("Error while showing screen5; ",str(e))

    # Sixth screen 30s
    try:
        if "Screen6" in userScreenChoices:
            draw_screen6()
            disp.display(screen_buffer)
            time.sleep(30)
    except Exception as e:
        print("Error while showing screen6; ",str(e))

    # Seventh screen 30s
    try:
        if "Screen7" in userScreenChoices:
            draw_screen7()
            disp.display(screen_buffer)
            time.sleep(30)
    except Exception as e:
        print("Error while showing screen7; ",str(e))
