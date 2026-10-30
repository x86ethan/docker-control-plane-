from fastapi import FastAPI, HTTPException
import json, yaml
from pydantic import BaseModel 
import os 

import subprocess


app = FastAPI() 

APP_DIR = "deployments/"

class Deployment(BaseModel):
    name: str
    description: str | None = None
    version: str | None = None 
    compose: dict

# Add a new deployment
@app.post("/deployments")
async def create_deployment(deployment: Deployment):

    # Check if app directory doesn't already exists
    DPL_DIR = os.path.join(APP_DIR, deployment.name)
    if not os.path.exists(DPL_DIR):
        os.mkdir(DPL_DIR)

        # Create manifest file
        with open(os.path.join(DPL_DIR, "manifest.json"), "w") as manifest:
            manifest_obj = deployment.copy()
            del manifest_obj.compose
            json.dump(manifest_obj.__dict__, manifest)

        with open(os.path.join(DPL_DIR, "compose.yml"), "w") as compose:
            yaml.safe_dump(deployment.__dict__["compose"], compose)

    else:
        raise HTTPException(409)

@app.get("/deployments")
async def list_deployments():

    res = []

    for file in os.listdir(APP_DIR):

        with open(os.path.join(APP_DIR, file, "manifest.json")) as manifest_file: 
            res.append(json.load(manifest_file))

    return res


@app.get("/deployments/{deployment}")
async def get_deployment_details(deployment: str): 

    DPL_DIR = os.path.join(APP_DIR, deployment)
    if os.path.exists(DPL_DIR):

        with open(os.path.join(DPL_DIR, "manifest.json")) as manifest:
            res = json.load(manifest)

        with open(os.path.join(DPL_DIR, "compose.yml")) as compose: 
            res["compose"] = yaml.safe_load(compose)

        # Get status
        docker = subprocess.run(["docker-compose", "-f", os.path.join(DPL_DIR, "compose.yml"), "ps", "--format", "json"], capture_output=True)
        if docker.returncode != 0:
            raise HTTPException(500, detail=docker.stderr.decode())

        if len(docker.stdout.decode()) == 0: 
            res["status"] = "down"
        else: 
            res["status"] = "up"
    
        return res
    
    raise HTTPException(404)

@app.get("/deployments/{deployment}/start")
def start_deployment(deployment: str): 

    DPL_DIR = os.path.join(APP_DIR, deployment)
    if os.path.exists(DPL_DIR):

        docker = subprocess.run(["docker-compose", "-f", os.path.join(DPL_DIR, "compose.yml"), "up", "-d"], capture_output=True)
        if docker.returncode != 0:
            raise HTTPException(500, detail = docker.stderr.decode())

        return {"status": "up"}
        

    raise HTTPException(404)

@app.get("/deployments/{deployment}/stop")
def stop_deployment(deployment: str):

    DPL_DIR = os.path.join(APP_DIR, deployment)
    if os.path.exists(DPL_DIR):

        docker = subprocess.run(["docker-compose", "-f", os.path.join(DPL_DIR, "compose.yml"), "down"], capture_output=True)
        if docker.returncode != 0:
            raise HTTPException(500, detail = docker.stderr.decode())

        return {"status": "down"}
            
    
    raise HTTPException(404)

@app.get("/deployments/{deployment}/logs")
def deployment_logs(deployment: str):

    DPL_DIR = os.path.join(APP_DIR, deployment)
    if os.path.exists(DPL_DIR):

        docker = subprocess.run(["docker-compose", "-f", os.path.join(DPL_DIR, "compose.yml"), "logs"], capture_output=True)
        if docker.returncode != 0:
            raise HTTPException(500, detail = docker.stderr.decode())

        return {"logs": [docker.stdout.decode().split('\n')]}
            
    
    raise HTTPException(404)