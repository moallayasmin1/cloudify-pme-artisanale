import os, time
import psycopg2
from flask import Flask, jsonify, request

app = Flask(__name__)
DATABASE_URL = os.environ["DATABASE_URL"]

def get_conn(): # تربط التطبيق بقاعدة البيانات
    return psycopg2.connect(DATABASE_URL)

def init_db(): #تجهّز جدول المنتجات وتحطّ فيه 3 produit
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
    cur.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS stock INT DEFAULT 10")
    cur.execute("SELECT COUNT(*) FROM products")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO products (name, price, category, stock) VALUES (%s,%s,%s,%s)",
            [("Savon d'Alep", 8.5, "Savons", 20),
             ("Huile d'argan", 35, "Huiles essentielles", 5),
             ("Crème au karité", 22, "Cosmétiques naturels", 10)])
    conn.commit(); cur.close(); conn.close()

@app.route("/products")  #عرض كل المنتجات والـ stock متاعهم. GET /products
def products():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT id, name, price, category, stock FROM products ORDER BY id")
    rows = [{"id": r[0], "name": r[1], "price": float(r[2]), "category": r[3], "stock": r[4]}
            for r in cur.fetchall()]
    cur.close(); conn.close()
    return jsonify(rows)

@app.route("/products/<int:pid>/reserve", methods=["POST"]) #تنقص الكمية من الـ stock وقت الحجز (404 produit ma yوجdch, 409 stock ma ykfich).
def reserve(pid): ###تتأكد اللي المنتج موجود والـ stock يكفي، وبعد تنقص الكمية.
    qty = int((request.get_json(force=True) or {}).get("quantity", 1))
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT stock FROM products WHERE id = %s", (pid,))
    row = cur.fetchone()
    if row is None:
        cur.close(); conn.close()
        return jsonify({"error": "produit introuvable"}), 404
    if row[0] < qty:
        cur.close(); conn.close()
        return jsonify({"error": "stock insuffisant", "stock": row[0]}), 409
    cur.execute("UPDATE products SET stock = stock - %s WHERE id = %s", (qty, pid))
    conn.commit(); cur.close(); conn.close()
    return jsonify({"status": "reserved", "remaining": row[0] - qty})

@app.route("/health") #تتأكد اللي service يخدم.
def health():
    return {"status": "ok"} #bech nعrfou el service y5dem

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)