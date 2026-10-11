import uuid
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel

tasks = [
    {"id": "1", "title": "学习 Python", "done": False},
    {"id": "2", "title": "学习 FastAPI", "done": True},
    {"id": "3", "title": "学习 Learn Agent", "done": False}
]

app = FastAPI(title="Agent Workspace")


class TaskCreate(BaseModel):
    title: str


class TaskUpdate(BaseModel):
    done: bool

def ver_tasks(item: dict) -> dict:
    if not item["title"]:
        return -3
    if item["title"].strip() == "":
        return -2
    return 0

def resh_tasks(items: list[dict]) -> list[dict]:
    return [task["title"].strip() for task in items]

def gen_task_id() -> int:
    return str(uuid.uuid4().hex[:8])

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/tasks")
def tasks_all():
    for task in tasks: 
        if 0 != ver_tasks(task):
            raise HTTPException(
            status_code=500,
            detail="internal erro: title verfiction failled"
    )
    return resh_tasks(tasks)

def get_pending_tasks(tasks: list[dict]) -> list[dict]:
    return [task for task in tasks if not task['done']]

@app.get("/tasks/search")
def search(q: str):
    if q is None or q.strip() == "":
        return tasks
    return [task for task in tasks if q.lower() in task['title'].lower()]

@app.get("/tasks/{id}")
def tasks_id(id:str):
    for task in tasks:
        if task["id"] == id:
            return task
    raise HTTPException(
        status_code=404,
        detail="task not found"
    )

@app.post("/tasks", status_code=201)
def task_create(data: TaskCreate):

    if not data or data.title is None or data.title.strip() == "":
        raise HTTPException(
                status_code=422,
                detail="task not found"
            )
    new_id = gen_task_id()
    new_task = {
        "id": new_id,
        "title": data.title.strip(),
        "done": False
    }
    tasks.append(new_task)
    return new_task

@app.patch("/tasks/{id}")
def tasks_patch(id:str, data: TaskUpdate):
    item = next(
        (task for task in tasks if task.get("id") == id),
        None
    )
    if item is not None:
        item["done"] = data.done
        return item
    else: 
        raise HTTPException(
            status_code=404,
            detail="task not found"
        )

@app.delete("/tasks/{id}", status_code=204)
def tasks_delete(id:str):
    item = next(
        (task for task in tasks if task.get("id") == id),
        None
    )
    if item is None:
        raise HTTPException(404, "Task not found")
    tasks.remove(item)
    return Response(status_code=204)




