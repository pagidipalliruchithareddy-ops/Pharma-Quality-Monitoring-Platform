from flask import Flask, request, redirect, url_for, render_template_string
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
DB = os.environ.get("DB_PATH", "pharma.db")

def connect():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with connect() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_no TEXT UNIQUE NOT NULL,
            product TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'In Progress',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id INTEGER NOT NULL,
            temperature REAL NOT NULL,
            humidity REAL NOT NULL,
            pressure REAL NOT NULL,
            equipment_status TEXT NOT NULL,
            recorded_at TEXT NOT NULL,
            FOREIGN KEY(batch_id) REFERENCES batches(id)
        );
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            details TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """)
        if con.execute("SELECT COUNT(*) FROM batches").fetchone()[0] == 0:
            con.execute("INSERT INTO batches(batch_no,product,status,created_at) VALUES(?,?,?,?)",
                        ("BATCH-001", "Paracetamol 500mg", "In Progress", datetime.now().isoformat(timespec="seconds")))
            con.execute("INSERT INTO audit(action,details,created_at) VALUES(?,?,?)",
                        ("CREATE", "Created sample batch BATCH-001", datetime.now().isoformat(timespec="seconds")))

init_db()

PAGE = """
<!doctype html><html><head><title>Pharma Quality Monitor</title>
<style>
body{font-family:Arial;margin:30px;background:#f4f6f8;color:#222}
main{max-width:1050px;margin:auto} section{background:white;padding:18px;margin:16px 0;border-radius:8px}
input,select{padding:8px;margin:5px} button{padding:9px 15px;background:#145da0;color:white;border:0;border-radius:4px}
table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccc;padding:8px;text-align:left}
.good{color:green}.bad{color:#c00}.small{color:#555;font-size:13px}
</style></head><body><main>
<h1>Smart Pharmaceutical Manufacturing Quality Monitoring Platform</h1>
<p>Monitor process readings, track batches, identify deviations and maintain audit records.</p>
<section><h2>Create production batch</h2>
<form method="post" action="/batch">
<input name="batch_no" placeholder="Batch number" required>
<input name="product" placeholder="Product name" required>
<button>Create batch</button></form></section>
<section><h2>Record manufacturing parameters</h2>
<form method="post" action="/reading">
<select name="batch_id" required>{% for b in batches %}<option value="{{b.id}}">{{b.batch_no}} - {{b.product}}</option>{% endfor %}</select><br>
<label>Temperature (°C) <input name="temperature" type="number" step="0.1" required></label>
<label>Humidity (%) <input name="humidity" type="number" step="0.1" required></label>
<label>Pressure (kPa) <input name="pressure" type="number" step="0.1" required></label>
<label>Equipment <select name="equipment_status"><option>Normal</option><option>Maintenance Required</option><option>Fault</option></select></label>
<button>Save reading</button></form>
<p class="small">Demo limits only: temperature 20–25°C, humidity 30–60%, pressure 95–105 kPa. Replace these with approved limits for the actual product/process.</p>
</section>
<section><h2>Production batches</h2><table><tr><th>Batch</th><th>Product</th><th>Status</th><th>Created</th></tr>
{% for b in batches %}<tr><td>{{b.batch_no}}</td><td>{{b.product}}</td><td>{{b.status}}</td><td>{{b.created_at}}</td></tr>{% endfor %}</table></section>
<section><h2>Latest process readings</h2><table><tr><th>Batch</th><th>Temperature</th><th>Humidity</th><th>Pressure</th><th>Equipment</th><th>Time</th></tr>
{% for r in readings %}<tr><td>{{r.batch_no}}</td><td>{{r.temperature}}</td><td>{{r.humidity}}</td><td>{{r.pressure}}</td><td>{{r.equipment_status}}</td><td>{{r.recorded_at}}</td></tr>{% endfor %}</table></section>
<section><h2>Quality alerts</h2>{% if alerts %}<ul>{% for a in alerts %}<li class="bad">{{a.batch_no}}: {{a.message}} — {{a.created_at}}</li>{% endfor %}</ul>{% else %}<p class="good">No deviations detected.</p>{% endif %}</section>
<section><h2>Audit trail</h2><table><tr><th>Action</th><th>Details</th><th>Time</th></tr>
{% for a in audit %}<tr><td>{{a.action}}</td><td>{{a.details}}</td><td>{{a.created_at}}</td></tr>{% endfor %}</table></section>
<section><h2>Batch quality report</h2><form method="get" action="/report">
<select name="batch_id">{% for b in batches %}<option value="{{b.id}}">{{b.batch_no}}</option>{% endfor %}</select><button>Generate report</button></form>
{% if report %}<p><b>Report:</b> {{report.batch_no}} | Readings: {{report.count}} | Deviations: {{report.deviations}} | Result: {{report.result}}</p>{% endif %}</section>
</main></body></html>
"""

@app.route("/")
def home():
    with connect() as con:
        batches = con.execute("SELECT * FROM batches ORDER BY id DESC").fetchall()
        readings = con.execute("""SELECT r.*, b.batch_no FROM readings r JOIN batches b ON b.id=r.batch_id ORDER BY r.id DESC LIMIT 10""").fetchall()
        alerts = con.execute("""SELECT a.*, b.batch_no FROM alerts a JOIN batches b ON b.id=a.batch_id ORDER BY a.id DESC LIMIT 10""").fetchall()
        audit = con.execute("SELECT * FROM audit ORDER BY id DESC LIMIT 15").fetchall()
    return render_template_string(PAGE, batches=batches, readings=readings, alerts=alerts, audit=audit, report=None)

@app.route("/batch", methods=["POST"])
def create_batch():
    batch_no, product = request.form["batch_no"].strip(), request.form["product"].strip()
    now = datetime.now().isoformat(timespec="seconds")
    with connect() as con:
        try:
            cur = con.execute("INSERT INTO batches(batch_no,product,status,created_at) VALUES(?,?,?,?)",
                              (batch_no, product, "In Progress", now))
            con.execute("INSERT INTO audit(action,details,created_at) VALUES(?,?,?)",
                        ("CREATE BATCH", f"Created {batch_no} for {product}", now))
        except sqlite3.IntegrityError:
            return "Batch number already exists. Go back and use a unique batch number.", 400
    return redirect(url_for("home"))

@app.route("/reading", methods=["POST"])
def add_reading():
    batch_id = int(request.form["batch_id"])
    t, h, p = float(request.form["temperature"]), float(request.form["humidity"]), float(request.form["pressure"])
    equipment = request.form["equipment_status"]
    now = datetime.now().isoformat(timespec="seconds")
    deviations = []
    if not 20 <= t <= 25: deviations.append(f"Temperature out of range: {t}°C (allowed 20–25°C)")
    if not 30 <= h <= 60: deviations.append(f"Humidity out of range: {h}% (allowed 30–60%)")
    if not 95 <= p <= 105: deviations.append(f"Pressure out of range: {p} kPa (allowed 95–105 kPa)")
    if equipment != "Normal": deviations.append(f"Equipment status: {equipment}")
    with connect() as con:
        con.execute("""INSERT INTO readings(batch_id,temperature,humidity,pressure,equipment_status,recorded_at)
                       VALUES(?,?,?,?,?,?)""", (batch_id,t,h,p,equipment,now))
        con.execute("INSERT INTO audit(action,details,created_at) VALUES(?,?,?)",
                    ("RECORD READING", f"T={t}°C, H={h}%, P={p} kPa, equipment={equipment}", now))
        for msg in deviations:
            con.execute("INSERT INTO alerts(batch_id,message,created_at) VALUES(?,?,?)", (batch_id,msg,now))
        if deviations:
            con.execute("INSERT INTO audit(action,details,created_at) VALUES(?,?,?)",
                        ("QUALITY DEVIATION", "; ".join(deviations), now))
    return redirect(url_for("home"))

@app.route("/report")
def report():
    batch_id = request.args.get("batch_id", type=int)
    with connect() as con:
        batches = con.execute("SELECT * FROM batches ORDER BY id DESC").fetchall()
        readings = con.execute("""SELECT r.*, b.batch_no FROM readings r JOIN batches b ON b.id=r.batch_id ORDER BY r.id DESC LIMIT 10""").fetchall()
        alerts = con.execute("""SELECT a.*, b.batch_no FROM alerts a JOIN batches b ON b.id=a.batch_id ORDER BY a.id DESC LIMIT 10""").fetchall()
        audit = con.execute("SELECT * FROM audit ORDER BY id DESC LIMIT 15").fetchall()
        row = con.execute("SELECT * FROM batches WHERE id=?", (batch_id,)).fetchone()
        count = con.execute("SELECT COUNT(*) FROM readings WHERE batch_id=?", (batch_id,)).fetchone()[0]
        deviations = con.execute("SELECT COUNT(*) FROM alerts WHERE batch_id=?", (batch_id,)).fetchone()[0]
        result = {"batch_no":row["batch_no"], "count":count, "deviations":deviations,
                  "result":"Review Required" if deviations else "No deviation recorded"} if row else None
        if row:
            con.execute("INSERT INTO audit(action,details,created_at) VALUES(?,?,?)",
                        ("GENERATE REPORT", f"Generated report for {row['batch_no']}", datetime.now().isoformat(timespec="seconds")))
    return render_template_string(PAGE, batches=batches, readings=readings, alerts=alerts, audit=audit, report=result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
