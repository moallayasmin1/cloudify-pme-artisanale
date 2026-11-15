import os, time
import psycopg2
from flask import Flask, jsonify

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
    cur.execute("""CREATE TABLE IF NOT EXISTS products (
        id SERIAL PRIMARY KEY, name TEXT, price NUMERIC, category TEXT)""")
    cur.execute("SELECT COUNT(*) FROM products")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO products (name, price, category) VALUES (%s,%s,%s)",
            [("Savon d'Alep", 8.5, "Savons"),
             ("Huile d'argan", 35, "Huiles essentielles"),
             ("Crème au karité", 22, "Cosmétiques naturels")])
    conn.commit(); cur.close(); conn.close()

@app.route("/products")
def products():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT id, name, price, category FROM products ORDER BY id")
    rows = [{"id": r[0], "name": r[1], "price": float(r[2]), "category": r[3]}
            for r in cur.fetchall()]
    cur.close(); conn.close()
    return jsonify(rows)

@app.route("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)