import os, time
import psycopg2, requests
from flask import Flask, request, jsonify

app = Flask(__name__)
DATABASE_URL = os.environ["DATABASE_URL"]
NOTIFICATIONS_URL = os.environ.get("NOTIFICATIONS_URL", "http://notifications:5000")
CATALOGUE_URL = os.environ.get("CATALOGUE_URL", "http://catalogue:5000")

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
    cur.execute("""CREATE TABLE IF NOT EXISTS orders (
        id SERIAL PRIMARY KEY, product_id INT, quantity INT,
        customer TEXT, created_at TIMESTAMP DEFAULT NOW())""")
    cur.execute("ALTER TABLE orders ADD COLUMN IF NOT EXISTS customer_email TEXT")
    conn.commit(); cur.close(); conn.close()

@app.route("/orders", methods=["POST"])
def create_order(): #####تحجز المنتج، تسجّل الطلبية، وتطلب إرسال notification.
    data = request.get_json(force=True)
    product_id = data.get("product_id")
    quantity = int(data.get("quantity", 1))
    customer = data.get("customer", "client")
    email = data.get("email")

    # Communication Commandes -> Catalogue (disponibilité + réservation du stock)
    r = requests.post(f"{CATALOGUE_URL}/products/{product_id}/reserve",
                      json={"quantity": quantity}, timeout=5)
    if r.status_code == 404:
        return jsonify({"error": "produit introuvable"}), 404
    if r.status_code == 409:
        return jsonify({"error": "stock insuffisant"}), 409

    conn = get_conn(); cur = conn.cursor() ### تسجّل الطلبية
    cur.execute("""INSERT INTO orders (product_id, quantity, customer, customer_email)
                   VALUES (%s,%s,%s,%s) RETURNING id""",
                (product_id, quantity, customer, email))
    order_id = cur.fetchone()[0]
    conn.commit(); cur.close(); conn.close()

    # Communication Commandes -> Notifications
    try:
        requests.post(f"{NOTIFICATIONS_URL}/notify",
                      json={"message": f"Nouvelle commande #{order_id} de {customer}",
                            "email": email, "order_id": order_id},
                      timeout=10)
    except requests.RequestException as e:
        print("Notification échouée:", e, flush=True)

    return jsonify({"order_id": order_id, "status": "created"}), 201

@app.route("/orders")
def list_orders(): #تعرض كل الطلبيات.
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT id, product_id, quantity, customer, customer_email FROM orders ORDER BY id")
    rows = [{"id": r[0], "product_id": r[1], "quantity": r[2], "customer": r[3], "email": r[4]}
            for r in cur.fetchall()]
    cur.close(); conn.close()
    return jsonify(rows)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)