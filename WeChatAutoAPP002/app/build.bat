@echo off
echo 正在安装依赖...
pip install -r requirements.txt

echo 正在打包应用...
pyinstaller --name "微信自动化助手" --windowed --icon=resources/icons/wechat.ico app/main.py

echo 打包完成！
pause