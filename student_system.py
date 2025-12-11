# Name - Mohit Mishra
# Enrollment - 0157CS231116
# Branch - CSE

import os
import sqlite3
import datetime
import difflib
from typing import List

logged_user = ""
logged = False

users = {}   # to store user data in memory (useful for Assignment 3)


def load_users():
    global users
    if not os.path.exists("students.txt"):
        return
    with open("students.txt", "r") as f:
        for line in f:
            data = line.strip().split(",")
            if len(data) >= 12:
                users[data[1]] = {
                    "full_name": data[0],
                    "password": data[2],
                    "college": data[3],
                    "enrollment_no": data[4],
                    "course": data[5],
                    "email": data[6],
                    "phone": data[7],
                    "dob": data[8],
                    "gender": data[9],
                    "guardian_name": data[10],
                    "role": data[11]
                }


def save_user(user_data):
    with open("students.txt", "a") as f:
        f.write(",".join(user_data) + "\n")


def register():
    print("\nCreate a new account.")
    username = input("Enter username: ")

    load_users()
    if username in users:
        print("Username already exists. Try another.")
        return

    full_name = input("Enter Full Name: ")
    password = input("Create Password: ")
    college = input("Enter College/Institute: ")
    enrollment_no = input("Enter Enrollment Number: ")
    course = input("Enter Course: ")
    email = input("Enter Email: ")
    phone = input("Enter Phone Number: ")
    dob = input("Enter Date of Birth (DD-MM-YYYY): ")
    gender = input("Gender: ")
    guardian_name = input("Guardian's Name: ")

    print("\nAre you registering as Admin or Student?")
    print("1. Student (Default)")
    print("2. Admin (Requires Secret Key)")
    role_choice = input("Choose 1 or 2: ")

    if role_choice == "2":
        key = input("Enter Admin Secret Key: ")
        if key == "admin@123":
            role = "admin"
            print("Admin account created ")
        else:
            print("Incorrect key. Creating normal student account.")
            role = "user"
    else:
        role = "user"

    user_data = [
        full_name, username, password, college, enrollment_no, course,
        email, phone, dob, gender, guardian_name, role
    ]

    save_user(user_data)
    print("\nSuccessfully Registered.\n")


def login():
    global logged, logged_user
    print("\nLog in:")
    username = input("Username: ")
    password = input("Password: ")

    load_users()

    if username in users and users[username]["password"] == password:
        logged = True
        logged_user = username
        print("\nLogin Successful.\n")
    else:
        print("\nIncorrect Username or Password.\n")


def show_profile():
    if not logged:
        print("Please login first.")
        return

    load_users()
    data = users[logged_user]

    print("\n--- Your Profile ---")
    print("Full Name:", data["full_name"])
    print("Username:", logged_user)
    print("Enrollment No:", data["enrollment_no"])
    print("Course:", data["course"])
    print("Email:", data["email"])
    print("Phone:", data["phone"])
    print("Date of Birth:", data["dob"])
    print("Gender:", data["gender"])
    print("Guardian Name:", data["guardian_name"])
    print("Role:", data["role"])


def update_profile():
    if not logged:
        print("Please login first.")
        return

    field_list = {
        "1": ("Full Name", "full_name"),
        "2": ("Password", "password"),
        "3": ("Course", "course"),
        "4": ("Email", "email"),
        "5": ("Phone", "phone"),
        "6": ("Date of Birth", "dob"),
        "7": ("Guardian Name", "guardian_name")
    }

    print("\n--- Update Profile ---")
    for key, val in field_list.items():
        print(key + ".", val[0])

    choice = input("Choose a field to update: ")

    if choice not in field_list:
        print("Invalid Option")
        return

    new_value = input("Enter new value: ")

    load_users()
    users[logged_user][field_list[choice][1]] = new_value

    with open("students.txt", "w") as f:
        for u, d in users.items():
            f.write(",".join([
                d["full_name"], u, d["password"], d["college"],
                d["enrollment_no"], d["course"], d["email"], d["phone"],
                d["dob"], d["gender"], d["guardian_name"], d["role"]
            ]) + "\n")

    print("\nProfile Updated.\n")


def logout():
    global logged, logged_user
    logged = False
    logged_user = ""
    print("\nLogged out.\n")


def terminate():
    print("Program Ended.")
    exit()


def main():
    while True:
        print("\n--- Student System (Assignment 2) ---")
        print("1. Register")
        print("2. Login")
        print("3. Show Profile")
        print("4. Update Profile")
        print("5. Logout")
        print("6. Exit")

        choice = input("Choose an option: ")

        if choice == "1":
            register()
        elif choice == "2":
            login()
        elif choice == "3":
            show_profile()
        elif choice == "4":
            update_profile()
        elif choice == "5":
            logout()
        elif choice == "6":
            terminate()
        else:
            print("Invalid Option")




# --- begin: question DB utilities  ---

DEFAULT_DB_PATH = "app.db"

def init_questions_table(db_path: str = DEFAULT_DB_PATH):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            qtext TEXT,
            opt_a TEXT,
            opt_b TEXT,
            opt_c TEXT,
            opt_d TEXT,
            answer TEXT
        )
    """)
    conn.commit()

    cur.execute("PRAGMA table_info(questions)")
    cols = [r[1] for r in cur.fetchall()]
    if "source" not in cols:
        cur.execute("ALTER TABLE questions ADD COLUMN source TEXT")
    if "created_at" not in cols:
        cur.execute("ALTER TABLE questions ADD COLUMN created_at TEXT")
    conn.commit()
    conn.close()

def _normalize_text(s: str) -> str:
    return " ".join(s.lower().strip().split())

def question_similar_exists(qtext: str, category: str, threshold: float = 0.8, db_path: str = DEFAULT_DB_PATH) -> bool:
    init_questions_table(db_path)
    q_norm = _normalize_text(qtext)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT qtext FROM questions WHERE category = ?", (category,))
    rows = cur.fetchall()
    conn.close()
    for (existing,) in rows:
        if not existing:
            continue
        existing_norm = _normalize_text(existing)
        ratio = difflib.SequenceMatcher(None, q_norm, existing_norm).ratio()
        if ratio >= threshold:
            return True
    return False

def insert_question_with_dup_check(category: str, qtext: str, opts: List[str], answer: str,
                                   source: str = "manual", threshold: float = 0.8,
                                   db_path: str = DEFAULT_DB_PATH) -> bool:
    if not isinstance(opts, list) or len(opts) != 4:
        return False
    answer = (answer or "").strip().upper()
    if answer not in ("A", "B", "C", "D"):
        return False

    init_questions_table(db_path)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT id FROM questions WHERE qtext = ? AND category = ?", (qtext, category))
    if cur.fetchone():
        conn.close()
        return False

    if question_similar_exists(qtext, category, threshold=threshold, db_path=db_path):
        conn.close()
        return False

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("""
        INSERT INTO questions (category, qtext, opt_a, opt_b, opt_c, opt_d, answer, source, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (category, qtext, opts[0].strip(), opts[1].strip(), opts[2].strip(), opts[3].strip(), answer, source, now))
    conn.commit()
    conn.close()
    return True

def list_questions(category: str = None, limit: int = 20, db_path: str = DEFAULT_DB_PATH):
    init_questions_table(db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    if category:
        cur.execute("SELECT qtext, opt_a, opt_b, opt_c, opt_d, answer, source, created_at FROM questions WHERE category = ? ORDER BY id DESC LIMIT ?", (category, limit))
    else:
        cur.execute("SELECT category, qtext, opt_a, opt_b, opt_c, opt_d, answer, source, created_at FROM questions ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows
# --- end: question DB utilities ---

if __name__ == "__main__":
    main()