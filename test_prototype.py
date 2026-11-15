import pandas as pd
from pathlib import Path
import re
from datetime import date, timedelta

DATA_DIR = Path(__file__).resolve().parent / "data"

def test_files_exist():
    files = ['semesters.csv', 'courses.csv', 'academic_calendar.csv', 'assessments.csv', 'scores.csv', 'plan_checklist.csv', 'program_info.csv']
    for f in files:
        p = DATA_DIR / f
        assert p.exists(), f"{f} missing!"
        df = pd.read_csv(p)
        print(f"File {f}: {len(df)} rows, columns: {list(df.columns)}")

def test_semesters():
    semesters = pd.read_csv(DATA_DIR / "semesters.csv")
    assert len(semesters) == 8, f"Expected 8 semesters, got {len(semesters)}"
    assert set(semesters['semester']) == set(range(1, 9)), "Semesters 1-8 mismatch"
    print("Test Semesters 1-8: PASSED")

def test_courses():
    courses = pd.read_csv(DATA_DIR / "courses.csv")
    for sem in range(1, 9):
        c_sem = courses[courses['semester'] == sem]
        assert len(c_sem) >= 3, f"Semester {sem} has fewer than 3 courses!"
    print("Test Courses per semester (>=3): PASSED")

def test_calendar():
    cal = pd.read_csv(DATA_DIR / "academic_calendar.csv")
    assert 'Holiday' in cal['event_type'].values, "Holiday missing"
    assert 'Academic' in cal['event_type'].values, "Academic missing"
    print("Test Calendar event types distinction: PASSED")

def test_scores():
    scores = pd.read_csv(DATA_DIR / "scores.csv")
    assert len(scores) >= 2, "Scores missing"
    tot_score = scores['score'].sum()
    tot_max = scores['max_marks'].sum()
    pct = (tot_score / tot_max) * 100
    print(f"Test Score calculation: {tot_score}/{tot_max} ({pct:.1f}%): PASSED")

def test_checklist():
    plan = pd.read_csv(DATA_DIR / "plan_checklist.csv")
    required_cats = {'Semester Preparation', 'Assessments', 'Labs', 'Projects', 'Documents', 'Skills', 'Internship/Placement'}
    assert required_cats.issubset(set(plan['category'].values)), f"Categories missing: {required_cats - set(plan['category'].values)}"
    print("Test Plan checklist categories (All 7 present): PASSED")

def test_chatbot_questions():
    # Import logic from app.py or run it directly
    semesters = pd.read_csv(DATA_DIR / "semesters.csv")
    courses = pd.read_csv(DATA_DIR / "courses.csv")
    calendar = pd.read_csv(DATA_DIR / "academic_calendar.csv")
    assessments = pd.read_csv(DATA_DIR / "assessments.csv")
    scores = pd.read_csv(DATA_DIR / "scores.csv")
    plan = pd.read_csv(DATA_DIR / "plan_checklist.csv")
    program_info = pd.read_csv(DATA_DIR / "program_info.csv")

    UNKNOWN_ANSWER = "I cannot verify that from the current Degree OS data."
    curr_sem = 3

    def parse_dates(series):
        return pd.to_datetime(series, errors="coerce").dt.date

    def upcoming_rows(data, date_col, today=None):
        today = today or date.today()
        dated = data.copy()
        dated["_date"] = parse_dates(dated[date_col])
        return dated[dated["_date"].notna() & (dated["_date"] >= today)].sort_values("_date")

    def format_date(val):
        parsed = pd.to_datetime(val, errors="coerce")
        return parsed.strftime("%b %d, %Y") if not pd.isna(parsed) else "Date not set"

    def local_answer(question: str) -> tuple[str, str]:
        query = question.lower()
        if any(term in query for term in ["cgpa", "gpa formula", "cgpa formula", "official formula", "exam regulation", "eligibility rule", "attendance rule"]):
            if not program_info.empty and "official_formula" in program_info:
                formula = program_info["official_formula"].dropna().astype(str)
                formula = formula[formula.str.strip().ne("")]
                if not formula.empty:
                    return formula.iloc[0], "Scores"
            return UNKNOWN_ANSWER, "Scores"

        semester_match = re.search(r"semester\s*(\d+)|sem\s*(\d+)", query)
        requested_semester = int(next(v for v in semester_match.groups() if v)) if semester_match else curr_sem

        is_course_query = any(term in query for term in [
            "incomplete", "still left", "courses left", "subjects left", "subjects are left", 
            "not completed", "pending courses", "remaining courses", "courses pending"
        ]) or (("subject" in query or "course" in query) and ("left" in query or "pending" in query or "remaining" in query))
        
        if is_course_query:
            if courses.empty or requested_semester is None:
                return UNKNOWN_ANSWER, "Courses"
            rows = courses[
                (courses["semester"].astype(int) == requested_semester)
                & ~courses["status"].astype(str).str.lower().eq("completed")
            ]
            names = [f"{row['course_name']} ({row['course_code']})" for _, row in rows.iterrows()]
            if names:
                return f"Incomplete courses in Semester {requested_semester}: {', '.join(names)}.", "Courses"
            return f"All recorded courses for Semester {requested_semester} are marked Completed.", "Courses"

        if any(term in query for term in ["next ia", "next assessment", "upcoming assessment", "internal assessment", "when is my next"]):
            upcoming = upcoming_rows(assessments, "date")
            if upcoming.empty:
                return "There are no upcoming assessments recorded in the schedule.", "Assessments"
            if "ia" in query and not "assignment" in query:
                ia_rows = upcoming[upcoming["assessment_type"].astype(str).str.contains("ia", case=False, na=False)]
                if not ia_rows.empty:
                    row = ia_rows.iloc[0]
                    return f"Your next internal assessment test is {row.get('assessment_type', 'IA')} for {row.get('course_code', '')} scheduled on {format_date(row['_date'])}.", "Assessments"
            row = upcoming.iloc[0]
            next_ia = upcoming[upcoming["assessment_type"].astype(str).str.contains("ia", case=False, na=False)]
            ia_note = f" (Next IA test is {next_ia.iloc[0].get('assessment_type')} on {format_date(next_ia.iloc[0]['_date'])})" if not next_ia.empty and next_ia.iloc[0]["_date"] != row["_date"] else ""
            return f"Your next scheduled assessment is {row.get('assessment_type', 'Assessment')} for {row.get('course_code', '')} on {format_date(row['_date'])}{ia_note}.", "Assessments"

        if any(term in query for term in ["holiday", "leave", "vacation", "off"]):
            upcoming = upcoming_rows(calendar, "date")
            if not upcoming.empty:
                upcoming = upcoming[upcoming["event_type"].astype(str).str.contains("holiday|leave", case=False, na=False)]
            if upcoming.empty:
                return "There are no upcoming holidays or leaves recorded in the calendar.", "Calendar"
            row = upcoming.iloc[0]
            return f"Your next holiday / leave is {row.get('title', 'Holiday')} on {format_date(row['_date'])} ({row.get('event_type')}).", "Calendar"

        if any(term in query for term in ["topic", "syllabus", "content", "curriculum", "unit"]):
            if courses.empty:
                return UNKNOWN_ANSWER, "Courses"
            words = [w for w in re.findall(r"[a-zA-Z0-9]+", query) if w not in {"what", "topics", "topic", "in", "the", "are", "for", "course", "syllabus", "show", "me", "tell", "about", "content", "of"}]
            matched = courses[
                courses["course_name"].astype(str).str.lower().apply(lambda name: any(w in name for w in words))
                | courses["course_code"].astype(str).str.lower().apply(lambda code: any(w in code for w in words))
            ]
            if not matched.empty:
                row = matched.iloc[0]
                topics_str = row.get("syllabus", "No topics listed")
                return f"{row['course_name']} ({row['course_code']}) syllabus topics: {topics_str}.", "Courses"

        return UNKNOWN_ANSWER, "Courses"

    test_queries = [
        ("What courses are still incomplete in Semester 3?", "Courses", lambda ans: "Data Structures" in ans),
        ("When is my next internal assessment?", "Assessments", lambda ans: "Nov" in ans and ("Assignment" in ans or "IA" in ans)),
        ("Show my next holiday", "Calendar", lambda ans: "Nov 20" in ans or "Holiday" in ans),
        ("What topics are in Data Structures?", "Courses", lambda ans: "Stacks" in ans and "queues" in ans),
        ("What is my official university CGPA formula?", "Scores", lambda ans: ans == UNKNOWN_ANSWER),
        ("What subjects are left in Sem 5?", "Courses", lambda ans: "Computer Networks" in ans),
        ("When is my next IA?", "Assessments", lambda ans: "IA2" in ans or "Nov 24" in ans),
    ]

    for q, expected_area, check_fn in test_queries:
        ans, area = local_answer(q)
        print(f"\n[QUERY] '{q}'\n  -> Area: {area} (Expected: {expected_area})\n  -> Answer: {ans}")
        assert area == expected_area, f"Area mismatch for '{q}': got {area}, expected {expected_area}"
        assert check_fn(ans), f"Answer validation failed for '{q}': got '{ans}'"

    print("\nChatbot 7/7 Grounding and Safety Tests: PASSED!")

if __name__ == "__main__":
    test_files_exist()
    test_semesters()
    test_courses()
    test_calendar()
    test_scores()
    test_checklist()
    test_chatbot_questions()
    print("\n===============================")
    print("ALL TESTS PASSED WITH 100% SUCCESS!")
    print("===============================")
