#!/bin/bash
#-------------------------------------------------------------------------------
#   Copyright (c) DOIDO Technologies
#   Version  : 1.5.0  (Umbrel 1.x compatible fork)
#   Changes  :
#     v1.5.0: Korean yes/no now also accepts 예/네/아니오/아니 in addition to yes/no.
#             YES_WORD variable removed (direct comparison in ask_screen).
#             Code cleanup: removed unused YES_WORD variable.
#     v1.4.0: Fixed language selection (eval bug replaced with case/if approach).
#             Duration prompts now read actual defaults from config.ini.
#             Default screen durations changed to 10s.
#     v1.3.0: Added multi-language support (EN/KR) for interactive setup.
#     v1.2.0: Added interactive screen duration settings.
#     v1.1.0: Fixed sudo echo redirect, added docker.service dependency.
#-------------------------------------------------------------------------------

# ──────────────────────────────────────────────────────────────────────────────
# Language Selection  (must come BEFORE any other output)
# ──────────────────────────────────────────────────────────────────────────────
clear
echo "======================================================================"
echo " Please select your language / 언어를 선택해주세요"
echo "======================================================================"
echo
echo "  1. English"
echo "  2. 한국어 (Korean)"
echo

while true; do
    read -p "Enter number / 번호 입력 [1-2]: " lang_choice
    case "$lang_choice" in
        1) LANG_CODE="EN"; break ;;
        2) LANG_CODE="KO"; break ;;
        *) echo "  Please enter 1 or 2 / 1 또는 2를 입력하세요." ;;
    esac
done

# ──────────────────────────────────────────────────────────────────────────────
# Helper: get localised string
# Usage: T "KEY"  →  echoes the string for the selected language
# ──────────────────────────────────────────────────────────────────────────────
T() {
    local key="$1"
    case "$LANG_CODE" in
        EN)
            case "$key" in
                BANNER)            echo "TBM (The Bitcoin Machine) - LCD Service Setup" ;;
                INTRO)             echo "This script will guide you through setting up the LCD service." ;;
                PROMPT_YN)         echo "Please answer with yes or no, then press Enter." ;;
                S1_DESC)           echo "Bitcoin price & sats/currency" ;;
                S2_DESC)           echo "Next block info" ;;
                S3_DESC)           echo "Block height" ;;
                S4_DESC)           echo "Date/Time" ;;
                S5_DESC)           echo "Network info" ;;
                S6_DESC)           echo "Lightning channels" ;;
                S7_DESC)           echo "Disk usage" ;;
                ASK_SCREEN)        echo "Display Screen $2 ($3)? [yes/no/y/n]: " ;;
                ADDED)             echo "✔ Screen $2 added." ;;
                SKIPPED)           echo "- Screen $2 skipped." ;;
                INVALID_YN)        echo "Invalid input. Please enter yes, no, y, or n." ;;
                SCREENS_SELECTED)  echo "Screens selected:" ;;
                CURRENCY_PROMPT)   echo "Please enter your currency code (e.g., USD, KRW, EUR, JPY): " ;;
                CURRENCY_VALID)    echo "✔ Currency set to: $2" ;;
                CURRENCY_INVALID)  echo "Invalid currency code. Please try again." ;;
                DURATION_HEADER)   echo "Screen Duration Setup (seconds)" ;;
                DURATION_INTRO)    echo "Enter the time in seconds for each screen to be displayed." ;;
                DURATION_DEFAULT)  echo "Press Enter to keep the current default value." ;;
                DUR_LOGO)          echo "Umbrel logo at startup (current default: ${2}s): " ;;
                DUR_S1)            echo "Bitcoin price screen (current default: ${2}s): " ;;
                DUR_OTHER)         echo "All other screens (current default: ${2}s): " ;;
                DUR_VALID)         echo "✔ $2 duration: ${3}s" ;;
                INVALID_NUM)       echo "Please enter a positive integer." ;;
                CONFIG_GENERATED)  echo "✔ config.ini generated successfully." ;;
                SERVICE_CREATING)  echo "Creating LCD Service..." ;;
                SERVICE_DONE)      echo "✔ LCD Service setup complete!" ;;
                LOG_CMD)           echo "Check logs:" ;;
                STOP_CMD)          echo "Stop service:" ;;
                RESTART_CMD)       echo "Restart service:" ;;
                RERUN_CMD)         echo "Re-run setup:" ;;
                YES_WORD)          echo "YES" ;;
            esac
            ;;
        KO)
            case "$key" in
                BANNER)            echo "TBM (The Bitcoin Machine) - LCD 서비스 설정" ;;
                INTRO)             echo "이 스크립트는 LCD 서비스 설정을 안내합니다." ;;
                PROMPT_YN)         echo "각 질문에 yes 또는 no 로 답하고 Enter 를 누르세요." ;;
                S1_DESC)           echo "비트코인 가격" ;;
                S2_DESC)           echo "다음 블록 정보" ;;
                S3_DESC)           echo "블록 높이" ;;
                S4_DESC)           echo "날짜/시간" ;;
                S5_DESC)           echo "네트워크 정보" ;;
                S6_DESC)           echo "라이트닝 채널" ;;
                S7_DESC)           echo "디스크 용량" ;;
                ASK_SCREEN)        echo "화면 $2 ($3) 을 표시할까요? [예/아니오 또는 yes/no]: " ;;
                ADDED)             echo "✔ 화면 $2 추가됨." ;;
                SKIPPED)           echo "- 화면 $2 건너뜀." ;;
                INVALID_YN)        echo "잘못된 입력입니다. 예/네/아니오/아니 또는 yes/no 로 입력해주세요." ;;
                SCREENS_SELECTED)  echo "선택된 화면:" ;;
                CURRENCY_PROMPT)   echo "통화 코드를 입력하세요 (예: USD, KRW, EUR, JPY): " ;;
                CURRENCY_VALID)    echo "✔ 통화 설정: $2" ;;
                CURRENCY_INVALID)  echo "유효하지 않은 통화 코드입니다. 다시 시도해주세요." ;;
                DURATION_HEADER)   echo "화면 전환 시간 설정 (초)" ;;
                DURATION_INTRO)    echo "각 화면이 표시될 시간을 초 단위로 입력하세요." ;;
                DURATION_DEFAULT)  echo "Enter 키를 누르면 현재 기본값이 그대로 유지됩니다." ;;
                DUR_LOGO)          echo "시작 로고 표시 시간 (현재 기본값: ${2}초): " ;;
                DUR_S1)            echo "비트코인 가격 화면 표시 시간 (현재 기본값: ${2}초): " ;;
                DUR_OTHER)         echo "나머지 모든 화면 표시 시간 (현재 기본값: ${2}초): " ;;
                DUR_VALID)         echo "✔ $2 시간: ${3}초" ;;
                INVALID_NUM)       echo "양의 정수를 입력해주세요." ;;
                CONFIG_GENERATED)  echo "✔ config.ini 생성 완료." ;;
                SERVICE_CREATING)  echo "LCD 서비스 생성 중..." ;;
                SERVICE_DONE)      echo "✔ LCD 서비스 설정 완료!" ;;
                LOG_CMD)           echo "로그 확인:" ;;
                STOP_CMD)          echo "서비스 중지:" ;;
                RESTART_CMD)       echo "서비스 재시작:" ;;
                RERUN_CMD)         echo "설정 재실행:" ;;
                YES_WORD)          echo "YES" ;;
            esac
            ;;
    esac
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

DEFAULT_LOGO=$(read_config_value "logo_duration" "10")
DEFAULT_S1=$(read_config_value "screen1_duration" "10")
DEFAULT_OTHER=$(read_config_value "screen_duration" "10")

# ──────────────────────────────────────────────────────────────────────────────
# Setup Start
# ──────────────────────────────────────────────────────────────────────────────
clear
echo "======================================================================"
echo " $(T BANNER)"
echo "======================================================================"
echo
echo " $(T INTRO)"
echo " $(T PROMPT_YN)"
echo

# ──────────────────────────────────────────────────────────────────────────────
# Screen Selection
# ──────────────────────────────────────────────────────────────────────────────
echo "--- [ 1/3 ] $(T SCREENS_SELECTED | sed 's/://' || echo 'Screen Selection') ---"
echo

userScreenChoices=""
YES_WORD=$(T YES_WORD)

ask_screen() {
    local num="$1"
    local desc
    desc=$(T "S${num}_DESC")
    local prompt
    prompt=$(T ASK_SCREEN "$num" "$desc")
    local gettingChoice=true
    while $gettingChoice; do
        read -rp "$prompt" ans
        ans_upper="${ans^^}"
        # Accept: yes/YES/y/Y (EN) and 예/네 (KO)
        if [ "$ans_upper" = "YES" ] || [ "$ans_upper" = "Y" ] || \
           [ "$ans" = "예" ] || [ "$ans" = "네" ]; then
            echo -e "  \e[1;32m$(T ADDED "$num")\e[0m"
            userScreenChoices="${userScreenChoices}Screen${num},"
            gettingChoice=false
        # Accept: no/NO/n/N (EN) and 아니오/아니/no (KO)
        elif [ "$ans_upper" = "NO" ] || [ "$ans_upper" = "N" ] || \
             [ "$ans" = "아니오" ] || [ "$ans" = "아니" ]; then
            echo "  $(T SKIPPED "$num")"
            gettingChoice=false
        else
            echo -e "  \e[1;31m$(T INVALID_YN)\e[0m"
        fi
    done
}

for n in 1 2 3 4 5 6 7; do
    ask_screen "$n"
done

echo
echo "$(T SCREENS_SELECTED) ${userScreenChoices}"
echo

# ──────────────────────────────────────────────────────────────────────────────
# Currency Selection
# ──────────────────────────────────────────────────────────────────────────────
echo "--- [ 2/3 ] Currency ---"
echo

gettingCurrency=true
while $gettingCurrency; do
    read -rp "$(T CURRENCY_PROMPT)" newCurrency
    newCurrency="${newCurrency^^}"
    validationResult=$(python3 ./CurrencyData.py "${newCurrency}")
    if [ "$validationResult" = "Valid" ]; then
        echo -e "  \e[1;32m$(T CURRENCY_VALID "$newCurrency")\e[0m"
        gettingCurrency=false
    else
        echo -e "  \e[1;31m$(T CURRENCY_INVALID)\e[0m"
    fi
done
echo

# ──────────────────────────────────────────────────────────────────────────────
# Duration Setup
# ──────────────────────────────────────────────────────────────────────────────
echo "--- [ 3/3 ] $(T DURATION_HEADER) ---"
echo
echo "$(T DURATION_INTRO)"
echo "$(T DURATION_DEFAULT)"
echo

ask_duration() {
    local prompt="$1"
    local default_val="$2"
    local name="$3"
    local result_var="$4"
    local val
    while true; do
        read -rp "$prompt" val
        val="${val:-$default_val}"
        if [[ "$val" =~ ^[0-9]+$ ]] && [ "$val" -gt 0 ]; then
            echo -e "  \e[1;32m$(T DUR_VALID "$name" "$val")\e[0m"
            eval "$result_var=$val"
            break
        else
            echo -e "  \e[1;31m$(T INVALID_NUM)\e[0m"
        fi
    done
}

ask_duration "$(T DUR_LOGO "$DEFAULT_LOGO")" "$DEFAULT_LOGO" "Logo" logoDuration
ask_duration "$(T DUR_S1 "$DEFAULT_S1")" "$DEFAULT_S1" "Price" screen1Duration
ask_duration "$(T DUR_OTHER "$DEFAULT_OTHER")" "$DEFAULT_OTHER" "Other" screenDuration
echo

# ──────────────────────────────────────────────────────────────────────────────
# Generate config.ini
# ──────────────────────────────────────────────────────────────────────────────
cat > "${cwd}/config.ini" << CONFIGEOF
# TBM LCD Configuration File (auto-generated by setup script)
# To apply changes, restart the service: sudo systemctl restart UmbrelST7735LCD

[DISPLAY]
logo_duration    = ${logoDuration}
screen1_duration = ${screen1Duration}
screen_duration  = ${screenDuration}

[BITCOIN]
# rpc_user = umbrel
# rpc_pass = moneyprintergobrrr

[LIGHTNING]
# container = lightning_lnd_1
CONFIGEOF

echo -e "\e[1;32m$(T CONFIG_GENERATED)\e[0m"
echo

# ──────────────────────────────────────────────────────────────────────────────
# Create systemd Service
# ──────────────────────────────────────────────────────────────────────────────
echo "======================================================================"
echo " $(T SERVICE_CREATING)"
echo "======================================================================"
echo

sudo tee /lib/systemd/system/UmbrelST7735LCD.service > /dev/null << EOF
[Unit]
Description=Umbrel LCD Service
After=multi-user.target docker.service
Wants=docker.service

[Service]
Restart=on-failure
RestartSec=30s
Type=idle
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/usr/bin/python3 ${cwd}/UmbrelLCD.py ${newCurrency} ${userScreenChoices}
StandardOutput=journal
StandardError=journal
SyslogIdentifier=UmbrelST7735LCD

[Install]
WantedBy=multi-user.target
EOF

sudo chmod 644 /lib/systemd/system/UmbrelST7735LCD.service
sudo systemctl daemon-reload
sudo systemctl enable UmbrelST7735LCD.service
sudo systemctl start UmbrelST7735LCD.service

echo
echo -e "\e[1;32m$(T SERVICE_DONE)\e[0m"
echo
printf "  %-22s sudo journalctl -u UmbrelST7735LCD -f\n"                                      "$(T LOG_CMD)"
printf "  %-22s sudo systemctl stop UmbrelST7735LCD\n"                                         "$(T STOP_CMD)"
printf "  %-22s sudo systemctl restart UmbrelST7735LCD\n"                                      "$(T RESTART_CMD)"
printf "  %-22s sudo systemctl stop UmbrelST7735LCD && bash umbrelLCDServiceSetup.sh\n"        "$(T RERUN_CMD)"
echo
