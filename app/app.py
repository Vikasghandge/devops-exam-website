
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import pymysql, os, random, json
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'devops-exam-secret-2024')

# ── DB connection ─────────────────────────────────────────
def get_db():
    return pymysql.connect(
        host=os.environ.get('DB_HOST', 'db'),
        user=os.environ.get('DB_USER', 'examuser'),
        password=os.environ.get('DB_PASSWORD', 'exampass'),
        database=os.environ.get('DB_NAME', 'examdb'),
        cursorclass=pymysql.cursors.DictCursor
    )

# ── Login required decorator ──────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# ── Routes ────────────────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        if not email or not password:
            error = 'Please fill in all fields.'
        else:
            try:
                db = get_db()
                with db.cursor() as cur:
                    cur.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
                    user = cur.fetchone()
                db.close()
                if user:
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    session['email'] = user['email']
                    return redirect(url_for('dashboard'))
                else:
                    error = 'Invalid email or password.'
            except Exception as e:
                error = f'Database error: {str(e)}'
    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    success = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        if not username or not email or not password:
            error = 'All fields are required.'
        else:
            try:
                db = get_db()
                with db.cursor() as cur:
                    cur.execute("SELECT id FROM users WHERE email=%s", (email,))
                    if cur.fetchone():
                        error = 'Email already registered.'
                    else:
                        cur.execute(
                            "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                            (username, email, password)
                        )
                        db.commit()
                        success = 'Account created! Please login.'
                db.close()
            except Exception as e:
                error = f'Error: {str(e)}'
    return render_template('register.html', error=error, success=success)

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        db = get_db()
        with db.cursor() as cur:
            cur.execute("""
                SELECT score, total, percentage, taken_at
                FROM results WHERE user_id=%s
                ORDER BY taken_at DESC LIMIT 5
            """, (session['user_id'],))
            history = cur.fetchall()
        db.close()
    except:
        history = []
    return render_template('dashboard.html', history=history)

@app.route('/start-exam')
@login_required
def start_exam():
    try:
        db = get_db()
        with db.cursor() as cur:
            cur.execute("SELECT * FROM questions ORDER BY RAND() LIMIT 15")
            questions = cur.fetchall()
        db.close()
    except Exception as e:
        return f"Error loading questions: {str(e)}"

    session['exam_questions'] = [q['id'] for q in questions]
    session['exam_start']     = datetime.now().isoformat()
    session['exam_answers']   = {}
    return render_template('exam.html', questions=questions, duration=20)

@app.route('/submit-exam', methods=['POST'])
@login_required
def submit_exam():
    if 'exam_questions' not in session:
        return redirect(url_for('dashboard'))

    answers      = request.form
    q_ids        = session.get('exam_questions', [])
    start_time   = datetime.fromisoformat(session.get('exam_start'))
    time_taken   = int((datetime.now() - start_time).total_seconds())

    try:
        db = get_db()
        score = 0
        results = []
        with db.cursor() as cur:
            for qid in q_ids:
                cur.execute("SELECT * FROM questions WHERE id=%s", (qid,))
                q = cur.fetchone()
                if not q:
                    continue
                user_ans    = answers.get(f'q_{qid}', None)
                is_correct  = (user_ans == q['correct_answer'])
                if is_correct:
                    score += 1
                results.append({
                    'question':       q['question'],
                    'options':        json.loads(q['options']),
                    'user_answer':    user_ans,
                    'correct_answer': q['correct_answer'],
                    'explanation':    q.get('explanation', ''),
                    'is_correct':     is_correct
                })

            total      = len(q_ids)
            percentage = round((score / total) * 100) if total else 0
            cur.execute("""
                INSERT INTO results (user_id, score, total, percentage, time_taken)
                VALUES (%s, %s, %s, %s, %s)
            """, (session['user_id'], score, total, percentage, time_taken))
            db.commit()
        db.close()
    except Exception as e:
        return f"Error saving results: {str(e)}"

    session.pop('exam_questions', None)
    session.pop('exam_start', None)

    return render_template('result.html',
        score=score, total=total,
        percentage=percentage,
        time_taken=time_taken,
        results=results
    )

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
