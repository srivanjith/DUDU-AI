import pytest
from fastapi.testclient import TestClient
from backend_app import app

client = TestClient(app)

def test_health():
    res = client.get('/health')
    assert res.status_code == 200
    assert res.json()['status'] == 'healthy'

def test_crud_flow():
    # 1. Create
    create_res = client.post('/api/tasks', json={'title': 'Autonomous Task 1'})
    assert create_res.status_code == 200
    created = create_res.json()
    task_id = created['id']
    assert created['title'] == 'Autonomous Task 1'
    assert created['completed'] is False

    # 2. List
    list_res = client.get('/api/tasks')
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 3. Update
    update_res = client.put(f'/api/tasks/{task_id}', json={'title': 'Updated Title', 'completed': True})
    assert update_res.status_code == 200
    assert update_res.json()['completed'] is True
    assert update_res.json()['title'] == 'Updated Title'

    # 4. Delete
    del_res = client.delete(f'/api/tasks/{task_id}')
    assert del_res.status_code == 200
    assert del_res.json()['success'] is True
