import os
import re
import subprocess
import platform
import time
from datetime import datetime

IS_WINDOWS = platform.system().lower() == "windows"

lat_regex = re.compile(r"(?:time=|tiempo=|time<|tiempo<|ms=)\s*<?\s*([\d.]+)", re.IGNORECASE)
failure_keywords = [
    "request timed out",
    "timed out",
    "destination host unreachable",
    "unreachable",
    "100% packet loss",
    "host unreachable",
    "no se puede encontrar el host",
    "tiempo de espera agotado",
    "red de destino inaccesible",
    "host de destino inaccesible",
    "paquetes perdidos",
    "sin respuesta",
    "sin respuesta para el host de destino",
]

def format_duration(td):
    total_seconds = int(td.total_seconds())
    mins, secs = divmod(total_seconds, 60)
    if mins > 0:
        if secs == 0:
            return f"{mins} min"
        return f"{mins} min {secs} s"
    return f"{secs} s"

def write_log_line(filename, line):
    with open(filename, "a", encoding="utf-8") as f:
        f.write(line)
        f.flush()

def write_incident(incidents_file, msg):
    with open(incidents_file, "a", encoding="utf-8") as incf:
        incf.write(msg)

def ping_worker(target, active_targets, client_folder=None):
    if client_folder is None:
        client_folder = os.path.join("clients", "default")
    filename = os.path.join(client_folder, f"ping_{target.replace('.', '_')}.txt")
    incidents_file = os.path.join(client_folder, f"incidencias_{target.replace('.', '_')}.log")

    is_up = None
    down_start_dt = None

    write_log_line(filename, f"\n--- Nueva sesión: {datetime.now()} ---\n")

    if IS_WINDOWS:
        cmd = ["ping", "-t", target]
    else:
        cmd = ["ping", target]

    try:
        # En Windows, la salida de ping está en cp850 (o similar), no utf-8
        encoding = "cp850" if IS_WINDOWS else "utf-8"
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding=encoding, bufsize=1)
        while target in active_targets:
            line = proc.stdout.readline()
            if not line:
                if proc.poll() is not None:
                    break
                # Espera más tiempo para reducir consumo de CPU
                time.sleep(0.5)
                continue
            now_dt = datetime.now()
            now = now_dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            write_log_line(filename, f"[{now}] {line.strip()}\n")
            # Analizar para detectar UP/DOWN
            line_l = line.lower()
            m_lat = lat_regex.search(line)
            if m_lat:
                if is_up is False:
                    up_dt = now_dt
                    duration = up_dt - down_start_dt if down_start_dt else None
                    if duration:
                        write_incident(incidents_file, f"[{up_dt.strftime('%Y-%m-%d %H:%M:%S')}] UP: {target} (Duración {format_duration(duration)})\n")
                    else:
                        write_incident(incidents_file, f"[{up_dt.strftime('%Y-%m-%d %H:%M:%S')}] UP: {target}\n")
                is_up = True
            elif any(kw in line_l for kw in failure_keywords):
                if is_up is None or is_up is True:
                    down_start_dt = now_dt
                    write_incident(incidents_file, f"[{now_dt.strftime('%Y-%m-%d %H:%M:%S')}] DOWN: {target}\n")
                is_up = False
        if proc.poll() is None:
            try:
                proc.terminate()
            except Exception:
                pass
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                try:
                    proc.kill()
                except Exception:
                    pass
    except Exception as e:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        write_log_line(filename, f"[{now}] Error lanzando ping: {e}\n")
    finally:
        if "proc" in locals() and getattr(proc, "stdout", None):
            try:
                proc.stdout.close()
            except Exception:
                pass
