import json
import uuid


def test_T001_create_and_fetch_user(swagger):
    email = f"demo-{uuid.uuid4().hex[:8]}@example.com"
    created = swagger.call(
        "POST", "/users",
        body=json.dumps({"email": email, "name": "Demo User"}),
        expect_status=201,
    )
    user_id = str(json.loads(created)["id"])

    fetched = swagger.call("GET", "/users/{user_id}", params={"user_id": user_id})
    assert json.loads(fetched)["email"] == email

    # validation error is also part of the feature
    swagger.page.reload()
    swagger.call("POST", "/users", body=json.dumps({"name": "No Email"}), expect_status=422)
