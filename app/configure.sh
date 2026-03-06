#!/bin/bash
#-------------------------------------------------------------------------------
#   Copyright (c) DOIDO Technologies
#   Version  : 2.0.0
#   Changes  :
#     v2.0.0: Removed multi-language support (English only).
#             Removed manual timezone input — auto-detected from system.
#             Removed logo_duration setting (hardcoded to 10s in tbm.py).
#             Removed screen1_duration (single screen_duration for all screens).
#     v1.6.0: Fixed syntax error - ES/JA/ZH language blocks were outside T().
#             Removed screen1_duration; single screen_duration for all screens.
#     v1.5.0: Korean yes/no support added.
#     v1.4.0: Fixed language selection. Duration prompts read from config.ini.
#     v1.3.0: Added multi-language support (EN/KR).
#     v1.2.0: Added interactive screen duration settings.
#     v1.1.0: Fixed sudo echo redirect, added docker.service dependency.
#-------------------------------------------------------------------------------

# ──────────────────────────────────────────────────────────────────────────────
# Auto-detect system timezone
# ──────────────────────────────────────────────────────────────────────────────
detect_timezone() {
    # Method 1: timedatectl
    local tz
    tz=$(timedatectl show --property=Timezone --value 2>/dev/null)
    if [ -n "$tz" ] && python3 -c "import pytz; pytz.timezone('${tz}')" 2>/dev/null; then
        echo "$tz"
        return
    fi
    # Method 2: /etc/timezone
    if [ -f /etc/timezone ]; then
        tz=$(cat /etc/timezone | tr -d '[:space:]')
        if [ -n "$tz" ] && python3 -c "import pytz; pytz.timezone('${tz}')" 2>/dev/null; then
            echo "$tz"
            return
        fi
    fi
    # Method 3: /etc/localtime symlink
    if [ -L /etc/localtime ]; then
        tz=$(readlink /etc/localtime | sed 's|.*/zoneinfo/||')
        if [ -n "$tz" ] && python3 -c "import pytz; pytz.timezone('${tz}')" 2>/dev/null; then
            echo "$tz"
            return
        fi
    fi
    echo "UTC"
}

# ──────────────────────────────────────────────────────────────────────────────
# Read current defaults from config.ini (if it exists)
# ──────────────────────────────────────────────────────────────────────────────
cwd=$(pwd)
CONFIG_FILE="${cwd}/config.ini"

read_config_value() {
    local key="$1"
    local fallback="$2"
    if [ -f "$CONFIG_FILE" ]; then
        local val
        val=$(grep -E "^\s*${key}\s*=" "$CONFIG_FILE" | head -1 | sed 's/.*=\s*//' | tr -d '[:space:]')
        if [ -n "$val" ]; then
            echo "$val"
            return
        fi
    fi
    echo "$fallback"
}

DEFAULT_OTHER=$(read_config_value "screen_duration" "4")
DETECTED_TZ=$(detect_timezone)

# ──────────────────────────────────────────────────────────────────────────────
# Setup Start
# ──────────────────────────────────────────────────────────────────────────────
clear
echo "======================================================================"
echo " TBM (The Bitcoin Machine) - LCD Service Setup"
echo "======================================================================"
echo
echo " This script will guide you through setting up the LCD service."
echo " Please answer with yes or no, then press Enter."
echo
echo " Timezone auto-detected: ${DETECTED_TZ}"
echo

# ──────────────────────────────────────────────────────────────────────────────
# Screen Selection
# ──────────────────────────────────────────────────────────────────────────────
echo "--- [ 1/3 ] Screen Selection ---"
echo

userScreenChoices=""

SCREEN_DESCS=(
    ""
    "Bitcoin price & sats/currency"
    "Next block info"
    "Block height"
    "Date/Time"
    "Network info"
    "Lightning channels"
    "Disk usage"
)

ask_screen() {
    local num="$1"
    local desc="${SCREEN_DESCS[$num]}"
    local gettingChoice=true
    while $gettingChoice; do
        read -rp "  Display Screen ${num} (${desc})? [y/n]: " ans
        ans_upper="${ans^^}"
        if [ "$ans_upper" = "YES" ] || [ "$ans_upper" = "Y" ]; then
            echo -e "  \e[1;32m✔ Screen ${num} added.\e[0m"
            userScreenChoices="${userScreenChoices}Screen${num},"
            gettingChoice=false
        elif [ "$ans_upper" = "NO" ] || [ "$ans_upper" = "N" ]; then
            echo "  - Screen ${num} skipped."
            gettingChoice=false
        else
            echo -e "  \e[1;31mInvalid input. Please enter yes or no.\e[0m"
        fi
    done
}

for n in 1 2 3 4 5 6 7; do
    ask_screen "$n"
done

echo
echo "Screens selected: ${userScreenChoices}"
echo

# ──────────────────────────────────────────────────────────────────────────────
# Currency Selection
# ──────────────────────────────────────────────────────────────────────────────
echo "--- [ 2/3 ] Currency ---"
echo
echo "  Supported currencies:"
echo "  AED  ARS  AUD  BDT  BHD  BMD  BRL  CAD  CHF  CLP"
echo "  CNY  CZK  DKK  EUR  GBP  GEL  HKD  HUF  IDR  ILS"
echo "  INR  JPY  KRW  KWD  LKR  MMK  MXN  MYR  NGN  NOK"
echo "  NZD  PHP  PKR  PLN  RUB  SAR  SEK  SGD  THB  TRY"
echo "  TWD  UAH  USD  VEF  VND  ZAR"
echo

gettingCurrency=true
while $gettingCurrency; do
    read -rp "  Enter currency code: " newCurrency
    newCurrency="${newCurrency^^}"
    validationResult=$(python3 ./CurrencyData.py "${newCurrency}")
    if [ "$validationResult" = "Valid" ]; then
        echo -e "  \e[1;32m✔ Currency set to: ${newCurrency}\e[0m"
        gettingCurrency=false
    else
        echo -e "  \e[1;31mInvalid currency code. Please try again.\e[0m"
    fi
done
echo

# ──────────────────────────────────────────────────────────────────────────────
# Duration Setup
# ──────────────────────────────────────────────────────────────────────────────
echo "--- [ 3/3 ] Screen Duration Setup ---"
echo
echo "  Enter the time in seconds each info screen is displayed."
echo "  Press Enter to keep the current default."
echo

screenDuration=""
while true; do
    read -rp "  Info screen duration (current default: ${DEFAULT_OTHER}s): " val
    val="${val:-$DEFAULT_OTHER}"
    if [[ "$val" =~ ^[0-9]+$ ]] && [ "$val" -gt 0 ]; then
        echo -e "  \e[1;32m✔ Screen duration: ${val}s\e[0m"
        screenDuration="$val"
        break
    else
        echo -e "  \e[1;31mPlease enter a positive integer.\e[0m"
    fi
done
echo

# ──────────────────────────────────────────────────────────────────────────────
# Generate config.ini
# ──────────────────────────────────────────────────────────────────────────────
cat > "${cwd}/config.ini" << CONFIGEOF
# ============================================================
#  TBM (The Bitcoin Machine) - LCD Configuration File
#  Location: ~/TBM/app/config.ini
# ============================================================
#
#  Edit this file to change settings without touching the code.
#  After editing, restart the service to apply changes:
#    sudo systemctl restart tbm-umbrel
#
#  Alternatively, run the script manually to use the interactive
#  setup wizard (10-second auto-start timeout).
#
# ============================================================

[USER]
# Your local timezone (auto-detected from system, IANA format).
# Examples: UTC, Asia/Seoul, America/New_York, Europe/London
timezone = ${DETECTED_TZ}

# Currency code for Bitcoin price display.
# Examples: USD, EUR, KRW, JPY, GBP, AUD, CAD
currency = ${newCurrency}

# Screens to display (any combination of digits 1-7).
# 1=Price, 2=Fees, 3=Block Height, 4=Date/Time, 5=Network, 6=Lightning, 7=Storage
screens = ${userScreenChoices//Screen/}

# Temperature unit: C (Celsius) or F (Fahrenheit)
temp_unit = C


[DISPLAY]
# Duration (in seconds) each screen is shown on the LCD.
# (Umbrel logo duration is fixed at 10s and not user-configurable)
screen_duration = ${screenDuration}


[BITCOIN]
# Bitcoin RPC connection settings.
# If Umbrel updates change the RPC password, only edit this file.
# Default values match standard Umbrel installation.

# rpc_user = umbrel
# rpc_pass = moneyprintergobrrr
# rpc_host = 127.0.0.1
# rpc_port = 8332

# Bitcoin container name (varies by Umbrel version).
# The script tries multiple names automatically, so this is usually not needed.
# container = bitcoin_bitcoind_1


[LIGHTNING]
# LND container name (varies by Umbrel version).
# The script tries multiple names automatically, so this is usually not needed.
# container = lightning_lnd_1
CONFIGEOF

echo -e "\e[1;32m✔ config.ini generated successfully.\e[0m"
echo

# ──────────────────────────────────────────────────────────────────────────────
# Create systemd Service
# ──────────────────────────────────────────────────────────────────────────────
echo "======================================================================"
echo " Creating LCD Service..."
echo "======================================================================"
echo

sudo tee /lib/systemd/system/tbm-umbrel.service > /dev/null << EOF
[Unit]
Description=Umbrel LCD Service
After=multi-user.target docker.service
Wants=docker.service

[Service]
Restart=on-failure
RestartSec=30s
Type=idle
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/usr/bin/python3 ${cwd}/tbm.py
StandardOutput=journal
StandardError=journal
SyslogIdentifier=tbm-umbrel

[Install]
WantedBy=multi-user.target
EOF

sudo chmod 644 /lib/systemd/system/tbm-umbrel.service
sudo systemctl daemon-reload
sudo systemctl enable tbm-umbrel.service
sudo systemctl start tbm-umbrel.service

echo
echo -e "\e[1;32m✔ LCD Service setup complete!\e[0m"
echo
printf "  %-22s sudo journalctl -u tbm-umbrel -f\n"                                   "Check logs:"
printf "  %-22s sudo systemctl stop tbm-umbrel\n"                                      "Stop service:"
printf "  %-22s sudo systemctl restart tbm-umbrel\n"                                   "Restart service:"
printf "  %-22s sudo systemctl stop tbm-umbrel && bash configure.sh\n"     "Re-run setup:"
echo
