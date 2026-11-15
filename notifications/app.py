import os, time
import psycopg2
from flask import Flask, request, jsonify

app = Flask(__name__)
DATABASE_URL = os.environ["DATABASE_URL"]

def get_conn():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    for _ in range(20):
        try:
            conn = get_conn()
            break
        except psycopg2.OperationalError:
            time.sleep(2)
    else:
        raise RuntimeError("DB inaccessible")
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS notifications (
        id SERIAL PRIMARY KEY, message TEXT, created_at TIMESTAMP DEFAULT NOW())""")
    conn.commit(); cur.close(); conn.close()

@app.route("/notify", methods=["POST"])
def notify():
    data = request.get_json(force=True)
    message = data.get("message", "")
    conn = get_conn(); cur = conn.cursor()
    cur.execute("INSERT INTO notifications (message) VALUES (%s)", (message,))
    conn.commit(); cur.close(); conn.close()
    print(f"[NOTIFICATION] {message}", flush=True)
    return jsonify({"status": "sent", "message": message}), 201

@app.route("/notifications")
def list_notifications():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT id, message, created_at FROM notifications ORDER BY id DESC")
    rows = [{"id": r[0], "message": r[1], "created_at": str(r[2])} for r in cur.fetchall()]
    cur.close(); conn.close()
    return jsonify(rows)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)