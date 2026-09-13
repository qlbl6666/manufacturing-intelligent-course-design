@echo off
title 工业缺陷检测系统 - C/S客户端
cd /d "%~dp0"
set PYTHON="C:\Users\whk66\AppData\Local\Doubao\User Data\sandbox_runtime\bases\c98c5042338ed152c6f10ecd8591889f\python\python.exe"
echo 正在启动C/S桌面客户端...
echo 请确保后端服务已启动 (http://localhost:5000)
echo.
%PYTHON% desktop_client.py
pause
