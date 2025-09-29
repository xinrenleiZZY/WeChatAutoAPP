@echo off
echo 正在安装依赖...
pip install -r requirements.txt

echo 正在清理旧文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del /q *.spec
if exist installer rmdir /s /q installer

echo 正在打包应用...
pyinstaller --name "何氏微信机器人助手" ^
--windowed ^
--icon=resources/icons/wechat.ico ^
--add-data "wechat_templates;wechat_templates" ^
--add-data "friends.txt;." ^
--add-data "resources;resources" ^
--add-data "wechat_config.json;." ^
app/main.py

:: 检查打包是否成功
if %errorlevel% equ 0 (
    echo 正在生成安装包...
    iscc installer_script.iss
    
    if %errorlevel% equ 0 (
        echo 打包完成！安装包已生成在 installer 目录
    ) else (
        echo 安装包生成失败，请检查 Inno Setup 配置
    )
) else (
    echo 应用打包失败，请查看错误信息
)

pause