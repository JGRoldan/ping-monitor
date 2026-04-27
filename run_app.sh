#!/bin/bash
# run_app.sh - Ejecuta la app en Linux/MacOS

VENV_DIR=".venv"

if [ ! -d "$VENV_DIR" ]; then
  echo "Entorno virtual no encontrado. Creando $VENV_DIR..."
  python3 -m venv "$VENV_DIR" || {
    echo "No se pudo crear el entorno virtual. Asegúrate de tener Python 3 instalado."
    exit 1
  }
  echo "Instalando dependencias desde requirements.txt..."
  "$VENV_DIR/bin/python3" -m pip install --upgrade pip
  "$VENV_DIR/bin/python3" -m pip install -r requirements.txt
fi

source "$VENV_DIR/bin/activate"

echo "Iniciando la app Streamlit (app.py)..."
streamlit run app.py
