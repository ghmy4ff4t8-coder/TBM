#!/bin/bash
#-------------------------------------------------------------------------------
#   Copyright (c) DOIDO Technologies
#   Version  : 1.2.0  (Umbrel 1.x compatible fork)
#   Changes  :
#     v1.2.0: Added interactive screen duration settings (config.ini 자동 생성)
#     v1.1.0: Fixed sudo echo redirect, added docker.service dependency
#-------------------------------------------------------------------------------
# This script creates the Umbrel LCD systemd service.
# It asks which screens to show, currency, and how long each screen stays on.
#-------------------------------------------------------------------------------

echo "=================================================================================="
echo "         TBM (The Bitcoin Machine) - LCD 서비스 설정"
echo "=================================================================================="
echo
echo "이 스크립트는 LCD에 표시할 화면, 통화, 화면 전환 시간을 설정합니다."
echo "각 질문에 yes 또는 no 로 답하고 Enter 를 누르세요."
echo

# ──────────────────────────────────────────────────────────────────────────────
# 화면 선택
# ──────────────────────────────────────────────────────────────────────────────
echo "=================================================================================="
echo "                              화면 선택"
echo "=================================================================================="
echo
echo "  화면 1: 비트코인 가격 및 단위 통화당 사토시"
echo "  화면 2: 다음 비트코인 블록 정보"
echo "  화면 3: 현재 비트코인 블록 높이"
echo "  화면 4: 현재 날짜 및 시간"
echo "  화면 5: 비트코인 네트워크 정보"
echo "  화면 6: 라이트닝 페이먼트 채널 정보"
echo "  화면 7: 노드 디스크 저장 공간 정보"
echo

userScreenChoices=""

ask_screen() {
    local num=$1
    local desc=$2
    local gettingChoice=true
    while $gettingChoice; do
        read -p "화면 ${num} (${desc}) 을 표시할까요? [yes/no]: " ans
        ans=${ans^^}
        if [ "$ans" == "YES" ]; then
            echo -e "\e[1;32m  ✔ 화면 ${num} 추가됨\e[0m"
            userScreenChoices="${userScreenChoices}Screen${num},"
            gettingChoice=false
        elif [ "$ans" == "NO" ]; then
            echo "  화면 ${num} 건너뜀"
            gettingChoice=false
        else
            echo -e "\e[1;31m  yes 또는 no 로 입력해주세요.\e[0m"
        fi
    done
}

ask_screen 1 "비트코인 가격"
ask_screen 2 "다음 블록 정보"
ask_screen 3 "블록 높이"
ask_screen 4 "날짜/시간"
ask_screen 5 "네트워크 정보"
ask_screen 6 "라이트닝 채널"
ask_screen 7 "디스크 용량"

echo
echo "선택된 화면: ${userScreenChoices}"
echo

# ──────────────────────────────────────────────────────────────────────────────
# 통화 선택
# ──────────────────────────────────────────────────────────────────────────────
echo "=================================================================================="
echo "                              통화 선택"
echo "=================================================================================="
echo

gettingCurrency=true
while $gettingCurrency; do
    read -p "통화 코드를 입력하세요 (예: USD, KRW, EUR, JPY): " newCurrency
    newCurrency=${newCurrency^^}
    validationResult=$(python3 ./CurrencyData.py ${newCurrency})
    if [ "$validationResult" = "Valid" ]; then
        echo -e "\e[1;32m  ✔ 통화: ${newCurrency}\e[0m"
        gettingCurrency=false
    else
        echo -e "\e[1;31m  유효하지 않은 통화 코드입니다. 다시 입력해주세요.\e[0m"
    fi
done

echo

# ──────────────────────────────────────────────────────────────────────────────
# 화면 전환 시간 설정
# ──────────────────────────────────────────────────────────────────────────────
echo "=================================================================================="
echo "                         화면 전환 시간 설정 (초)"
echo "=================================================================================="
echo
echo "각 화면이 LCD에 표시되는 시간을 초 단위로 입력하세요."
echo "그냥 Enter 를 누르면 기본값이 적용됩니다."
echo

# 시작 로고 표시 시간
while true; do
    read -p "시작 시 Umbrel 로고 표시 시간 (기본값: 60초): " logoDuration
    logoDuration=${logoDuration:-60}
    if [[ "$logoDuration" =~ ^[0-9]+$ ]] && [ "$logoDuration" -gt 0 ]; then
        echo -e "\e[1;32m  ✔ 로고 표시 시간: ${logoDuration}초\e[0m"
        break
    else
        echo -e "\e[1;31m  양의 정수를 입력해주세요.\e[0m"
    fi
done

# 비트코인 가격 화면 표시 시간
while true; do
    read -p "비트코인 가격 화면 표시 시간 (기본값: 6초): " screen1Duration
    screen1Duration=${screen1Duration:-6}
    if [[ "$screen1Duration" =~ ^[0-9]+$ ]] && [ "$screen1Duration" -gt 0 ]; then
        echo -e "\e[1;32m  ✔ 가격 화면 표시 시간: ${screen1Duration}초\e[0m"
        break
    else
        echo -e "\e[1;31m  양의 정수를 입력해주세요.\e[0m"
    fi
done

# 나머지 화면 표시 시간
while true; do
    read -p "나머지 화면들 표시 시간 (기본값: 6초): " screenDuration
    screenDuration=${screenDuration:-6}
    if [[ "$screenDuration" =~ ^[0-9]+$ ]] && [ "$screenDuration" -gt 0 ]; then
        echo -e "\e[1;32m  ✔ 나머지 화면 표시 시간: ${screenDuration}초\e[0m"
        break
    else
        echo -e "\e[1;31m  양의 정수를 입력해주세요.\e[0m"
    fi
done

echo

# ──────────────────────────────────────────────────────────────────────────────
# config.ini 자동 생성
# ──────────────────────────────────────────────────────────────────────────────
cwd=$(pwd)

cat > "${cwd}/config.ini" << CONFIGEOF
# ============================================================
#  TBM (The Bitcoin Machine) - LCD 설정 파일 (자동 생성됨)
#  설정 변경 후: sudo systemctl restart UmbrelST7735LCD
# ============================================================

[DISPLAY]
logo_duration    = ${logoDuration}
screen1_duration = ${screen1Duration}
screen_duration  = ${screenDuration}

[BITCOIN]
# rpc_user = umbrel
# rpc_pass = moneyprintergobrrr
# rpc_host = 127.0.0.1
# rpc_port = 8332
# container = bitcoin_bitcoind_1

[LIGHTNING]
# container = lightning_lnd_1
CONFIGEOF

echo -e "\e[1;32m  ✔ config.ini 생성 완료\e[0m"
echo

# ──────────────────────────────────────────────────────────────────────────────
# systemd 서비스 생성
# ──────────────────────────────────────────────────────────────────────────────
echo "=================================================================================="
echo "                         LCD 서비스 생성 중..."
echo "=================================================================================="
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
echo -e "\e[1;32m✔ LCD 서비스 설정 완료!\e[0m"
echo
echo "  로그 확인: sudo journalctl -u UmbrelST7735LCD -f"
echo "  서비스 중지: sudo systemctl stop UmbrelST7735LCD"
echo "  서비스 재시작: sudo systemctl restart UmbrelST7735LCD"
echo "  설정 재실행: sudo systemctl stop UmbrelST7735LCD && ./umbrelLCDServiceSetup.sh"
echo
