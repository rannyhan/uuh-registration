from flask import Flask, request, jsonify, render_template, abort, Response
import os
import csv
import io
import json
import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)
ADMIN_PW = os.environ.get('ADMIN_PW', '6574')
SHEET_ID = os.environ.get('SHEET_ID', '')

LIMITS = {'adult': 14, 'mental': 2, 'women': 2, 'child': 2}
TOTAL_LIMIT = 20
DEPT_LABELS = {'adult': '성인', 'mental': '정신', 'women': '여성', 'child': '아동'}
ROUND_LABELS = {'r1': '1차수', 'r2': '2차수'}

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def get_sheet():
    creds_json = os.environ.get('GOOGLE_CREDENTIALS', '')
    if not creds_json:
        raise Exception('GOOGLE_CREDENTIALS 환경 변수가 비어 있습니다.')
    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet_id = os.environ.get('SHEET_ID', '')
    if not sheet_id:
        raise Exception('SHEET_ID 환경 변수가 비어 있습니다.')
    sheet = client.open_by_key(sheet_id).sheet1
    return sheet

def init_sheet():
    try:
        sheet = get_sheet()
        if sheet.row_count == 0 or sheet.cell(1, 1).value != 'id':
            sheet.clear()
            sheet.append_row(['id', 'name', 'org', 'phone', 'round', 'dept', 'created_at'])
    except Exception as e:
        print(f'Sheet init error: {e}')

def get_all_rows():
    sheet = get_sheet()
    records = sheet.get_all_records()
    return records

def get_counts():
    counts = {
        'r1': {'adult': 0, 'mental': 0, 'women': 0, 'child': 0, 'total': 0},
        'r2': {'adult': 0, 'mental': 0, 'women': 0, 'child': 0, 'total': 0}
    }
    try:
        rows = get_all_rows()
        for r in rows:
            rnd = r.get('round', '')
            dept = r.get('dept', '')
            if rnd in counts and dept in counts[rnd]:
                counts[rnd][dept] += 1
                counts[rnd]['total'] += 1
    except Exception as e:
        import traceback
        print(f'Count error: {type(e).__name__}: {e}')
        traceback.print_exc()
    return counts

def get_next_id():
    try:
        rows = get_all_rows()
        if not rows:
            return 1
        ids = [int(r.get('id', 0)) for r in rows if str(r.get('id', '')).isdigit()]
        return max(ids) + 1 if ids else 1
    except:
        return 1

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

    try:
        rows = get_all_rows()

        # 중복 체크
        for r in rows:
            if r.get('name') == name and r.get('phone') == phone:
                return jsonify({'ok': False, 'msg': '이미 신청하신 내역이 있습니다.\n중복 신청은 불가합니다.'}), 409

        counts = get_counts()
        if counts[round_]['total'] >= TOTAL_LIMIT:
            return jsonify({'ok': False, 'msg': '해당 차수가 마감되었습니다.'}), 409
        if counts[round_][dept] >= LIMITS[dept]:
            return jsonify({'ok': False, 'msg': '해당 부서가 마감되었습니다.'}), 409

        from datetime import datetime
        now = datetime.now().strftime('%Y-%m-%d %H:%M')
        new_id = get_next_id()

        sheet = get_sheet()
        sheet.append_row([new_id, name, org, phone, round_, dept, now])

        return jsonify({
            'ok': True,
            'msg': f"{name}님의 신청이 완료되었습니다.\n{ROUND_LABELS[round_]} · {DEPT_LABELS[dept]} 부서로 접수되었습니다.\n문의사항은 담당자에게 연락해 주세요."
        })
    except Exception as e:
        print(f'Register error: {type(e).__name__}: {e}')
        import traceback; traceback.print_exc()
        return jsonify({'ok': False, 'msg': '서버 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.'}), 500

@app.route('/api/admin/list', methods=['POST'])
def api_admin_list():
    data = request.json
    if data.get('pw') != ADMIN_PW:
        return jsonify({'ok': False, 'msg': '비밀번호가 올바르지 않습니다.'}), 401

    filter_ = data.get('filter', 'all')
    try:
        rows = get_all_rows()
        if filter_ in ('r1', 'r2'):
            rows = [r for r in rows if r.get('round') == filter_]
        elif filter_ in ('adult', 'mental', 'women', 'child'):
            rows = [r for r in rows if r.get('dept') == filter_]

        result = []
        for r in rows:
            result.append({
                'id': r.get('id'),
                'name': r.get('name'),
                'org': r.get('org'),
                'phone': r.get('phone'),
                'round': r.get('round'),
                'dept': r.get('dept'),
                'created_at': r.get('created_at'),
                'round_label': ROUND_LABELS.get(r.get('round', ''), ''),
                'dept_label': DEPT_LABELS.get(r.get('dept', ''), ''),
            })
        return jsonify({'ok': True, 'data': result})
    except Exception as e:
        print(f'List error: {e}')
        return jsonify({'ok': False, 'msg': '서버 오류가 발생했습니다.'}), 500

@app.route('/api/admin/delete', methods=['POST'])
def api_admin_delete():
    data = request.json
    if data.get('pw') != ADMIN_PW:
        return jsonify({'ok': False, 'msg': '비밀번호가 올바르지 않습니다.'}), 401
    target_id = str(data.get('id'))
    if not target_id:
        return jsonify({'ok': False, 'msg': '삭제할 항목이 없습니다.'}), 400
    try:
        sheet = get_sheet()
        all_values = sheet.get_all_values()
        for i, row in enumerate(all_values):
            if i == 0:
                continue
            if str(row[0]) == target_id:
                sheet.delete_rows(i + 1)
                return jsonify({'ok': True})
        return jsonify({'ok': False, 'msg': '해당 항목을 찾을 수 없습니다.'}), 404
    except Exception as e:
        print(f'Delete error: {e}')
        return jsonify({'ok': False, 'msg': '서버 오류가 발생했습니다.'}), 500

@app.route('/api/admin/reset', methods=['POST'])
def api_admin_reset():
    data = request.json
    if data.get('pw') != ADMIN_PW:
        return jsonify({'ok': False, 'msg': '비밀번호가 올바르지 않습니다.'}), 401
    try:
        sheet = get_sheet()
        sheet.clear()
        sheet.append_row(['id', 'name', 'org', 'phone', 'round', 'dept', 'created_at'])
        return jsonify({'ok': True})
    except Exception as e:
        print(f'Reset error: {e}')
        return jsonify({'ok': False, 'msg': '서버 오류가 발생했습니다.'}), 500

@app.route('/api/admin/export', methods=['POST'])
def api_admin_export():
    data = request.json
    if data.get('pw') != ADMIN_PW:
        abort(401)
    filter_ = data.get('filter', 'all')
    try:
        rows = get_all_rows()
        if filter_ in ('r1', 'r2'):
            rows = [r for r in rows if r.get('round') == filter_]
        elif filter_ in ('adult', 'mental', 'women', 'child'):
            rows = [r for r in rows if r.get('dept') == filter_]

        output = io.StringIO()
        output.write('\ufeff')
        writer = csv.writer(output)
        writer.writerow(['번호', '이름', '소속', '연락처', '차수', '부서', '신청일시'])
        for i, r in enumerate(rows, 1):
            writer.writerow([
                i, r.get('name'), r.get('org'), r.get('phone'),
                ROUND_LABELS.get(r.get('round', ''), ''),
                DEPT_LABELS.get(r.get('dept', ''), ''),
                r.get('created_at')
            ])
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename*=UTF-8\'\'uuh_registration.csv'}
        )
    except Exception as e:
        print(f'Export error: {e}')
        abort(500)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
