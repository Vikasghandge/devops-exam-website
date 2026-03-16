from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import pymysql, os, random, json
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'devops-exam-secret-2024')
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

app.jinja_env.filters['fromjson'] = json.loads

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
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        if not email or not password:
            error = 'Please fill in all fields.'
        else:
            try:
                db = get_db()
                with db.cursor() as cur:
                    cur.execute(
                        "SELECT * FROM users WHERE email=%s AND password=%s",
                        (email, password)
                    )
                    user = cur.fetchone()
                db.close()
                if user:
                    session['user_id']  = user['id']
                    session['username'] = user['username']
                    session['email']    = user['email']
                    return redirect(url_for('dashboard'))
                else:
                    error = 'Invalid email or password.'
            except Exception as e:
                error = f'Database error: {str(e)}'
    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    error   = None
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

    # ── FIX — parse options JSON string into dict ──────────
    for q in questions:
        if isinstance(q['options'], str):
            q['options'] = json.loads(q['options'])

    session['exam_questions'] = [q['id'] for q in questions]
    session['exam_start']     = datetime.now().isoformat()
    session['exam_answers']   = {}

    return render_template('exam.html', questions=questions, duration=20)

@app.route('/submit-exam', methods=['POST'])
@login_required
def submit_exam():
    if 'exam_questions' not in session:
        return redirect(url_for('dashboard'))

    answers    = request.form
    q_ids      = session.get('exam_questions', [])
    start_time = datetime.fromisoformat(session.get('exam_start'))
    time_taken = int((datetime.now() - start_time).total_seconds())

    try:
        db      = get_db()
        score   = 0
        results = []
        with db.cursor() as cur:
            for qid in q_ids:
                cur.execute("SELECT * FROM questions WHERE id=%s", (qid,))
                q = cur.fetchone()
                if not q:
                    continue
                # parse options for result page
                if isinstance(q['options'], str):
                    q['options'] = json.loads(q['options'])

                user_ans   = answers.get(f'q_{qid}', None)
                is_correct = (user_ans == q['correct_answer'])
                if is_correct:
                    score += 1

                results.append({
                    'question':       q['question'],
                    'options':        q['options'],
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
        score=score,
        total=total,
        percentage=percentage,
        time_taken=time_taken,
        results=results
    )

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ── Leaderboard route ─────────────────────────────────────
@app.route('/leaderboard')
@login_required
def leaderboard():
    try:
        db = get_db()
        with db.cursor() as cur:

            # Top 10 — best percentage, ties broken by fastest time
            cur.execute("""
                SELECT
                    r.user_id,
                    u.username,
                    MAX(r.percentage)                          AS best_pct,
                    MAX(r.score)                               AS best_score,
                    MAX(r.total)                               AS total,
                    MIN(CASE WHEN r.percentage = sub.max_pct
                             THEN r.time_taken END)            AS fastest_time,
                    COUNT(r.id)                                AS attempts
                FROM results r
                JOIN users u ON r.user_id = u.id
                JOIN (
                    SELECT user_id, MAX(percentage) AS max_pct
                    FROM results GROUP BY user_id
                ) sub ON r.user_id = sub.user_id
                GROUP BY r.user_id, u.username
                ORDER BY best_pct DESC, fastest_time ASC
                LIMIT 10
            """)
            rows = cur.fetchall()

            # Stats
            cur.execute("SELECT COUNT(DISTINCT user_id) AS cnt FROM results")
            total_players = cur.fetchone()['cnt']

            cur.execute("SELECT COUNT(*) AS cnt FROM results")
            total_exams = cur.fetchone()['cnt']

            cur.execute("SELECT MAX(percentage) AS top FROM results")
            top_score_row = cur.fetchone()
            top_score = round(top_score_row['top']) if top_score_row['top'] else None

            # Current user rank
            cur.execute("""
                SELECT COUNT(*) + 1 AS rnk
                FROM (
                    SELECT user_id, MAX(percentage) AS best_pct
                    FROM results GROUP BY user_id
                ) ranked
                WHERE best_pct > (
                    SELECT COALESCE(MAX(percentage), 0)
                    FROM results WHERE user_id = %s
                )
            """, (session['user_id'],))
            my_rank_row = cur.fetchone()
            my_rank = my_rank_row['rnk'] if my_rank_row else None

            # Current user best score
            cur.execute("""
                SELECT MAX(percentage) AS best_pct
                FROM results WHERE user_id = %s
            """, (session['user_id'],))
            my_pct_row = cur.fetchone()
            my_best_pct = my_pct_row['best_pct'] if my_pct_row and my_pct_row['best_pct'] else 0

        db.close()

        # Format display names — "Vikas G."
        leaderboard = []
        for row in rows:
            parts = row['username'].strip().split()
            if len(parts) >= 2:
                display = f"{parts[0]} {parts[-1][0]}."
            else:
                display = parts[0] if parts else 'User'
            row['display_name'] = display
            leaderboard.append(row)

    except Exception as e:
        leaderboard    = []
        total_players  = 0
        total_exams    = 0
        top_score      = None
        my_rank        = None
        my_best_pct    = 0

    return render_template('leaderboard.html',
        leaderboard   = leaderboard,
        total_players = total_players,
        total_exams   = total_exams,
        top_score     = top_score,
        my_rank       = my_rank,
        my_best_pct   = my_best_pct
    )



# ── Admin config ──────────────────────────────────────────
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin@devops2024')

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('is_admin'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

# ── Admin login ───────────────────────────────────────────
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        password = request.form.get('password', '').strip()
        if password == ADMIN_PASSWORD:
            session['is_admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            error = 'Invalid admin password.'
    return render_template('admin_login.html', error=error)

@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    return redirect(url_for('admin_login'))

# ── Admin dashboard — view all questions ──────────────────
@app.route('/admin')
@admin_required
def admin_dashboard():
    try:
        db = get_db()
        with db.cursor() as cur:
            cur.execute("SELECT * FROM questions ORDER BY id ASC")
            questions = cur.fetchall()
            cur.execute("SELECT COUNT(*) AS cnt FROM questions")
            total_q = cur.fetchone()['cnt']
            cur.execute("SELECT COUNT(*) AS cnt FROM results")
            total_results = cur.fetchone()['cnt']
            cur.execute("SELECT COUNT(*) AS cnt FROM users")
            total_users = cur.fetchone()['cnt']
        db.close()
        for q in questions:
            if isinstance(q['options'], str):
                q['options'] = json.loads(q['options'])
    except Exception as e:
        questions = []
        total_q = total_results = total_users = 0
    return render_template('admin_dashboard.html',
        questions=questions,
        total_q=total_q,
        total_results=total_results,
        total_users=total_users
    )

# ── Admin add question ────────────────────────────────────
@app.route('/admin/add', methods=['GET', 'POST'])
@admin_required
def admin_add():
    error = None
    success = None
    if request.method == 'POST':
        question   = request.form.get('question', '').strip()
        opt_a      = request.form.get('opt_a', '').strip()
        opt_b      = request.form.get('opt_b', '').strip()
        opt_c      = request.form.get('opt_c', '').strip()
        opt_d      = request.form.get('opt_d', '').strip()
        correct    = request.form.get('correct', '').strip().upper()
        explanation= request.form.get('explanation', '').strip()
        category   = request.form.get('category', 'DevOps').strip()

        if not all([question, opt_a, opt_b, opt_c, opt_d, correct]):
            error = 'All fields except explanation are required.'
        elif correct not in ['A', 'B', 'C', 'D']:
            error = 'Correct answer must be A, B, C or D.'
        else:
            options = json.dumps({"A": opt_a, "B": opt_b, "C": opt_c, "D": opt_d})
            try:
                db = get_db()
                with db.cursor() as cur:
                    cur.execute("""
                        INSERT INTO questions
                        (question, options, correct_answer, explanation, category)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (question, options, correct, explanation, category))
                    db.commit()
                db.close()
                success = 'Question added successfully!'
            except Exception as e:
                error = f'Database error: {str(e)}'
    return render_template('admin_form.html',
        mode='add', error=error, success=success, q=None)

# ── Admin edit question ───────────────────────────────────
@app.route('/admin/edit/<int:qid>', methods=['GET', 'POST'])
@admin_required
def admin_edit(qid):
    error = None
    success = None
    try:
        db = get_db()
        with db.cursor() as cur:
            if request.method == 'POST':
                question    = request.form.get('question', '').strip()
                opt_a       = request.form.get('opt_a', '').strip()
                opt_b       = request.form.get('opt_b', '').strip()
                opt_c       = request.form.get('opt_c', '').strip()
                opt_d       = request.form.get('opt_d', '').strip()
                correct     = request.form.get('correct', '').strip().upper()
                explanation = request.form.get('explanation', '').strip()
                category    = request.form.get('category', 'DevOps').strip()

                if not all([question, opt_a, opt_b, opt_c, opt_d, correct]):
                    error = 'All fields except explanation are required.'
                elif correct not in ['A', 'B', 'C', 'D']:
                    error = 'Correct answer must be A, B, C or D.'
                else:
                    options = json.dumps({"A": opt_a, "B": opt_b, "C": opt_c, "D": opt_d})
                    cur.execute("""
                        UPDATE questions
                        SET question=%s, options=%s, correct_answer=%s,
                            explanation=%s, category=%s
                        WHERE id=%s
                    """, (question, options, correct, explanation, category, qid))
                    db.commit()
                    success = 'Question updated successfully!'

            cur.execute("SELECT * FROM questions WHERE id=%s", (qid,))
            q = cur.fetchone()
            if q and isinstance(q['options'], str):
                q['options'] = json.loads(q['options'])
        db.close()
    except Exception as e:
        error = f'Database error: {str(e)}'
        q = None
    return render_template('admin_form.html',
        mode='edit', error=error, success=success, q=q, qid=qid)

# ── Admin delete question ─────────────────────────────────
@app.route('/admin/delete/<int:qid>', methods=['POST'])
@admin_required
def admin_delete(qid):
    try:
        db = get_db()
        with db.cursor() as cur:
            cur.execute("DELETE FROM questions WHERE id=%s", (qid,))
            db.commit()
        db.close()
    except Exception as e:
        pass
    return redirect(url_for('admin_dashboard'))

# ── Admin preview question ────────────────────────────────
@app.route('/admin/preview/<int:qid>')
@admin_required
def admin_preview(qid):
    try:
        db = get_db()
        with db.cursor() as cur:
            cur.execute("SELECT * FROM questions WHERE id=%s", (qid,))
            q = cur.fetchone()
            if q and isinstance(q['options'], str):
                q['options'] = json.loads(q['options'])
        db.close()
    except Exception as e:
        q = None
    return render_template('admin_preview.html', q=q)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
