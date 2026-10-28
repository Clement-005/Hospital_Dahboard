"""Realistic but entirely made-up hospital data for the public demo. No real patients."""
from datetime import date, timedelta

import numpy as np
import pandas as pd

FIRST = ["Kwame", "Ama", "Kofi", "Akosua", "Yaw", "Abena", "Kwabena", "Efua", "Kojo", "Adwoa", "Kwesi", "Esi",
         "Kweku", "Afia", "Fiifi", "Yaa", "Selorm", "Dzifa", "Elikem", "Mawuli", "Abdul", "Fatima", "Ibrahim",
         "Amina", "Daniel", "Grace", "Samuel", "Mercy", "Emmanuel", "Joyce", "Prince", "Gifty", "Isaac", "Linda"]
LAST = ["Mensah", "Boateng", "Owusu", "Asante", "Osei", "Agyeman", "Amoah", "Appiah", "Darko", "Addo", "Ofori",
        "Quaye", "Tetteh", "Annan", "Ansah", "Bonsu", "Gyamfi", "Nkrumah", "Sarpong", "Frimpong", "Adjei",
        "Kumah", "Agbeko", "Dogbe", "Mahama", "Iddrisu", "Abubakar", "Yeboah", "Danquah", "Antwi"]
CONDITIONS = {  # name: (share, typical stay days, typical bill GHS)
    "Malaria": (.22, 3, 900), "Hypertension": (.15, 4, 1600), "Diabetes": (.13, 5, 2100),
    "Typhoid Fever": (.10, 5, 1300), "Pneumonia": (.09, 6, 2600), "Gastroenteritis": (.09, 2, 700),
    "Asthma": (.07, 3, 1100), "Sickle Cell Crisis": (.06, 5, 1900), "Maternity": (.09, 2, 1500),
}
MEDS = {"Malaria": "Artemether-Lumefantrine", "Hypertension": "Amlodipine", "Diabetes": "Metformin",
        "Typhoid Fever": "Ciprofloxacin", "Pneumonia": "Amoxicillin", "Gastroenteritis": "ORS and Zinc",
        "Asthma": "Salbutamol", "Sickle Cell Crisis": "Hydroxyurea", "Maternity": "Iron and Folic Acid"}
INSURERS = {"NHIS": .55, "Cash / Self-pay": .18, "Private Insurance A": .12, "Private Insurance B": .08,
            "Corporate Scheme": .07}
HOSPITALS = ["CarePoint Kumasi", "CarePoint Accra", "CarePoint Takoradi"]
DOCTORS = ["Dr. Asante", "Dr. Owusu", "Dr. Mensah", "Dr. Boateng", "Dr. Adjei", "Dr. Danquah",
           "Dr. Iddrisu", "Dr. Tetteh", "Dr. Sarpong", "Dr. Agbeko"]


def make_sample_data(n_patients=3500, n_admissions=5000, days=730, seed=26):
    rng = np.random.default_rng(seed)
    pids = [f"PT-{i:04d}" for i in range(1, n_patients + 1)]
    patients = pd.DataFrame({
        "patient_id": pids,
        "name": [f"{rng.choice(FIRST)} {rng.choice(LAST)}" for _ in pids],
        "age": rng.integers(1, 90, n_patients),
        "gender": rng.choice(["Female", "Male"], n_patients),
        "blood_type": rng.choice(["O+", "A+", "B+", "AB+", "O-", "A-", "B-", "AB-"], n_patients,
                                 p=[.45, .22, .2, .04, .04, .02, .02, .01]),
    })

    names = list(CONDITIONS)
    cond = rng.choice(names, n_admissions, p=[CONDITIONS[c][0] for c in names])
    start = date.today() - timedelta(days=days)
    offsets = np.sort((days * rng.uniform(0, 1, n_admissions) ** .8).astype(int))   # slowly rising volume
    adm_dates = [start + timedelta(days=int(o)) for o in offsets]
    stays = np.maximum(1, rng.poisson([CONDITIONS[c][1] for c in cond]))
    dis_dates = [d + timedelta(days=int(s)) for d, s in zip(adm_dates, stays)]
    today = date.today()
    dis_dates = [None if d > today else d for d in dis_dates]          # still in the ward
    aids = [f"AD-{i:04d}" for i in range(1, n_admissions + 1)]
    admissions = pd.DataFrame({
        "admission_id": aids,
        "patient_id": rng.choice(pids, n_admissions),
        "date_of_admission": adm_dates,
        "discharge_date": dis_dates,
        "admission_type": rng.choice(["Emergency", "Urgent", "Elective"], n_admissions, p=[.45, .3, .25]),
        "hospital": rng.choice(HOSPITALS, n_admissions, p=[.5, .35, .15]),
        "doctor": rng.choice(DOCTORS, n_admissions),
        "room_number": rng.integers(101, 450, n_admissions),
        "medical_condition": cond,
        "medication": [MEDS[c] for c in cond],
        "test_results": rng.choice(["Normal", "Abnormal", "Inconclusive"], n_admissions, p=[.5, .35, .15]),
    })

    base = np.array([CONDITIONS[c][2] for c in cond]) * (stays / np.array([CONDITIONS[c][1] for c in cond])) ** .5
    billings = pd.DataFrame({
        "bill_id": [f"BL-{i:04d}" for i in range(1, n_admissions + 1)],
        "admission_id": aids,
        "billing_amount": np.round(base * rng.lognormal(0, .25, n_admissions), 2),
        "insurance_provider": rng.choice(list(INSURERS), n_admissions, p=list(INSURERS.values())),
    })
    return {"patients": patients, "admissions": admissions, "billings": billings}


if __name__ == "__main__":
    for name, df in make_sample_data().items():
        print(name, df.shape)
