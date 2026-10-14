"""Tasks API with a separate, hand-authored OpenAPI YAML specification.

Run:
    pip install -r requirements.txt
    python app.py

OpenAPI JSON: http://127.0.0.1:5000/openapi.json
Swagger UI:   http://127.0.0.1:5000/docs
"""

from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

import yaml
from flask import Flask, Response, current_app, jsonify, request
from marshmallow import Schema, ValidationError, fields, validate

VALID_STATUSES = ("open", "in_progress", "done")
VALID_PRIORITIES = ("low", "normal", "high")
SPEC_FILE = Path(__file__).resolve().with_name("tasks-api.yaml")


# Marshmallow schemas validate runtime request data. The independently authored
# tasks-api.yaml is the document served to OpenAPI clients and Swagger UI.
class TaskSchema(Schema):
    id = fields.UUID(dump_only=True)
    title = fields.String(required=True, validate=validate.Length(min=1, max=200))
    status = fields.String(required=True, validate=validate.OneOf(VALID_STATUSES))
    priority = fields.String(required=True, validate=validate.OneOf(VALID_PRIORITIES))
    due_date = fields.Date(data_key="dueDate", allow_none=True, required=True)
    assignee_id = fields.UUID(data_key="assigneeId", allow_none=True, required=True)


class CreateTaskSchema(Schema):
    title = fields.String(required=True, validate=validate.Length(min=1, max=200))
    status = fields.String(
        load_default="open", validate=validate.OneOf(VALID_STATUSES)
    )
    priority = fields.String(
        load_default="normal", validate=validate.OneOf(VALID_PRIORITIES)
    )
    due_date = fields.Date(data_key="dueDate", allow_none=True, load_default=None)
    assignee_id = fields.UUID(data_key="assigneeId", allow_none=True, load_default=None)


class UpdateTaskSchema(Schema):
    title = fields.String(validate=validate.Length(min=1, max=200))
    status = fields.String(validate=validate.OneOf(VALID_STATUSES))
    priority = fields.String(validate=validate.OneOf(VALID_PRIORITIES))
    due_date = fields.Date(data_key="dueDate", allow_none=True)
    assignee_id = fields.UUID(data_key="assigneeId", allow_none=True)


class ListTasksQuerySchema(Schema):
    limit = fields.Integer(
        load_default=20,
        validate=validate.Range(min=1, max=100),
    )
    status = fields.String(validate=validate.OneOf(VALID_STATUSES))


TASK_SCHEMA = TaskSchema()
TASK_LIST_SCHEMA = TaskSchema(many=True)
CREATE_TASK_SCHEMA = CreateTaskSchema()
UPDATE_TASK_SCHEMA = UpdateTaskSchema()
LIST_QUERY_SCHEMA = ListTasksQuerySchema()


def _store() -> dict[str, dict]:
    return current_app.extensions["task_store"]


def _serialize_task(task: dict) -> dict:
    return TASK_SCHEMA.dump(task)


def _load_json(schema: Schema) -> dict:
    payload = request.get_json(silent=True)
    if payload is None:
        payload = {}
    if not isinstance(payload, dict):
        raise ValidationError({"_schema": ["JSON request body must be an object."]})
    return schema.load(payload)


def _validation_response(error: ValidationError):
    return jsonify({"message": "Request validation failed.", "errors": error.messages}), 422


def _parse_task_id(raw_id: str) -> UUID | None:
    try:
        return UUID(raw_id)
    except (ValueError, TypeError, AttributeError):
        return None


def _find_task(task_id: UUID) -> dict | None:
    return _store().get(str(task_id))


def _new_task(
    title: str,
    status: str = "open",
    priority: str = "normal",
    due_date=None,
    assignee_id=None,
) -> dict:
    return {
        "id": uuid4(),
        "title": title,
        "status": status,
        "priority": priority,
        "due_date": due_date,
        "assignee_id": assignee_id,
    }


def create_app(*, seed_data: bool = True, spec_path: Path | None = None) -> Flask:
    app = Flask(__name__)
    app.config["OPENAPI_SPEC_PATH"] = str(spec_path or SPEC_FILE)

    # GET /openapi.json reads the separate YAML and returns it as JSON, as
    # requested by the assignment. Swagger UI loads this same endpoint.
    @app.get("/openapi.json")
    def openapi_json():
        path = Path(current_app.config["OPENAPI_SPEC_PATH"])
        with path.open("r", encoding="utf-8") as file:
            spec = yaml.safe_load(file)
        return jsonify(spec)

    @app.get("/docs")
    def swagger_docs():
        html = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Tasks API — Swagger UI</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>
    window.onload = () => {
      window.ui = SwaggerUIBundle({
        url: "/openapi.json",
        dom_id: "#swagger-ui",
        deepLinking: true,
        displayRequestDuration: true
      });
    };
  </script>
</body>
</html>"""
        return Response(html, mimetype="text/html")

    @app.get("/tasks")
    def list_tasks():
        try:
            query = LIST_QUERY_SCHEMA.load(request.args.to_dict())
        except ValidationError as error:
            return _validation_response(error)

        tasks = list(_store().values())
        if query.get("status"):
            tasks = [task for task in tasks if task["status"] == query["status"]]
        return jsonify(TASK_LIST_SCHEMA.dump(tasks[: query["limit"]]))

    @app.post("/tasks")
    def create_task():
        try:
            data = _load_json(CREATE_TASK_SCHEMA)
        except ValidationError as error:
            return _validation_response(error)

        task = _new_task(**data)
        _store()[str(task["id"])] = task
        return jsonify(_serialize_task(task)), 201

    @app.get("/tasks/<task_id>")
    def get_task(task_id: str):
        parsed_id = _parse_task_id(task_id)
        if parsed_id is None:
            return jsonify({"message": "taskId must be a valid UUID."}), 400
        task = _find_task(parsed_id)
        if task is None:
            return jsonify({"message": f"Task '{parsed_id}' was not found."}), 404
        return jsonify(_serialize_task(task))

    @app.patch("/tasks/<task_id>")
    def patch_task(task_id: str):
        parsed_id = _parse_task_id(task_id)
        if parsed_id is None:
            return jsonify({"message": "taskId must be a valid UUID."}), 400
        task = _find_task(parsed_id)
        if task is None:
            return jsonify({"message": f"Task '{parsed_id}' was not found."}), 404

        try:
            changes = _load_json(UPDATE_TASK_SCHEMA)
            if not changes:
                raise ValidationError({"_schema": ["Provide at least one field to update."]})
        except ValidationError as error:
            return _validation_response(error)

        task.update(changes)
        return jsonify(_serialize_task(task))

    @app.delete("/tasks/<task_id>")
    def delete_task(task_id: str):
        parsed_id = _parse_task_id(task_id)
        if parsed_id is None:
            return jsonify({"message": "taskId must be a valid UUID."}), 400
        task = _find_task(parsed_id)
        if task is None:
            return jsonify({"message": f"Task '{parsed_id}' was not found."}), 404
        del _store()[str(parsed_id)]
        return "", 204

    # In-memory data allows CRUD demonstrations without a database. The data
    # resets when the app process restarts.
    task_store: dict[str, dict] = {}
    if seed_data:
        seed_tasks = [
            _new_task("Read the OpenAPI Petstore example", priority="high"),
            _new_task("Implement and test Tasks API", status="in_progress"),
        ]
        task_store.update({str(task["id"]): task for task in seed_tasks})
    app.extensions["task_store"] = task_store
    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
