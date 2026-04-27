# Ping Monitor Pro

Monitor de latencia y disponibilidad por IP con interfaz Streamlit.

## Índice

1. [Descripción](#descripción)
2. [Objetivo](#objetivo)
3. [Características principales](#características-principales)
4. [Requisitos](#requisitos)
5. [Instalación](#instalación)
6. [Ejecución rápida (un solo click)](#ejecución-rápida-un-solo-click)
7. [Ejecución manual](#ejecución-manual)

## Descripción

Ping Monitor Pro es una aplicación ligera en Streamlit para ejecutar pings continuos a uno o varios destinos (IPs o dominios), registrar la salida, detectar incidentes (DOWN/UP) y mostrar dashboards con métricas y gráficos de latencia en tiempo real.

El proyecto fue diseñado para usarse en un entorno Windows o Linux y organiza logs por cliente en carpetas bajo `clients/`.

## Objetivo

- Monitorear de forma continua varios targets (IPs/domains).
- Registrar logs por target y detectar automáticamente caídas y recuperaciones.
- Visualizar métricas básicas (promedio, máximo, mínimo) y series temporales interactivas con Altair.
- Permitir gestión por cliente (carpetas en `clients/`) y subir listas de targets por cliente.

## Características principales

- Worker por target (hilo) ejecutando `ping` y escribiendo en `ping_<IP>.txt`.
- Registro de incidentes en `incidencias_<IP>.log` con marcas `DOWN`/`UP` y duración.
- Dashboard con gráficos Altair (eje X con timestamp sin milisegundos) y `st.metric` para métricas por target.
- Soporte simple por cliente: archivos de clientes y logs agrupados en `clients/<cliente>/`.
- Protección contra acceso directo a `st.session_state` desde hilos — los hilos reciben una referencia segura (`active_targets` set).

## Requisitos

- Python 3.10+ (3.12 recomendado)
- Dependencias listadas en `requirements.txt` (ej. `streamlit`, `pandas`, `altair`)

## Instalación

Se recomienda usar un entorno virtual para aislar las dependencias.

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Linux/MacOS (bash)

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```

## Ejecución rápida (un solo click)

Puedes iniciar la aplicación y el entorno virtual automáticamente usando los siguientes scripts:

- **Windows:** Haz doble click en `run_app.bat` o ejecútalo desde PowerShell:
    ```powershell
    ./run_app.bat
    ```
- **Linux/MacOS:** Da permisos y ejecuta:
    ```bash
    chmod +x run_app.sh
    ./run_app.sh
    ```

Esto creará el entorno virtual si no existe, instalará dependencias y lanzará la app.

## Ejecución manual

Si prefieres ejecutar manualmente:

1. Activa el entorno virtual:
    - **Windows:**
        ```powershell
        .\.venv\Scripts\Activate.ps1
        ```
    - **Linux/MacOS:**
        ```bash
        source .venv/bin/activate
        ```
2. Instala dependencias (si no lo hiciste antes):
    ```bash
    pip install -r requirements.txt
    ```
3. Ejecuta la app:
    ```bash
    streamlit run app.py
    ```

En Windows (cmd):

```cmd
python -m venv .venv
.\.venv\Scripts\activate.bat
pip install -r requirements.txt
```

En macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Ejecutar la app

Con el entorno activo:

```bash
streamlit run app.py
```

La interfaz web se abrirá en `http://localhost:8501` por defecto.

## Estructura de la carpeta (resumen)

- `app.py` — aplicación Streamlit principal.
- `requirements.txt` — dependencias.
- `clients/` — directorio donde deben existir las carpetas de cada cliente. Ej:
    - `clients/cliente_1/` — carpeta del cliente X
    - `clients/cliente_2/` — carpeta del cliente Y
- `ping_<ip>.txt` y `incidencias_<ip>.log` — archivos de log generados por target (ubicación depende de si se asoció a cliente o es IP manual).

> Nota: las carpetas de cliente deben existir en el servidor/FS antes de usar el uploader de la UI. La app detecta la carpeta cliente buscando el nombre del archivo dentro de `clients/*`.

## Uso (flujo)

1. Manual:
    - Introduce una IP o dominio en la barra lateral en "Ingresa IP o Dominio" y pulsa "Agregar y Monitorear".
    - Las IPs añadidas manualmente NO se asocian a clientes y sus logs se guardan en la raíz del proyecto (directorio de trabajo actual).

2. Por cliente (archivo):
    - El uploader permite subir un archivo `.txt` con una lista de IPs (separadas por comas o nuevas líneas).
    - Reglas de detección del cliente:
        - La app busca en cada subcarpeta de `clients/` si ya existe un archivo con el mismo nombre.
        - Si existe exactamente una coincidencia por nombre -> se asume esa carpeta como el cliente.
        - Si el archivo existe con el mismo nombre en varias carpetas, la app compara el contenido (bytes):
            - Si exactamente una carpeta tiene contenido idéntico al subido -> se usa esa carpeta.
            - Si varias carpetas tienen contenido idéntico o ninguna coincide exactamente -> la app mostrará un error y pedirá renombrar / mover el archivo para que la detección sea unívoca.
        - Si el archivo NO existe en ninguna subcarpeta -> la app muestra un error solicitando colocar el archivo dentro de la carpeta del cliente en el servidor antes de subir.

    - Una vez detectada la carpeta cliente, el archivo se copia/sobrescribe en `clients/<cliente>/` y se lanzan los workers para cada IP encontrada.

## Formato del archivo de cliente

- Texto plano `.txt`.
- IPs o dominios separados por comas, saltos de línea o retornos de carro.
- Ejemplo de contenido:

```
8.8.8.8, 8.8.4.4
2001:4860:4860::8888
example.com
```

## Logs y archivos generados

- `clients/<cliente>/ping_<ip_con_puntos_reemplazados_por_guiones>.txt` — salida de ping con timestamps.
    - Cada línea se almacena con prefijo: `[YYYY-MM-DD HH:MM:SS.sss] <línea de ping>`.
- `clients/<cliente>/incidencias_<ip_con_puntos_reemplazados_por_guiones>.log` — entradas `DOWN`/`UP` con timestamps y duración de la caída.
- Para IPs añadidas manualmente (no asociadas a cliente), los archivos `ping_...` y `incidencias_...` se escriben en la raíz del proyecto (cwd).

Ejemplo de ruta:

```
clients/cliente_1/ping_8_8_8_8.txt
clients/cliente_1/incidencias_8_8_8_8.log
```

## Cómo detener monitoreos

- Botón `Limpiar todo` en la barra lateral: borra `active_targets` y `target_map`, lo que hace que los workers finalicen y el app se recargue.
- No hay (por ahora) botón para detener solo una IP desde la UI; se puede implementar como mejora.

## Detalles técnicos / notas para desarrolladores

- `ping_worker(target, active_targets, client_folder=None)`:
    - No debe acceder a `st.session_state` directamente desde el hilo.
    - Recibe `active_targets` (un `set`) por referencia y comprueba `while target in active_targets:` para permanecer activo.
    - `client_folder` controla dónde se escriben los logs; si `None`, se usa `clients/default`.
- Evitar reasignar contenedores dentro de `st.session_state` que los hilos usan: por ejemplo, no hacer `st.session_state['active_targets'] = set()` mientras hay hilos leyendo la antigua referencia; en su lugar usar `clear()` para vaciar.
- Diferencias por SO:
    - Windows: el comando `ping` se ejecuta con `-t` para modo continuo.
    - Unix/macOS: se ejecuta `ping <host>` y depende del comportamiento del binario local.

## Problemas comunes / Troubleshooting

- Permisos al escribir archivos: asegúrate de que el usuario que corre Streamlit tenga permisos de escritura en las carpetas `clients/` y en la raíz.
- Si los gráficos no aparecen: comprueba que `altair` y `pandas` están instalados y que `streamlit` no está lanzando errores en la consola.
- Si los pings no se ejecutan correctamente en un host: prueba ejecutar `ping <ip>` manualmente en una consola para validar el comando del sistema.
- Si ves errores relacionados con "missing ScriptRunContext" o problemas por acceder a `st.*` desde hilos: revisa que ningún worker llame a `st.*` directamente y que pases referencias seguras a los hilos.

## Personalización rápida

- Cambiar la carpeta raíz de clientes: modificar la variable `clients_root = "clients"` en `app.py`.
- Cambiar comportamiento de IP manual a guardado en subcarpeta `ungrouped/`:
    - Reemplazar `client_folder = os.getcwd()` por `client_folder = os.path.join(os.getcwd(), "ungrouped")` y crear la carpeta si se desea.
- Añadir botón para detener IP individual: implementar UI por target y eliminar del `active_targets` correspondiente.

## Desarrollo y pruebas

- Para ejecutar comprobaciones de sintaxis rápida:

```bash
python -m py_compile app.py
```

## Ejecutar con doble clic (Windows)

Se han añadido dos lanzadores en la raíz del proyecto:

- `run_app.bat` — archivo para ejecutar con doble clic en Windows (abre una ventana de CMD).
- `run_app.ps1` — script PowerShell (útil si prefieres PowerShell; la política de ejecución del sistema puede requerir ajustar `ExecutionPolicy`).

Cómo funcionan:

- Si no existe el entorno virtual `.venv`, el lanzador lo crea e instala las dependencias desde `requirements.txt` (primera ejecución puede tardar).
- Luego ejecuta `streamlit run app.py` usando el Python del entorno virtual.
- La ventana queda abierta al finalizar para poder leer mensajes y errores.

Uso rápido:

1. Doble clic en `run_app.bat`.
2. Espera a que (si es la primera vez) se cree `.venv` e instalen paquetes.
3. El navegador se abrirá en `http://localhost:8501` (por defecto) con la interfaz Streamlit.

Notas:

- Si prefieres PowerShell, puedes ejecutar `run_app.ps1` o abrir una PowerShell y ejecutarlo. Si tu sistema bloquea la ejecución de scripts, ajusta la política temporalmente con `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` en PowerShell.
- Si deseas un `.exe` empaquetado, puedo generar un lanzador con `pyinstaller`, pero el ejecutable resultante puede ser grande y requerir pruebas adicionales.

- Para formateo / linting (opcional): agregar `black`, `flake8` al `requirements-dev` y ejecutar según la política del proyecto.
