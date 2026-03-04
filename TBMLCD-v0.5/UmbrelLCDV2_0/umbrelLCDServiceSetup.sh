#!/bin/bash
#-------------------------------------------------------------------------------
#   Copyright (c) DOIDO Technologies
#   Version  : 1.3.0  (Umbrel 1.x compatible fork)
#   Changes  :
#     v1.3.0: Added multi-language support (EN/KR) for interactive setup.
#             Default screen durations changed to 10s.
#     v1.2.0: Added interactive screen duration settings.
#     v1.1.0: Fixed sudo echo redirect, added docker.service dependency.
#-------------------------------------------------------------------------------

# ──────────────────────────────────────────────────────────────────────────────
# Language Strings (i18n)
# ──────────────────────────────────────────────────────────────────────────────

# English (en)
L_EN_BANNER="TBM (The Bitcoin Machine) - LCD Service Setup"
L_EN_INTRO="This script will guide you through setting up the LCD service."
L_EN_PROMPT_YN="Please answer with yes or no, then press Enter."
L_EN_S1_DESC="Bitcoin price & sats/currency"
L_EN_S2_DESC="Next block info"
L_EN_S3_DESC="Block height"
L_EN_S4_DESC="Date/Time"
L_EN_S5_DESC="Network info"
L_EN_S6_DESC="Lightning channels"
L_EN_S7_DESC="Disk usage"
L_EN_ASK_SCREEN="Display Screen %s (%s)? [yes/no]: "
L_EN_ADDED="✔ Screen %s added."
L_EN_SKIPPED="- Screen %s skipped."
L_EN_INVALID_YN="Invalid input. Please enter yes or no."
L_EN_SCREENS_SELECTED="Screens selected:"
L_EN_CURRENCY_PROMPT="Please enter your currency code (e.g., USD, KRW, EUR, JPY): "
L_EN_CURRENCY_VALID="✔ Currency set to: %s"
L_EN_CURRENCY_INVALID="Invalid currency code. Please try again."
L_EN_DURATION_HEADER="Screen Duration Setup (seconds)"
L_EN_DURATION_INTRO="Enter the time in seconds for each screen to be displayed."
L_EN_DURATION_DEFAULT="Press Enter to use the default value."
L_EN_DUR_LOGO="Umberl logo at startup (default: 10s): "
L_EN_DUR_S1="Bitcoin price screen (default: 10s): "
L_EN_DUR_OTHER="All other screens (default: 10s): "
L_EN_DUR_VALID="✔ %s duration: %ss"
L_EN_INVALID_NUM="Please enter a positive integer."
L_EN_CONFIG_GENERATED="✔ config.ini generated successfully."
L_EN_SERVICE_CREATING="Creating LCD Service..."
L_EN_SERVICE_DONE="✔ LCD Service setup complete!"
L_EN_LOG_CMD="To check logs:"
L_EN_STOP_CMD="To stop service:"
L_EN_RESTART_CMD="To restart service:"
L_EN_RERUN_CMD="To re-run setup:"
L_EN_YES="YES"

# Korean (ko)
L_KO_BANNER="TBM (The Bitcoin Machine) - LCD 서비스 설정"
L_KO_INTRO="이 스크립트는 LCD 서비스 설정을 안내합니다."
L_KO_PROMPT_YN="각 질문에 yes 또는 no 로 답하고 Enter 를 누르세요."
L_KO_S1_DESC="비트코인 가격"
L_KO_S2_DESC="다음 블록 정보"
L_KO_S3_DESC="블록 높이"
L_KO_S4_DESC="날짜/시간"
L_KO_S5_DESC="네트워크 정보"
L_KO_S6_DESC="라이트닝 채널"
L_KO_S7_DESC="디스크 용량"
L_KO_ASK_SCREEN="화면 %s (%s) 을 표시할까요? [yes/no]: "
L_KO_ADDED="✔ 화면 %s 추가됨."
L_KO_SKIPPED="- 화면 %s 건너뜀."
L_KO_INVALID_YN="잘못된 입력입니다. yes 또는 no 로 입력해주세요."
L_KO_SCREENS_SELECTED="선택된 화면:"
L_KO_CURRENCY_PROMPT="통화 코드를 입력하세요 (예: USD, KRW, EUR, JPY): "
L_KO_CURRENCY_VALID="✔ 통화 설정: %s"
L_KO_CURRENCY_INVALID="유효하지 않은 통화 코드입니다. 다시 시도해주세요."
L_KO_DURATION_HEADER="화면 전환 시간 설정 (초)"
L_KO_DURATION_INTRO="각 화면이 표시될 시간을 초 단위로 입력하세요."
L_KO_DURATION_DEFAULT="Enter 키를 누르면 기본값이 적용됩니다."
L_KO_DUR_LOGO="시작 로고 표시 시간 (기본값: 10초): "
L_KO_DUR_S1="비트코인 가격 화면 표시 시간 (기본값: 10초): "
L_KO_DUR_OTHER="나머지 모든 화면 표시 시간 (기본값: 10초): "
L_KO_DUR_VALID="✔ %s 시간: %s초"
L_KO_INVALID_NUM="양의 정수를 입력해주세요."
L_KO_CONFIG_GENERATED="✔ config.ini 생성 완료."
L_KO_SERVICE_CREATING="LCD 서비스 생성 중..."
L_KO_SERVICE_DONE="✔ LCD 서비스 설정 완료!"
L_KO_LOG_CMD="로그 확인:"
L_KO_STOP_CMD="서비스 중지:"
L_KO_RESTART_CMD="서비스 재시작:"
L_KO_RERUN_CMD="설정 재실행:"
L_KO_YES="YES"

# ──────────────────────────────────────────────────────────────────────────────
# Language Selection
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
    read -p "Enter the number for your language [1-2]: " lang_choice
    case $lang_choice in
        1) lang="EN"; break ;;
        2) lang="KO"; break ;;
        *) echo "Invalid selection. Please enter 1 or 2." ;;
    esac
done

# Dynamically set language variables
for i in $(compgen -v L_${lang}_); do
    short_name=$(echo $i | sed "s/L_${lang}_//")
    eval "L_$short_name=\"${!i}""
done

# ──────────────────────────────────────────────────────────────────────────────
# Setup Start
# ──────────────────────────────────────────────────────────────────────────────
clear
echo "======================================================================"
printf " %s\n" "$L_BANNER"
echo "======================================================================"
echo
printf " %s\n" "$L_INTRO"
printf " %s\n\n" "$L_PROMPT_YN"

# ──────────────────────────────────────────────────────────────────────────────
# Screen Selection
# ──────────────────────────────────────────────────────────────────────────────
echo "--- [ 1/3 ] Screen Selection ---"
echo

userScreenChoices=""

ask_screen() {
    local num=$1
    local desc_var="L_S${num}_DESC"
    local desc="${!desc_var}"
    local gettingChoice=true
    while $gettingChoice; do
        printf "$L_ASK_SCREEN" "$num" "$desc"
        read -r ans
        ans=${ans^^}
        if [ "$ans" == "$L_YES" ]; then
            printf "  \e[1;32m$L_ADDED\e[0m\n" "$num"
            userScreenChoices="${userScreenChoices}Screen${num},"
            gettingChoice=false
        elif [ "$ans" == "NO" ]; then
            printf "  $L_SKIPPED\n" "$num"
            gettingChoice=false
        else
            printf "  \e[1;31m$L_INVALID_YN\e[0m\n"
        fi
    done
}

ask_screen 1
ask_screen 2
ask_screen 3
ask_screen 4
ask_screen 5
ask_screen 6
ask_screen 7

echo
printf "$L_SCREENS_SELECTED %s\n\n" "$userScreenChoices"

# ──────────────────────────────────────────────────────────────────────────────
# Currency Selection
# ──────────────────────────────────────────────────────────────────────────────
echo "--- [ 2/3 ] Currency Selection ---"
echo

gettingCurrency=true
while $gettingCurrency; do
    read -p "$L_CURRENCY_PROMPT" newCurrency
    newCurrency=${newCurrency^^}
    validationResult=$(python3 ./CurrencyData.py "${newCurrency}")
    if [ "$validationResult" = "Valid" ]; then
        printf "  \e[1;32m$L_CURRENCY_VALID\e[0m\n" "$newCurrency"
        gettingCurrency=false
    else
        printf "  \e[1;31m$L_CURRENCY_INVALID\e[0m\n"
    fi
done
echo

# ──────────────────────────────────────────────────────────────────────────────
# Duration Setup
# ──────────────────────────────────────────────────────────────────────────────
echo "--- [ 3/3 ] $L_DURATION_HEADER ---"
echo
printf "%s\n" "$L_DURATION_INTRO"
printf "%s\n\n" "$L_DURATION_DEFAULT"

ask_duration() {
    local prompt_var=$1
    local default_val=$2
    local name=$3
    local duration_val
    while true; do
        read -p "$prompt_var" duration_val
        duration_val=${duration_val:-$default_val}
        if [[ "$duration_val" =~ ^[0-9]+$ ]] && [ "$duration_val" -gt 0 ]; then
            printf "  \e[1;32m$L_DUR_VALID\e[0m\n" "$name" "$duration_val"
            echo "$duration_val"
            break
        else
            printf "  \e[1;31m$L_INVALID_NUM\e[0m\n"
        fi
    done
}

logoDuration=$(ask_duration "$L_DUR_LOGO" 10 "Logo")
screen1Duration=$(ask_duration "$L_DUR_S1" 10 "Price screen")
screenDuration=$(ask_duration "$L_DUR_OTHER" 10 "Other screens")
echo

# ──────────────────────────────────────────────────────────────────────────────
# Generate config.ini
# ──────────────────────────────────────────────────────────────────────────────
cwd=$(pwd)

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

printf "\e[1;32m%s\e[0m\n\n" "$L_CONFIG_GENERATED"

# ──────────────────────────────────────────────────────────────────────────────
# Create systemd Service
# ──────────────────────────────────────────────────────────────────────────────
echo "======================================================================"
printf " %s\n" "$L_SERVICE_CREATING"
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
ExecStart=/usr/bin/python3 $cwd/UmbrelLCD.py $newCurrency $userScreenChoices
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
echo -e "\e[1;32m$L_SERVICE_DONE\e[0m"
echo
printf "  %-20s sudo journalctl -u UmbrelST7735LCD -f\n" "$L_LOG_CMD"
printf "  %-20s sudo systemctl stop UmbrelST7735LCD\n" "$L_STOP_CMD"
printf "  %-20s sudo systemctl restart UmbrelST7735LCD\n" "$L_RESTART_CMD"
printf "  %-20s 'sudo systemctl stop UmbrelST7735LCD && ./umbrelLCDServiceSetup.sh'\n" "$L_RERUN_CMD"
echo
