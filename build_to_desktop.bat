@echo off
chcp 65001 > nul
echo جاري تجهيز التطبيق ليعمل من سطح المكتب...
echo ---------------------------------------------------
pip install pyinstaller

echo.
echo جاري تحويل كود بايثون الى تطبيق تنفيذي (EXE)...
pyinstaller --noconfirm --onefile --windowed --icon="icon.ico" --add-data="icon.ico;." "race_timer_app.py"

echo.
echo جاري نقل التطبيق إلى سطح المكتب...
move /Y "dist\race_timer_app.exe" "%USERPROFILE%\Desktop\Nabtakir_Race_Timer.exe"

echo.
echo تم الانتهاء بنجاح! ستجد التطبيق الآن على سطح المكتب باسم Nabtakir_Race_Timer
pause