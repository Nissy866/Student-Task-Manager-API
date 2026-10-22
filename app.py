
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)
DATABASE = "tasks.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            status TEXT DEFAULT 'Pending'
        )
    """)
    conn.commit()
    conn.close()


@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Welcome to Student Task Manager API",
        "status": "Running"
    })


@app.route("/tasks", methods=["GET"])
def get_tasks():
    conn = get_db_connection()
    tasks = conn.execute("SELECT * FROM tasks").fetchall()
    conn.close()
    return jsonify([dict(task) for task in tasks])


@app.route("/tasks", methods=["POST"])
def add_task():
    data = request.get_json(silent=True) or {}
    title = data.get("title", "").strip()

    if not title:
        return jsonify({"error": "Task title is required"}), 400

    description = data.get("description", "")
    conn = get_db_connection()
    cursor = conn.execute(
        "INSERT INTO tasks (title, description) VALUES (?, ?)",
        (title, description)
    )
    conn.commit()
    task_id = cursor.lastrowid
    conn.close()

    return jsonify({
        "message": "Task created successfully",
        "id": task_id,
        "title": title,
        "description": description,
        "status": "Pending"
    }), 201


@app.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    data = request.get_json(silent=True) or {}
    conn = get_db_connection()

    task = conn.execute(
        "SELECT * FROM tasks WHERE id = ?", (task_id,)
    ).fetchone()

    if task is None:
        conn.close()
        return jsonify({"error": "Task not found"}), 404

    title = data.get("title", task["title"])
    description = data.get("description", task["description"])
    status = data.get("status", task["status"])

    if not isinstance(title, str) or not title.strip():
        conn.close()
        return jsonify({"error": "Task title cannot be empty"}), 400

    if status not in ["Pending", "In Progress", "Completed"]:
        conn.close()
        return jsonify({"error": "Invalid task status"}), 400

    conn.execute(
        """UPDATE tasks
           SET title = ?, description = ?, status = ?
           WHERE id = ?""",
        (title.strip(), description, status, task_id)
    )
    conn.commit()
    conn.close()

    return jsonify({"message": "Task updated successfully"})


@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    conn = get_db_connection()
    cursor = conn.execute(
        "DELETE FROM tasks WHERE id = ?", (task_id,)
    )
    conn.commit()
    deleted = cursor.rowcount
    conn.close()

    if deleted == 0:
        return jsonify({"error": "Task not found"}), 404

    return jsonify({"message": "Task deleted successfully"})


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
