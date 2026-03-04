
# -------------------------------------------------------------------------------
#   ST7735 TFT LCD Driver for TBM (The Bitcoin Machine)
#   Based on doido-technologies/st7735-python (v0.0.4.doidotech)
#   Original: Copyright (c) 2014 Adafruit Industries, Author: Tony DiCola
#
#   Modified for Umbrel OS 1.x compatibility:
#   - Replaced RPi.GPIO with gpiod 2.x API (Linux GPIO character device)
#   - Replaced RPi.GPIO SPI with spidev direct calls
#   - Removed all pimoroni/st7735-python dependencies
#   - Kept original MADCTL=0xC8, ST7735_COLS=128, ST7735_ROWS=160
#     (doido-technologies values, NOT pimoroni's 132x162)
#
#   gpiod 2.x API changes (gpiod >= 2.0):
#   - chip.get_line() + line.request() REMOVED
#   - New API: chip.request_lines(config={offset: LineSettings(...)}, ...)
#   - set_value() now takes gpiod.line.Value.ACTIVE / INACTIVE
#
#   Key hardware parameters for TBM 1.8" 128x160 ST7735 panel:
#   - offset_left = 0  (ST7735_COLS=128, panel width=128, no offset needed)
#   - offset_top  = 0  (ST7735_ROWS=160, panel height=160, no offset needed)
#   - MADCTL = 0xC8    (MX=1, MY=1, MV=0, RGB mode)
# -------------------------------------------------------------------------------

import numbers
import time
import numpy as np
import spidev
import gpiod

# ST7735 register constants
ST7735_TFTWIDTH  = 128
ST7735_TFTHEIGHT = 160
ST7735_COLS      = 128
ST7735_ROWS      = 160

ST7735_NOP     = 0x00
ST7735_SWRESET = 0x01
ST7735_RDDID   = 0x04
ST7735_RDDST   = 0x09
ST7735_SLPIN   = 0x10
ST7735_SLPOUT  = 0x11
ST7735_PTLON   = 0x12
ST7735_NORON   = 0x13
ST7735_INVOFF  = 0x20
ST7735_INVON   = 0x21
ST7735_DISPOFF = 0x28
ST7735_DISPON  = 0x29
ST7735_CASET   = 0x2A
ST7735_RASET   = 0x2B
ST7735_RAMWR   = 0x2C
ST7735_RAMRD   = 0x2E
ST7735_PTLAR   = 0x30
ST7735_MADCTL  = 0x36
ST7735_COLMOD  = 0x3A
ST7735_FRMCTR1 = 0xB1
ST7735_FRMCTR2 = 0xB2
ST7735_FRMCTR3 = 0xB3
ST7735_INVCTR  = 0xB4
ST7735_DISSET5 = 0xB6
ST7735_PWCTR1  = 0xC0
ST7735_PWCTR2  = 0xC1
ST7735_PWCTR3  = 0xC2
ST7735_PWCTR4  = 0xC3
ST7735_PWCTR5  = 0xC4
ST7735_VMCTR1  = 0xC5
ST7735_RDID1   = 0xDA
ST7735_RDID2   = 0xDB
ST7735_RDID3   = 0xDC
ST7735_RDID4   = 0xDD
ST7735_GMCTRP1 = 0xE0
ST7735_GMCTRN1 = 0xE1
ST7735_PWCTR6  = 0xFC


def image_to_data(image):
    """Convert a PIL image to 16-bit RGB565 bytes (no rotation applied).
    The TBM drawing code already rotates elements 270 degrees before writing
    to the screen buffer, so we send the buffer as-is.
    """
    pb = np.array(image.convert('RGB')).astype('uint16')
    color = ((pb[:, :, 0] & 0xF8) << 8) | ((pb[:, :, 1] & 0xFC) << 3) | (pb[:, :, 2] >> 3)
    return np.dstack(((color >> 8) & 0xFF, color & 0xFF)).flatten().tolist()


class ST7735(object):
    """ST7735 TFT LCD driver using spidev + gpiod (no RPi.GPIO dependency)."""

    def __init__(self, port, cs, dc, rst=None,
                 width=ST7735_TFTWIDTH, height=ST7735_TFTHEIGHT,
                 offset_left=None, offset_top=None,
                 invert=False, bgr=False, spi_speed_hz=16000000):
        """Initialise the ST7735 display.

        :param port:         SPI port number (e.g. 0)
        :param cs:           SPI chip-select number (e.g. 0)
        :param dc:           GPIO pin number (BCM) for Data/Command
        :param rst:          GPIO pin number (BCM) for Reset (optional)
        :param width:        Display width in pixels
        :param height:       Display height in pixels
        :param offset_left:  Column offset in ST7735 RAM
        :param offset_top:   Row offset in ST7735 RAM
        :param invert:       Invert display colours
        :param bgr:          True if panel uses BGR colour order (fixes blue icons)
        :param spi_speed_hz: SPI clock speed in Hz
        """
        self._width  = width
        self._height = height
        self._invert = invert
        self._bgr    = bgr
        self._dc_pin = dc
        self._rst_pin = rst

        # Offsets: doido-technologies uses COLS=128, ROWS=160 (same as panel)
        # so default offset is 0 for both axes.
        self._offset_left = offset_left if offset_left is not None else (ST7735_COLS - width) // 2
        self._offset_top  = offset_top  if offset_top  is not None else (ST7735_ROWS - height) // 2

        # --- SPI setup ---
        self._spi = spidev.SpiDev(port, cs)
        self._spi.mode = 0
        self._spi.lsbfirst = False
        self._spi.max_speed_hz = spi_speed_hz

        # --- GPIO setup via gpiod 2.x API ---
        # gpiod 2.x completely replaced the 1.x API:
        #   OLD (1.x): chip.get_line(n) + line.request(type=LINE_REQ_DIR_OUT)
        #   NEW (2.x): chip.request_lines(config={n: LineSettings(direction=Direction.OUTPUT)})
        #
        # Try gpiochip0 first (Pi 4), fall back to gpiochip4 (Pi 5)
        self._gpio_chip = None
        for chip_path in ('/dev/gpiochip0', '/dev/gpiochip4', '/dev/gpiochip1'):
            try:
                chip = gpiod.Chip(chip_path)
                self._gpio_chip = chip
                self._gpio_chip_path = chip_path
                break
            except Exception:
                continue
        if self._gpio_chip is None:
            raise RuntimeError('Cannot open any gpiochip device. Is gpiod installed?')

        # Build pin config dict for gpiod 2.x request_lines()
        dc_settings = gpiod.LineSettings(
            direction=gpiod.line.Direction.OUTPUT,
            output_value=gpiod.line.Value.INACTIVE
        )
        pin_config = {dc: dc_settings}

        if rst is not None:
            rst_settings = gpiod.LineSettings(
                direction=gpiod.line.Direction.OUTPUT,
                output_value=gpiod.line.Value.ACTIVE
            )
            pin_config[rst] = rst_settings

        self._gpio_request = self._gpio_chip.request_lines(
            config=pin_config,
            consumer='st7735-tbm'
        )

        self.reset()
        self._init()

    def _set_dc(self, value):
        # gpiod 2.x uses gpiod.line.Value enum instead of integers
        v = gpiod.line.Value.ACTIVE if value else gpiod.line.Value.INACTIVE
        self._gpio_request.set_value(self._dc_pin, v)

    def send(self, data, is_data=True, chunk_size=4096):
        """Write bytes to the display. is_data=True for pixel data, False for commands."""
        self._set_dc(1 if is_data else 0)
        if isinstance(data, numbers.Number):
            data = [data & 0xFF]
        # spidev xfer3 handles large transfers; chunk if needed
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
        """Send the ST7735 initialisation command sequence.
        This is identical to the doido-technologies original, which is known
        to work correctly with the TBM 1.8" 128x160 panel.
        """
        self.command(ST7735_SWRESET)    # Software reset
        time.sleep(0.150)

        self.command(ST7735_SLPOUT)     # Out of sleep mode
        time.sleep(0.500)

        self.command(ST7735_FRMCTR1)    # Frame rate ctrl - normal mode
        self.data(0x01)
        self.data(0x2C)
        self.data(0x2D)

        self.command(ST7735_FRMCTR2)    # Frame rate ctrl - idle mode
        self.data(0x01)
        self.data(0x2C)
        self.data(0x2D)

        self.command(ST7735_FRMCTR3)    # Frame rate ctrl - partial mode
        self.data(0x01)
        self.data(0x2C)
        self.data(0x2D)
        self.data(0x01)
        self.data(0x2C)
        self.data(0x2D)

        self.command(ST7735_INVCTR)     # Display inversion ctrl
        self.data(0x07)

        self.command(ST7735_PWCTR1)     # Power control
        self.data(0xA2)
        self.data(0x02)
        self.data(0x84)

        self.command(ST7735_PWCTR2)
        self.data(0x0A)
        self.data(0x00)

        self.command(ST7735_PWCTR4)
        self.data(0x8A)
        self.data(0x2A)

        self.command(ST7735_PWCTR5)
        self.data(0x8A)
        self.data(0xEE)

        self.command(ST7735_VMCTR1)
        self.data(0x0E)

        if self._invert:
            self.command(ST7735_INVON)
        else:
            self.command(ST7735_INVOFF)

        # MADCTL register controls scan direction:
        #   Bit 7 (MY)  = Row address order    (1=bottom-to-top)
        #   Bit 6 (MX)  = Column address order (1=right-to-left)
        #   Bit 5 (MV)  = Row/Column exchange
        #   Bit 3 (RGB) = 0=RGB order, 1=BGR order
        #
        # TBM panel orientation determination (from user photos):
        #   0xC8 (MY=1,MX=1,RGB): 180° rotated
        #   0x08 (MY=0,MX=0,RGB): top-bottom OK, left-right mirrored
        #   0x48 (MY=0,MX=1,RGB): left-right OK, but top-bottom flipped
        #   0xC8 (MY=1,MX=1,RGB): both flipped again
        #   0xC0 (MY=1,MX=1,BGR): correct orientation + BGR colour order
        #   0xC8 (MY=1,MX=1,RGB): correct orientation, RGB colour order
        #
        # Confirmed by user photos:
        #   bgr=True + MY=1 + MX=1 = correct image, correct colours
        #   MADCTL: bit7=MY, bit6=MX, bit3=0(BGR)/1(RGB)
        #   0xC0 = 1100 0000 = MY=1, MX=1, BGR
        #   0xC8 = 1100 1000 = MY=1, MX=1, RGB
        madctl = 0xC0 if self._bgr else 0xC8
        self.command(ST7735_MADCTL)
        self.data(madctl)

        self.command(ST7735_COLMOD)     # 16-bit colour
        self.data(0x05)

        # Set full display window using doido-technologies offset values
        self.command(ST7735_CASET)
        self.data(0x00)
        self.data(self._offset_left)
        self.data(0x00)
        self.data(self._width + self._offset_left - 1)

        self.command(ST7735_RASET)
        self.data(0x00)
        self.data(self._offset_top)
        self.data(0x00)
        self.data(self._height + self._offset_top - 1)

        self.command(ST7735_GMCTRP1)    # Gamma correction
        self.data(0x02)
        self.data(0x1c)
        self.data(0x07)
        self.data(0x12)
        self.data(0x37)
        self.data(0x32)
        self.data(0x29)
        self.data(0x2d)
        self.data(0x29)
        self.data(0x25)
        self.data(0x2B)
        self.data(0x39)
        self.data(0x00)
        self.data(0x01)
        self.data(0x03)
        self.data(0x10)

        self.command(ST7735_GMCTRN1)
        self.data(0x03)
        self.data(0x1d)
        self.data(0x07)
        self.data(0x06)
        self.data(0x2E)
        self.data(0x2C)
        self.data(0x29)
        self.data(0x2D)
        self.data(0x2E)
        self.data(0x2E)
        self.data(0x37)
        self.data(0x3F)
        self.data(0x00)
        self.data(0x00)
        self.data(0x02)
        self.data(0x10)

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

        y0 += self._offset_top
        y1 += self._offset_top
        x0 += self._offset_left
        x1 += self._offset_left

        self.command(ST7735_CASET)
        self.data(x0 >> 8)
        self.data(x0 & 0xFF)
        self.data(x1 >> 8)
        self.data(x1 & 0xFF)

        self.command(ST7735_RASET)
        self.data(y0 >> 8)
        self.data(y0 & 0xFF)
        self.data(y1 >> 8)
        self.data(y1 & 0xFF)

        self.command(ST7735_RAMWR)

    def display(self, image):
        """Write a PIL Image to the LCD.
        Image must be RGB mode and exactly width x height pixels.
        """
        self.set_window()
        pixelbytes = image_to_data(image)
        self.data(pixelbytes)
