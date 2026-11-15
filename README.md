# 🎓 My Engineering Degree OS

A self-managed 1st-to-8th semester engineering degree command center with schedules, syllabus, assessments, academic progress, performance scorecards, execution checklist, and a grounded AI chatbot.

Built with **Python**, **Streamlit**, and **Pandas**, powered by maintainable CSV data under `/data` and optional Gemini API integration via `google-genai`.

---

## 🚀 Quickstart & Local Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Streamlit Web Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

### 3. Optional: Configure Gemini API Key
To enable cloud LLM generation for **Ask Degree AI**, add your key to `.streamlit/secrets.toml`:
```toml
GEMINI_API_KEY = "your-api-key-here"
```
*(If no key is configured, the built-in deterministic local intelligence automatically answers all student questions without crashing or hallucinating).*

---

## 📋 Architecture & Data Model

The application is completely maintainable through clean CSV datasets in `/data/`:

| Dataset | CSV File | Content & Function |
| :--- | :--- | :--- |
| **Semesters** | `semesters.csv` | Semesters 1 to 8, status, total credits, completed credits |
| **Courses** | `courses.csv` | Semester, course code, title, credits, faculty, syllabus topics, status |
| **Academic Calendar** | `academic_calendar.csv` | Academic year, semester, date, event type (Holiday/Leave/Academic), title |
| **Assessments** | `assessments.csv` | Semester, course code, assessment type (IA1, IA2, assignment, lab, exam), date, marks, status |
| **Scores** | `scores.csv` | Semester, course code, assessment type, marks scored, max marks, grade |
| **Plan & Checklist** | `plan_checklist.csv` | Category, action item, target date, status (`Not Started`/`In Progress`/`Done`), notes |
| **Programme Info** | `program_info.csv` | Programme name, total semesters, graduation credits, syllabus reference |

---

## 🧭 Navigation & Modules

1. **Dashboard**: High-level command center displaying current active semester, overall completion %, completed credits, next upcoming assessment, next holiday/leave, prototype score average, and a semester progress chart.
2. **Semesters 1-8**: 8 interactive semester cards displaying course counts, credits completed vs required, progress bars, and filterable course details.
3. **Courses & Syllabus**: Semester-filterable catalog with search across course codes, faculty, titles, and syllabus units.
4. **University Syllabus**: Official programme summary, expected credits, and verified handbook reference document.
5. **Academic Calendar**: Filterable by academic year, semester, and event category (🏖️ Holiday, 🌴 Leave, 📖 Academic).
6. **Internal Assessments**: Schedule of IA1, IA2, assignments, lab evaluations, project reviews, and end-semester exams.
7. **Status Tracker**: Course-by-course status breakdown (`Not Started`, `In Progress`, `Completed`) with semester completion bar.
8. **Scorecard**: Semester-by-semester scores, evaluated credits, simple prototype percentage calculation, and cumulative progress tracking.
9. **Plan & Checklist**: Degree execution control panel with summary metrics (Total, Done, Due in 7 Days, Overdue), **This Week** action items, **Semester Milestones**, **Degree Milestones**, and an interactive editor with save capability.
10. **Ask Degree AI**: Grounded chatbot answering student queries strictly using loaded CSV data with strict safety guardrails against inventing formulas or rules.
11. **Data Admin**: Built-in data editor allowing students to update and persist all 7 CSV files directly through the UI.

---

## 🧪 Seven Acceptance Tests Verification

| # | Acceptance Test | Status | Evidence |
| :---: | :--- | :---: | :--- |
| 1 | **All 11 required navigation items are visible** | ✅ PASS | All 11 pages present in sidebar navigation radio |
| 2 | **Semester 1 to Semester 8 can all be selected** | ✅ PASS | All 8 semesters modeled with course counts, credits, and details |
| 3 | **Course data changes when semester filter changes** | ✅ PASS | Switching Sem 1 ➔ Sem 3 dynamically filters course table |
| 4 | **Calendar can distinguish academic events and leave/holidays** | ✅ PASS | Event types tagged with visual indicators and filterable |
| 5 | **Assessment dates and score data are visible** | ✅ PASS | Chronological assessments and score breakdown rendered |
| 6 | **Plan & Checklist can be edited without touching code** | ✅ PASS | Interactive `st.data_editor` persists directly to CSV |
| 7 | **Chatbot gives grounded answer and safe "cannot verify" response** | ✅ PASS | Grounded answers for valid queries; safe refusal for unverified formulas |

---

## 🔒 Safe-AI Guardrail Verification

### 1. Grounded Question Test
- **Question**: *"What courses are still incomplete in Semester 3?"*
- **Response**: `Incomplete courses in Semester 3: Data Structures (CS301), Discrete Mathematics (MA301), Database Systems (CS302), Digital Logic Design (EC301).`
- **Data Area Used**: `Courses`

### 2. Safety Refusal Test (Unsupported Question)
- **Question**: *"What is my official university CGPA formula?"*
- **Response**: `I cannot verify that from the current Degree OS data.`
- **Data Area Used**: `Scores`

---

## 🚢 Deployment to Streamlit Community Cloud

1. Push this repository to GitHub:
   ```bash
   git init
   git add .
   git commit -m "feat: complete engineering degree OS prototype"
   git remote add origin https://github.com/<your-username>/engineering-degree-os.git
   git push -u origin main
   ```
2. Open [share.streamlit.io](https://share.streamlit.io/) and click **New App**.
3. Select your repository, branch (`main`), and main file path (`app.py`).
4. (Optional) In **Advanced Settings > Secrets**, set `GEMINI_API_KEY = "..."`.
5. Click **Deploy**.
