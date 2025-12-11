LLM-Powered Quiz Generation & Student Management System

A Python-based quiz and student management platform enhanced with Generative AI (Google Gemini LLM) to automatically generate high-quality MCQs.
The system supports user registration, login, quiz attempts, scoring, admin controls, and an AI-driven question bank stored using SQLite (SQL).

Features:-

AI / LLM Features:-
Uses Google Gemini (Generative AI) to generate MCQs.
Automatically formats, validates, and normalizes questions.
Prevents duplicates using fuzzy similarity detection.
Stores generated MCQs in an SQLite SQL database (app.db).

Student Features:-
Register & login securely
View & update profile
Take quizzes
Automatic scoring
Score history stored in scores.txt

Admin Features:-
View all students
View all scores
Generate AI-powered MCQs for DSA, DBMS, Python
Insert questions directly into SQL database
Maintain question bank via LLM


| Component            | Technology                        |
| -------------------- | --------------------------------- |
| Programming Language | Python                            |
| Generative AI        | Google Gemini (LLM)               |
| Database             | SQLite (SQL)                      |
| Authentication       | Custom Python login system        |
| Storage              | Text files + Database integration |
