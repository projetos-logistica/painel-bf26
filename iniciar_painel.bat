@echo off
title Painel BF26 - Azzas 2154 (Soma e Reserva)
echo ==========================================================
echo  Iniciando Painel BF26 no Streamlit...
echo  Acesso direto para Grupo SOMA e Reserva
echo ==========================================================
cd /d "%~dp0"

echo Verificando instalacao do Streamlit...
python -m pip install -r requirements.txt

echo.
echo Abrindo aplicacao no navegador...
python -m streamlit run app.py --server.port 8501 --server.address 0.0.0.0

pause
