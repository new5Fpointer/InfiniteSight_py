@echo off
python -m nuitka main.py ^
  --standalone --windows-console-mode=disable ^
  --include-package-data=pyvips ^
  --include-data-dir=vips=vips ^
  --include-data-dir=i18n=i18n ^
  --plugin-enable=pyside6 ^
  --include-qt-plugins=sensible,styles,platforms,imageformats ^
  --nofollow-import-to=pyside6.QtNetwork ^
  --nofollow-import-to=pyside6.QtMultimedia ^
  --nofollow-import-to=pyside6.QtQml ^
  --nofollow-import-to=pyside6.QtQuick ^
  --nofollow-import-to=pyside6.QtSql ^
  --nofollow-import-to=pyside6.QtTest ^
  --nofollow-import-to=pyside6.QtXml ^
  --output-dir=dist
pause