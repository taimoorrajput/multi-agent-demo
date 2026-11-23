import json
import uuid


def test_T002_create_and_fetch_project(swagger):
    email = f"owner-{uuid.uuid4().hex[:8]}@example.com"
    created_user = swagger.call(
        "POST", "/users",
        body=json.dumps({"email": email, "name": "Project Owner"}),
        expect_status=201,
    )
    owner_id = json.loads(created_user)["id"]

    swagger.page.reload()
    created_project = swagger.call(
        "POST", "/projects",
        body=json.dumps({"name": "Demo Project", "description": "demo", "owner_id": owner_id}),
        expect_status=201,
    )
    project_id = str(json.loads(created_project)["id"])

    swagger.page.reload()
    fetched = swagger.call("GET", "/projects/{project_id}", params={"project_id": project_id})
    assert json.loads(fetched)["name"] == "Demo Project"

    # validation error is also part of the feature
    swagger.page.reload()
    swagger.call("POST", "/projects", body=json.dumps({"owner_id": owner_id}), expect_status=422)
