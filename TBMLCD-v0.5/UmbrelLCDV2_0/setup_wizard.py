"""
setup_wizard.py — Interactive configuration wizard for The Bitcoin Machine LCD.

Flow:
  1. Show current settings summary (in saved language)
  2. "Start now [Y/n]? (auto-start in 10s if no input)"
  3. If Y or timeout → return settings, main script starts
  4. If N → show settings menu, save to config.ini, then return settings
"""

import os
import sys
import select
import configparser
import pytz

# ---------------------------------------------------------------------------
# Translations
# ---------------------------------------------------------------------------
TRANSLATIONS = {
    'en': {
        'lang_name':      'English',
        'current_settings': '--- Current Settings ---',
        'language':       'Language',
        'timezone':       'Timezone',
        'currency':       'Currency',
        'screens':        'Screens',
        'logo_duration':  'Logo duration',
        'screen_duration':'Screen duration',
        'temp_unit':      'Temperature unit',
        'seconds':        's',
        'prompt_start':   'Start now? [Y/n] (auto-start in {n}s if no input): ',
        'menu_title':     '--- Settings Menu ---',
        'menu_items': [
            '1. Language',
            '2. Timezone',
            '3. Currency',
            '4. Screens to display',
            '5. Logo duration (seconds)',
            '6. Screen duration (seconds)',
            '7. Temperature unit',
            '8. Save & Start',
        ],
        'menu_prompt':    'Select [1-8]: ',
        'saved':          'Settings saved.',
        'starting':       'Starting...',
        # Language selection
        'select_lang':    'Select language:',
        # Timezone
        'tz_prompt':      'Enter timezone (e.g. Asia/Seoul, America/New_York, Europe/London): ',
        'tz_invalid':     'Invalid timezone. Keeping current: {tz}',
        # Currency
        'currency_prompt':'Enter currency code (e.g. USD, EUR, KRW, JPY, GBP): ',
        # Screens
        'screens_prompt': 'Enter screens to show (e.g. 1234567 or 135): ',
        'screens_invalid':'Invalid input. Use digits 1-7 only.',
        # Durations
        'logo_dur_prompt':'Logo duration in seconds (default 4): ',
        'scr_dur_prompt': 'Screen duration in seconds (default 4): ',
        'dur_invalid':    'Invalid number. Keeping current: {v}',
        # Temp unit
        'temp_prompt':    'Temperature unit — 1) Celsius (°C)  2) Fahrenheit (°F): ',
        'temp_invalid':   'Invalid choice. Keeping current: {v}',
    },
    'ko': {
        'lang_name':      '한국어',
        'current_settings': '--- 현재 설정 ---',
        'language':       '언어',
        'timezone':       '시간대',
        'currency':       '통화',
        'screens':        '화면',
        'logo_duration':  '로고 표시 시간',
        'screen_duration':'화면 전환 시간',
        'temp_unit':      '온도 단위',
        'seconds':        '초',
        'prompt_start':   '지금 바로 시작하려면 Y, 설정을 변경하려면 N을 누르세요. [Y/n] (무응답 시 {n}초 후 자동 시작): ',
        'menu_title':     '--- 설정 메뉴 ---',
        'menu_items': [
            '1. 언어',
            '2. 시간대',
            '3. 통화',
            '4. 표시할 화면 선택',
            '5. 로고 표시 시간 (초)',
            '6. 화면 전환 시간 (초)',
            '7. 온도 단위',
            '8. 저장 후 시작',
        ],
        'menu_prompt':    '선택 [1-8]: ',
        'saved':          '설정이 저장되었습니다.',
        'starting':       '시작합니다...',
        'select_lang':    '언어를 선택하세요:',
        'tz_prompt':      '시간대를 입력하세요 (예: Asia/Seoul, America/New_York): ',
        'tz_invalid':     '잘못된 시간대입니다. 현재 값 유지: {tz}',
        'currency_prompt':'통화 코드를 입력하세요 (예: USD, EUR, KRW, JPY): ',
        'screens_prompt': '표시할 화면 번호를 입력하세요 (예: 1234567 또는 135): ',
        'screens_invalid':'잘못된 입력입니다. 1~7 숫자만 사용하세요.',
        'logo_dur_prompt':'로고 표시 시간(초, 기본값 4): ',
        'scr_dur_prompt': '화면 전환 시간(초, 기본값 4): ',
        'dur_invalid':    '잘못된 숫자입니다. 현재 값 유지: {v}',
        'temp_prompt':    '온도 단위 — 1) 섭씨(°C)  2) 화씨(°F): ',
        'temp_invalid':   '잘못된 선택입니다. 현재 값 유지: {v}',
    },
    'es': {
        'lang_name':      'Español',
        'current_settings': '--- Configuración actual ---',
        'language':       'Idioma',
        'timezone':       'Zona horaria',
        'currency':       'Moneda',
        'screens':        'Pantallas',
        'logo_duration':  'Duración del logo',
        'screen_duration':'Duración de pantalla',
        'temp_unit':      'Unidad de temperatura',
        'seconds':        's',
        'prompt_start':   '¿Iniciar ahora? [Y/n] (inicio automático en {n}s si no hay respuesta): ',
        'menu_title':     '--- Menú de configuración ---',
        'menu_items': [
            '1. Idioma',
            '2. Zona horaria',
            '3. Moneda',
            '4. Pantallas a mostrar',
            '5. Duración del logo (segundos)',
            '6. Duración de pantalla (segundos)',
            '7. Unidad de temperatura',
            '8. Guardar e iniciar',
        ],
        'menu_prompt':    'Seleccione [1-8]: ',
        'saved':          'Configuración guardada.',
        'starting':       'Iniciando...',
        'select_lang':    'Seleccione idioma:',
        'tz_prompt':      'Ingrese zona horaria (ej. America/New_York, Europe/Madrid): ',
        'tz_invalid':     'Zona horaria inválida. Manteniendo: {tz}',
        'currency_prompt':'Ingrese código de moneda (ej. USD, EUR, KRW): ',
        'screens_prompt': 'Ingrese pantallas a mostrar (ej. 1234567 o 135): ',
        'screens_invalid':'Entrada inválida. Use solo dígitos 1-7.',
        'logo_dur_prompt':'Duración del logo en segundos (predeterminado 4): ',
        'scr_dur_prompt': 'Duración de pantalla en segundos (predeterminado 4): ',
        'dur_invalid':    'Número inválido. Manteniendo: {v}',
        'temp_prompt':    'Unidad de temperatura — 1) Celsius (°C)  2) Fahrenheit (°F): ',
        'temp_invalid':   'Selección inválida. Manteniendo: {v}',
    },
    'ja': {
        'lang_name':      '日本語',
        'current_settings': '--- 現在の設定 ---',
        'language':       '言語',
        'timezone':       'タイムゾーン',
        'currency':       '通貨',
        'screens':        '画面',
        'logo_duration':  'ロゴ表示時間',
        'screen_duration':'画面切替時間',
        'temp_unit':      '温度単位',
        'seconds':        '秒',
        'prompt_start':   '今すぐ開始しますか？ [Y/n] (入力なしの場合{n}秒後に自動開始): ',
        'menu_title':     '--- 設定メニュー ---',
        'menu_items': [
            '1. 言語',
            '2. タイムゾーン',
            '3. 通貨',
            '4. 表示する画面',
            '5. ロゴ表示時間（秒）',
            '6. 画面切替時間（秒）',
            '7. 温度単位',
            '8. 保存して開始',
        ],
        'menu_prompt':    '選択 [1-8]: ',
        'saved':          '設定が保存されました。',
        'starting':       '開始します...',
        'select_lang':    '言語を選択してください:',
        'tz_prompt':      'タイムゾーンを入力してください（例: Asia/Tokyo, America/New_York）: ',
        'tz_invalid':     '無効なタイムゾーンです。現在の値を維持: {tz}',
        'currency_prompt':'通貨コードを入力してください（例: USD, EUR, JPY）: ',
        'screens_prompt': '表示する画面番号を入力してください（例: 1234567 または 135）: ',
        'screens_invalid':'無効な入力です。1〜7の数字のみ使用してください。',
        'logo_dur_prompt':'ロゴ表示時間（秒、デフォルト4）: ',
        'scr_dur_prompt': '画面切替時間（秒、デフォルト4）: ',
        'dur_invalid':    '無効な数値です。現在の値を維持: {v}',
        'temp_prompt':    '温度単位 — 1) 摂氏（°C）  2) 華氏（°F）: ',
        'temp_invalid':   '無効な選択です。現在の値を維持: {v}',
    },
    'zh': {
        'lang_name':      '简体中文',
        'current_settings': '--- 当前设置 ---',
        'language':       '语言',
        'timezone':       '时区',
        'currency':       '货币',
        'screens':        '屏幕',
        'logo_duration':  'Logo显示时间',
        'screen_duration':'屏幕切换时间',
        'temp_unit':      '温度单位',
        'seconds':        '秒',
        'prompt_start':   '立即开始？[Y/n]（无输入{n}秒后自动开始）: ',
        'menu_title':     '--- 设置菜单 ---',
        'menu_items': [
            '1. 语言',
            '2. 时区',
            '3. 货币',
            '4. 显示的屏幕',
            '5. Logo显示时间（秒）',
            '6. 屏幕切换时间（秒）',
            '7. 温度单位',
            '8. 保存并开始',
        ],
        'menu_prompt':    '选择 [1-8]: ',
        'saved':          '设置已保存。',
        'starting':       '正在启动...',
        'select_lang':    '请选择语言:',
        'tz_prompt':      '请输入时区（例如: Asia/Shanghai, America/New_York）: ',
        'tz_invalid':     '无效的时区。保持当前值: {tz}',
        'currency_prompt':'请输入货币代码（例如: USD, EUR, CNY）: ',
        'screens_prompt': '请输入要显示的屏幕编号（例如: 1234567 或 135）: ',
        'screens_invalid':'输入无效。请只使用1-7的数字。',
        'logo_dur_prompt':'Logo显示时间（秒，默认4）: ',
        'scr_dur_prompt': '屏幕切换时间（秒，默认4）: ',
        'dur_invalid':    '无效的数字。保持当前值: {v}',
        'temp_prompt':    '温度单位 — 1) 摄氏度（°C）  2) 华氏度（°F）: ',
        'temp_invalid':   '无效的选择。保持当前值: {v}',
    },
}

LANG_MENU = [
    ('en', 'English'),
    ('ko', '한국어'),
    ('es', 'Español'),
    ('ja', '日本語'),
    ('zh', '简体中文'),
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def timed_input(prompt, timeout=10):
    """Print prompt and wait up to `timeout` seconds for a line of input.
    Returns the stripped input string, or '' if timed out or stdin not a tty.
    """
    print(prompt, end='', flush=True)
    # If stdin is not a tty (e.g. systemd service), return '' immediately
    if not sys.stdin.isatty():
        print()
        return ''
    ready, _, _ = select.select([sys.stdin], [], [], timeout)
    if ready:
        return sys.stdin.readline().strip()
    print()  # newline after timeout
    return ''


def _load_config(config_path):
    cfg = configparser.ConfigParser()
    cfg.read(config_path)
    return cfg


def _save_config(cfg, config_path):
    """Save [USER] and [DISPLAY] values to config.ini while preserving comments.

    Reads the original file line by line, replaces values for known keys in
    [USER] and [DISPLAY] sections, and preserves all comments and other
    sections unchanged. New keys are appended to their section if not found.
    """
    user_vals = dict(cfg.items('USER')) if cfg.has_section('USER') else {}
    disp_vals = dict(cfg.items('DISPLAY')) if cfg.has_section('DISPLAY') else {}

    try:
        with open(config_path, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        lines = []

    out_lines = []
    current_section = None
    written_user = set()
    written_disp = set()

    for line in lines:
        stripped = line.strip()

        # Detect section header
        if stripped.startswith('[') and ']' in stripped:
            # Before switching sections, flush any unwritten keys
            if current_section == 'USER':
                for k, v in user_vals.items():
                    if k not in written_user:
                        out_lines.append(f'{k} = {v}\n')
                        written_user.add(k)
            elif current_section == 'DISPLAY':
                for k, v in disp_vals.items():
                    if k not in written_disp:
                        out_lines.append(f'{k} = {v}\n')
                        written_disp.add(k)
            current_section = stripped[1:stripped.index(']')].upper()
            out_lines.append(line)
            continue

        # Replace active key=value lines (not comments)
        if '=' in stripped and not stripped.startswith('#') and not stripped.startswith(';'):
            key = stripped.split('=', 1)[0].strip().lower()
            if current_section == 'USER' and key in user_vals:
                out_lines.append(f'{key} = {user_vals[key]}\n')
                written_user.add(key)
                continue
            elif current_section == 'DISPLAY' and key in disp_vals:
                out_lines.append(f'{key} = {disp_vals[key]}\n')
                written_disp.add(key)
                continue

        out_lines.append(line)

    # Flush remaining unwritten keys at end of file
    if current_section == 'USER':
        for k, v in user_vals.items():
            if k not in written_user:
                out_lines.append(f'{k} = {v}\n')
    elif current_section == 'DISPLAY':
        for k, v in disp_vals.items():
            if k not in written_disp:
                out_lines.append(f'{k} = {v}\n')

    # If [USER] section was never found in the file, append it
    existing_sections = [
        l.strip()[1:l.strip().index(']')].upper()
        for l in out_lines
        if l.strip().startswith('[') and ']' in l.strip()
    ]
    if 'USER' not in existing_sections:
        out_lines.append('\n[USER]\n')
        for k, v in user_vals.items():
            out_lines.append(f'{k} = {v}\n')

    with open(config_path, 'w') as f:
        f.writelines(out_lines)


def _get(cfg, section, key, fallback):
    return cfg.get(section, key, fallback=fallback)


# ---------------------------------------------------------------------------
# Settings menu handlers
# ---------------------------------------------------------------------------

def _menu_language(cfg, t):
    print()
    print(t['select_lang'])
    for i, (code, name) in enumerate(LANG_MENU, 1):
        print(f'  {i}) {name}')
    choice = input('Select [1-5]: ').strip()
    if choice.isdigit() and 1 <= int(choice) <= len(LANG_MENU):
        code = LANG_MENU[int(choice) - 1][0]
        if 'USER' not in cfg:
            cfg['USER'] = {}
        cfg['USER']['language'] = code
        return TRANSLATIONS[code]
    return t


def _menu_timezone(cfg, t):
    tz_current = _get(cfg, 'USER', 'timezone', 'UTC')
    val = input(t['tz_prompt']).strip()
    if not val:
        return
    try:
        pytz.timezone(val)
        if 'USER' not in cfg:
            cfg['USER'] = {}
        cfg['USER']['timezone'] = val
    except pytz.exceptions.UnknownTimeZoneError:
        print(t['tz_invalid'].format(tz=tz_current))


def _menu_currency(cfg, t):
    val = input(t['currency_prompt']).strip().upper()
    if val:
        if 'USER' not in cfg:
            cfg['USER'] = {}
        cfg['USER']['currency'] = val


def _menu_screens(cfg, t):
    val = input(t['screens_prompt']).strip()
    # Accept digits 1-7 only, deduplicate, sort
    digits = sorted(set(c for c in val if c in '1234567'))
    if not digits:
        print(t['screens_invalid'])
        return
    screens_str = ''.join(digits)
    if 'USER' not in cfg:
        cfg['USER'] = {}
    cfg['USER']['screens'] = screens_str


def _menu_logo_duration(cfg, t):
    current = _get(cfg, 'DISPLAY', 'logo_duration', '4')
    val = input(t['logo_dur_prompt']).strip()
    if not val:
        return
    try:
        v = int(val)
        if v < 1:
            raise ValueError
        if 'DISPLAY' not in cfg:
            cfg['DISPLAY'] = {}
        cfg['DISPLAY']['logo_duration'] = str(v)
    except ValueError:
        print(t['dur_invalid'].format(v=current))


def _menu_screen_duration(cfg, t):
    current = _get(cfg, 'DISPLAY', 'screen_duration', '4')
    val = input(t['scr_dur_prompt']).strip()
    if not val:
        return
    try:
        v = int(val)
        if v < 1:
            raise ValueError
        if 'DISPLAY' not in cfg:
            cfg['DISPLAY'] = {}
        cfg['DISPLAY']['screen_duration'] = str(v)
    except ValueError:
        print(t['dur_invalid'].format(v=current))


def _menu_temp_unit(cfg, t):
    current = _get(cfg, 'USER', 'temp_unit', 'C')
    val = input(t['temp_prompt']).strip()
    if val == '1':
        unit = 'C'
    elif val == '2':
        unit = 'F'
    else:
        print(t['temp_invalid'].format(v=current))
        return
    if 'USER' not in cfg:
        cfg['USER'] = {}
    cfg['USER']['temp_unit'] = unit


# ---------------------------------------------------------------------------
# Main wizard entry point
# ---------------------------------------------------------------------------

def run_wizard(config_path):
    """Run the interactive setup wizard.

    Returns a dict with the effective settings:
      {
        'currency': str,
        'screens': str,          # e.g. 'Screen1Screen2...'
        'timezone': str,
        'temp_unit': str,        # 'C' or 'F'
        'logo_duration': int,
        'screen_duration': int,
        'language': str,
      }
    """
    cfg = _load_config(config_path)

    # Ensure USER section exists with defaults
    if 'USER' not in cfg:
        cfg['USER'] = {}
    if 'DISPLAY' not in cfg:
        cfg['DISPLAY'] = {}

    # Read current values (with defaults)
    lang      = _get(cfg, 'USER', 'language',  'en')
    if lang not in TRANSLATIONS:
        lang = 'en'
    t = TRANSLATIONS[lang]

    currency  = _get(cfg, 'USER', 'currency',  'USD')
    timezone  = _get(cfg, 'USER', 'timezone',  'UTC')
    screens   = _get(cfg, 'USER', 'screens',   '1234567')
    temp_unit = _get(cfg, 'USER', 'temp_unit', 'C')
    logo_dur  = int(_get(cfg, 'DISPLAY', 'logo_duration',   '4'))
    scr_dur   = int(_get(cfg, 'DISPLAY', 'screen_duration', '4'))

    # Build human-readable screens string
    screens_display = ', '.join(f'Screen{c}' for c in screens)
    temp_display = '°C' if temp_unit == 'C' else '°F'

    # --- Show current settings summary ---
    print()
    print(t['current_settings'])
    print(f"  {t['language']:20s}: {t['lang_name']}")
    print(f"  {t['timezone']:20s}: {timezone}")
    print(f"  {t['currency']:20s}: {currency}")
    print(f"  {t['screens']:20s}: {screens_display}")
    print(f"  {t['logo_duration']:20s}: {logo_dur}{t['seconds']}")
    print(f"  {t['screen_duration']:20s}: {scr_dur}{t['seconds']}")
    print(f"  {t['temp_unit']:20s}: {temp_display}")
    print()

    # --- Ask to start or configure ---
    answer = timed_input(t['prompt_start'].format(n=10), timeout=10)

    if answer.lower() not in ('n', 'no'):
        # Y, empty, or timeout → start immediately
        print(t['starting'])
    else:
        # --- Settings menu loop ---
        while True:
            print()
            print(t['menu_title'])
            for item in t['menu_items']:
                print(f'  {item}')
            print()
            choice = input(t['menu_prompt']).strip()

            if choice == '1':
                t = _menu_language(cfg, t)
                lang = _get(cfg, 'USER', 'language', 'en')
            elif choice == '2':
                _menu_timezone(cfg, t)
            elif choice == '3':
                _menu_currency(cfg, t)
            elif choice == '4':
                _menu_screens(cfg, t)
            elif choice == '5':
                _menu_logo_duration(cfg, t)
            elif choice == '6':
                _menu_screen_duration(cfg, t)
            elif choice == '7':
                _menu_temp_unit(cfg, t)
            elif choice == '8':
                _save_config(cfg, config_path)
                print(t['saved'])
                print(t['starting'])
                break
            else:
                continue

    # Re-read final values after possible changes
    cfg = _load_config(config_path)
    currency  = _get(cfg, 'USER', 'currency',  'USD').upper()
    timezone  = _get(cfg, 'USER', 'timezone',  'UTC')
    screens   = _get(cfg, 'USER', 'screens',   '1234567')
    temp_unit = _get(cfg, 'USER', 'temp_unit', 'C')
    logo_dur  = int(_get(cfg, 'DISPLAY', 'logo_duration',   '4'))
    scr_dur   = int(_get(cfg, 'DISPLAY', 'screen_duration', '4'))

    # Convert screens string (e.g. '1234567') to userScreenChoices format
    screens_choices = ''.join(f'Screen{c}' for c in screens)

    return {
        'currency':        currency,
        'screens':         screens_choices,
        'timezone':        timezone,
        'temp_unit':       temp_unit,
        'logo_duration':   logo_dur,
        'screen_duration': scr_dur,
        'language':        lang,
    }
