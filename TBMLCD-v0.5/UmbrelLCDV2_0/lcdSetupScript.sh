#!/bin/bash
#-------------------------------------------------------------------------------
#   Copyright (c) 2022 DOIDO Technologies
#   Version  : 1.1.0  (Umbrel 1.x compatible fork)
#   Location : github
#   Changes  :
#     - Added --break-system-packages flag for Python 3.11+ compatibility
#     - Added support for /boot/firmware/config.txt (newer Raspberry Pi OS)
#     - Added fallback for both /boot/config.txt and /boot/firmware/config.txt
#     - Replaced deprecated setup.py install with pip install
#-------------------------------------------------------------------------------
# This script installs all requirements needed for ST7735 LCD
#-------------------------------------------------------------------------------

echo " "
echo "Installing packages required for the library to work..."
echo " "
sudo apt update
sudo apt install -y build-essential python3-dev python3-smbus python3-pip python3-pil python3-numpy
sudo apt install -y python3-rpi.gpio python3-spidev

echo " "
echo "Installing Raspberry Pi GPIO and Adafruit GPIO libraries for Python..."
echo " "
# Use --break-system-packages for Python 3.11+ (externally-managed-environment)
# Use --user as fallback if --break-system-packages is not available
PIP_FLAGS="--break-system-packages"
python3 -m pip install $PIP_FLAGS RPi.GPIO 2>/dev/null || python3 -m pip install --user RPi.GPIO
python3 -m pip install $PIP_FLAGS Adafruit_GPIO 2>/dev/null || python3 -m pip install --user Adafruit_GPIO
python3 -m pip install $PIP_FLAGS psutil 2>/dev/null || python3 -m pip install --user psutil
python3 -m pip install $PIP_FLAGS --upgrade certifi 2>/dev/null || python3 -m pip install --user --upgrade certifi
python3 -m pip install $PIP_FLAGS requests 2>/dev/null || python3 -m pip install --user requests
python3 -m pip install $PIP_FLAGS "requests[socks]" 2>/dev/null || python3 -m pip install --user "requests[socks]"
python3 -m pip install $PIP_FLAGS pysocks 2>/dev/null || python3 -m pip install --user pysocks
# Ensure Pillow >= 10.0.0 is installed (required for textbbox support)
python3 -m pip install $PIP_FLAGS "Pillow>=10.0.0" 2>/dev/null || python3 -m pip install --user "Pillow>=10.0.0"

echo " "
echo "Cloning and installing the LCD library..."
echo " "
git clone https://github.com/doido-technologies/st7735-python.git
cd st7735-python/library
# Use pip install instead of deprecated setup.py install
sudo python3 -m pip install $PIP_FLAGS . 2>/dev/null || sudo python3 setup.py install
cd ../..

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
    echo "SPI enabled in $CONFIG_PATH"
fi

echo " "
echo "Setup complete! Please reboot your Raspberry Pi to apply SPI changes."
echo "After reboot, run umbrelLCDServiceSetup.sh to configure and start the LCD service."
echo " "
