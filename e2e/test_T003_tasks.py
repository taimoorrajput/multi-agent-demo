import json
from uuid import uuid4


def test_T003_create_patch_and_fetch_task(swagger):
    # Set up a project (and its owner) through the API, same as a real client would.
    user = swagger.call(
        "POST", "/users",
        body=json.dumps({"email": f"owner-{uuid4().hex}@example.com", "name": "Owner"}),
        expect_status=201,
    )
    owner_id = json.loads(user)["id"]

    swagger.page.reload()
    project = swagger.call(
        "POST", "/projects",
        body=json.dumps({"name": "Demo Project", "description": "", "owner_id": owner_id}),
        expect_status=201,
    )
    project_id = json.loads(project)["id"]

    swagger.page.reload()
    created = swagger.call(
        "POST", "/tasks",
        body=json.dumps({"title": "Record the demo", "project_id": project_id}),
        expect_status=201,
    )
    task = json.loads(created)
    assert task["status"] == "todo"
    task_id = str(task["id"])

    swagger.page.reload()
    patched = swagger.call(
        "PATCH", "/tasks/{task_id}",
        params={"task_id": task_id},
        body=json.dumps({"status": "in_progress"}),
        expect_status=200,
    )
    assert json.loads(patched)["status"] == "in_progress"

    swagger.page.reload()
    fetched = swagger.call("GET", "/tasks/{task_id}", params={"task_id": task_id})
    assert json.loads(fetched)["title"] == "Record the demo"

    # validation error is also part of the feature: an unknown status must 422
    swagger.page.reload()
    swagger.call(
        "PATCH", "/tasks/{task_id}",
        params={"task_id": task_id},
        body=json.dumps({"status": "bogus"}),
        expect_status=422,
    )
