
# -------------------------------------------------------------------------------
#   ST7735 TFT LCD Driver for TBM (The Bitcoin Machine)
#   Based on doido-technologies/st7735-python (v0.0.4.doidotech)
#   Original: Copyright (c) 2014 Adafruit Industries, Author: Tony DiCola
#
#   Modified for Umbrel OS 1.x compatibility:
#   - Replaced RPi.GPIO with gpiod 2.x API (Linux GPIO character device)
#   - Replaced RPi.GPIO SPI with spidev direct calls
#   - Removed all pimoroni/st7735-python dependencies
#
#   Hardware: TBM 1.8" 128×160 ST7735 panel
#   - ST7735_COLS = 128, ST7735_ROWS = 160  (no offset needed)
#   - MADCTL = 0xC0 (MY=1, MX=1, MV=0, BGR order when bgr=True)
#     v2.10.0 base (0x40, MX=1) + MY=1 to correct upside-down.
#
#   Display orientation pipeline:
#   1. UmbrelLCD.py draws all content rotated 270° CCW onto a 128×160 buffer.
#   2. image_to_data() converts the buffer to RGB565 (no additional flip).
#   3. MADCTL=0x40 (MX=1, BGR) sets the hardware scan direction so that
#      the 270° CCW software rotation produces correct portrait orientation.
#   4. The RGB565 data is sent to the LCD via SPI.
#
#   Net transform: rotate(270 CCW) + MADCTL MX=1 = correct portrait.
# -------------------------------------------------------------------------------

import numbers
import time
import numpy as np
import spidev
import gpiod

# ---------------------------------------------------------------------------
# ST7735 register constants
# ---------------------------------------------------------------------------
ST7735_TFTWIDTH  = 128
ST7735_TFTHEIGHT = 160
ST7735_COLS      = 128
ST7735_ROWS      = 160

ST7735_NOP     = 0x00
ST7735_SWRESET = 0x01
ST7735_SLPOUT  = 0x11
ST7735_NORON   = 0x13
ST7735_INVOFF  = 0x20
ST7735_INVON   = 0x21
ST7735_DISPON  = 0x29
ST7735_CASET   = 0x2A
ST7735_RASET   = 0x2B
ST7735_RAMWR   = 0x2C
ST7735_MADCTL  = 0x36
ST7735_COLMOD  = 0x3A
ST7735_FRMCTR1 = 0xB1
ST7735_FRMCTR2 = 0xB2
ST7735_FRMCTR3 = 0xB3
ST7735_INVCTR  = 0xB4
ST7735_PWCTR1  = 0xC0
ST7735_PWCTR2  = 0xC1
ST7735_PWCTR4  = 0xC3
ST7735_PWCTR5  = 0xC4
ST7735_VMCTR1  = 0xC5
ST7735_GMCTRP1 = 0xE0
ST7735_GMCTRN1 = 0xE1


def image_to_data(image):
    """Convert a PIL Image to a flat list of 16-bit RGB565 bytes.

    UmbrelLCD.py applies rotate(270 CCW) to all images before calling this
    function. Combined with MADCTL=0x40 (MX=1, BGR), this produces the
    correct portrait orientation on hardware.
    No additional row/column flip is needed here.
    """
    pb = np.array(image.convert('RGB')).astype('uint16')
    color = ((pb[:, :, 0] & 0xF8) << 8) | \
            ((pb[:, :, 1] & 0xFC) << 3) | \
             (pb[:, :, 2] >> 3)
    return np.dstack(((color >> 8) & 0xFF, color & 0xFF)).flatten().tolist()


class ST7735(object):
    """ST7735 TFT LCD driver using spidev + gpiod 2.x (no RPi.GPIO)."""

    def __init__(self, port, cs, dc, rst=None,
                 width=ST7735_TFTWIDTH, height=ST7735_TFTHEIGHT,
                 offset_left=None, offset_top=None,
                 invert=False, bgr=False, spi_speed_hz=16000000):
        self._width  = width
        self._height = height
        self._invert = invert
        self._bgr    = bgr
        self._dc_pin = dc
        self._rst_pin = rst
        self._offset_left = offset_left if offset_left is not None else (ST7735_COLS - width) // 2
        self._offset_top  = offset_top  if offset_top  is not None else (ST7735_ROWS - height) // 2

        # SPI setup
        self._spi = spidev.SpiDev(port, cs)
        self._spi.mode = 0
        self._spi.lsbfirst = False
        self._spi.max_speed_hz = spi_speed_hz

        # GPIO setup via gpiod 2.x
        # Try gpiochip0 (Pi 4), gpiochip4 (Pi 5), gpiochip1 as fallback
        self._gpio_chip = None
        for chip_path in ('/dev/gpiochip0', '/dev/gpiochip4', '/dev/gpiochip1'):
            try:
                self._gpio_chip = gpiod.Chip(chip_path)
                break
            except Exception:
                continue
        if self._gpio_chip is None:
            raise RuntimeError('Cannot open any gpiochip device. Is gpiod installed?')

        pin_config = {
            dc: gpiod.LineSettings(
                direction=gpiod.line.Direction.OUTPUT,
                output_value=gpiod.line.Value.INACTIVE)
        }
        if rst is not None:
            pin_config[rst] = gpiod.LineSettings(
                direction=gpiod.line.Direction.OUTPUT,
                output_value=gpiod.line.Value.ACTIVE)

        self._gpio_request = self._gpio_chip.request_lines(
            config=pin_config, consumer='st7735-tbm')

        self.reset()
        self._init()

    def _set_dc(self, value):
        v = gpiod.line.Value.ACTIVE if value else gpiod.line.Value.INACTIVE
        self._gpio_request.set_value(self._dc_pin, v)

    def send(self, data, is_data=True, chunk_size=4096):
        """Write bytes to the display."""
        self._set_dc(1 if is_data else 0)
        if isinstance(data, numbers.Number):
            data = [data & 0xFF]
        for i in range(0, len(data), chunk_size):
            self._spi.xfer3(data[i:i + chunk_size])

    def command(self, data):
        self.send(data, False)

    def data(self, data):
        self.send(data, True)

    def reset(self):
        """Hardware reset via RST pin (if connected)."""
        if self._rst_pin is not None:
            self._gpio_request.set_value(self._rst_pin, gpiod.line.Value.ACTIVE)
            time.sleep(0.500)
            self._gpio_request.set_value(self._rst_pin, gpiod.line.Value.INACTIVE)
            time.sleep(0.500)
            self._gpio_request.set_value(self._rst_pin, gpiod.line.Value.ACTIVE)
            time.sleep(0.500)

    def begin(self):
        """Deprecated stub — initialisation happens in __init__."""
        pass

    def _init(self):
        """ST7735 initialisation sequence (doido-technologies original)."""
        self.command(ST7735_SWRESET)
        time.sleep(0.150)

        self.command(ST7735_SLPOUT)
        time.sleep(0.500)

        self.command(ST7735_FRMCTR1)    # Frame rate - normal mode
        self.data([0x01, 0x2C, 0x2D])

        self.command(ST7735_FRMCTR2)    # Frame rate - idle mode
        self.data([0x01, 0x2C, 0x2D])

        self.command(ST7735_FRMCTR3)    # Frame rate - partial mode
        self.data([0x01, 0x2C, 0x2D, 0x01, 0x2C, 0x2D])

        self.command(ST7735_INVCTR)
        self.data(0x07)

        self.command(ST7735_PWCTR1)
        self.data([0xA2, 0x02, 0x84])

        self.command(ST7735_PWCTR2)
        self.data([0x0A, 0x00])

        self.command(ST7735_PWCTR4)
        self.data([0x8A, 0x2A])

        self.command(ST7735_PWCTR5)
        self.data([0x8A, 0xEE])

        self.command(ST7735_VMCTR1)
        self.data(0x0E)

        self.command(ST7735_INVON if self._invert else ST7735_INVOFF)

        # MADCTL: MY=0, MX=0, MV=0
        # MX=0 (bit 6) = column address left-to-right (no horizontal flip)
        # MY=0 (bit 7) = row address top-to-bottom (default)
        # BGR bit (bit 3): 0 = BGR order, 1 = RGB order
        #
        # With software rotate(270, expand=1) in UmbrelLCD.py:
        #   rotate(270 CCW) + MX=0 = correct portrait orientation (no LR flip)
        #
        # bgr=True  → 0x00 (MX=0, BGR)
        # bgr=False → 0x08 (MX=0, RGB)
        self.command(ST7735_MADCTL)
        self.data(0x00 if self._bgr else 0x08)

        self.command(ST7735_COLMOD)
        self.data(0x05)                 # 16-bit colour

        self.command(ST7735_GMCTRP1)
        self.data([0x02, 0x1C, 0x07, 0x12, 0x37, 0x32, 0x29, 0x2D,
                   0x29, 0x25, 0x2B, 0x39, 0x00, 0x01, 0x03, 0x10])

        self.command(ST7735_GMCTRN1)
        self.data([0x03, 0x1D, 0x07, 0x06, 0x2E, 0x2C, 0x29, 0x2D,
                   0x2E, 0x2E, 0x37, 0x3F, 0x00, 0x00, 0x02, 0x10])

        self.command(ST7735_NORON)
        time.sleep(0.10)

        self.command(ST7735_DISPON)
        time.sleep(0.100)

    def set_window(self, x0=0, y0=0, x1=None, y1=None):
        """Set the pixel address window for subsequent RAMWR commands."""
        if x1 is None:
            x1 = self._width - 1
        if y1 is None:
            y1 = self._height - 1

        x0 += self._offset_left
        x1 += self._offset_left
        y0 += self._offset_top
        y1 += self._offset_top

        self.command(ST7735_CASET)
        self.data([x0 >> 8, x0 & 0xFF, x1 >> 8, x1 & 0xFF])

        self.command(ST7735_RASET)
        self.data([y0 >> 8, y0 & 0xFF, y1 >> 8, y1 & 0xFF])

        self.command(ST7735_RAMWR)

    def display(self, image):
        """Write a PIL Image (RGB, width×height) to the LCD."""
        self.set_window()
        self.data(image_to_data(image))
