@echo off
chcp 65001
:: 解决编码问题：确保此文件以ANSI编码保存（用记事本另存为ANSI）

echo 1/4：正在安装依赖...
pip install -r requirements.txt

echo 2/4：正在清理旧文件...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "*.spec" del /q "*.spec"
if exist "installer" rmdir /s /q "installer"

echo 3/4：正在打包EXE程序...
:: 关键：所有参数写在一行，避免使用续行符^
pyinstaller --name "何氏微信机器人助手" --windowed --icon=resources/icons/wechat.ico --add-data "wechat_templates;wechat_templates" --add-data "friends.txt;." --add-data "resources;resources" --add-data "wechat_config.json;." app/main.py

:: 检查EXE打包是否成功
if %errorlevel% neq 0 (
  echo ！EXE打包失败，请查看上方错误信息
  pause
  exit /b 1
)

echo 4/4：正在生成安装包...
:: 替换为你的iscc.exe实际路径（必须用英文引号包裹）
"C:\Program Files (x86)\Inno Setup 6\iscc.exe" installer_script.iss

:: 检查安装包生成结果
if %errorlevel% equ 0 (
  echo ✅ 全部完成！
  echo - 可执行程序：dist\何氏微信机器人助手
  echo - 安装包：installer\何氏微信机器人助手安装包.exe
) else (
  echo ❌ 安装包生成失败！请检查Inno Setup路径是否正确
)

pause