from fastapi import FastAPI, HTTPException
import json, yaml
from pydantic import BaseModel 
import os 


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
        