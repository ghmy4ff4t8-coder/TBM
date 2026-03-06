[English](README.md) | [한국어](README.ko.md) | [Español](README.es.md) | [日本語](README.ja.md) | [简体中文](README.zh.md)

# TBM — The Bitcoin Machine (Umbrel 1.x Compatible Fork)

> **This is an unofficial community fork.** This is a modified version of the original [doidotech/TBM](https://github.com/doidotech/TBM) project, updated to work with **Umbrel OS 1.x** and **Pillow 10+** environments.
> The original project is no longer maintained, and this fork resolves the **white screen of death (WSOD)** issue that many users experience after upgrading Umbrel.

---

## Beginner-Friendly Installation Guide (for Mac users)

This guide is written for those with no terminal or coding experience. Please follow the steps carefully.

### Step 1: Connect to Your Umbrel Node Remotely (SSH)

First, you need to connect to your Umbrel node (Raspberry Pi) from your Mac. We'll use the 'Terminal' app for this.

1.  **Open the Terminal App**
    *   Press `Command (⌘)` + `Space` to open Spotlight search, type `Terminal`, and press Enter.

2.  **Connect with SSH Command**
    *   In the terminal window, type the following command. `umbrel.local` is the default address that works on most home networks.

    ```bash
    ssh umbrel@umbrel.local
    ```

3.  **Enter Your Password**
    *   You will be prompted for a password. This is the same password you use to log in to your Umbrel dashboard.
    *   **Note:** For security, nothing will be displayed on the screen as you type your password. Just type it and press Enter.

    ```bash
    umbrel@umbrel.local's password:
    ```

4.  **Confirm Successful Connection**
    *   If the connection is successful, you will see a welcome message with the Umbrel logo. From now on, all commands you type will be executed on your Umbrel node.

    ```
       _   _ ____  _   _ ____  _     
      | | | | __ )| | | | __ )| |    
      | | | |  _ \| | | |  _ \| |    
      | |_| | |_) | |_| | |_) | |___ 
       \___/|____/ \___/|____/|_____|
    ```

### Step 2: Download the Code and Run the Installation Script

Now it's time to download the code with the white screen fix and install it. **Copy and paste the commands below one line at a time into the terminal and press Enter.**

1.  **Clone the Code from GitHub**
    *   This command downloads the modified TBM code from my GitHub repository to your Umbrel node.

    ```bash
    git clone https://github.com/ghmy4ff4t8-coder/TBM.git
    ```

2.  **Navigate to the Working Directory**

    ```bash
    cd TBM/TBMLCD-v0.5/UmbrelLCDV2_0
    ```

3.  **Run the Setup Script**
    *   This script automatically installs all the necessary programs and libraries for the LCD to work.

    ```bash
    chmod +x lcdSetupScript.sh
    ./lcdSetupScript.sh
    ```

    *   You will see many lines of text scrolling by during the installation. If you see the `Setup complete!` message, it was successful.

### Step 3: Reboot Your Umbrel Node

To ensure all settings are applied correctly, you need to reboot the system.

```bash
sudo reboot
```

*   This command will disconnect your SSH session. Please wait about 3-5 minutes for your Umbrel node to fully restart.

### Step 4: Set Up and Start the LCD Service

Once the reboot is complete, reconnect to your Umbrel node via SSH as you did in Step 1, and then enter the following commands in order.

1.  **Navigate to the Working Directory Again**

    ```bash
    cd ~/TBM/TBMLCD-v0.5/UmbrelLCDV2_0
    ```

2.  **Run the Service Setup Script**

    ```bash
    chmod +x umbrelLCDServiceSetup.sh
    ./umbrelLCDServiceSetup.sh
    ```

3.  **Select Screens and Currency (Very Important)**
    *   When you run the script, you will be asked which screens to display on the LCD and in which currency (USD, EUR, KRW, etc.) to view the Bitcoin price.
    *   Answer each question with `yes` or `no` and press Enter.
    *   Finally, enter your desired currency code (e.g., `USD`), and all settings will be complete, and the LCD service will start automatically.

Now you can see your TBM LCD working correctly!

---

## Troubleshooting

**My LCD is still a white screen:**
*   First, check that the wiring is correct (see the wiring diagram below).
*   Try running `./lcdSetupScript.sh` and `./umbrelLCDServiceSetup.sh` again.

**I want to check if the service is running correctly:**
*   You can check the service status with the following command:
    ```bash
    sudo systemctl status UmbrelST7735LCD
    ```
*   To view real-time logs, enter the command below. This is useful for checking for error messages.
    ```bash
    sudo journalctl -u UmbrelST7735LCD -f
    ```

---

## Wiring Diagram (ST7735 1.8" LCD → Raspberry Pi)

| LCD Pin | Raspberry Pi Pin Number | GPIO | Description |
| :--- | :--- | :--- | :--- |
| VCC | Pin 1 | 3.3V | Power |
| GND | Pin 6 | GND | Ground |
| SCL/CLK | Pin 23 | GPIO 11 | SPI Clock |
| SDA/MOSI | Pin 19 | GPIO 10 | SPI Data |
| RES/RST | Pin 22 | GPIO 25 | Reset |
| DC | Pin 18 | GPIO 24 | Data/Command Select |
| CS | Pin 24 | GPIO 8 | Chip Select |
| BL/LED | Pin 17 | 3.3V | Backlight Power |

---

## Technical Issues Fixed

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| **LCD White Screen** | The `draw.textsize()` function was removed in Pillow 10.0.0. | Replaced with a compatibility function that uses `draw.textbbox()`. |
| **pip Install Fails** | Stricter system package protection policy in Python 3.11+. | Added the `--break-system-packages` flag to the `pip` command. |
| **Service Execution Error** | systemd service does not recognize the Docker path. | Explicitly added the `PATH` environment variable to the service unit file. |
| **Umbrel 1.x Compatibility** | Changes in Docker container names, `bitcoin-cli`, and `lncli` execution methods. | Enhanced fallback logic by trying multiple container names and adding direct HTTP RPC calls. |

---

## Credits

*   Original Project: [doidotech/TBM](https://github.com/doidotech/TBM) by DOIDO Technologies
*   This fork was created to address issues reported in the [Umbrel Community Forum](https://community.umbrel.com/t/the-bitcoin-machine-blank-lcd-since-umbrel-os-1/15720).
