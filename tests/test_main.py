from fastapi.testclient import TestClient
from app.main import app, tasks

client = TestClient(app)


def setup_function():
    tasks.clear()
    # pass


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_task_list():
    resp = client.get(
        "/tasks"
    )
    assert resp.status_code == 200
    assert resp.json() == []

    created = client.post(
        "/tasks",
        json={"title": "Learn Agent"}
    )
    assert created.status_code == 201
    resp = client.get(
        "/tasks"
    )
    assert resp.status_code == 200
    assert resp.json() == ["Learn Agent"]
    print(resp.json())

def test_create_task():
    response = client.post(
        "/tasks",
        json={"title": "Learn Agent"}
    )
    assert response.json()
    data = response.json()
    print(data)
    assert data["title"] == "Learn Agent"
    assert data["done"] is False
    assert isinstance(data["id"], str)


def test_update_task():
    created = client.post(
        "/tasks",
        json={"title": "Learn Python"}
    ).json()

    response = client.patch(
        f"/tasks/{created['id']}",
        json={"done": True}
    )
    print("status_code", response.status_code)
    print("response json = ", response.json()) # 打印422的详细报错！
    assert response.status_code == 200
    assert response.json()["done"] is True


def test_missing_task():
    response = client.get("/tasks/999999")
    assert response.status_code == 404


def test_empty_title():
    response = client.post(
        "/tasks",
        json={"title": "   "}
    )
    print(response.json())
    assert response.status_code == 422

def test_del_get_search():
    created = client.post(
        "/tasks",
        json={"title": "Learn Python"}
    ).json()

    delete = client.delete(
        f"/tasks/{created['id']}"
    )
    assert delete.status_code == 204
    resp = client.get(
        f'/tasks/{created['id']}'
    )
    assert resp.status_code == 404
    print(resp.json())

def test_search():
    created = client.post(
        "/tasks",
        json={"title": "Learn Python"}
    ).json()
    resp_empty = client.get(
        "tasks/search",
        params={"q": "asdasdasdaS"}
    )
    assert resp_empty.status_code == 200
    data = resp_empty.json()
    assert len(data) == 0

    response = client.get(
        "tasks/search",
        params={"q": "Learn"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    print(response.json())