# TBM — The Bitcoin Machine (Umbrel 1.x 호환 포크)

> **이것은 비공식 커뮤니티 포크입니다.** [doidotech/TBM](https://github.com/doidotech/TBM)의 원본 프로젝트를 **Umbrel OS 1.x** 및 **Pillow 10+** 환경에서 작동하도록 수정한 버전입니다.  
> 원본 프로젝트는 더 이상 유지보수되지 않고 있으며, 이 포크는 많은 사용자들이 Umbrel 업그레이드 후 겪는 **LCD 흰색 화면(먹통) 문제**를 해결합니다.

---

## 초보자를 위한 설치 가이드 (Mac 사용자 기준)

이 가이드는 터미널이나 코딩 경험이 없는 분들도 쉽게 따라 할 수 있도록 작성되었습니다. 차근차근 진행해 주세요.

### 1단계: Umbrel 노드에 원격으로 접속하기 (SSH)

가장 먼저, 사용자의 Mac 컴퓨터에서 Umbrel 노드(라즈베리파이)로 원격 접속해야 합니다. 이를 위해 '터미널(Terminal)' 앱을 사용합니다.

1.  **터미널 앱 열기**
    *   `Command (⌘)` + `Space` 키를 눌러 Spotlight 검색을 열고, `Terminal`을 입력한 후 엔터 키를 누릅니다.

2.  **SSH 명령어로 접속하기**
    *   터미널 창에 아래 명령어를 입력합니다. `umbrel.local`은 대부분의 홈 네트워크에서 작동하는 기본 주소입니다.

    ```bash
    ssh umbrel@umbrel.local
    ```

3.  **비밀번호 입력**
    *   비밀번호를 입력하라는 메시지가 나타납니다. 이것은 Umbrel 대시보드에 로그인할 때 사용하는 비밀번호와 같습니다.
    *   **참고:** 터미널에서는 보안을 위해 비밀번호를 입력해도 화면에 아무것도 표시되지 않습니다. 그냥 입력하고 엔터 키를 누르세요.

    ```bash
    umbrel@umbrel.local's password:
    ```

4.  **접속 성공 확인**
    *   접속에 성공하면, 아래와 같이 Umbrel 로고와 함께 환영 메시지가 나타납니다. 이제부터 입력하는 모든 명령어는 여러분의 Umbrel 노드에서 실행됩니다.

    ```
       _   _ ____  _   _ ____  _     
      | | | | __ )| | | | __ )| |    
      | | | |  _ \| | | |  _ \| |    
      | |_| | |_) | |_| | |_) | |___ 
       \___/|____/ \___/|____/|_____|
    
    ```

### 2단계: 코드 다운로드 및 설치 스크립트 실행

이제 흰색 화면 문제가 해결된 코드를 다운로드하고 설치할 차례입니다. 아래 명령어들을 **한 줄씩 복사해서 터미널에 붙여넣고 엔터**를 누르세요.

1.  **깃허브(GitHub)에서 코드 복제하기**
    *   이 명령어는 제 GitHub 레포지토리에서 수정된 TBM 코드를 여러분의 Umbrel 노드로 다운로드합니다.

    ```bash
    git clone https://github.com/ghmy4ff4t8-coder/TBM.git
    ```

2.  **작업 폴더로 이동하기**

    ```bash
    cd TBM/TBMLCD-v0.5/UmbrelLCDV2_0
    ```

3.  **설치 스크립트 실행하기**
    *   이 스크립트는 LCD 작동에 필요한 모든 프로그램과 라이브러리를 자동으로 설치합니다.

    ```bash
    chmod +x lcdSetupScript.sh
    ./lcdSetupScript.sh
    ```

    *   설치 과정에서 여러 줄의 텍스트가 빠르게 지나갈 것입니다. `Setup complete!` 메시지가 보이면 성공입니다.

### 3단계: Umbrel 노드 재부팅

설정한 내용이 올바르게 적용되려면 시스템을 재부팅해야 합니다.

```bash
sudo reboot
```

*   이 명령어를 입력하면 SSH 연결이 끊어집니다. Umbrel 노드가 완전히 다시 켜질 때까지 약 3~5분 정도 기다려주세요.

### 4단계: LCD 서비스 설정 및 시작

재부팅이 완료되면, 다시 1단계의 방법으로 Umbrel 노드에 SSH로 접속한 후 아래 명령어들을 순서대로 입력하세요.

1.  **작업 폴더로 다시 이동하기**

    ```bash
    cd TBM/TBMLCD-v0.5/UmbrelLCDV2_0
    ```

2.  **서비스 설정 스크립트 실행하기**

    ```bash
    chmod +x umbrelLCDServiceSetup.sh
    ./umbrelLCDServiceSetup.sh
    ```

3.  **화면 및 통화 선택 (매우 중요)**
    *   스크립트를 실행하면, LCD에 어떤 화면들을 표시할지, 그리고 비트코인 가격을 어떤 통화(USD, EUR, KRW 등)로 볼지 묻는 질문이 나타납니다.
    *   각 질문에 `yes` 또는 `no`를 입력하고 엔터를 누르세요.
    *   마지막으로 원하는 통화 코드를 입력하면 (예: `USD`), 모든 설정이 완료되고 LCD 서비스가 자동으로 시작됩니다.

이제 여러분의 TBM LCD가 정상적으로 작동하는 것을 확인할 수 있습니다!

---

## 문제 해결

**LCD가 여전히 흰색 화면이에요:**
*   가장 먼저 배선이 올바른지 확인하세요. (아래 배선도 참고)
*   `./lcdSetupScript.sh` 와 `./umbrelLCDServiceSetup.sh` 를 다시 실행해 보세요.

**서비스가 잘 실행되고 있는지 확인하고 싶어요:**
*   아래 명령어로 서비스 상태를 확인할 수 있습니다.
    ```bash
    sudo systemctl status UmbrelST7735LCD
    ```
*   실시간 로그를 보려면 아래 명령어를 입력하세요. 오류 메시지를 확인하는 데 유용합니다.
    ```bash
    sudo journalctl -u UmbrelST7735LCD -f
    ```

---

## 배선도 (ST7735 1.8" LCD → 라즈베리파이)

| LCD 핀 | 라즈베리파이 핀 번호 | GPIO | 설명 |
| :--- | :--- | :--- | :--- |
| VCC | Pin 1 | 3.3V | 전원 |
| GND | Pin 6 | GND | 접지 |
| SCL/CLK | Pin 23 | GPIO 11 | SPI 클럭 |
| SDA/MOSI | Pin 19 | GPIO 10 | SPI 데이터 |
| RES/RST | Pin 22 | GPIO 25 | 리셋 |
| DC | Pin 18 | GPIO 24 | 데이터/명령 선택 |
| CS | Pin 24 | GPIO 8 | 칩 선택 |
| BL/LED | Pin 17 | 3.3V | 백라이트 전원 |

---

## 수정된 기술적 문제들

| 문제 | 원인 | 해결 방안 |
| :--- | :--- | :--- |
| **LCD 흰색 화면** | Pillow 10.0.0 라이브러리에서 `draw.textsize()` 함수가 제거됨 | `draw.textbbox()`를 사용하는 호환성 함수로 대체하여 해결 |
| **pip 설치 실패** | Python 3.11+ 환경에서 시스템 패키지 보호 정책 강화 | `pip` 명령어에 `--break-system-packages` 플래그를 추가하여 해결 |
| **서비스 실행 오류** | systemd 서비스가 Docker 경로를 인식하지 못함 | 서비스 유닛 파일에 `PATH` 환경 변수를 명시적으로 추가 |
| **Umbrel 1.x 호환성** | Docker 컨테이너 이름, `bitcoin-cli` 및 `lncli` 실행 방식 변경 | 여러 컨테이너 이름을 시도하고, HTTP RPC 직접 호출을 추가하는 등 Fallback 로직 강화 |

---

## Credits

*   원본 프로젝트: [doidotech/TBM](https://github.com/doidotech/TBM) by DOIDO Technologies
*   이 포크는 [Umbrel 커뮤니티 포럼](https://community.umbrel.com/t/the-bitcoin-machine-blank-lcd-since-umbrel-os-1/15720)에 보고된 문제를 해결하기 위해 만들어졌습니다.
