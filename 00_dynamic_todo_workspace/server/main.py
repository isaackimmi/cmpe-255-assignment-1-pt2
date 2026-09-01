from copy import deepcopy
from typing import Literal
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="Fieldnote Project 00 API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])

class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    priority: Literal["high", "medium", "low"] = "medium"
class TaskUpdate(BaseModel):
    done: bool

SEED = {"project":{"name":"Retail demand forecast","brief":"Plan the next 12 weeks of demand forecasting","goal":"Reduce stock-outs while keeping recommendations explainable to the merchandising team."},"readiness":{"status":"PLANNED","dataset":"retail_orders.parquet","score":0,"note":"No dataset is connected; this is a readiness plan, not a measured profile.","boundary":"planning-only · no model artifact"},"tasks":[{"id":1,"title":"Capture business constraints","area":"Business understanding","priority":"high","done":True},{"id":2,"title":"Document the feature plan","area":"Data preparation","priority":"medium","done":True},{"id":3,"title":"Validate promotion and holiday flags","area":"Data preparation","priority":"high","done":False},{"id":4,"title":"Compare seasonal naive baseline","area":"Modeling","priority":"medium","done":False},{"id":5,"title":"Write stakeholder readout","area":"Evaluation","priority":"low","done":False}],"workflow":{"current":"Modeling phase","stages":[{"name":"Business understanding","status":"complete","evidence":"Goal and constraints captured","detail":"Define the stock-out objective, forecast horizon, and explainability needs."},{"name":"Data understanding","status":"complete","evidence":"Schema and quality review planned","detail":"Profile dates, missingness, duplicate orders, and coverage before fitting anything."},{"name":"Data preparation","status":"complete","evidence":"Feature plan documented","detail":"Specify calendar, promotion, and lag features without leaking future demand."},{"name":"Modeling","status":"planned","evidence":"Baseline comparison planned","detail":"Start with a seasonal-naive baseline before evaluating a learned model."},{"name":"Evaluation","status":"planned","evidence":"Waiting on model artifacts","detail":"Use a chronological holdout and report error by store, horizon, and season."},{"name":"Deployment","status":"planned","evidence":"Planned after sign-off","detail":"Define monitoring and rollback criteria only after evidence exists."}]},"activity":[{"message":"Workspace initialized","detail":"Planning boundary is explicit; no model run was claimed."}]}
state = deepcopy(SEED)
@app.get("/api/health")
def health(): return {"status":"ok","service":"fieldnote-api"}
@app.get("/api/workspace")
def workspace(): return deepcopy(state)
@app.get("/api/readiness")
def readiness(): return deepcopy(state["readiness"])
@app.post("/api/tasks")
def create_task(task: TaskCreate):
    title = task.title.strip()
    if not title: raise HTTPException(422, "Task title cannot be blank")
    next_id = max((item["id"] for item in state["tasks"]), default=0) + 1
    state["tasks"].insert(0, {"id":next_id,"title":title,"area":"Workspace","priority":task.priority,"done":False})
    return deepcopy(state["tasks"])
@app.patch("/api/tasks/{task_id}")
def update_task(task_id: int, update: TaskUpdate):
    for task in state["tasks"]:
        if task["id"] == task_id: task["done"] = update.done; return deepcopy(state["tasks"])
    raise HTTPException(404, "Task not found")
@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int):
    before=len(state["tasks"]); state["tasks"]=[task for task in state["tasks"] if task["id"] != task_id]
    if len(state["tasks"]) == before: raise HTTPException(404, "Task not found")
    return deepcopy(state["tasks"])
@app.post("/api/agent-check")
def agent_check():
    state["activity"].insert(0,{"message":"Demo check completed","detail":"Queue reviewed. Forecasting, leakage, and model evaluation were not run."})
    return {"status":"demo-only"}
