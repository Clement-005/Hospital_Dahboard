"""Make a new staff account (or a new password) for the hospital app.

Run:  python create_user.py
It prints an SQL line. Copy it into MySQL Workbench (logged in as root) and run it.
"""
from getpass import getpass
import bcrypt

ROLES = ["front_desk", "doctor", "billing", "admin"]

username = input("Username: ").strip()
full_name = input("Full name: ").strip()
role = ""
while role not in ROLES:
    role = input(f"Role {ROLES}: ").strip()
pw = getpass("Password (hidden): ")
if pw != getpass("Repeat password: "):
    raise SystemExit("Passwords do not match.")
if len(pw) < 8:
    raise SystemExit("Use at least 8 characters.")

h = bcrypt.hashpw(pw.encode(), bcrypt.gensalt(rounds=12)).decode()
print("\nNew user, run this in Workbench:")
print(f"INSERT INTO app_users (username, full_name, password_hash, role) "
      f"VALUES ('{username}', '{full_name}', '{h}', '{role}');")
print("\nOr, to change an existing user's password:")
print(f"UPDATE app_users SET password_hash = '{h}' WHERE username = '{username}';")
