
from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "hospital_secret_key"


def get_db_connection():
    conn = sqlite3.connect("hospital.db")
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():

    conn = get_db_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialization TEXT NOT NULL,
            experience INTEGER
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id INTEGER,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            is_available INTEGER DEFAULT 1
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            doctor_id INTEGER,
            slot_id INTEGER,
            status TEXT DEFAULT 'Booked'
        )
    """)

    doctor_count = conn.execute(
        "SELECT COUNT(*) FROM doctors"
    ).fetchone()[0]

    if doctor_count == 0:

        conn.execute(
            "INSERT INTO doctors (name, specialization, experience) VALUES (?, ?, ?)",
            ("Dr. Ravi Kumar", "Cardiologist", 10)
        )

        conn.execute(
            "INSERT INTO doctors (name, specialization, experience) VALUES (?, ?, ?)",
            ("Dr. Priya Sharma", "Dermatologist", 7)
        )

        conn.execute(
            "INSERT INTO doctors (name, specialization, experience) VALUES (?, ?, ?)",
            ("Dr. Anil Reddy", "General Physician", 12)
        )

    conn.commit()

    doctors = conn.execute(
        "SELECT id FROM doctors"
    ).fetchall()

    slot_count = conn.execute(
        "SELECT COUNT(*) FROM slots"
    ).fetchone()[0]

    if slot_count == 0:

        for doctor in doctors:

            doctor_id = doctor["id"]

            conn.execute(
                """
                INSERT INTO slots
                (doctor_id, date, time, is_available)
                VALUES (?, ?, ?, ?)
                """,
                (doctor_id, "2026-09-26", "10:00 AM", 1)
            )

            conn.execute(
                """
                INSERT INTO slots
                (doctor_id, date, time, is_available)
                VALUES (?, ?, ?, ?)
                """,
                (doctor_id, "2026-09-26", "11:00 AM", 1)
            )

            conn.execute(
                """
                INSERT INTO slots
                (doctor_id, date, time, is_available)
                VALUES (?, ?, ?, ?)
                """,
                (doctor_id, "2026-09-26", "02:00 PM", 1)
            )

            conn.execute(
                """
                INSERT INTO slots
                (doctor_id, date, time, is_available)
                VALUES (?, ?, ?, ?)
                """,
                (doctor_id, "2026-09-26", "04:00 PM", 1)
            )

    conn.commit()
    conn.close()


@app.route("/")
def home():
    return redirect("/login")

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = request.form["password"]

        conn = get_db_connection()

        try:

            conn.execute(
                """
                INSERT INTO patients
                (name, email, phone, password)
                VALUES (?, ?, ?, ?)
                """,
                (name, email, phone, password)
            )

            conn.commit()
            conn.close()

            return redirect("/login")

        except sqlite3.IntegrityError:

            conn.close()
            return "Email already registered!"

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()

        patient = conn.execute(
            """
            SELECT *
            FROM patients
            WHERE email = ? AND password = ?
            """,
            (email, password)
        ).fetchone()

        conn.close()

        if patient:

            session["patient_id"] = patient["id"]
            session["patient_name"] = patient["name"]

            return redirect("/dashboard")

        return "Invalid email or password!"

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():

    if "patient_id" not in session:
        return redirect("/login")

    return render_template(
        "dashboard.html",
        name=session["patient_name"]
    )


@app.route("/doctors")
def doctors():

    if "patient_id" not in session:
        return redirect("/login")

    conn = get_db_connection()

    doctors = conn.execute(
        "SELECT * FROM doctors"
    ).fetchall()

    conn.close()

    return render_template(
        "doctors.html",
        doctors=doctors
    )


@app.route("/book/<int:doctor_id>", methods=["GET", "POST"])
def book_appointment(doctor_id):

    if "patient_id" not in session:
        return redirect("/login")

    conn = get_db_connection()

    doctor = conn.execute(
        "SELECT * FROM doctors WHERE id = ?",
        (doctor_id,)
    ).fetchone()

    if request.method == "POST":

        slot_id = request.form["slot_id"]

        slot = conn.execute(
            """
            SELECT *
            FROM slots
            WHERE id = ?
            AND doctor_id = ?
            AND is_available = 1
            """,
            (slot_id, doctor_id)
        ).fetchone()

        if slot:

            conn.execute(
                """
                INSERT INTO appointments
                (patient_id, doctor_id, slot_id, status)
                VALUES (?, ?, ?, ?)
                """,
                (
                    session["patient_id"],
                    doctor_id,
                    slot_id,
                    "Booked"
                )
            )

            conn.execute(
                """
                UPDATE slots
                SET is_available = 0
                WHERE id = ?
                """,
                (slot_id,)
            )

            conn.commit()
            conn.close()

            return redirect("/appointments")

    slots = conn.execute(
        """
        SELECT *
        FROM slots
        WHERE doctor_id = ?
        AND is_available = 1
        """,
        (doctor_id,)
    ).fetchall()

    conn.close()

    return render_template(
        "book_appointment.html",
        doctor=doctor,
        slots=slots
    )


@app.route("/appointments")
def appointments():

    if "patient_id" not in session:
        return redirect("/login")

    conn = get_db_connection()

    appointments = conn.execute(
        """
        SELECT
            appointments.id,
            doctors.name AS doctor_name,
            doctors.specialization,
            slots.date,
            slots.time,
            appointments.status
        FROM appointments
        JOIN doctors
        ON appointments.doctor_id = doctors.id
        JOIN slots
        ON appointments.slot_id = slots.id
        WHERE appointments.patient_id = ?
        """,
        (session["patient_id"],)
    ).fetchall()

    conn.close()

    return render_template(
        "appointments.html",
        appointments=appointments
    )


@app.route("/cancel/<int:appointment_id>")
def cancel_appointment(appointment_id):

    if "patient_id" not in session:
        return redirect("/login")

    conn = get_db_connection()

    appointment = conn.execute(
        """
        SELECT slot_id
        FROM appointments
        WHERE id = ?
        AND patient_id = ?
        """,
        (appointment_id, session["patient_id"])
    ).fetchone()

    if appointment:

        conn.execute(
            """
            UPDATE appointments
            SET status = 'Cancelled'
            WHERE id = ?
            """,
            (appointment_id,)
        )

        conn.execute(
            """
            UPDATE slots
            SET is_available = 1
            WHERE id = ?
            """,
            (appointment["slot_id"],)
        )

        conn.commit()

    conn.close()

    return redirect("/appointments")


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


if __name__ == "__main__":
    create_tables()
    app.run(debug=True)

