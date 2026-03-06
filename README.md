# TBM — The Bitcoin Machine (Umbrel 1.x Compatible Fork)

> **This is an unofficial community fork.** This is a modified version of the original [doidotech/TBM](https://github.com/doidotech/TBM) project, updated to work with **Umbrel OS 1.x** and **Pillow 10+** environments.
> The original project is no longer maintained, and this fork resolves the **white screen of death (WSOD)** issue that many users experience after upgrading Umbrel.

---

![TBM LCD Screen](https://raw.githubusercontent.com/ghmy4ff4t8-coder/TBM/master/Images/Main.jpg)

## Features

*   **Plug & Play:** Designed for the 1.8" ST7735 (128x160) LCD screen commonly sold with TBM kits.
*   **7 Information Screens:**
    1.  **Bitcoin Price:** Real-time price and sats/currency value with thousands separator.
    2.  **Next Block Info:** Estimated fees for next block.
    3.  **Block Height:** Current Bitcoin block height.
    4.  **Date & Time:** System date and time (timezone auto-detected from system).
    5.  **Network Info:** Umbrel IP address and network status.
    6.  **Lightning Channels:** Active/inactive channel count.
    7.  **Disk Usage:** Umbrel storage usage.
*   **Interactive Setup Wizard:** Guides you through screen selection, currency (46 supported), temperature unit, and screen duration.
*   **Auto-Start:** Runs as a `systemd` service, starting automatically on boot.
*   **Umbrel 1.x Ready:** Works with the latest Umbrel OS, including robust fallback logic for changing Docker container names.

## Repository Structure

```
tbm-umbrel/
├── app/
│   ├── tbm.py              # Main LCD display script
│   ├── setup_wizard.py     # Interactive settings wizard
│   ├── configure.sh        # Service setup script (run this to configure)
│   ├── install.sh          # Dependency installation script
│   ├── config.ini          # User settings (auto-updated by wizard)
│   ├── CurrencyData.py     # Supported currency list (46 fiat currencies)
│   ├── connections.py      # Bitcoin/LND connection helpers
│   ├── st7735_tbm.py       # Bundled ST7735 LCD driver
│   ├── calibrate.py        # LCD calibration utility
│   ├── images/             # Screen background images
│   └── poppins/            # Poppins font files
├── Images/                 # Repository images (for README)
├── uninstall.sh            # Uninstallation script
├── LICENSE
└── README.md
```

## Installation

These instructions are for a fresh installation on an Umbrel node. All commands should be run on your Umbrel device after connecting via SSH.

### Step 1: Connect to Your Umbrel Node (SSH)

1.  **Open a Terminal** on your computer (Terminal on macOS/Linux, PowerShell or WSL on Windows).
2.  **Connect via SSH.** `umbrel.local` is the default address.
    ```bash
    ssh umbrel@umbrel.local
    ```
3.  **Enter your Umbrel password.** This is the same password you use for the web dashboard.

### Step 2: Download & Run Installation Scripts

1.  **Clone this repository:**
    ```bash
    git clone https://github.com/ghmy4ff4t8-coder/TBM.git
    cd TBM/app
    ```

2.  **Run the dependency setup script.** This will install required Python libraries and enable the SPI interface.
    ```bash
    bash install.sh
    ```

3.  **Reboot your Umbrel** to apply the SPI interface changes.
    ```bash
    sudo reboot
    ```

### Step 3: Configure & Start the LCD Service

1.  **Reconnect via SSH** after your Umbrel has rebooted.

2.  **Navigate back to the script directory:**
    ```bash
    cd ~/TBM/app
    ```

3.  **Run the service setup wizard.** This will guide you through selecting which screens to display, your currency, and screen duration. It will then create and start the background service.
    ```bash
    bash configure.sh
    ```

That's it! Your LCD should now be running.

## Managing the Service

*   **Check Logs:**
    ```bash
    sudo journalctl -u tbm -f
    ```
*   **Restart Service:**
    ```bash
    sudo systemctl restart tbm
    ```
*   **Stop Service:**
    ```bash
    sudo systemctl stop tbm
    ```
*   **Re-run Setup Wizard:**
    ```bash
    sudo systemctl stop tbm && bash ~/TBM/app/configure.sh
    ```

## Updating

```bash
cd ~/TBM
git stash
git pull
git stash drop
sudo systemctl restart tbm
```

## Uninstallation

To completely remove the service and all related files:

```bash
cd ~/TBM
bash uninstall.sh
```

## Wiring Diagram (ST7735 1.8" LCD → Raspberry Pi)

| LCD Pin | Raspberry Pi Pin | GPIO | Description |
|---------|-----------------|------|-------------|
| VCC | Pin 1 | 3.3V | Power |
| GND | Pin 6 | GND | Ground |
| SCL/CLK | Pin 23 | GPIO 11 | SPI Clock |
| SDA/MOSI | Pin 19 | GPIO 10 | SPI Data |
| RES/RST | Pin 22 | GPIO 25 | Reset |
| DC | Pin 18 | GPIO 24 | Data/Command |
| CS | Pin 24 | GPIO 8 | Chip Select |
| BL/LED | Pin 17 | 3.3V | Backlight |

## Troubleshooting

*   **White Screen:** Check your GPIO wiring. Also verify the service is running with `sudo systemctl status tbm`.
*   **Garbled/Stripey Display:** This fork includes a bundled ST7735 driver (`st7735_tbm.py`) tuned for the TBM 1.8" panel. If issues persist, it may be a hardware problem.
*   **`config.ini` Conflicts on `git pull`:** Use `git stash` before pulling (see Updating section above).

## Credits

*   Original Project: [doidotech/TBM](https://github.com/doidotech/TBM) by DOIDO Technologies
*   This fork was created to address issues reported in the [Umbrel Community Forum](https://community.umbrel.com/t/the-bitcoin-machine-blank-lcd-since-umbrel-os-1/15720).

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
