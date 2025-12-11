# Name - Mohit Mishra
# Enrollment - 0157CS231116
# Branch - CSE

import student_system
import os
import random
import datetime

current_user = ""


def load_questions(filename):
    questions = []
    if not os.path.exists(filename):
        print(f"File '{filename}' not found.")
        return questions

    f = open(filename, "r")
    block = []
    for line in f:
        if line.strip() == "":
            continue
        block.append(line.strip())
        if "ANSWER:" in line:
            questions.append(block)
            block = []
    f.close()
    return questions


def attempt_quiz(category, filename):
    student_system.load_users()

    print(f"\n--- {category} QUIZ ---")
    data = load_questions(filename)

    if not data:
        return

    random.shuffle(data)
    data = data[:5]

    score = 0
    for q in data:
        print("\n" + q[0])
        print(q[1])
        print(q[2])
        print(q[3])
        print(q[4])
        correct = q[5].split("ANSWER:")[1].strip().upper()
        ans = input("Your Answer (A/B/C/D): ").upper()
        if ans == correct:
            score += 1

    print(f"\nYour Score: {score}/5")

    time_now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    f = open("scores.txt", "a")
    f.write(f"{student_system.logged_user},{category},{score}/5,{time_now}\n")
    f.close()

    print("Score Saved.\n")


def view_my_scores():
    if not os.path.exists("scores.txt"):
        print("No score record found yet.")
        return

    print("\n--- My Score History ---\n")
    f = open("scores.txt", "r")
    found = False
    for line in f:
        data = line.strip().split(",")
        if data[0] == student_system.logged_user:
            print(f"Category: {data[1]} | Score: {data[2]} | Date: {data[3]}")
            found = True
    f.close()

    if not found:
        print("No score history yet.")


def admin_panel():
    # ensure users are loaded
    student_system.load_users()

    # safe role lookup
    if not student_system.logged:
        print("Please login first.")
        return
    if student_system.logged_user not in student_system.users:
        print("Unknown logged-in user. Please login again.")
        return

    role = student_system.users[student_system.logged_user].get("role", "user")
    if role != "admin":
        print("Admin access only.")
        return

    while True:
        print("\n--- ADMIN PANEL ---")
        print("1. View All Students")
        print("2. View All Scores")
        print("3. Generate AI Questions (Gemini -> DB)")
        print("4. Back")
        ch = input("Choose: ").strip()

        if ch == "1":
            print("\n--- Registered Students ---\n")
            for u, d in student_system.users.items():
                print(f"{d['full_name']} ({u}) - {d.get('role','user')}")
        elif ch == "2":
            if not os.path.exists("scores.txt"):
                print("No scores recorded.")
            else:
                print("\n--- Score Records ---\n")
                with open("scores.txt", "r", encoding="utf-8") as f:
                    for line in f:
                        print(line.strip())
        elif ch == "3":
            # Generate AI questions using Gemini -> DB
            try:
                cat = input("Category (DSA/DBMS/PYTHON): ").strip().upper()
                if cat == "":
                    print("No category entered. Cancelled.")
                    continue
                try:
                    n = int(input("How many questions to generate? (default 5): ").strip() or "5")
                except ValueError:
                    n = 5

                # lazy import so module only required when used
                try:
                    from ai_questions_gemini_db import generate_questions_to_db
                except Exception as e:
                    print("AI generator module not found or failed to import:", e)
                    print("Make sure ai_questions_gemini_db.py exists and google-genai is installed.")
                    continue

                preview = input("Preview generated questions before inserting? (y/N): ").strip().lower() == "y"
                if preview:
                    items = generate_questions_to_db(cat, n, preview=True)
                    if not items:
                        print("No valid questions parsed from the model.")
                        continue
                    print("\n--- Preview ---")
                    for i, it in enumerate(items, 1):
                        print(f"\nQ{i}: {it['question']}")
                        print("A.", it["options"][0])
                        print("B.", it["options"][1])
                        print("C.", it["options"][2])
                        print("D.", it["options"][3])
                        print("ANSWER:", it["answer"])
                    if input("\nInsert these into DB? (y/N): ").strip().lower() == "y":
                        added = generate_questions_to_db(cat, n, preview=False)
                        print(f"Inserted {added} question(s) into the database.")
                    else:
                        print("Cancelled. No questions inserted.")
                else:
                    added = generate_questions_to_db(cat, n, preview=False)
                    print(f"Inserted {added} question(s) into the database.")
            except Exception as e:
                print("Failed to generate AI questions:", e)
        elif ch == "4":
            break
        else:
            print("Invalid Choice.")



def quiz_menu():
    while True:
        print("\n--- QUIZ MENU ---")
        print("1. DSA")
        print("2. DBMS")
        print("3. PYTHON")
        print("4. Back")

        choice = input("Choose: ")

        if choice == "1":
            attempt_quiz("DSA", "questions_dsa.txt")
        elif choice == "2":
            attempt_quiz("DBMS", "questions_dbms.txt")
        elif choice == "3":
            attempt_quiz("PYTHON", "questions_python.txt")
        elif choice == "4":
            break
        else:
            print("Invalid Choice.")


def main():
    while True:
        print("\n===== ASSIGNMENT 3 MENU =====")
        print("1. Register (Assignment 2)")
        print("2. Login (Assignment 2)")
        print("3. Attempt Quiz")
        print("4. View My Scores")
        print("5. Show Profile")
        print("6. Update Profile")
        print("7. Admin Panel")
        print("8. Logout")
        print("9. Exit")

        ch = input("Choose an option: ")

        if ch == "1":
            student_system.register()
        elif ch == "2":
            student_system.login()
        elif ch == "3":
            if not student_system.logged:
                print("Login first.")
            else:
                quiz_menu()
        elif ch == "4":
            view_my_scores()
        elif ch == "5":
            student_system.show_profile()
        elif ch == "6":
            student_system.update_profile()
        elif ch == "7":
            admin_panel()
        elif ch == "8":
            student_system.logout()
        elif ch == "9":
            print("Program Ended.")
            break
        else:
            print("Invalid Option.")


if __name__ == "__main__":
    main()
