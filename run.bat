@echo off
title Glosario de Inteligencia Artificial
echo ===================================================
echo INICIANDO SERVIDOR DEL GLOSARIO DE IA
echo ===================================================
echo Verificando dependencias e iniciando aplicacion en http://localhost:5000 ...
python -m pip install -r requirements.txt
python app.py
pause
