@echo off
echo Starting MyBrarian Frontend Dev Server...
echo.
echo Dev Server:
echo   - URL: http://localhost:5173/
echo.
rem --- diagnostics (helps investigate path issues)
pushd "%~dp0frontend"
npm run dev

popd
