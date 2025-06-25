from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
CORS(app)

# ——— MySQL CONFIG ———

def get_conn():
    return sqlite3.connect("database.db")

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, age INTEGER, gender TEXT,
            contact TEXT, blood_group TEXT, health_problem TEXT
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

init_db()

# ——— FRONTEND ———
@app.route("/")
def index():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Smart Healthcare System</title>
  <style>
    body { font-family: Arial, sans-serif; background: #f0f8ff; margin: 0; padding: 0; color: #333; }
    header { background: #00bcd4; color: #fff; padding: 2rem; text-align: center; border-bottom: 4px solid #00796b; }
    header h1 { margin: 0; font-size: 2.5rem; }
    nav ul { list-style: none; padding: 0; margin: 1rem 0; }
    nav ul li { display: inline; margin: 0 15px; }
    nav ul li a { color: #fff; text-decoration: none; font-weight: bold; }
    nav ul li a:hover { color: #ffeb3b; }
    main { padding: 2rem; max-width: 1000px; margin: auto; }
    section { display: none; margin-bottom: 2rem; padding: 1rem; background: #fff; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
    h2 { color: #00796b; margin-bottom: 1rem; }
    form label { display: block; margin: 10px 0 5px; }
    form input, form select, form button, form textarea {
      width: 100%; padding: 10px; margin-bottom: 15px;
      border-radius: 8px; border: 1px solid #ccc;
    }
    form button { background: #00bcd4; color: white; border: none; font-weight: bold; }
    form button:hover { background: #00796b; }
    #patientList {
      display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px;
    }
    .patient-card {
      background: #e0f7fa; padding: 20px; border-radius: 10px;
      box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .delete-btn {
      background: #f44336; color: white; border: none; padding: 10px; border-radius: 8px;
      width: 100%; font-weight: bold;
    }
    footer { background: #333; color: #fff; text-align: center; padding: 10px; position: fixed; bottom: 0; width: 100%; }

    #chatbox {
      position: fixed; bottom: 80px; right: 20px; background: #fff;
      width: 300px; height: 400px; border: 1px solid #ccc; border-radius: 10px;
      display: none; flex-direction: column; overflow: hidden;
    }
    #chatlog { flex: 1; overflow-y: auto; padding: 10px; }
    #chatinput { display: flex; }
    #chatinput input { flex: 1; border: none; padding: 10px; }
    #chatinput button { background: #00bcd4; color: white; border: none; padding: 10px; }
  </style>
</head>
<body>
  <header>
    <h1>Smart Healthcare System</h1>
    <nav>
      <ul>
        <li><a href="#home" onclick="showSection('home')">Home</a></li>
        <li><a href="#patients" onclick="showSection('patients')">Patients</a></li>
        <li><a href="#ai" onclick="showChatbot()">AI-Doc</a></li>
        <li><a href="#reports" onclick="showSection('reports'); loadPatients()">Reports</a></li>
      </ul>
    </nav>
  </header>

  <main>
    <section id="home" style="display: block;">
      <h2>Welcome</h2>
      <p>This system helps manage patients, appointments, and access AI Doc for guidance.</p>
    </section>

    <section id="patients">
      <h2>Patient Management</h2>
      <form id="patientForm">
        <label>Name:</label><input type="text" id="patientName" required>
        <label>Age:</label><input type="number" id="patientAge" required>
        <label>Gender:</label>
        <select id="patientGender">
          <option>Male</option><option>Female</option><option>Other</option>
        </select>
        <label>Contact:</label><input type="text" id="patientContact" required>
        <label>Blood Group:</label><input type="text" id="patientBlood" required>
        <label>Health Problem:</label><textarea id="patientProblem" rows="3"></textarea>
        <button type="submit">Add Patient</button>
      </form>
    </section>

    <section id="reports">
      <h2>Patient Reports</h2>
      <div id="patientList"></div>
    </section>
  </main>

  <div id="chatbox">
    <div id="chatlog"></div>
    <div id="chatinput">
      <input type="text" id="chatMessage" placeholder="Ask AI-Doc..."/>
      <button onclick="sendToGemini()">Send</button>
    </div>
  </div>

  <footer>
    &copy; 2025 Smart Healthcare System
  </footer>

<script>
function showSection(id) {
  document.querySelectorAll("main section").forEach(s => s.style.display = "none");
  document.getElementById(id).style.display = "block";
}

function showChatbot() {
  document.getElementById("chatbox").style.display = "flex";
}

document.getElementById("patientForm").addEventListener("submit", async e => {
  e.preventDefault();
  const data = {
    name: document.getElementById("patientName").value,
    age: document.getElementById("patientAge").value,
    gender: document.getElementById("patientGender").value,
    contact: document.getElementById("patientContact").value,
    blood_group: document.getElementById("patientBlood").value,
    health_problem: document.getElementById("patientProblem").value
  };
  const res = await fetch("/api/patients", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });
  const json = await res.json();
  alert(json.message || json.error);
  document.getElementById("patientForm").reset();
});

async function loadPatients() {
  const res = await fetch("/api/patients");
  const patients = await res.json();
  const list = document.getElementById("patientList");
  list.innerHTML = '';
  patients.forEach(p => {
    const card = document.createElement("div");
    card.className = "patient-card";
    card.innerHTML = `
      <h3>${p.name}</h3>
      <p><strong>Age:</strong> ${p.age}</p>
      <p><strong>Gender:</strong> ${p.gender}</p>
      <p><strong>Contact:</strong> ${p.contact}</p>
      <p><strong>Blood Group:</strong> ${p.blood_group}</p>
      <p><strong>Health Problem:</strong> ${p.health_problem}</p>
      <button class="delete-btn" onclick="deletePatient(${p.id})">Delete</button>
    `;
    list.appendChild(card);
  });
}

async function deletePatient(id) {
  if (!confirm("Delete this patient?")) return;
  const res = await fetch(`/api/patients/${id}`, { method: "DELETE" });
  const json = await res.json();
  alert(json.message || json.error);
  loadPatients();
}

async function sendToGemini() {
  const msg = document.getElementById("chatMessage").value;
  const res = await fetch("/api/gemini", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: msg })
  });
  const data = await res.json();
  document.getElementById("chatlog").innerHTML += `<p><strong>You:</strong> ${msg}</p><p><strong>AI-Doc:</strong> ${data.response}</p>`;
  document.getElementById("chatMessage").value = "";
}
</script>
</body>
</html>
"""

# ——— API Routes ———
@app.route("/api/patients", methods=["GET", "POST"])
def api_patients():
    if request.method == "POST":
        data = request.get_json() or {}
        try:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO patients (name, age, gender, contact, blood_group, health_problem) VALUES (?,?,?,?,?,?)",
                (data["name"], data["age"], data["gender"], data["contact"], data["blood_group"], data["health_problem"])
            )
            conn.commit()
            cur.close(); conn.close()
            return jsonify(message="Patient added successfully"), 201
        except Exception as e:
            logging.error("Error inserting patient", exc_info=e)
            return jsonify(error=str(e)), 500
    else:
        try:
            conn = get_conn()
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT * FROM patients")
            rows = cur.fetchall()
            cur.close(); conn.close()
            return jsonify(rows)
        except Exception as e:
            return jsonify(error=str(e)), 500

@app.route("/api/patients/<int:pid>", methods=["DELETE"])
def delete_patient(pid):
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM patients WHERE id = %s", (pid,))
        conn.commit()
        cur.close(); conn.close()
        return jsonify(message="Patient deleted successfully")
    except Exception as e:
        return jsonify(error=str(e)), 500

# ——— Gemini Chatbot API ———
import google.generativeai as genai
genai.configure(api_key="AIzaSyDl0n9pAbjSX6spNexRdWC1vAdKkeLEM14")

@app.route("/api/gemini", methods=["POST"])
def gemini_chat():
    data = request.get_json()
    prompt = data.get("message", "")
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(prompt)
        return jsonify(response=response.text)
    except Exception as e:
        return jsonify(error=str(e)), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
