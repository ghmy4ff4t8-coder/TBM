# TBM — The Bitcoin Machine (Umbrel 1.x Compatible Fork)

> **This is an unofficial community fork** of [doidotech/TBM](https://github.com/doidotech/TBM), updated to work with **Umbrel OS 1.x** and **Pillow 10+**.  
> The original project is no longer maintained. This fork resolves the **white/blank LCD screen** issue reported by many users after upgrading Umbrel.

---

## What Was Fixed

The following issues caused the blank white screen on Umbrel 1.x systems:

| Issue | Root Cause | Fix Applied |
|---|---|---|
| **White screen on LCD** | `draw.textsize()` removed in Pillow 10.0.0 (Jul 2023) | Replaced with `draw.textbbox()` via `get_text_size()` helper |
| **pip install fails** | Python 3.11+ enforces externally-managed-environment | Added `--break-system-packages` flag with `--user` fallback |
| **`sudo echo >` redirect fails** | `sudo` does not apply to shell redirection | Replaced with `sudo tee` in service setup script |
| **systemd service can't find docker** | systemd has a minimal `PATH` that excludes `/usr/bin` | Added `Environment="PATH=..."` to unit file |
| **Temperature display crashes** | `vcgencmd` not always available | Added `/sys/class/thermal` fallback |
| **Disk detection fails** | Only checked `/dev/sda1`, missing NVMe/SD card paths | Added fallback chain: sda1 → sda → mmcblk0p1 → nvme0n1p1 → `/` |
| **Bitcoin price API fails** | CoinGecko rate limits / downtime | Added Coinbase API as fallback |
| **SPI config path** | Newer RPi OS uses `/boot/firmware/config.txt` | Auto-detects correct path |
| **Docker container names** | Umbrel 1.x may use different naming | Tries multiple container name variants |

---

## Requirements

- Raspberry Pi 4 (or compatible) running **Umbrel OS 1.x**
- 1.8 inch ST7735 SPI LCD display (160×128)
- Python 3.9 or higher (Python 3.11+ fully supported)
- Pillow **10.0.0 or higher** (installed automatically by setup script)

---

## Installation

### Step 1: Clone this repository

```bash
cd ~
git clone https://github.com/ghmy4ff4t8-coder/TBM.git
cd TBM/TBMLCD-v0.5/UmbrelLCDV2_0
```

### Step 2: Run the setup script

```bash
chmod +x lcdSetupScript.sh
./lcdSetupScript.sh
```

This script will:
- Install all required system packages
- Install Python dependencies (Pillow >= 10, RPi.GPIO, Adafruit_GPIO, requests, etc.)
- Clone and install the ST7735 LCD library
- Enable SPI in `/boot/firmware/config.txt` (or `/boot/config.txt` for older RPi OS)

### Step 3: Reboot

```bash
sudo reboot
```

### Step 4: Configure and start the LCD service

```bash
cd ~/TBM/TBMLCD-v0.5/UmbrelLCDV2_0
chmod +x umbrelLCDServiceSetup.sh
./umbrelLCDServiceSetup.sh
```

Follow the interactive prompts to select which screens to display and your preferred currency.

---

## Checking Service Status

```bash
# Check if the service is running
sudo systemctl status UmbrelST7735LCD

# View live logs
sudo journalctl -u UmbrelST7735LCD -f

# Restart the service
sudo systemctl restart UmbrelST7735LCD
```

---

## Screens

| Screen | Content | Display Duration |
|---|---|---|
| Screen 1 (Startup) | Umbrel logo | 60 seconds (once) |
| Screen 1 | Bitcoin price + Sats per currency unit | 60 seconds |
| Screen 2 | Next block fees + mempool transactions | 30 seconds |
| Screen 3 | Current block height | 30 seconds |
| Screen 4 | Current date and time | 30 seconds |
| Screen 5 | Network info (peers, hash rate, blockchain size, mempool) | 30 seconds |
| Screen 6 | Lightning channels (peers, channels, max send/receive) | 30 seconds |
| Screen 7 | Disk storage usage | 30 seconds |

---

## Wiring (ST7735 1.8" LCD to Raspberry Pi)

| LCD Pin | RPi Pin | GPIO |
|---|---|---|
| VCC | Pin 1 | 3.3V |
| GND | Pin 6 | GND |
| SCL/CLK | Pin 23 | GPIO 11 (SPI CLK) |
| SDA/MOSI | Pin 19 | GPIO 10 (SPI MOSI) |
| RES/RST | Pin 22 | GPIO 25 |
| DC | Pin 18 | GPIO 24 |
| CS | Pin 24 | GPIO 8 (SPI CE0) |
| BL/LED | Pin 17 | 3.3V |

---

## Troubleshooting

**LCD still shows white screen after update:**
```bash
# Check Python and Pillow versions
python3 --version
python3 -c "import PIL; print(PIL.__version__)"
# Pillow must be >= 10.0.0
```

**Service fails to start:**
```bash
sudo journalctl -u UmbrelST7735LCD -n 50 --no-pager
```

**Docker commands fail:**
```bash
# Check which container name your Umbrel uses
sudo docker ps | grep bitcoin
sudo docker ps | grep lightning
```

---

## Credits

- Original project: [doidotech/TBM](https://github.com/doidotech/TBM) by DOIDO Technologies
- ST7735 library: [doido-technologies/st7735-python](https://github.com/doido-technologies/st7735-python)
- This fork addresses issues reported in the [Umbrel Community Forum](https://community.umbrel.com/t/the-bitcoin-machine-blank-lcd-since-umbrel-os-1/15720)

---

## License

This project inherits the license from the original [doidotech/TBM](https://github.com/doidotech/TBM) repository.
