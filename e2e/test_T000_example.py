"""Example e2e test. Builders copy this pattern as e2e/test_T00X_<feature>.py, then delete this file.

Assumes the app exposes POST /tasks and GET /tasks/{task_id}. Change it to match your API.
"""
import json

import pytest

pytestmark = pytest.mark.skip(reason="example only: adapt to your endpoints")


def test_T000_create_and_fetch_task(swagger):
    created = swagger.call(
        "POST", "/tasks",
        body=json.dumps({"title": "Record the demo", "priority": "high"}),
        expect_status=201,
    )
    task_id = str(json.loads(created)["id"])

    fetched = swagger.call("GET", "/tasks/{task_id}", params={"task_id": task_id})
    assert json.loads(fetched)["title"] == "Record the demo"

    # validation error is also part of the feature
    swagger.page.reload()
    swagger.call("POST", "/tasks", body=json.dumps({"priority": "high"}), expect_status=422)
