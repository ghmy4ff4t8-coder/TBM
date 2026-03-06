"""
setup_wizard.py — Interactive configuration wizard for The Bitcoin Machine LCD.

Flow:
  1. Auto-detect system timezone and write to config.ini if not already set
  2. Show current settings summary (English only)
  3. "Start now [Y/n]? (auto-start in 10s if no input)"
  4. If Y or timeout → return settings, main script starts
  5. If N → show settings menu, save to config.ini, then return settings
"""

import os
import sys
import select
import subprocess
import configparser
import pytz


# ---------------------------------------------------------------------------
# Auto-detect system timezone
# ---------------------------------------------------------------------------

def detect_system_timezone():
    """Try to read the system timezone from the OS.

    Tries (in order):
      1. timedatectl show --property=Timezone --value
      2. /etc/timezone
      3. Resolve /etc/localtime symlink
    Returns a valid IANA timezone string, or 'UTC' as fallback.
    """
    # Method 1: timedatectl (most reliable on systemd-based systems)
    try:
        result = subprocess.run(
            ['timedatectl', 'show', '--property=Timezone', '--value'],
            capture_output=True, text=True, timeout=3
        )
        tz = result.stdout.strip()
        if tz:
            pytz.timezone(tz)  # validate
            return tz
    except Exception:
        pass

    # Method 2: /etc/timezone (Debian/Ubuntu/Raspberry Pi OS)
    try:
        with open('/etc/timezone', 'r') as f:
            tz = f.read().strip()
        if tz:
            pytz.timezone(tz)  # validate
            return tz
    except Exception:
        pass

    # Method 3: /etc/localtime symlink
    try:
        link = os.readlink('/etc/localtime')
        # e.g. /usr/share/zoneinfo/Asia/Seoul
        if 'zoneinfo/' in link:
            tz = link.split('zoneinfo/', 1)[1]
            pytz.timezone(tz)  # validate
            return tz
    except Exception:
        pass

    return 'UTC'


# ---------------------------------------------------------------------------
# Timed input helper
# ---------------------------------------------------------------------------

def timed_input(prompt, timeout=10):
    """Print prompt and wait up to `timeout` seconds for user input.

    Returns the stripped input string, or '' on timeout or non-tty stdin.
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
    """Save [USER] and [DISPLAY] values to config.ini while preserving comments."""
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

        if stripped.startswith('[') and ']' in stripped:
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

    if current_section == 'USER':
        for k, v in user_vals.items():
            if k not in written_user:
                out_lines.append(f'{k} = {v}\n')
    elif current_section == 'DISPLAY':
        for k, v in disp_vals.items():
            if k not in written_disp:
                out_lines.append(f'{k} = {v}\n')

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

def _menu_currency(cfg):
    val = input('Enter currency code (e.g. USD, EUR, KRW, JPY, GBP): ').strip().upper()
    if val:
        if 'USER' not in cfg:
            cfg['USER'] = {}
        cfg['USER']['currency'] = val


def _menu_screens(cfg):
    val = input('Enter screens to show (e.g. 1234567 or 135): ').strip()
    digits = sorted(set(c for c in val if c in '1234567'))
    if not digits:
        print('Invalid input. Use digits 1-7 only.')
        return
    if 'USER' not in cfg:
        cfg['USER'] = {}
    cfg['USER']['screens'] = ''.join(digits)


def _menu_screen_duration(cfg):
    current = _get(cfg, 'DISPLAY', 'screen_duration', '4')
    val = input(f'Info screen duration in seconds (current: {current}s): ').strip()
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
        print(f'Invalid number. Keeping current: {current}')


def _menu_temp_unit(cfg):
    current = _get(cfg, 'USER', 'temp_unit', 'C')
    val = input('Temperature unit — 1) Celsius (°C)  2) Fahrenheit (°F): ').strip()
    if val == '1':
        unit = 'C'
    elif val == '2':
        unit = 'F'
    else:
        print(f'Invalid choice. Keeping current: {"°C" if current == "C" else "°F"}')
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
        'screen_duration': int,
      }
    """
    cfg = _load_config(config_path)

    if 'USER' not in cfg:
        cfg['USER'] = {}
    if 'DISPLAY' not in cfg:
        cfg['DISPLAY'] = {}

    # --- Auto-detect and set timezone if not already configured ---
    saved_tz = _get(cfg, 'USER', 'timezone', '').strip()
    if not saved_tz or saved_tz == 'UTC':
        detected_tz = detect_system_timezone()
        cfg['USER']['timezone'] = detected_tz
        _save_config(cfg, config_path)
        cfg = _load_config(config_path)

    # Read current values
    currency  = _get(cfg, 'USER', 'currency',  'USD')
    timezone  = _get(cfg, 'USER', 'timezone',  'UTC')
    screens   = _get(cfg, 'USER', 'screens',   '1234567')
    temp_unit = _get(cfg, 'USER', 'temp_unit', 'C')
    scr_dur   = int(_get(cfg, 'DISPLAY', 'screen_duration', '4'))

    screens_display = ', '.join(f'Screen{c}' for c in screens)
    temp_display = '°C' if temp_unit == 'C' else '°F'

    # --- Show current settings summary ---
    print()
    print('--- Current Settings ---')
    print(f'  {"Timezone":<22}: {timezone}')
    print(f'  {"Currency":<22}: {currency}')
    print(f'  {"Screens":<22}: {screens_display}')
    print(f'  {"Info screen duration":<22}: {scr_dur}s')
    print(f'  {"Temperature unit":<22}: {temp_display}')
    print()

    # --- Ask to start or configure ---
    answer = timed_input('Start now? [Y/n] (auto-start in 10s if no input): ', timeout=10)

    if answer.lower() not in ('n', 'no'):
        print('Starting...')
    else:
        # --- Settings menu loop ---
        while True:
            print()
            print('--- Settings Menu ---')
            print('  1. Currency')
            print('  2. Screens to display')
            print('  3. Info screen duration (seconds)')
            print('  4. Temperature unit')
            print('  5. Save & Start')
            print()
            choice = input('Select [1-5]: ').strip()

            if choice == '1':
                _menu_currency(cfg)
            elif choice == '2':
                _menu_screens(cfg)
            elif choice == '3':
                _menu_screen_duration(cfg)
            elif choice == '4':
                _menu_temp_unit(cfg)
            elif choice == '5':
                _save_config(cfg, config_path)
                print('Settings saved.')
                print('Starting...')
                break
            else:
                continue

    # Re-read final values
    cfg = _load_config(config_path)
    currency  = _get(cfg, 'USER', 'currency',  'USD').upper()
    timezone  = _get(cfg, 'USER', 'timezone',  'UTC')
    screens   = _get(cfg, 'USER', 'screens',   '1234567')
    temp_unit = _get(cfg, 'USER', 'temp_unit', 'C')
    scr_dur   = int(_get(cfg, 'DISPLAY', 'screen_duration', '4'))

    screens_choices = ''.join(f'Screen{c}' for c in screens)

    return {
        'currency':        currency,
        'screens':         screens_choices,
        'timezone':        timezone,
        'temp_unit':       temp_unit,
        'screen_duration': scr_dur,
    }
