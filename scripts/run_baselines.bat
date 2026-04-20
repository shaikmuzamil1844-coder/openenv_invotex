@echo off
setlocal

echo =======================================================
echo    Invotex Baseline Generator (Meta Hackathon Round 2)
echo =======================================================
echo.
echo Running default open-weights model against all 3 Domains...
echo This will generate the "Before Training" logs to satisfy the 20%% Improvement criteria.
echo.

set DOMAINS=email_triage traffic_control customer_support

for %%D in (%DOMAINS%) do (
    echo -------------------------------------------------------
    echo    Running Domain: %%D
    echo -------------------------------------------------------
    
    set DOMAIN=%%D
    REM Setting the default model provided by hackathon (Qwen) as our pre-finetuned baseline
    set MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
    set API_BASE_URL=https://router.huggingface.co/v1
    
    REM Capture the stdout logs directly to a baselines folder
    if not exist "baseline_logs" mkdir "baseline_logs"
    
    python inference.py > baseline_logs\baseline_%%D.log 2>&1
    
    echo Finished %%D. Saved to baseline_logs\baseline_%%D.log
    echo.
)

echo =======================================================
echo All baselines generated!
echo Present the failed task scores (specifically customer_support)
echo to prove that standard models fail the "Schema Drift" task.
echo =======================================================
