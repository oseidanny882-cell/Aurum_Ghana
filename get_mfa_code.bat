@echo off
REM Prints the current AUTUM LUXE admin MFA code (TOTP, 30s validity window).
python -c "import pyotp; print('Your MFA code:', pyotp.TOTP('5DQELXW2SNLFMSXLGLMOXJHZRQDRGZDB').now())"
pause
