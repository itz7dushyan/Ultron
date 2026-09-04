Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\ULTRON"
WshShell.Run "pythonw.exe main.py --voice", 1, False
Set WshShell = Nothing
