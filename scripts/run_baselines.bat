@echo off
setlocal

echo =======================================================
echo    Invotex Baseline Generator (Meta Hackathon Round 2)
echo =======================================================
echo.
echo Running default open-weights model against all 3 Domains...
echo This will generate the "Before Training" logs.
echo.

REM ---- SET YOUR HF TOKEN HERE ----
set /p HF_TOKEN="Enter your HuggingFace Token (hf_...): "
set API_BASE_URL=https://router.huggingface.co/v1
set MODEL_NAME=Qwen/Qwen2.5-72B-Instruct

if not exist "baseline_logs" mkdir "baseline_logs"

set DOMAINS=email_triage traffic_control customer_support

for %%D in (%DOMAINS%) do (
    echo -------------------------------------------------------
    echo    Running Domain: %%D
    echo -------------------------------------------------------
    set DOMAIN=%%D
    python inference.py > baseline_logs\baseline_%%D.log 2>&1
    echo Finished %%D. Check baseline_logs\baseline_%%D.log
    echo.
)

echo =======================================================
echo All baselines generated in baseline_logs\ folder!
echo Present the customer_support log to show Schema Drift
echo causes standard models to FAIL the hard task.
echo =======================================================
pause
