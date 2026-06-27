from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime
import subprocess
import sys

router = APIRouter()

job_status = {
    "refresh": {"status": "idle", "last_run": None, "message": None},
    "retrain": {"status": "idle", "last_run": None, "message": None},
}

def run_refresh():
    job_status["refresh"]["status"] = "running"
    try:
        subprocess.run(
            [sys.executable, "app/ml/features.py"],
            check=True, capture_output=True
        )
        job_status["refresh"]["status"] = "success"
        job_status["refresh"]["message"] = "Features refreshed successfully"
    except subprocess.CalledProcessError as e:
        job_status["refresh"]["status"] = "error"
        job_status["refresh"]["message"] = str(e)
    finally:
        job_status["refresh"]["last_run"] = datetime.utcnow().isoformat() + "Z"

def run_retrain():
    job_status["retrain"]["status"] = "running"
    try:
        subprocess.run(
            [sys.executable, "app/ml/train.py"],
            check=True, capture_output=True
        )
        job_status["retrain"]["status"] = "success"
        job_status["retrain"]["message"] = "Model retrained successfully"
    except subprocess.CalledProcessError as e:
        job_status["retrain"]["status"] = "error"
        job_status["retrain"]["message"] = str(e)
    finally:
        job_status["retrain"]["last_run"] = datetime.utcnow().isoformat()

@router.post("/refresh")
def refresh_data(background_tasks: BackgroundTasks):
    if job_status["refresh"]["status"] == "running":
        return {"message": "Refresh already in progress"}
    background_tasks.add_task(run_refresh)
    return {"message": "Data refresh started"}

@router.post("/retrain")
def retrain_model(background_tasks: BackgroundTasks):
    if job_status["retrain"]["status"] == "running":
        return {"message": "Retrain already in progress"}
    background_tasks.add_task(run_retrain)
    return {"message": "Model retrain started"}

@router.get("/status")
def get_status():
    return job_status
