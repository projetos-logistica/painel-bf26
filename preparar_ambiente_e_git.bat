@echo off
title Preparar Ambiente Virtual e Git - Painel BF26
echo ==========================================================
echo  Configurando Ambiente Virtual (venv) e Dependencias
echo ==========================================================
cd /d "%~dp0"

echo 1. Criando ambiente virtual (venv)...
if not exist "venv" (
    python -m venv venv
    echo Ambiente virtual criado com sucesso!
) else (
    echo O ambiente virtual 'venv' ja existe.
)

echo.
echo 2. Instalando / Atualizando dependencias no venv...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ==========================================================
echo  Ambiente pronto!
echo.
echo  Para subir para o GitHub:
echo  1. Abra o terminal (Git Bash ou Prompt de comando) aqui nesta pasta
echo  2. Execute:
echo     git init
echo     git add .
echo     git commit -m "feat: Painel BF26 Streamlit para Soma e Reserva"
echo     git branch -M main
echo     git remote add origin https://github.com/SEU-USUARIO/painel-bf26.git
echo     git push -u origin main
echo ==========================================================
pause
