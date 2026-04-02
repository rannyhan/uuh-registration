from flask import Flask, request, jsonify, render_template, abort, Response
import sqlite3
import os
import csv
import io

app = Flask(__name__)
DB_PATH = os.environ.get('DB_PATH', 'registrations.db')
ADMIN_PW = os.environ.get('ADMIN_PW', '6574')

LIMITS = {'adult': 10, 'mental': 2, 'women': 2, 'child': 2}
TOTAL_LIMIT = 15
DEPT_LABELS = {'adult': '성인', 'mental': '정신', 'women': '여성', 'child': '아동'}
ROUND_LABELS = {'r1': '1차수', 'r2': '2차수'}

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            org TEXT NOT NULL,
            phone TEXT NOT NULL,
            round TEXT NOT NULL,
            dept TEXT NOT NULL,
            created_at DATETIME DEFAULT (datetime('now', 'localtime'))
        )
    ''')
    conn.commit()
    conn.close()

def get_counts():
    conn = get_db()
    rows = conn.execute('SELECT round, dept, COUNT(*) as cnt FROM registrations GROUP BY round, dept').fetchall()
    conn.close()
    counts = {
        'r1': {'adult': 0, 'mental': 0, 'women': 0, 'child': 0, 'total': 0},
        'r2': {'adult': 0, 'mental': 0, 'women': 0, 'child': 0, 'total': 0}
    }
    for row in rows:
        r, d, c = row['round'], row['dept'], row['cnt']
        if r in counts and d in counts[r]:
            counts[r][d] = c
            counts[r]['total'] += c
    return counts

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/counts')
def api_counts():
    return jsonify(get_counts())

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json
    name  = (data.get('name') or '').strip()
    org   = (data.get('org') or '').strip()
    phone = (data.get('phone') or '').strip()
    round_ = data.get('round')
    dept  = data.get('dept')

    if not all([name, org, phone, round_, dept]):
        return jsonify({'ok': False, 'msg': '모든 항목을 입력해 주세요.'}), 400
    if round_ not in ('r1', 'r2') or dept not in ('adult', 'mental', 'women', 'child'):
        return jsonify({'ok': False, 'msg': '잘못된 요청입니다.'}), 400

    # 중복 신청 체크 (이름 + 전화번호 기준, 모든 차수 통틀어)
    conn = get_db()
    existing = conn.execute(
        'SELECT id FROM registrations WHERE name=? AND phone=?',
        (name, phone)
    ).fetchone()
    if existing:
        conn.close()
        return jsonify({'ok': False, 'msg': '이미 신청하신 내역이 있습니다.\n중복 신청은 불가합니다.'}), 409

    counts = get_counts()
    if counts[round_]['total'] >= TOTAL_LIMIT:
        conn.close()
        return jsonify({'ok': False, 'msg': '해당 차수가 마감되었습니다.'}), 409
    if counts[round_][dept] >= LIMITS[dept]:
        conn.close()
        return jsonify({'ok': False, 'msg': '해당 부서가 마감되었습니다.'}), 409

    conn.execute(
        'INSERT INTO registrations (name, org, phone, round, dept) VALUES (?, ?, ?, ?, ?)',
        (name, org, phone, round_, dept)
    )
    conn.commit()
    conn.close()

    return jsonify({
        'ok': True,
        'msg': f"{name}님의 신청이 완료되었습니다.\n{ROUND_LABELS[round_]} · {DEPT_LABELS[dept]} 부서로 접수되었습니다.\n문의사항은 담당자에게 연락해 주세요."
    })

@app.route('/api/admin/list', methods=['POST'])
def api_admin_list():
    data = request.json
    if data.get('pw') != ADMIN_PW:
        return jsonify({'ok': False, 'msg': '비밀번호가 올바르지 않습니다.'}), 401

    filter_ = data.get('filter', 'all')
    conn = get_db()
    if filter_ in ('r1', 'r2'):
        rows = conn.execute('SELECT * FROM registrations WHERE round=? ORDER BY id', (filter_,)).fetchall()
    elif filter_ in ('adult', 'mental', 'women'):
        rows = conn.execute('SELECT * FROM registrations WHERE dept=? ORDER BY id', (filter_,)).fetchall()
    else:
        rows = conn.execute('SELECT * FROM registrations ORDER BY id').fetchall()
    conn.close()

    result = [dict(r) for r in rows]
    for r in result:
        r['round_label'] = ROUND_LABELS.get(r['round'], r['round'])
        r['dept_label']  = DEPT_LABELS.get(r['dept'], r['dept'])
    return jsonify({'ok': True, 'data': result})

@app.route('/api/admin/delete', methods=['POST'])
def api_admin_delete():
    data = request.json
    if data.get('pw') != ADMIN_PW:
        return jsonify({'ok': False, 'msg': '비밀번호가 올바르지 않습니다.'}), 401
    reg_id = data.get('id')
    if not reg_id:
        return jsonify({'ok': False, 'msg': '삭제할 항목이 없습니다.'}), 400
    conn = get_db()
    conn.execute('DELETE FROM registrations WHERE id=?', (reg_id,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/admin/reset', methods=['POST'])
def api_admin_reset():
    data = request.json
    if data.get('pw') != ADMIN_PW:
        return jsonify({'ok': False, 'msg': '비밀번호가 올바르지 않습니다.'}), 401
    conn = get_db()
    conn.execute('DELETE FROM registrations')
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/admin/export', methods=['POST'])
def api_admin_export():
    data = request.json
    if data.get('pw') != ADMIN_PW:
        abort(401)

    filter_ = data.get('filter', 'all')
    conn = get_db()
    if filter_ in ('r1', 'r2'):
        rows = conn.execute('SELECT * FROM registrations WHERE round=? ORDER BY id', (filter_,)).fetchall()
    elif filter_ in ('adult', 'mental', 'women'):
        rows = conn.execute('SELECT * FROM registrations WHERE dept=? ORDER BY id', (filter_,)).fetchall()
    else:
        rows = conn.execute('SELECT * FROM registrations ORDER BY id').fetchall()
    conn.close()

    output = io.StringIO()
    output.write('\ufeff')
    writer = csv.writer(output)
    writer.writerow(['번호', '이름', '소속', '연락처', '차수', '부서', '신청일시'])
    for i, r in enumerate(rows, 1):
        writer.writerow([
            i, r['name'], r['org'], r['phone'],
            ROUND_LABELS.get(r['round'], r['round']),
            DEPT_LABELS.get(r['dept'], r['dept']),
            r['created_at']
        ])

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename*=UTF-8\'\'%EA%B5%90%EC%88%98%EC%9E%84%EC%83%81%EC%97%B0%EC%88%98%EA%B3%BC%EC%A0%95_%EC%8B%A0%EC%B2%AD%EC%9E%90%EB%AA%A9%EB%A1%9D.csv'}
    )

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

init_db()
