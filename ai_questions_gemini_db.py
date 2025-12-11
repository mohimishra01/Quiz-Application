# ai_questions_gemini_db.py
# Generate MCQs via Google Gemini (GenAI) and insert directly into SQLite app.db (questions table).
# Requires: pip install google-genai
# Set env var: GEMINI_API_KEY (your key from Google AI Studio)

import os, json, re, sqlite3, time
from google import genai   # pip install google-genai
import student_system

DB_PATH = "app.db"
MODEL = "gemini-2.5-flash"   # change if needed

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    """Create DB and questions table if not present."""
    with get_conn() as conn:
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

def build_prompt(category: str, n: int):
    return (
        f'You are an expert college instructor. Produce exactly {n} distinct multiple-choice questions '
        f'for the category \"{category}\".\n\n'
        "Return a single valid JSON array. Each item must be an object with keys:\n"
        '  "question": string,\n'
        '  "options": array of 4 strings (order = [A,B,C,D]),\n'
        '  "answer": one of "A","B","C","D"\n\n'
        "Do NOT include explanations or extra text. Output valid JSON only (no markdown)."
    )

def call_gemini(prompt: str, temperature: float = 0.2):
    """
    Call Google GenAI (Gemini) using google-genai SDK (v1.55.0 compatible).
    Returns the assistant text (string).
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set in environment")

    client = genai.Client(api_key=api_key)

    # Preferred call pattern for google-genai SDK: models.generate_content
    try:
        # Many SDK examples accept a simple string for `contents`.
        # In some cases `contents` can be a list of blocks/dicts; using string should work.
        resp = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            temperature=temperature
        )
    except TypeError:
        # some SDK builds might not accept 'temperature' as kwarg here; retry without it
        resp = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )
    except Exception as e:
        # If generate_content fails, try a couple of older method names as fallback
        # (keep these attempts, but primary path is generate_content)
        last_exc = e
        try:
            if hasattr(client, "generate_text"):
                resp = client.generate_text(model=MODEL, input=prompt, temperature=temperature)
            elif hasattr(client, "generate"):
                resp = client.generate(model=MODEL, prompt=prompt, temperature=temperature)
            else:
                raise last_exc
        except Exception as e2:
            # raise a clear error with underlying exceptions for debugging
            raise RuntimeError(
                "Failed to call Gemini API using generate_content / generate_text / generate.\n"
                f"generate_content error: {repr(last_exc)}\n"
                f"fallback error: {repr(e2)}\n"
                "Try `pip install -U google-genai` to upgrade the SDK."
            ) from e2

    # Try several ways to extract textual content from the response object
    # 1) resp.text
    if hasattr(resp, "text") and resp.text:
        return resp.text

    # 2) resp.output -> list of blocks (common in some SDK responses)
    try:
        out = getattr(resp, "output", None)
        if out:
            # output may be list of items where each item has .content, which is list of dicts
            # try to traverse common shapes
            if isinstance(out, (list, tuple)) and len(out) > 0:
                first = out[0]
                # first may have .content which is list of dicts with 'text' or 'type' keys
                if hasattr(first, "content"):
                    content = first.content
                    if isinstance(content, (list, tuple)) and len(content) > 0:
                        # look for text fields
                        cand = content[0]
                        # try multiple attribute/key accesses
                        if hasattr(cand, "text"):
                            return cand.text
                        if isinstance(cand, dict) and "text" in cand:
                            return cand["text"]
                        if isinstance(cand, dict) and "value" in cand:
                            return cand["value"]
                # sometimes first has .text
                if hasattr(first, "text"):
                    return first.text
    except Exception:
        pass

    # 3) resp.candidates (older shape)
    try:
        cands = getattr(resp, "candidates", None)
        if cands and len(cands) > 0:
            first = cands[0]
            if hasattr(first, "text") and first.text:
                return first.text
            # maybe first has .content
            if hasattr(first, "content"):
                content = first.content
                if isinstance(content, (list, tuple)) and len(content) > 0:
                    cand = content[0]
                    if hasattr(cand, "text"):
                        return cand.text
                    if isinstance(cand, dict) and "text" in cand:
                        return cand["text"]
    except Exception:
        pass

    # 4) resp.data or resp.response or str(resp)
    try:
        # Some SDK variants return a nested dict-like structure accessible via .__dict__ or by str()
        # Try to stringify, and attempt to pull out a JSON-like substring
        s = str(resp)
        # If s is long, attempt to extract first JSON array or object (best-effort)
        import re, json
        m = re.search(r'(\{.*\})', s, flags=re.S)
        if m:
            candidate = m.group(1)
            try:
                obj = json.loads(candidate)
                # try common keys
                for key in ("text", "output", "candidates", "content"):
                    if key in obj:
                        return str(obj[key])
            except Exception:
                pass
        # fallback to returning the str(resp) if nothing else
        return s
    except Exception:
        pass

    # If we reach here, extraction failed — raise useful debugging info
    raise RuntimeError(f"Could not extract text from Gemini response. Raw response repr: {repr(resp)}")



def parse_json_from_text(text: str):
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"(\[.*\])", text, flags=re.S)
        if not m:
            raise RuntimeError("Couldn't parse JSON from Gemini response.\nResponse:\n" + text)
        return json.loads(m.group(1))

def insert_question_db(category: str, qtext: str, opts: list, answer: str, conn=None):
    """
    Delegate insertion to student_system.insert_question_with_dup_check.
    Returns True if inserted, False if skipped.
    """
    # Normalize inputs
    if not isinstance(opts, list) or len(opts) != 4:
        return False
    answer = (answer or "").strip().upper()
    if answer not in ("A","B","C","D"):
        return False

    # Ensure student_system has questions table and helpers ready
    try:
        student_system.init_questions_table()
    except Exception:
        # if student_system doesn't yet have init_questions_table, fall back to direct insert
        pass

    try:
        # use student_system insertion (adds 'source' and fuzzy-dup check)
        return student_system.insert_question_with_dup_check(category, qtext, opts, answer, source="gemini", threshold=0.82)
    except AttributeError:
        # student_system missing helper: fallback to file-local insert
        close = False
        if conn is None:
            conn = get_conn()
            close = True
        try:
            cur = conn.cursor()
            cur.execute("SELECT id FROM questions WHERE qtext = ? AND category = ?", (qtext, category))
            if cur.fetchone():
                return False
            cur.execute(
                "INSERT INTO questions (category, qtext, opt_a, opt_b, opt_c, opt_d, answer) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (category, qtext, opts[0].strip(), opts[1].strip(), opts[2].strip(), opts[3].strip(), answer)
            )
            conn.commit()
            return True
        finally:
            if close:
                conn.close()


def generate_questions_to_db(category: str, n: int = 5, preview: bool = False, sleep_after: float = 0.5):
    """
    Generate `n` questions for `category` using Gemini and insert into app.db.
    If preview=True, returns parsed questions list without inserting.
    Returns number of inserted questions when preview=False.
    """
    # make sure the questions table and columns exist (student_system helper)
    try:
        student_system.init_questions_table()
    except Exception:
        # fallback: if student_system isn't available for some reason, ignore and proceed
        pass

    prompt = build_prompt(category, n)
    raw = call_gemini(prompt)
    parsed = parse_json_from_text(raw)
    if not isinstance(parsed, list):
        raise RuntimeError("Gemini did not return a JSON array.")

    # normalize and validate model output
    normalized = []
    for item in parsed:
        q = item.get("question") or item.get("q") or ""
        opts = item.get("options") or item.get("opts") or []
        ans = (item.get("answer") or item.get("ans") or "").strip().upper()
        if not q or not isinstance(opts, list) or len(opts) != 4 or ans not in ("A", "B", "C", "D"):
            continue
        normalized.append({"question": q.strip(), "options": opts, "answer": ans})

    # preview mode: return parsed items without inserting
    if preview:
        return normalized

    # insert using student_system helper (which does fuzzy duplicate check)
    inserted = 0
    skipped = 0
    for it in normalized:
        try:
            ok = student_system.insert_question_with_dup_check(
                category=category,
                qtext=it["question"],
                opts=it["options"],
                answer=it["answer"],
                source="gemini",
                threshold=0.82
            )
            if ok:
                inserted += 1
            else:
                skipped += 1
        except Exception:
            # if anything goes wrong with the helper, count as skipped
            skipped += 1

    # small pause to respect rate limits
    time.sleep(sleep_after)

    # you can return a tuple if you want both counts, but keep compatibility by returning inserted
    # return inserted, skipped
    return inserted

# CLI quick-run
if __name__ == "__main__":
    cat = input("Category (DSA/DBMS/PYTHON): ").strip().upper()
    try:
        n = int(input("How many questions to generate? (default 5): ").strip() or "5")
    except ValueError:
        n = 5
    if input("Preview before inserting? (y/N): ").strip().lower() == "y":
        items = generate_questions_to_db(cat, n, preview=True)
        print("Preview:")
        for i, it in enumerate(items, 1):
            print(f"\nQ{i}: {it['question']}")
            print("A.", it["options"][0])
            print("B.", it["options"][1])
            print("C.", it["options"][2])
            print("D.", it["options"][3])
            print("ANSWER:", it["answer"])
        if input("\nInsert these? (y/N): ").strip().lower() == "y":
            added = generate_questions_to_db(cat, n, preview=False)
            print(f"Inserted {added} questions.")
        else:
            print("Cancelled.")
    else:
        added = generate_questions_to_db(cat, n, preview=False)
        print(f"Inserted {added} questions.")
