IF NOT EXIST %LOCALAPPDATA%\ankerctl\ankerctl\default.json (
    .\ankerctl.exe config import
)
.\ankerctl.exe webserver run
