@echo off
echo 正在安装依赖...
pip install -r requirements.txt

echo 正在打包应用...
pyinstaller --name "何氏微信机器人助手" --windowed --icon=resources/icons/wechat.ico app/main.py

echo 打包完成！
pause