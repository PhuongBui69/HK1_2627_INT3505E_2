"""Runnable Tasks API demo using Flask-Smorest.

Run:
    pip install -r requirements.txt
    python app.py

OpenAPI document: http://127.0.0.1:5000/openapi.json
Swagger UI:       http://127.0.0.1:5000/docs
"""

from __future__ import annotations

from uuid import UUID, uuid4

from flask import Flask, current_app
from flask.views import MethodView
from flask_smorest import Api, Blueprint, abort
from marshmallow import Schema, ValidationError, fields, validate, validates_schema

VALID_STATUSES = ("open", "in_progress", "done")
VALID_PRIORITIES = ("low", "normal", "high")


# ---------------------------------------------------------------------------
# Request/response schemas. Flask-Smorest uses these both for validation and
# for generating the OpenAPI document.
# ---------------------------------------------------------------------------
class TaskSchema(Schema):
    """The Task representation returned by the API."""

    id = fields.UUID(dump_only=True, metadata={"description": "Unique task ID"})
    title = fields.String(required=True, validate=validate.Length(min=1, max=200))
    status = fields.String(validate=validate.OneOf(VALID_STATUSES))
    priority = fields.String(validate=validate.OneOf(VALID_PRIORITIES))
    due_date = fields.Date(data_key="dueDate", allow_none=True)
    assignee_id = fields.UUID(data_key="assigneeId", allow_none=True)


class CreateTaskSchema(Schema):
    """Fields accepted when creating a task."""

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
    """Optional fields for partial updates."""

    title = fields.String(validate=validate.Length(min=1, max=200))
    status = fields.String(validate=validate.OneOf(VALID_STATUSES))
    priority = fields.String(validate=validate.OneOf(VALID_PRIORITIES))
    due_date = fields.Date(data_key="dueDate", allow_none=True)
    assignee_id = fields.UUID(data_key="assigneeId", allow_none=True)

    @validates_schema
    def require_at_least_one_field(self, data, **kwargs):
        if not data:
            raise ValidationError("Provide at least one field to update.")


class ListTasksQuerySchema(Schema):
    """Query parameters used by GET /tasks."""

    limit = fields.Integer(
        load_default=20,
        validate=validate.Range(min=1, max=100),
        metadata={"description": "Maximum number of tasks to return (1-100)"},
    )
    status = fields.String(
        required=False,
        validate=validate.OneOf(VALID_STATUSES),
        metadata={"description": "Filter by task status"},
    )


blp = Blueprint(
    "tasks",
    __name__,
    url_prefix="/tasks",
    description="Create, list, retrieve, update, and delete tasks.",
)


def _store() -> dict[str, dict]:
    """Return the in-memory store belonging to the current Flask application."""
    return current_app.extensions["task_store"]


def _normalize_task(task: dict) -> dict:
    """Return all response fields, including nullable fields, consistently."""
    return {
        "id": task["id"],
        "title": task["title"],
        "status": task["status"],
        "priority": task["priority"],
        "due_date": task.get("due_date"),
        "assignee_id": task.get("assignee_id"),
    }


def _find_task(task_id: UUID) -> dict:
    task = _store().get(str(task_id))
    if task is None:
        abort(404, message=f"Task '{task_id}' was not found.")
    return task


@blp.route("")
class TasksCollection(MethodView):
    @blp.doc(
        summary="List tasks",
        description="Return tasks, optionally filtered by status and limited in number.",
    )
    @blp.arguments(ListTasksQuerySchema, location="query")
    @blp.response(200, TaskSchema(many=True))
    def get(self, query_args: dict):
        tasks = list(_store().values())
        if query_args.get("status"):
            tasks = [task for task in tasks if task["status"] == query_args["status"]]
        return [_normalize_task(task) for task in tasks[: query_args["limit"]]]

    @blp.doc(
        summary="Create a task",
        description="Create a task. Status defaults to open and priority defaults to normal.",
    )
    @blp.arguments(CreateTaskSchema)
    @blp.response(201, TaskSchema)
    def post(self, new_task: dict):
        task = {"id": uuid4(), **new_task}
        key = str(task["id"])
        _store()[key] = task
        return _normalize_task(task)


@blp.route("/<uuid:taskId>")
class TaskById(MethodView):
    @blp.doc(summary="Get a task by ID", responses={404: "Task not found"})
    @blp.response(200, TaskSchema)
    def get(self, taskId: UUID):
        return _normalize_task(_find_task(taskId))

    @blp.doc(
        summary="Update a task partially",
        description="Only the fields included in the request body are changed.",
        responses={404: "Task not found"},
    )
    @blp.arguments(UpdateTaskSchema)
    @blp.response(200, TaskSchema)
    def patch(self, changes: dict, taskId: UUID):
        task = _find_task(taskId)
        task.update(changes)
        return _normalize_task(task)

    @blp.doc(summary="Delete a task", responses={404: "Task not found"})
    @blp.response(204)
    def delete(self, taskId: UUID):
        _find_task(taskId)
        del _store()[str(taskId)]
        return None


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


def create_app(*, seed_data: bool = True) -> Flask:
    app = Flask(__name__)
    app.config.update(
        API_TITLE="Tasks API",
        API_VERSION="v1",
        OPENAPI_VERSION="3.0.3",
        # Flask-Smorest creates GET /openapi.json and Swagger UI at /docs.
        OPENAPI_URL_PREFIX="/",
        OPENAPI_JSON_PATH="openapi.json",
        OPENAPI_SWAGGER_UI_PATH="/docs",
        OPENAPI_SWAGGER_UI_URL="https://cdn.jsdelivr.net/npm/swagger-ui-dist/",
    )

    api = Api(app)
    api.register_blueprint(blp)

    # In-memory data keeps this teaching example runnable without a database.
    # Data is reset every time the app process is restarted.
    task_store: dict[str, dict] = {}
    if seed_data:
        samples = [
            _new_task(
                "Read the OpenAPI Petstore example",
                status="open",
                priority="high",
                due_date=None,
            ),
            _new_task(
                "Implement and test Tasks API",
                status="in_progress",
                priority="normal",
                due_date=None,
            ),
        ]
        task_store.update({str(task["id"]): task for task in samples})
    app.extensions["task_store"] = task_store
    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
