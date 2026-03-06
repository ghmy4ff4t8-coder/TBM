[English](README.md) | [한국어](README.ko.md) | [Español](README.es.md) | [日本語](README.ja.md) | [简体中文](README.zh.md)

> # TBM — The Bitcoin Machine (兼容 Umbrel 1.x 的分叉版本)
> 
> > **这是一个非官方的社区分叉版本。** 这是对原始 [doidotech/TBM](https://github.com/doidotech/TBM) 项目的修改版本，已更新以在 **Umbrel OS 1.x** 和 **Pillow 10+** 环境下工作。
> > 原始项目已不再维护，此分叉版本解决了许多用户在升级 Umbrel 后遇到的 **LCD 白屏死机 (WSOD)** 问题。
> 
> ---
> 
> ## 新手友好安装指南 (适用于 Mac 用户)
> 
> 本指南专为没有终端或编码经验的用户编写。请仔细按照步骤操作。
> 
> ### 步骤 1：远程连接到您的 Umbrel 节点 (SSH)
> 
> 首先，您需要从您的 Mac 电脑远程连接到您的 Umbrel 节点 (Raspberry Pi)。我们将使用“终端”应用程序来完成此操作。
> 
> 1.  **打开终端应用程序**
>     *   按 `Command (⌘)` + `空格键` 打开 Spotlight 搜索，输入 `Terminal`，然后按 Enter 键。
> 
> 2.  **使用 SSH 命令连接**
>     *   在终端窗口中，输入以下命令。`umbrel.local` 是在大多数家庭网络中都有效的默认地址。
> 
>     ```bash
>     ssh umbrel@umbrel.local
>     ```
> 
> 3.  **输入您的密码**
>     *   系统将提示您输入密码。这与您用于登录 Umbrel 仪表板的密码相同。
>     *   **注意：** 出于安全考虑，当您输入密码时，屏幕上不会显示任何内容。只需输入并按 Enter 键即可。
> 
>     ```bash
>     umbrel@umbrel.local's password:
>     ```
> 
> 4.  **确认连接成功**
>     *   如果连接成功，您将看到带有 Umbrel 徽标的欢迎消息。从现在开始，您输入的所有命令都将在您的 Umbrel 节点上执行。
> 
>     ```
>        _   _ ____  _   _ ____  _     
>       | | | | __ )| | | | __ )| |    
>       | | | |  _ \| | | |  _ \| |    
>       | |_| | |_) | |_| | |_) | |___ 
>        \___/|____/ \___/|____/|_____|
>     ```
> 
> ### 步骤 2：下载代码并运行安装脚本
> 
> 现在是时候下载修复了白屏问题的代码并进行安装了。**请将以下命令逐行复制并粘贴到终端中，然后按 Enter 键。**
> 
> 1.  **从 GitHub 克隆代码**
>     *   此命令将从我的 GitHub 存储库中下载修改后的 TBM 代码到您的 Umbrel 节点。
> 
>     ```bash
>     git clone https://github.com/ghmy4ff4t8-coder/TBM.git
>     ```
> 
> 2.  **导航到工作目录**
> 
>     ```bash
>     cd TBM/TBMLCD-v0.5/UmbrelLCDV2_0
>     ```
> 
> 3.  **运行设置脚本**
>     *   此脚本会自动安装 LCD 工作所需的所有程序和库。
> 
>     ```bash
>     chmod +x lcdSetupScript.sh
>     ./lcdSetupScript.sh
>     ```
> 
>     *   在安装过程中，您会看到许多文本行滚动而过。如果您看到 `Setup complete!` 消息，则表示安装成功。
> 
> ### 步骤 3：重新启动您的 Umbrel 节点
> 
> 为确保所有设置都正确应用，您需要重新启动系统。
> 
> ```bash
> sudo reboot
> ```
> 
> *   此命令将断开您的 SSH 会话。请等待大约 3-5 分钟，以便您的 Umbrel 节点完全重新启动。
> 
> ### 步骤 4：设置并启动 LCD 服务
> 
> 重启完成后，请像步骤 1 中那样通过 SSH 重新连接到您的 Umbrel 节点，然后按顺序输入以下命令。
> 
> 1.  **再次导航到工作目录**
> 
>     ```bash
>     cd ~/TBM/TBMLCD-v0.5/UmbrelLCDV2_0
>     ```
> 
> 2.  **运行服务设置脚本**
> 
>     ```bash
>     chmod +x umbrelLCDServiceSetup.sh
>     ./umbrelLCDServiceSetup.sh
>     ```
> 
> 3.  **选择屏幕和货币 (非常重要)**
>     *   当您运行脚本时，系统会询问您要在 LCD 上显示哪些屏幕，以及以哪种货币 (USD, EUR, KRW 等) 查看比特币价格。
>     *   对每个问题回答 `yes` 或 `no`，然后按 Enter 键。
>     *   最后，输入您想要的货币代码 (例如 `USD`)，所有设置都将完成，LCD 服务将自动启动。
> 
> 现在您可以看到您的 TBM LCD 正常工作了！
> 
> ---
> 
> ## 故障排除
> 
> **我的 LCD 仍然是白屏：**
> *   首先，检查接线是否正确 (请参阅下面的接线图)。
> *   尝试再次运行 `./lcdSetupScript.sh` 和 `./umbrelLCDServiceSetup.sh`。
> 
> **我想检查服务是否正常运行：**
> *   您可以使用以下命令检查服务状态：
>     ```bash
>     sudo systemctl status UmbrelST7735LCD
>     ```
> *   要查看实时日志，请输入以下命令。这对于检查错误消息很有用。
>     ```bash
>     sudo journalctl -u UmbrelST7735LCD -f
>     ```
> 
> ---
> 
> ## 接线图 (ST7735 1.8" LCD → Raspberry Pi)
> 
> | LCD 引脚 | Raspberry Pi 引脚号 | GPIO | 描述 |
> | :--- | :--- | :--- | :--- |
> | VCC | Pin 1 | 3.3V | 电源 |
> | GND | Pin 6 | GND | 接地 |
> | SCL/CLK | Pin 23 | GPIO 11 | SPI 时钟 |
> | SDA/MOSI | Pin 19 | GPIO 10 | SPI 数据 |
> | RES/RST | Pin 22 | GPIO 25 | 复位 |
> | DC | Pin 18 | GPIO 24 | 数据/命令选择 |
> | CS | Pin 24 | GPIO 8 | 芯片选择 |
> | BL/LED | Pin 17 | 3.3V | 背光电源 |
> 
> ---
> 
> ## 已修复的技术问题
> 
> | 问题 | 原因 | 解决方案 |
> | :--- | :--- | :--- |
> | **LCD 白屏** | Pillow 10.0.0 库中移除了 `draw.textsize()` 函数。 | 替换为使用 `draw.textbbox()` 的兼容性函数。 |
> | **pip 安装失败** | Python 3.11+ 中更严格的系统包保护策略。 | 在 `pip` 命令中添加了 `--break-system-packages` 标志。 |
> | **服务执行错误** | systemd 服务无法识别 Docker 路径。 | 在服务单元文件中明确添加了 `PATH` 环境变量。 |
> | **Umbrel 1.x 兼容性** | Docker 容器名称、`bitcoin-cli` 和 `lncli` 执行方法的更改。 | 通过尝试多个容器名称并添加直接的 HTTP RPC 调用来增强了后备逻辑。 |
> 
> ---
> 
> ## 鸣谢
> 
> *   原始项目：[doidotech/TBM](https://github.com/doidotech/TBM) by DOIDO Technologies
> *   此分叉版本的创建是为了解决 [Umbrel 社区论坛](https://community.umbrel.com/t/the-bitcoin-machine-blank-lcd-since-umbrel-os-1/15720)中报告的问题。
