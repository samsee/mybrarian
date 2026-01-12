@echo off
echo Starting MyBrarian API Server...
echo.
echo API Endpoints:
echo   - Root: http://localhost:8000/
echo   - Search: http://localhost:8000/search?q=QUERY
echo   - Sources: http://localhost:8000/sources
echo   - Config: http://localhost:8000/config
echo   - Swagger UI: http://localhost:8000/docs
echo   - ReDoc: http://localhost:8000/redoc
echo.
rem --- diagnostics (helps investigate "Failed to canonicalize script path")
pushd "%~dp0backend"
uv run python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

popd
