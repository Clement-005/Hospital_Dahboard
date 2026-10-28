import bcrypt
import pandas as pd
import streamlit as st
from datetime import date
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool
from pathlib import Path

from dashboard import show_dashboard, DASHBOARD_SQL

st.set_page_config(page_title="Hospital Management System (Demo)", page_icon="🏥", layout="wide")


# =============================================================== Demo data layer
# The live system runs on MySQL. This public demo loads the same tables from CSV files
# into a private in-memory database for each visitor, so nothing anyone does is saved.

DATA_DIR = Path(__file__).parent / "data"

DEMO_USERS = [  # username, full name, bcrypt hash, role   (passwords are shown on the sign-in page)
    ("admin",     "System Administrator", "$2b$12$Fb7w60zrJxasaXEmuXm6rug64FgtY5r1qFFCxvBKbgqz3RPSmyQkq", "admin"),
    ("frontdesk", "Front Desk Officer",   "$2b$12$zad8hQdlPBXqwlGRw2i30OCmuMyWbYUguU7DUNPh1CgPt8rMvWoFq", "front_desk"),
    ("drmensah",  "Dr. Mensah",           "$2b$12$OyapILz/8fg31az71Z8RW.82tE9opyZskfgPhNT/2u9GGdWveviwK", "doctor"),
    ("billing1",  "Billing Officer",      "$2b$12$5WYSUBVWj0wnlRGSND59ROUNRuxFPUmOZeXVq3X4UktEamVLYRNNO", "billing"),
]


@st.cache_data(show_spinner="Loading sample data...")
def base_tables():
    """Read data/*.csv if present, otherwise generate realistic sample data."""
    files = {t: DATA_DIR / f"{t}.csv" for t in ("patients", "admissions", "billings")}
    if all(f.exists() for f in files.values()):
        return {t: pd.read_csv(f) for t, f in files.items()}
    from sample_data import make_sample_data
    return make_sample_data()


def get_engine():
    """One private in-memory database per visitor session."""
    if "engine" not in st.session_state:
        eng = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
        for name, df in base_tables().items():
            df.to_sql(name, eng, index=False)
        with eng.begin() as conn:
            conn.execute(text("""CREATE TABLE app_users (user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE, full_name TEXT, password_hash TEXT, role TEXT, is_active INTEGER DEFAULT 1)"""))
            for u, n, h, r in DEMO_USERS:
                conn.execute(text("INSERT INTO app_users (username, full_name, password_hash, role) "
                                  "VALUES (:u, :n, :h, :r)"), dict(u=u, n=n, h=h, r=r))
            conn.execute(text("""CREATE TABLE audit_log (log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER, username TEXT, action TEXT, table_name TEXT, record_id TEXT,
                details TEXT, logged_at TEXT DEFAULT CURRENT_TIMESTAMP)"""))
        st.session_state.engine = eng
    return st.session_state.engine


engine = get_engine()


def query(sql, params=None):
    return pd.read_sql(text(sql), engine, params=params)


def next_id(conn, table, column, prefix):
    """Next ID in the PT-01 / AD-01 / BL-01 style."""
    n = conn.execute(text(
        f"SELECT MAX(CAST(SUBSTRING({column}, {len(prefix) + 1}) AS UNSIGNED)) FROM {table}"
    )).scalar()
    n = 0 if n is None else int(n)
    return f"{prefix}{n + 1:02d}"


# =============================================================== Audit log (step 11)

def log_action(action, table_name=None, record_id=None, details=None):
    """Write one row to audit_log. Never let a logging problem crash the app."""
    user = st.session_state.get("user")
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO audit_log (user_id, username, action, table_name, record_id, details)
                VALUES (:uid, :uname, :action, :tbl, :rid, :details)
            """), dict(uid=user["id"] if user else None,
                       uname=user["username"] if user else None,
                       action=action, tbl=table_name,
                       rid=None if record_id is None else str(record_id),
                       details=None if details is None else str(details)[:255]))
    except Exception as e:
        st.toast(f"Audit log not written: {getattr(e, 'orig', e)}")


# =============================================================== Login and roles (step 10)

ROLE_PAGES = {
    "front_desk": ["Find Patient", "Register Patient"],
    "doctor":     ["Find Patient"],
    "billing":    ["Dashboard", "Find Patient"],
    "admin":      ["Dashboard", "Find Patient", "Register Patient", "Audit Log"],
}
ROLE_LABELS = {"front_desk": "Front Desk", "doctor": "Doctor", "billing": "Billing", "admin": "Administrator"}

# Which admission/billing columns each role may see in Find Patient
HISTORY_COLUMNS = {
    "front_desk": ["admission_id", "date_of_admission", "discharge_date", "admission_type",
                   "hospital", "doctor", "room_number"],
    "doctor":     ["admission_id", "date_of_admission", "discharge_date", "admission_type",
                   "hospital", "doctor", "room_number", "medical_condition", "medication", "test_results"],
    "billing":    ["admission_id", "date_of_admission", "discharge_date", "admission_type",
                   "hospital", "medical_condition", "billing_amount", "insurance_provider"],
    "admin":      None,   # everything
}


def login_page():
    st.markdown("<div style='height:6vh'></div>", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 1.1, 1])
    with mid:
        st.markdown("## Hospital System")
        st.caption("Staff sign in · public demo with sample data")
        with st.form("login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            ok = st.form_submit_button("Sign in", type="primary", use_container_width=True)
        if ok:
            with engine.connect() as conn:
                row = conn.execute(text("""
                    SELECT user_id, username, full_name, password_hash, role
                    FROM app_users WHERE username = :u AND is_active = 1
                """), {"u": username.strip()}).fetchone()
            if row and bcrypt.checkpw(password.encode(), row.password_hash.encode()):
                st.session_state.user = {"id": row.user_id, "username": row.username,
                                         "full_name": row.full_name or row.username, "role": row.role}
                log_action("LOGIN")
                st.rerun()
            else:
                log_action("LOGIN_FAILED", details=f"username={username.strip()[:50]}")
                st.error("Wrong username or password.")
        st.info("**Demo accounts**, each role sees different pages and fields:\n\n"
                "| Username | Password | Role |\n|---|---|---|\n"
                "| admin | Admin@2026! | Administrator |\n"
                "| frontdesk | Front@2026! | Front Desk |\n"
                "| drmensah | Doctor@2026! | Doctor |\n"
                "| billing1 | Billing@2026! | Billing |")
        st.caption("Anything you add is kept only for your visit and disappears when you close the page.")


if "user" not in st.session_state:
    login_page()
    st.stop()

user = st.session_state.user
role = user["role"]

st.sidebar.caption("🧪 Demo: sample data, changes are not saved.")
with st.sidebar:
    st.markdown(f"**{user['full_name']}**  \n{ROLE_LABELS.get(role, role)}")
    page = st.radio("Menu", ROLE_PAGES.get(role, []))
    st.divider()
    if st.button("Refresh data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    if st.button("Sign out", use_container_width=True):
        log_action("LOGOUT")
        st.session_state.clear()
        st.rerun()

# =============================================================== Dashboard

if page == "Dashboard":
    if not st.session_state.get("dashboard_logged"):     # once per session, not on every click
        log_action("VIEW", "dashboard")
        st.session_state.dashboard_logged = True
    show_dashboard(df=pd.read_sql(text(DASHBOARD_SQL), engine))


# =============================================================== Find Patient

elif page == "Find Patient":
    st.title("Find Patient")
    q = st.text_input("Search by name or patient ID").strip()

    if q:
        if len(q) < 2:
            st.warning("Type at least 2 characters.")
            st.stop()
        found = query(
            "SELECT patient_id, name, age, gender, blood_type FROM patients "
            "WHERE name LIKE :q OR patient_id LIKE :q ORDER BY name LIMIT 50",
            {"q": f"%{q}%"},
        )
        st.write(f"{len(found)} patient(s) found")
        st.dataframe(found, use_container_width=True, hide_index=True)

        if not found.empty:
            pid = st.selectbox("View history for", found["patient_id"],
                               format_func=lambda p: f"{p}  ·  {found.loc[found.patient_id == p, 'name'].iloc[0]}")
            history = query("""
                SELECT a.admission_id, a.date_of_admission, a.discharge_date, a.admission_type,
                       a.hospital, a.doctor, a.room_number,
                       a.medical_condition, a.medication, a.test_results,
                       b.billing_amount, b.insurance_provider
                FROM admissions a
                LEFT JOIN billings b ON b.admission_id = a.admission_id
                WHERE a.patient_id = :pid
                ORDER BY a.date_of_admission DESC
            """, {"pid": pid})
            cols = HISTORY_COLUMNS.get(role)
            if cols is not None:
                history = history[[c for c in cols if c in history.columns]]

            # log each patient view once per session, not on every rerun
            viewed = st.session_state.setdefault("viewed", set())
            if pid not in viewed:
                log_action("VIEW", "patients", pid)
                viewed.add(pid)

            st.subheader(f"Admissions for {pid}")
            st.dataframe(history, use_container_width=True, hide_index=True)


# =============================================================== Register Patient (step 9)

elif page == "Register Patient":
    st.title("Register Patient and Admission")
    st.caption("Fields marked * are required.")

    OTHER = "Other (type new)"

    def options(sql):
        return [v for v in pd.read_sql(text(sql), engine).iloc[:, 0].dropna().astype(str) if v.strip()]

    conditions = options("SELECT DISTINCT medical_condition FROM admissions ORDER BY 1")
    insurers = options("SELECT DISTINCT insurance_provider FROM billings ORDER BY 1")
    medications = options("SELECT DISTINCT medication FROM admissions ORDER BY 1")

    # a counter in the widget keys lets us clear the form after a successful save
    k = st.session_state.setdefault("form_n", 0)

    def pick(col, label, opts, key):
        choice = col.selectbox(label, opts + [OTHER], index=None, placeholder="Select...", key=f"{key}{k}")
        if choice == OTHER:
            return col.text_input(f"Type the new {label.rstrip(' *').lower()}", key=f"{key}_new{k}").strip().title()
        return choice or ""

    st.subheader("Patient")
    name = st.text_input("Full name *", key=f"name{k}").strip()
    c1, c2, c3 = st.columns(3)
    age = c1.number_input("Age *", min_value=0, max_value=120, value=None, step=1, key=f"age{k}")
    gender = c2.selectbox("Gender *", ["Female", "Male"], index=None, placeholder="Select...", key=f"gender{k}")
    blood = c3.selectbox("Blood type *", ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
                         index=None, placeholder="Select...", key=f"blood{k}")

    st.subheader("Admission")
    d1, d2, d3 = st.columns(3)
    admitted = d1.date_input("Date of admission *", value=date.today(), max_value=date.today(),
                             format="DD/MM/YYYY", key=f"adm{k}")
    still_in = d3.checkbox("Still admitted (no discharge date yet)", key=f"still{k}")
    discharged = None if still_in else d2.date_input("Discharge date *", value=date.today(),
                                                     format="DD/MM/YYYY", key=f"dis{k}")
    e1, e2, e3 = st.columns(3)
    adm_type = e1.selectbox("Admission type *", ["Emergency", "Elective", "Urgent"],
                            index=None, placeholder="Select...", key=f"type{k}")
    doctor = e2.text_input("Doctor *", key=f"doc{k}").strip()
    room = e3.number_input("Room number *", min_value=1, max_value=999, value=None, step=1, key=f"room{k}")
    h1, h2 = st.columns(2)
    hospital = h1.text_input("Hospital *", key=f"hosp{k}").strip()
    condition = pick(h2, "Medical condition *", conditions, "cond")
    m1, m2 = st.columns(2)
    medication = pick(m1, "Medication", medications, "med")
    result = m2.selectbox("Test results", ["Normal", "Abnormal", "Inconclusive", "Pending"],
                          index=3, key=f"res{k}")

    st.subheader("Billing")
    f1, f2 = st.columns(2)
    amount = f1.number_input("Billing amount *", min_value=0.0, max_value=10_000_000.0,
                             value=None, step=100.0, format="%.2f", key=f"amt{k}")
    insurer = pick(f2, "Insurance provider *", insurers, "ins")

    if st.button("Save patient", type="primary"):
        errors = []
        if len(name) < 3 or not any(ch.isalpha() for ch in name):
            errors.append("Enter the patient's full name (at least 3 letters).")
        if any(ch.isdigit() for ch in name):
            errors.append("Name should not contain numbers.")
        required = {"Age": age, "Gender": gender, "Blood type": blood, "Admission type": adm_type,
                    "Doctor": doctor, "Room number": room, "Hospital": hospital,
                    "Medical condition": condition, "Billing amount": amount, "Insurance provider": insurer}
        missing = [label for label, v in required.items() if v is None or v == ""]
        if missing:
            errors.append("Please fill in: " + ", ".join(missing) + ".")
        if amount is not None and amount <= 0:
            errors.append("Billing amount must be more than 0.")
        if discharged is not None and discharged < admitted:
            errors.append("Discharge date cannot be before the admission date.")

        if errors:
            for e in errors:
                st.error(e)
        else:
            try:
                with engine.begin() as conn:
                    pid = next_id(conn, "patients", "patient_id", "PT-")
                    aid = next_id(conn, "admissions", "admission_id", "AD-")
                    bid = next_id(conn, "billings", "bill_id", "BL-")
                    conn.execute(text("""
                        INSERT INTO patients (patient_id, name, age, gender, blood_type)
                        VALUES (:pid, :name, :age, :gender, :blood)
                    """), dict(pid=pid, name=name.title(), age=int(age), gender=gender, blood=blood))
                    conn.execute(text("""
                        INSERT INTO admissions
                            (admission_id, patient_id, date_of_admission, discharge_date,
                             admission_type, hospital, doctor, room_number,
                             medical_condition, medication, test_results)
                        VALUES (:aid, :pid, :d1, :d2, :t, :h, :doc, :room, :cond, :med, :res)
                    """), dict(aid=aid, pid=pid, d1=admitted, d2=discharged, t=adm_type,
                               h=hospital.title(), doc=doctor.title(), room=int(room),
                               cond=condition, med=(medication or None), res=result))
                    conn.execute(text("""
                        INSERT INTO billings (bill_id, admission_id, billing_amount, insurance_provider)
                        VALUES (:bid, :aid, :amt, :ins)
                    """), dict(bid=bid, aid=aid, amt=round(float(amount), 2), ins=insurer))
                log_action("INSERT", "patients", pid, f"admission {aid}, bill {bid}")
                st.cache_data.clear()
                st.session_state.form_n += 1          # clears the form
                st.session_state.saved_msg = f"Saved. Patient {pid}, admission {aid}, bill {bid}."
                st.rerun()
            except Exception as e:
                st.error(f"Could not save: {getattr(e, 'orig', e)}")

    if "saved_msg" in st.session_state:
        st.success(st.session_state.pop("saved_msg"))


# =============================================================== Audit Log (admin only)

elif page == "Audit Log":
    st.title("Audit Log")
    st.caption("Who signed in, viewed or added records, and when.")
    c1, c2, c3 = st.columns(3)
    who = c1.text_input("Username contains").strip()
    action = c2.selectbox("Action", ["All", "LOGIN", "LOGIN_FAILED", "LOGOUT", "VIEW", "INSERT"])
    limit = c3.selectbox("Show last", [100, 500, 2000])
    sql = "SELECT logged_at, username, action, table_name, record_id, details FROM audit_log WHERE 1=1"
    params = {}
    if who:
        sql += " AND username LIKE :who"
        params["who"] = f"%{who}%"
    if action != "All":
        sql += " AND action = :action"
        params["action"] = action
    sql += f" ORDER BY logged_at DESC LIMIT {int(limit)}"
    log = pd.read_sql(text(sql), engine, params=params)   # not cached: always current
    st.dataframe(log, use_container_width=True, hide_index=True)
