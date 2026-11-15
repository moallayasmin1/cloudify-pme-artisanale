import os, time, smtplib
from email.message import EmailMessage
import psycopg2
from flask import Flask, request, jsonify

app = Flask(__name__)
DATABASE_URL = os.environ["DATABASE_URL"]
SMTP_HOST = os.environ.get("SMTP_HOST", "mailhog")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "1025"))

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

def send_email(to, subject, body):
    msg = EmailMessage()
    msg["From"] = "boutique@pme-artisanale.tn"
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=5) as s:
        s.send_message(msg)

@app.route("/notify", methods=["POST"])
def notify():
    data = request.get_json(force=True)
    message = data.get("message", "")
    email = data.get("email")

    conn = get_conn(); cur = conn.cursor()
    cur.execute("INSERT INTO notifications (message) VALUES (%s)", (message,))
    conn.commit(); cur.close(); conn.close()
    print(f"[NOTIFICATION] {message}", flush=True)

    email_status = "non demandé"
    if email:
        try:
            send_email(email, f"Confirmation de commande #{data.get('order_id', '')}",
                       f"Bonjour,\n\n{message}.\nMerci pour votre achat !\n\nPME artisanale")
            email_status = "envoyé"
            print(f"[EMAIL] envoyé à {email}", flush=True)
        except Exception as e:
            email_status = "échec"
            print("[EMAIL] échec:", e, flush=True)

    return jsonify({"status": "sent", "message": message, "email": email_status}), 201

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