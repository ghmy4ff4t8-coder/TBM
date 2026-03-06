#!/bin/bash
#-------------------------------------------------------------------------------
#   Copyright (c) DOIDO Technologies
#   Version  : 1.6.0  (Umbrel 1.x compatible fork)
#   Changes  :
#     v1.6.0: Fixed syntax error - ES/JA/ZH language blocks were outside T().
#             Removed screen1_duration (bitcoin price screen); now uses single
#             screen_duration for all screens. Only logo_duration + screen_duration.
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
echo "  3. Español (Spanish)"
echo "  4. 日本語 (Japanese)"
echo "  5. 简体中文 (Simplified Chinese)"
echo

while true; do
    read -p "Enter number / 번호 입력 [1-5]: " lang_choice
    case "$lang_choice" in
        1) LANG_CODE="EN"; break ;;
        2) LANG_CODE="KO"; break ;;
        3) LANG_CODE="ES"; break ;;
        4) LANG_CODE="JA"; break ;;
        5) LANG_CODE="ZH"; break ;;
        *) echo "  Please enter 1-5 / 1~5를 입력하세요." ;;
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
                DUR_OTHER)         echo "Info screen duration (current default: ${2}s): " ;;
                TZ_PROMPT)         echo "Enter timezone (e.g. Asia/Seoul, America/New_York, Europe/London): " ;;
                TZ_INVALID)        echo "Invalid timezone. Please try again." ;;
                TZ_VALID)          echo "✔ Timezone set to: $2" ;;
                DUR_VALID)         echo "✔ $2 duration: ${3}s" ;;
                INVALID_NUM)       echo "Please enter a positive integer." ;;
                CONFIG_GENERATED)  echo "✔ config.ini generated successfully." ;;
                SERVICE_CREATING)  echo "Creating LCD Service..." ;;
                SERVICE_DONE)      echo "✔ LCD Service setup complete!" ;;
                LOG_CMD)           echo "Check logs:" ;;
                STOP_CMD)          echo "Stop service:" ;;
                RESTART_CMD)       echo "Restart service:" ;;
                RERUN_CMD)         echo "Re-run setup:" ;;
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
                DUR_OTHER)         echo "정보 화면 전환 시간 (현재 기본값: ${2}초): " ;;
                TZ_PROMPT)         echo "시간대를 입력하세요 (예: Asia/Seoul, America/New_York): " ;;
                TZ_INVALID)        echo "유효하지 않은 시간대입니다. 다시 시도해주세요." ;;
                TZ_VALID)          echo "✔ 시간대 설정: $2" ;;
                DUR_VALID)         echo "✔ $2 시간: ${3}초" ;;
                INVALID_NUM)       echo "양의 정수를 입력해주세요." ;;
                CONFIG_GENERATED)  echo "✔ config.ini 생성 완료." ;;
                SERVICE_CREATING)  echo "LCD 서비스 생성 중..." ;;
                SERVICE_DONE)      echo "✔ LCD 서비스 설정 완료!" ;;
                LOG_CMD)           echo "로그 확인:" ;;
                STOP_CMD)          echo "서비스 중지:" ;;
                RESTART_CMD)       echo "서비스 재시작:" ;;
                RERUN_CMD)         echo "설정 재실행:" ;;
            esac
            ;;
        ES)
            case "$key" in
                BANNER)            echo "TBM (The Bitcoin Machine) - Configuración del Servicio LCD" ;;
                INTRO)             echo "Este script le guiará a través de la configuración del servicio LCD." ;;
                PROMPT_YN)         echo "Por favor, responda con yes o no, luego presione Enter." ;;
                S1_DESC)           echo "Precio de Bitcoin y sats/moneda" ;;
                S2_DESC)           echo "Información del siguiente bloque" ;;
                S3_DESC)           echo "Altura del bloque" ;;
                S4_DESC)           echo "Fecha/Hora" ;;
                S5_DESC)           echo "Información de la red" ;;
                S6_DESC)           echo "Canales de Lightning" ;;
                S7_DESC)           echo "Uso del disco" ;;
                ASK_SCREEN)        echo "¿Mostrar Pantalla $2 ($3)? [yes/no/y/n]: " ;;
                ADDED)             echo "✔ Pantalla $2 añadida." ;;
                SKIPPED)           echo "- Pantalla $2 omitida." ;;
                INVALID_YN)        echo "Entrada no válida. Por favor, ingrese yes, no, y, o n." ;;
                SCREENS_SELECTED)  echo "Pantallas seleccionadas:" ;;
                CURRENCY_PROMPT)   echo "Por favor, ingrese su código de moneda (ej., USD, KRW, EUR, JPY): " ;;
                CURRENCY_VALID)    echo "✔ Moneda establecida en: $2" ;;
                CURRENCY_INVALID)  echo "Código de moneda no válido. Por favor, inténtelo de nuevo." ;;
                DURATION_HEADER)   echo "Configuración de Duración de Pantalla (segundos)" ;;
                DURATION_INTRO)    echo "Ingrese el tiempo en segundos que se mostrará cada pantalla." ;;
                DURATION_DEFAULT)  echo "Presione Enter para mantener el valor predeterminado actual." ;;
                DUR_LOGO)          echo "Logotipo de Umbrel al inicio (predeterminado actual: ${2}s): " ;;
                DUR_OTHER)         echo "Duración de pantalla de información (predeterminado actual: ${2}s): " ;;
                TZ_PROMPT)         echo "Ingrese zona horaria (ej. America/New_York, Europe/Madrid): " ;;
                TZ_INVALID)        echo "Zona horaria inválida. Por favor, inténtelo de nuevo." ;;
                TZ_VALID)          echo "✔ Zona horaria establecida en: $2" ;;
                DUR_VALID)         echo "✔ Duración de $2: ${3}s" ;;
                INVALID_NUM)       echo "Por favor, ingrese un entero positivo." ;;
                CONFIG_GENERATED)  echo "✔ config.ini generado exitosamente." ;;
                SERVICE_CREATING)  echo "Creando Servicio LCD..." ;;
                SERVICE_DONE)      echo "✔ ¡Configuración del Servicio LCD completa!" ;;
                LOG_CMD)           echo "Ver registros:" ;;
                STOP_CMD)          echo "Detener servicio:" ;;
                RESTART_CMD)       echo "Reiniciar servicio:" ;;
                RERUN_CMD)         echo "Re-ejecutar configuración:" ;;
            esac
            ;;
        JA)
            case "$key" in
                BANNER)            echo "TBM (The Bitcoin Machine) - LCDサービス設定" ;;
                INTRO)             echo "このスクリプトはLCDサービスの設定を案内します。" ;;
                PROMPT_YN)         echo "各質問にyesまたはnoで答えてEnterキーを押してください。" ;;
                S1_DESC)           echo "ビットコイン価格＆sats/通貨" ;;
                S2_DESC)           echo "次のブロック情報" ;;
                S3_DESC)           echo "ブロック高" ;;
                S4_DESC)           echo "日付/時刻" ;;
                S5_DESC)           echo "ネットワーク情報" ;;
                S6_DESC)           echo "ライトニングチャネル" ;;
                S7_DESC)           echo "ディスク使用量" ;;
                ASK_SCREEN)        echo "画面 $2 ($3) を表示しますか？ [yes/no/y/n]: " ;;
                ADDED)             echo "✔ 画面 $2 を追加しました。" ;;
                SKIPPED)           echo "- 画面 $2 をスキップしました。" ;;
                INVALID_YN)        echo "無効な入力です。yes, no, y, または n を入力してください。" ;;
                SCREENS_SELECTED)  echo "選択された画面：" ;;
                CURRENCY_PROMPT)   echo "通貨コードを入力してください（例：USD, KRW, EUR, JPY）：" ;;
                CURRENCY_VALID)    echo "✔ 通貨を $2 に設定しました。" ;;
                CURRENCY_INVALID)  echo "無効な通貨コードです。もう一度お試しください。" ;;
                DURATION_HEADER)   echo "画面表示時間の設定（秒）" ;;
                DURATION_INTRO)    echo "各画面が表示される時間を秒単位で入力してください。" ;;
                DURATION_DEFAULT)  echo "現在のデフォルト値を維持するにはEnterキーを押してください。" ;;
                DUR_LOGO)          echo "起動時のUmbrelロゴ（現在のデフォルト：${2}秒）：" ;;
                DUR_OTHER)         echo "情報画面切替時間（現在のデフォルト：${2}秒）：" ;;
                TZ_PROMPT)         echo "タイムゾーンを入力してください（例: Asia/Tokyo, America/New_York）：" ;;
                TZ_INVALID)        echo "無効なタイムゾーンです。もう一度お試しください。" ;;
                TZ_VALID)          echo "✔ タイムゾーンを $2 に設定しました。" ;;
                DUR_VALID)         echo "✔ $2 の表示時間：${3}秒" ;;
                INVALID_NUM)       echo "正の整数を入力してください。" ;;
                CONFIG_GENERATED)  echo "✔ config.ini が正常に生成されました。" ;;
                SERVICE_CREATING)  echo "LCDサービスを作成中..." ;;
                SERVICE_DONE)      echo "✔ LCDサービスの設定が完了しました！" ;;
                LOG_CMD)           echo "ログの確認：" ;;
                STOP_CMD)          echo "サービスの停止：" ;;
                RESTART_CMD)       echo "サービスの再起動：" ;;
                RERUN_CMD)         echo "設定の再実行：" ;;
            esac
            ;;
        ZH)
            case "$key" in
                BANNER)            echo "TBM (The Bitcoin Machine) - LCD 服务设置" ;;
                INTRO)             echo "此脚本将引导您完成 LCD 服务的设置。" ;;
                PROMPT_YN)         echo "请用 yes 或 no 回答，然后按 Enter 键。" ;;
                S1_DESC)           echo "比特币价格和 sats/货币" ;;
                S2_DESC)           echo "下一个区块信息" ;;
                S3_DESC)           echo "区块高度" ;;
                S4_DESC)           echo "日期/时间" ;;
                S5_DESC)           echo "网络信息" ;;
                S6_DESC)           echo "闪电网络通道" ;;
                S7_DESC)           echo "磁盘使用情况" ;;
                ASK_SCREEN)        echo "是否显示屏幕 $2 ($3)？ [yes/no/y/n]: " ;;
                ADDED)             echo "✔ 已添加屏幕 $2。" ;;
                SKIPPED)           echo "- 已跳过屏幕 $2。" ;;
                INVALID_YN)        echo "输入无效。请输入 yes, no, y, 或 n。" ;;
                SCREENS_SELECTED)  echo "已选择的屏幕：" ;;
                CURRENCY_PROMPT)   echo "请输入您的货币代码（例如：USD, KRW, EUR, JPY）：" ;;
                CURRENCY_VALID)    echo "✔ 货币已设置为：$2" ;;
                CURRENCY_INVALID)  echo "无效的货币代码。请重试。" ;;
                DURATION_HEADER)   echo "屏幕持续时间设置（秒）" ;;
                DURATION_INTRO)    echo "请输入每个屏幕显示的秒数。" ;;
                DURATION_DEFAULT)  echo "按 Enter 键以保留当前默认值。" ;;
                DUR_LOGO)          echo "启动时的 Umbrel 徽标（当前默认值：${2}秒）：" ;;
                DUR_OTHER)         echo "信息屏幕切换时间（当前默认值：${2}秒）：" ;;
                TZ_PROMPT)         echo "请输入时区（例如: Asia/Shanghai, America/New_York）：" ;;
                TZ_INVALID)        echo "无效的时区。请重试。" ;;
                TZ_VALID)          echo "✔ 时区已设置为：$2" ;;
                DUR_VALID)         echo "✔ $2 持续时间：${3}秒" ;;
                INVALID_NUM)       echo "请输入一个正整数。" ;;
                CONFIG_GENERATED)  echo "✔ config.ini 已成功生成。" ;;
                SERVICE_CREATING)  echo "正在创建 LCD 服务..." ;;
                SERVICE_DONE)      echo "✔ LCD 服务设置完成！" ;;
                LOG_CMD)           echo "查看日志：" ;;
                STOP_CMD)          echo "停止服务：" ;;
                RESTART_CMD)       echo "重启服务：" ;;
                RERUN_CMD)         echo "重新运行设置：" ;;
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
# Timezone Selection
# ──────────────────────────────────────────────────────────────────────────────
echo "--- [ 2/4 ] Timezone ---"
echo

DEFAULT_TZ=$(read_config_value "timezone" "UTC")

gettingTimezone=true
while $gettingTimezone; do
    read -rp "$(T TZ_PROMPT)" newTimezone
    newTimezone="${newTimezone:-$DEFAULT_TZ}"
    # Validate using Python's pytz
    tzValid=$(python3 -c "import pytz; pytz.timezone('${newTimezone}'); print('Valid')" 2>/dev/null || echo "Invalid")
    if [ "$tzValid" = "Valid" ]; then
        echo -e "  \e[1;32m$(T TZ_VALID "$newTimezone")\e[0m"
        gettingTimezone=false
    else
        echo -e "  \e[1;31m$(T TZ_INVALID)\e[0m"
    fi
done
echo

# ──────────────────────────────────────────────────────────────────────────────
# Currency Selection
# ──────────────────────────────────────────────────────────────────────────────
echo "--- [ 3/4 ] Currency ---"
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
# Duration Setup  (logo + all screens — no separate bitcoin price duration)
# ──────────────────────────────────────────────────────────────────────────────
echo "--- [ 4/4 ] $(T DURATION_HEADER) ---"
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
ask_duration "$(T DUR_OTHER "$DEFAULT_OTHER")" "$DEFAULT_OTHER" "Screen" screenDuration
echo

# ──────────────────────────────────────────────────────────────────────────────
# Generate config.ini
# ──────────────────────────────────────────────────────────────────────────────
cat > "${cwd}/config.ini" << CONFIGEOF
# TBM LCD Configuration File (auto-generated by setup script)
# To apply changes, restart the service: sudo systemctl restart UmbrelST7735LCD
# Or run manually: cd ${cwd} && python3 UmbrelLCD.py

[USER]
language = ${LANG_CODE,,}
timezone = ${newTimezone}
currency = ${newCurrency}
screens = ${userScreenChoices//Screen/}
temp_unit = C

[DISPLAY]
logo_duration   = ${logoDuration}
screen_duration = ${screenDuration}

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
ExecStart=/usr/bin/python3 ${cwd}/UmbrelLCD.py
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
printf "  %-22s sudo journalctl -u UmbrelST7735LCD -f\n"                                   "$(T LOG_CMD)"
printf "  %-22s sudo systemctl stop UmbrelST7735LCD\n"                                      "$(T STOP_CMD)"
printf "  %-22s sudo systemctl restart UmbrelST7735LCD\n"                                   "$(T RESTART_CMD)"
printf "  %-22s sudo systemctl stop UmbrelST7735LCD && bash umbrelLCDServiceSetup.sh\n"     "$(T RERUN_CMD)"
echo
