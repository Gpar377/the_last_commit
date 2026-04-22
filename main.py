from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List, Optional
import os
from universal_agent import agent

app = FastAPI()

class Payload(BaseModel):
    query: str
    assets: Optional[List[str]] = []

async def process_any_request(request: Request):
    try:
        body = await request.json()
        query = body.get("query", "")
        assets = body.get("assets", [])
        ans = await agent.run(query, assets)
        return {"output": ans}
    except Exception as e:
        # Fallback for non-JSON or malformed requests
        return {"output": "Error", "detail": str(e)}

# EXPLICIT ROOT POST (Crucial for Agon)
@app.post("/")
async def root_post(request: Request):
    return await process_any_request(request)

@app.post("/{full_path:path}")
async def catch_all_post(full_path: str, request: Request):
    return await process_any_request(request)

@app.get("/{full_path:path}")
async def catch_all_get(full_path: str):
    return {"status": "alive", "path": full_path}
