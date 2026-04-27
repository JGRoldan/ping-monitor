import streamlit as st
import pandas as pd
import altair as alt


import threading
import time
import os
import sys
import re
from datetime import datetime
from ping_utils import ping_worker
from log_utils import get_clients_root, list_available_clients, find_client_folder_by_uploaded_file, parse_ips_from_text


st.set_page_config(page_title="Ping Monitor Pro", layout="wide")

# Inicializar session_state para evitar errores
if "active_targets" not in st.session_state:
    st.session_state.active_targets = set()
if "target_map" not in st.session_state:
    st.session_state.target_map = {}


# --- INTERFAZ DE USUARIO (FLUJO PRINCIPAL) ---
st.title("🌐 Monitor de Red en Tiempo Real")
st.sidebar.subheader("Cliente / Batch")
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

clients_root = get_clients_root(BASE_DIR)
available_clients = list_available_clients(clients_root)

uploaded_file = st.sidebar.file_uploader("Seleccionar archivo de clientes (.txt)", type=["txt"])

new_ip = st.sidebar.text_input("Ingresa IP o Dominio (ej: 8.8.8.8) — (logs se guardan en la raíz por IP manual):")
if st.sidebar.button("Agregar y Monitorear"):
    if new_ip and new_ip not in st.session_state.active_targets:
        client_folder = os.getcwd()
        st.session_state.active_targets.add(new_ip)
        st.session_state.target_map[new_ip] = client_folder
        t = threading.Thread(target=ping_worker, args=(new_ip, st.session_state.active_targets, client_folder), daemon=True)
        t.start()
        st.sidebar.success(f"Monitoreando {new_ip} (logs en {client_folder})")

if uploaded_file is not None:
    if st.sidebar.button("Agregar desde archivo"):
        try:
            content = uploaded_file.getvalue().decode("utf-8")
        except Exception:
            content = uploaded_file.getvalue().decode("latin-1")
        ips = parse_ips_from_text(content)
        uploaded_bytes = uploaded_file.getvalue()
        client_folder, status, matches = find_client_folder_by_uploaded_file(clients_root, uploaded_file.name, uploaded_bytes)
        if status == "not_found":
            st.sidebar.error(
                f"No se encontró '{uploaded_file.name}' dentro de ninguna subcarpeta de '{clients_root}'.\n"
                "Coloca el archivo en la carpeta del cliente en el servidor antes de subir."
            )
        elif status == "multiple_content":
            st.sidebar.error(
                f"El archivo '{uploaded_file.name}' existe en múltiples clientes {matches} y el contenido coincide en más de uno.\n"
                "Renombra o elimina duplicados para que la detección sea unívoca."
            )
        elif status == "no_content_match":
            st.sidebar.error(
                f"El archivo '{uploaded_file.name}' existe en varios clientes {matches},\n"
                "pero su contenido no coincide exactamente con ninguno. Coloca el archivo en la carpeta adecuada en el servidor o renómbralo."
            )
        elif client_folder:
            with open(os.path.join(client_folder, uploaded_file.name), "wb") as wf:
                wf.write(uploaded_file.getvalue())
            added = 0
            for ip in ips:
                if ip and ip not in st.session_state.active_targets:
                    st.session_state.active_targets.add(ip)
                    st.session_state.target_map[ip] = client_folder
                    t = threading.Thread(target=ping_worker, args=(ip, st.session_state.active_targets, client_folder), daemon=True)
                    t.start()
                    added += 1
            st.sidebar.success(f"Agregadas {added} IPs en cliente '{os.path.basename(client_folder)}'")
if st.sidebar.button("Limpiar todo"):
    st.session_state.active_targets.clear()
    st.session_state.target_map.clear()
    st.rerun()


# --- VISUALIZACIÓN ---
if not st.session_state.active_targets:
    st.info("Ingresa una IP en la barra lateral para comenzar.")
else:
    targets = sorted(st.session_state.active_targets)
    # Mostrar 2 gráficos por fila
    for row_start in range(0, len(targets), 2):
        row_targets = targets[row_start:row_start + 2]
        cols = st.columns(len(row_targets))

        for col, target in zip(cols, row_targets):
            with col:
                st.subheader(f"📍 {target}")
                client_folder = st.session_state.target_map.get(target, os.path.join("clients", "default"))
                filename = os.path.join(client_folder, f"ping_{target.replace('.', '_')}.txt")

                if os.path.exists(filename):
                    with open(filename, "r", encoding="utf-8") as f:
                        lines = f.readlines()[-200:]

                    ts_pattern = re.compile(r"^\[(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d{3})?)\]\s*(?P<rest>.*)$")
                    lat_pattern = re.compile(r"(?:time=|tiempo=|time<|tiempo<|ms=)\s*<?\s*([\d.]+)", re.IGNORECASE)

                    all_count = 0
                    times = []
                    latencies = []
                    for line in lines:
                        m_ts = ts_pattern.match(line)
                        if not m_ts:
                            continue
                        all_count += 1
                        ts_str = m_ts.group("ts")
                        rest = m_ts.group("rest")

                        m_lat = lat_pattern.search(rest)
                        if m_lat:
                            try:
                                lat = float(m_lat.group(1))
                            except ValueError:
                                continue
                            times.append(ts_str)
                            latencies.append(lat)

                    if all_count > 0:
                        avg = sum(latencies) / len(latencies) if latencies else None
                        mx = max(latencies) if latencies else None
                        mn = min(latencies) if latencies else None

                        # Mostrar métricas: Promedio, Máximo, Mínimo (sin packet loss)
                        m1, m2, m3 = st.columns([1, 1, 1])
                        with m1:
                            st.metric("Promedio", f"{avg:.0f} ms" if avg is not None else "N/A")
                        with m2:
                            st.metric("Máximo", f"{mx:.0f} ms" if mx is not None else "N/A")
                        with m3:
                            st.metric("Mínimo", f"{mn:.0f} ms" if mn is not None else "N/A")

                        if latencies:
                            idx = pd.to_datetime(times)
                            df = pd.DataFrame({"Latencia (ms)": latencies}, index=idx)
                            df2 = df.reset_index().rename(columns={"index": "time"})


                            # Siempre formatear time_str sin milisegundos
                            df2["time_str"] = df2["time"].dt.strftime("%Y-%m-%d %H:%M:%S")

                            chart = (
                                alt.Chart(df2)
                                .mark_line(point=True)
                                .encode(
                                    x=alt.X(
                                        "time:T",
                                        axis=alt.Axis(
                                            format="%H:%M:%S",
                                            title="Hora",
                                        ),
                                    ),
                                    y=alt.Y("Latencia (ms):Q", title="Latencia (ms)"),
                                    tooltip=[
                                        alt.Tooltip("time_str:N", title="Fecha y hora"),
                                        alt.Tooltip("Latencia (ms):Q", title="Latencia (ms)")
                                    ],
                                )
                                .interactive()
                            ).properties(height=220)

                            st.altair_chart(chart, width="stretch")
                            st.caption(f"Archivo: {filename}")
                        else:
                            st.warning("No successful pings in the sampled period.")

    # Auto-refresco
    time.sleep(2)
    st.rerun()
