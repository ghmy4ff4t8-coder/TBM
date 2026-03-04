#!/bin/bash
#-------------------------------------------------------------------------------
#   Copyright (c) 2022 DOIDO Technologies
#   Version  : 1.3.0  (Umbrel 1.x compatible fork)
#   Location : github
#   Changes  :
#     v1.3.0:
#       - Removed pimoroni/st7735-python dependency entirely.
#         The bundled st7735_tbm.py driver is now used instead.
#         This fixes the diagonal stripe issue caused by pimoroni's
#         incorrect ST7735_COLS=132 / offset_left=2 values.
#       - Still installs gpiod + spidev (used by st7735_tbm.py directly)
#       - Removed gpiodevice (pimoroni-only dependency)
#     v1.2.0:
#       - Install pimoroni/st7735-python v1.0.0 via 'pip install st7735'
#       - Install gpiod and python3-gpiod
#     v1.1.0:
#       - Added --break-system-packages flag for Python 3.11+ compatibility
#       - Added support for /boot/firmware/config.txt (newer Raspberry Pi OS)
#       - Replaced deprecated setup.py install with pip install
#-------------------------------------------------------------------------------
# This script installs all requirements needed for ST7735 LCD
#-------------------------------------------------------------------------------

echo " "
echo "Installing packages required for the library to work..."
echo " "
sudo apt update
sudo apt install -y build-essential python3-dev python3-smbus python3-pip python3-pil python3-numpy
# python3-spidev: correct apt package name (not 'spidev')
sudo apt install -y python3-spidev || true
# gpiod: install via pip (apt package 'python3-gpiod' may not exist on all distros)
sudo apt install -y gpiod libgpiod-dev || true

echo " "
echo "Installing Python libraries..."
echo " "
# Use --break-system-packages for Python 3.11+ (externally-managed-environment)
PIP_FLAGS="--break-system-packages"
python3 -m pip install $PIP_FLAGS RPi.GPIO 2>/dev/null || python3 -m pip install --user RPi.GPIO
python3 -m pip install $PIP_FLAGS psutil 2>/dev/null || python3 -m pip install --user psutil
python3 -m pip install $PIP_FLAGS --upgrade certifi 2>/dev/null || python3 -m pip install --user --upgrade certifi
python3 -m pip install $PIP_FLAGS requests 2>/dev/null || python3 -m pip install --user requests
python3 -m pip install $PIP_FLAGS "requests[socks]" 2>/dev/null || python3 -m pip install --user "requests[socks]"
python3 -m pip install $PIP_FLAGS pysocks 2>/dev/null || python3 -m pip install --user pysocks
# Ensure Pillow >= 10.0.0 is installed (required for textbbox support)
python3 -m pip install $PIP_FLAGS "Pillow>=10.0.0" 2>/dev/null || python3 -m pip install --user "Pillow>=10.0.0"
# gpiod Python bindings (required by bundled st7735_tbm.py driver)
python3 -m pip install $PIP_FLAGS gpiod 2>/dev/null || python3 -m pip install --user gpiod
python3 -m pip install $PIP_FLAGS spidev 2>/dev/null || python3 -m pip install --user spidev
# numpy is used by the bundled st7735_tbm.py driver
python3 -m pip install $PIP_FLAGS numpy 2>/dev/null || python3 -m pip install --user numpy

echo " "
echo "NOTE: The bundled st7735_tbm.py driver is used (no external ST7735 library needed)."
echo "      gpiod and spidev are used directly by the bundled driver."
echo " "

echo " "
echo "Enabling SPI port..."
echo " "
# Support both older (/boot/config.txt) and newer (/boot/firmware/config.txt) RPi OS
if [ -f /boot/firmware/config.txt ]; then
    CONFIG_PATH="/boot/firmware/config.txt"
    echo "Using $CONFIG_PATH (newer Raspberry Pi OS)"
elif [ -f /boot/config.txt ]; then
    CONFIG_PATH="/boot/config.txt"
    echo "Using $CONFIG_PATH (older Raspberry Pi OS)"
else
    echo "WARNING: Could not find config.txt. Please enable SPI manually."
    CONFIG_PATH=""
fi

if [ -n "$CONFIG_PATH" ]; then
    sudo sed -i 's/dtparam=spi=off/dtparam=spi=on/g' "$CONFIG_PATH"
    sudo sed -i 's/#dtparam=spi=on/dtparam=spi=on/g' "$CONFIG_PATH"
    # If dtparam=spi=on is not present at all, add it
    if ! grep -q "dtparam=spi=on" "$CONFIG_PATH"; then
        echo "dtparam=spi=on" | sudo tee -a "$CONFIG_PATH"
    fi
    echo "SPI enabled in $CONFIG_PATH"
fi

echo " "
echo "Setup complete! Please reboot your Raspberry Pi to apply SPI changes."
echo "After reboot, run umbrelLCDServiceSetup.sh to configure and start the LCD service."
echo " "
