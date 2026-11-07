import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import mongomock

app = FastAPI(title='DODO Task Manager API')

# Local In-Memory MongoDB Engine
client = mongomock.MongoClient()
db = client['task_manager_db']
tasks_col = db['tasks']

class TaskItem(BaseModel):
    id: Optional[str] = None
    title: str
    description: Optional[str] = ''
    completed: bool = False
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

@app.get('/api/tasks', response_model=List[TaskItem])
def get_tasks():
    items = list(tasks_col.find())
    res = []
    for it in items:
        t = dict(it)
        t['id'] = str(t['_id'])
        del t['_id']
        res.append(t)
    return res

@app.post('/api/tasks', response_model=TaskItem)
def create_task(item: TaskItem):
    doc = item.dict(exclude={'id'})
    result = tasks_col.insert_one(doc)
    doc['id'] = str(result.inserted_id)
    return doc

@app.put('/api/tasks/{task_id}', response_model=TaskItem)
def update_task(task_id: str, item: TaskItem):
    from bson import ObjectId
    q = {'_id': ObjectId(task_id)} if ObjectId.is_valid(task_id) else {'_id': task_id}
    update_data = {k: v for k, v in item.dict().items() if k != 'id' and v is not None}
    res = tasks_col.update_one(q, {'$set': update_data})
    found = tasks_col.find_one(q)
    if not found:
        raise HTTPException(status_code=404, detail='Task not found')
    found['id'] = str(found['_id'])
    del found['_id']
    return found

@app.delete('/api/tasks/{task_id}')
def delete_task(task_id: str):
    from bson import ObjectId
    q = {'_id': ObjectId(task_id)} if ObjectId.is_valid(task_id) else {'_id': task_id}
    res = tasks_col.delete_one(q)
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail='Task not found')
    return {'success': True, 'deleted_id': task_id}

@app.get('/health')
def health():
    return {'status': 'healthy', 'service': 'task_manager_api'}
