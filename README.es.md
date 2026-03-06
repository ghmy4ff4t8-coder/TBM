[English](README.md) | [한국어](README.ko.md) | [Español](README.es.md) | [日本語](README.ja.md) | [简体中文](README.zh.md)

> # TBM — The Bitcoin Machine (Bifurcación Compatible con Umbrel 1.x)
> 
> > **Esta es una bifurcación comunitaria no oficial.** Esta es una versión modificada del proyecto original [doidotech/TBM](https://github.com/doidotech/TBM), actualizada para funcionar con los entornos **Umbrel OS 1.x** y **Pillow 10+**.
> > El proyecto original ya no se mantiene, y esta bifurcación resuelve el problema de la **pantalla blanca de la muerte (WSOD)** que muchos usuarios experimentan después de actualizar Umbrel.
> 
> ---
> 
> ## Guía de Instalación para Principiantes (para usuarios de Mac)
> 
> Esta guía está escrita para aquellos sin experiencia en terminal o codificación. Por favor, siga los pasos con atención.
> 
> ### Paso 1: Conéctese a su Nodo Umbrel de Forma Remota (SSH)
> 
> Primero, necesita conectarse a su nodo Umbrel (Raspberry Pi) desde su Mac. Usaremos la aplicación 'Terminal' para esto.
> 
> 1.  **Abra la Aplicación Terminal**
>     *   Presione `Comando (⌘)` + `Espacio` para abrir la búsqueda de Spotlight, escriba `Terminal` y presione Enter.
> 
> 2.  **Conéctese con el Comando SSH**
>     *   En la ventana de la terminal, escriba el siguiente comando. `umbrel.local` es la dirección predeterminada que funciona en la mayoría de las redes domésticas.
> 
>     ```bash
>     ssh umbrel@umbrel.local
>     ```
> 
> 3.  **Ingrese su Contraseña**
>     *   Se le pedirá una contraseña. Esta es la misma contraseña que usa para iniciar sesión en su panel de control de Umbrel.
>     *   **Nota:** Por seguridad, no se mostrará nada en la pantalla mientras escribe su contraseña. Simplemente escríbala y presione Enter.
> 
>     ```bash
>     umbrel@umbrel.local's password:
>     ```
> 
> 4.  **Confirme la Conexión Exitosa**
>     *   Si la conexión es exitosa, verá un mensaje de bienvenida con el logotipo de Umbrel. A partir de ahora, todos los comandos que escriba se ejecutarán en su nodo Umbrel.
> 
>     ```
>        _   _ ____  _   _ ____  _     
>       | | | | __ )| | | | __ )| |    
>       | | | |  _ \| | | |  _ \| |    
>       | |_| | |_) | |_| | |_) | |___ 
>        \___/|____/ \___/|____/|_____|
>     ```
> 
> ### Paso 2: Descargue el Código y Ejecute el Script de Instalación
> 
> Ahora es el momento de descargar el código con la solución para la pantalla blanca e instalarlo. **Copie y pegue los siguientes comandos uno por uno en la terminal y presione Enter.**
> 
> 1.  **Clone el Código desde GitHub**
>     *   Este comando descarga el código TBM modificado de mi repositorio de GitHub a su nodo Umbrel.
> 
>     ```bash
>     git clone https://github.com/ghmy4ff4t8-coder/TBM.git
>     ```
> 
> 2.  **Navegue al Directorio de Trabajo**
> 
>     ```bash
>     cd TBM/TBMLCD-v0.5/UmbrelLCDV2_0
>     ```
> 
> 3.  **Ejecute el Script de Configuración**
>     *   Este script instala automáticamente todos los programas y bibliotecas necesarios para que la pantalla LCD funcione.
> 
>     ```bash
>     chmod +x lcdSetupScript.sh
>     ./lcdSetupScript.sh
>     ```
> 
>     *   Verá muchas líneas de texto desplazándose durante la instalación. Si ve el mensaje `Setup complete!`, tuvo éxito.
> 
> ### Paso 3: Reinicie su Nodo Umbrel
> 
> Para asegurarse de que todas las configuraciones se apliquen correctamente, necesita reiniciar el sistema.
> 
> ```bash
> sudo reboot
> ```
> 
> *   Este comando desconectará su sesión SSH. Espere entre 3 y 5 minutos para que su nodo Umbrel se reinicie por completo.
> 
> ### Paso 4: Configure e Inicie el Servicio LCD
> 
> Una vez que se complete el reinicio, vuelva a conectarse a su nodo Umbrel a través de SSH como lo hizo en el Paso 1, y luego ingrese los siguientes comandos en orden.
> 
> 1.  **Navegue Nuevamente al Directorio de Trabajo**
> 
>     ```bash
>     cd ~/TBM/TBMLCD-v0.5/UmbrelLCDV2_0
>     ```
> 
> 2.  **Ejecute el Script de Configuración del Servicio**
> 
>     ```bash
>     chmod +x umbrelLCDServiceSetup.sh
>     ./umbrelLCDServiceSetup.sh
>     ```
> 
> 3.  **Seleccione Pantallas y Moneda (Muy Importante)**
>     *   Cuando ejecute el script, se le preguntará qué pantallas mostrar en la pantalla LCD y en qué moneda (USD, EUR, KRW, etc.) ver el precio de Bitcoin.
>     *   Responda cada pregunta con `yes` o `no` y presione Enter.
>     *   Finalmente, ingrese el código de su moneda deseada (por ejemplo, `USD`), y todas las configuraciones se completarán, y el servicio LCD se iniciará automáticamente.
> 
> ¡Ahora puede ver su pantalla LCD TBM funcionando correctamente!
> 
> ---
> 
> ## Solución de Problemas
> 
> **Mi pantalla LCD sigue en blanco:**
> *   Primero, verifique que el cableado sea correcto (vea el diagrama de cableado a continuación).
> *   Intente ejecutar `./lcdSetupScript.sh` y `./umbrelLCDServiceSetup.sh` nuevamente.
> 
> **Quiero verificar si el servicio se está ejecutando correctamente:**
> *   Puede verificar el estado del servicio con el siguiente comando:
>     ```bash
>     sudo systemctl status UmbrelST7735LCD
>     ```
> *   Para ver los registros en tiempo real, ingrese el siguiente comando. Esto es útil para buscar mensajes de error.
>     ```bash
>     sudo journalctl -u UmbrelST7735LCD -f
>     ```
> 
> ---
> 
> ## Diagrama de Cableado (ST7735 1.8" LCD → Raspberry Pi)
> 
> | Pin LCD | Número de Pin Raspberry Pi | GPIO | Descripción |
> | :--- | :--- | :--- | :--- |
> | VCC | Pin 1 | 3.3V | Alimentación |
> | GND | Pin 6 | GND | Tierra |
> | SCL/CLK | Pin 23 | GPIO 11 | Reloj SPI |
> | SDA/MOSI | Pin 19 | GPIO 10 | Datos SPI |
> | RES/RST | Pin 22 | GPIO 25 | Reinicio |
> | DC | Pin 18 | GPIO 24 | Selección de Datos/Comandos |
> | CS | Pin 24 | GPIO 8 | Selección de Chip |
> | BL/LED | Pin 17 | 3.3V | Alimentación de Retroiluminación |
> 
> ---
> 
> ## Problemas Técnicos Solucionados
> 
> | Problema | Causa | Solución |
> | :--- | :--- | :--- |
> | **Pantalla LCD en Blanco** | La función `draw.textsize()` fue eliminada en Pillow 10.0.0. | Reemplazada con una función de compatibilidad que usa `draw.textbbox()`. |
> | **Fallo en la Instalación de pip** | Política de protección de paquetes del sistema más estricta en Python 3.11+. | Se agregó la bandera `--break-system-packages` al comando `pip`. |
> | **Error de Ejecución del Servicio** | El servicio systemd no reconoce la ruta de Docker. | Se agregó explícitamente la variable de entorno `PATH` al archivo de unidad del servicio. |
> | **Compatibilidad con Umbrel 1.x** | Cambios en los nombres de los contenedores de Docker, métodos de ejecución de `bitcoin-cli` y `lncli`. | Lógica de respaldo mejorada al probar múltiples nombres de contenedores y agregar llamadas RPC HTTP directas. |
> 
> ---
> 
> ## Créditos
> 
> *   Proyecto Original: [doidotech/TBM](https://github.com/doidotech/TBM) por DOIDO Technologies
> *   Esta bifurcación fue creada para abordar los problemas reportados en el [Foro de la Comunidad de Umbrel](https://community.umbrel.com/t/the-bitcoin-machine-blank-lcd-since-umbrel-os-1/15720).
