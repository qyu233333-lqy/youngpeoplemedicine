"""
智能药箱 Demo - 第一版（药箱屏幕模拟器形态）
服务用户：25-30 岁独居/合租白领
核心：把"翻抽屉找药"变成"看屏幕就知道"
形态：智能药箱（带屏幕），App 是管理后台
边界：不做症状推荐、不做诊断、不做处方药管理
"""
import os
import json
import random
import sqlite3
import base64
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
import requests

# ============== 配置 ==============
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get('DB_PATH', os.path.join(BASE_DIR, 'data', 'medicine_box.db'))
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'webp'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH


# ============== 数据库 ==============
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS medicines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            brand TEXT,
            spec TEXT,
            category TEXT NOT NULL,
            location TEXT DEFAULT '未指定',
            expiry_date TEXT,
            remaining_pct INTEGER DEFAULT 100,
            notes TEXT,
            image_path TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active'
        )
    ''')
    conn.commit()

    count = conn.execute('SELECT COUNT(*) FROM medicines').fetchone()[0]
    if count == 0:
        today = datetime.now()
        samples = [
            # (name, brand, spec, category, location, expiry_date, remaining_pct, notes)
            ('感冒灵颗粒', '999', '10g*9袋', '感冒', '抽屉A·第2格',
             (today - timedelta(days=240)).strftime('%Y-%m-%d'), 100, '去年感冒买的'),
            ('红霉素眼膏', '白云山', '2.5g', '外用', '抽屉B·第1格',
             (today + timedelta(days=20)).strftime('%Y-%m-%d'), 90, ''),
            ('布洛芬', '芬必得', '0.3g*20粒', '感冒', '抽屉A·第1格',
             (today + timedelta(days=180)).strftime('%Y-%m-%d'), 50, '搬家时妈妈给的'),
            ('蒙脱石散', '思密达', '3g*10袋', '肠胃', '抽屉A·第3格',
             (today + timedelta(days=240)).strftime('%Y-%m-%d'), 80, ''),
            ('创可贴', '邦迪', '20片', '外用', '抽屉B·第2格',
             (today + timedelta(days=400)).strftime('%Y-%m-%d'), 100, '搬家时塞进去的'),
            ('维生素C', '养生堂', '100片', '保健', '上层·小盒',
             (today + timedelta(days=300)).strftime('%Y-%m-%d'), 70, '直播买的'),
            ('维生素C', '汤臣倍健', '100片', '保健', '上层·小盒',
             (today + timedelta(days=500)).strftime('%Y-%m-%d'), 100, '双11又囤了一瓶'),
            ('云南白药', '云南白药', '4g', '外用', '抽屉B·第3格',
             (today + timedelta(days=600)).strftime('%Y-%m-%d'), 100, ''),
        ]
        for s in samples:
            conn.execute(
                'INSERT INTO medicines (name, brand, spec, category, location, expiry_date, remaining_pct, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                s
            )
        conn.commit()
    conn.close()


# ============== 业务工具 ==============
def calc_status(expiry_date):
    if not expiry_date:
        return ('unknown', '未知', 'gray')
    try:
        expiry = datetime.strptime(expiry_date, '%Y-%m-%d')
        today = datetime.now()
        days_left = (expiry - today).days
        if days_left < 0:
            return ('expired', f'已过期 {-days_left} 天', 'red')
        elif days_left <= 30:
            return ('expiring', f'还有 {days_left} 天', 'yellow')
        else:
            return ('ok', f'还有 {days_left} 天', 'green')
    except ValueError:
        return ('unknown', '日期无效', 'gray')


def enrich_medicine(row):
    d = dict(row)
    status, days_text, color = calc_status(d.get('expiry_date'))
    d['status'] = status
    d['days_text'] = days_text
    d['color'] = color
    return d


# ============== Mock OCR ==============
def call_minimax_vision(image_path, prompt=None):
    """调用 MiniMax M3.1 Flash Preview（视觉模型）识别药品盒"""
    api_key = os.environ.get('MINIMAX_API_KEY')
    api_base = os.environ.get('MINIMAX_API_BASE', 'https://api.minimaxi.com/v1')
    model = os.environ.get('MINIMAX_MODEL', 'MiniMax-M3')

    if not api_key:
        return None  # 未配置则降级 Mock

    if not prompt:
        prompt = '''你是一个药品识别助手。请仔细观察这张药品盒图片，识别并返回 JSON 格式：
{
    "name": "药品通用名（如布洛芬、阿莫西林）",
    "brand": "品牌名（如芬必得、石药）",
    "spec": "规格（如0.3g*20粒）",
    "expiry_date": "有效期（YYYY-MM-DD格式，看不到就返回null）",
    "category": "分类（感冒/肠胃/外用/保健/其他）",
    "confidence": 0.0到1.0之间的数字
}
如果图片模糊或不是药品，返回 {"error": "原因说明"}。
只返回 JSON，不要其他解释。'''

    try:
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')

        # 检测图片格式
        ext = image_path.rsplit('.', 1)[-1].lower()
        mime = 'image/jpeg' if ext in ['jpg', 'jpeg'] else f'image/{ext}'

        response = requests.post(
            f'{api_base}/text/chatcompletion_v2',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': model,
                'messages': [{
                    'role': 'user',
                    'content': [
                        {'type': 'text', 'text': prompt},
                        {'type': 'image_url', 'image_url': {'url': f'data:{mime};base64,{image_data}'}}
                    ]
                }],
                'response_format': {'type': 'json_object'},
                'temperature': 0.1
            },
            timeout=30
        )
        response.raise_for_status()
        result = response.json()

        # 解析返回
        if 'choices' in result and len(result['choices']) > 0:
            content_str = result['choices'][0]['message']['content']
            return json.loads(content_str)
        return {'error': 'API 返回格式异常'}

    except requests.exceptions.Timeout:
        return {'error': 'API 调用超时'}
    except requests.exceptions.RequestException as e:
        return {'error': f'API 调用失败: {str(e)[:100]}'}
    except json.JSONDecodeError:
        return {'error': 'API 返回的不是合法 JSON'}
    except Exception as e:
        return {'error': f'未知错误: {str(e)[:100]}'}


def mock_ocr(filename):
    filename_lower = filename.lower()
    medicines_pool = [
        {'name': '布洛芬', 'brand': '芬必得', 'spec': '0.3g*20粒'},
        {'name': '布洛芬', 'brand': '美林', 'spec': '100ml'},
        {'name': '感冒灵颗粒', 'brand': '999', 'spec': '10g*9袋'},
        {'name': '蒙脱石散', 'brand': '思密达', 'spec': '3g*10袋'},
        {'name': '红霉素眼膏', 'brand': '白云山', 'spec': '2.5g'},
        {'name': '创可贴', 'brand': '邦迪', 'spec': '20片'},
        {'name': '维生素C', 'brand': '养生堂', 'spec': '100片'},
        {'name': '维生素D', 'brand': '星鲨', 'spec': '400单位*60粒'},
        {'name': '阿莫西林', 'brand': '石药', 'spec': '0.25g*24粒'},
        {'name': '云南白药', 'brand': '云南白药', 'spec': '4g*6瓶'},
    ]

    if 'fail' in filename_lower:
        return {'success': False, 'error': '图片模糊，关键字段无法识别'}

    matched = None
    for m in medicines_pool:
        if m['name'].lower() in filename_lower or m['brand'].lower() in filename_lower:
            matched = m
            break

    if not matched:
        matched = random.choice(medicines_pool)

    confidence = round(random.uniform(0.75, 0.98), 2)
    expiry = (datetime.now() + timedelta(days=random.randint(30, 720))).strftime('%Y-%m-%d')
    result = {
        'success': True,
        'confidence': confidence,
        **matched,
        'expiry_date': expiry,
        'mock': True,
    }
    if random.random() < 0.10:
        result['expiry_date'] = None
        result['warning'] = '有效期识别失败，请手动补全'
    return result


def real_ocr(image_path, filename=''):
    """真实 OCR 调用：优先用 MiniMax API，失败则降级 Mock"""
    api_result = call_minimax_vision(image_path)

    if api_result is None:
        # 未配置 API key，降级到 Mock
        return None

    if 'error' in api_result:
        return {
            'success': False,
            'error': api_result['error'],
            'source': 'minimax'
        }

    # 转换为统一格式
    return {
        'success': True,
        'name': api_result.get('name', ''),
        'brand': api_result.get('brand', ''),
        'spec': api_result.get('spec', ''),
        'expiry_date': api_result.get('expiry_date'),
        'category': api_result.get('category', '其他'),
        'confidence': api_result.get('confidence', 0.9),
        'source': 'minimax'
    }


# ============== Mock LLM 分类 ==============
def classify_medicine(name, brand=''):
    rules = {
        '感冒': ['感冒', '布洛芬', '泰诺', '芬必得', '999', '板蓝根', '阿莫西林', '美林', '退烧', '止痛', '消炎'],
        '肠胃': ['蒙脱石', '思密达', '奥美拉唑', '胃', '肠', '止泻', '吗丁啉', '保和丸'],
        '外用': ['创可贴', '邦迪', '红霉素', '眼膏', '云南白药', '膏药', '药膏', '碘伏', '纱布'],
        '保健': ['维生素', '养生堂', '钙片', 'DHA', '鱼油', '叶酸', '蛋白', '氨糖', '葡萄籽'],
    }
    text = name + brand
    for category, keywords in rules.items():
        for k in keywords:
            if k in text:
                return category
    return '其他'


# ============== 页面路由 ==============
@app.route('/')
def index():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM medicines WHERE status='active' ORDER BY expiry_date ASC"
    ).fetchall()
    conn.close()

    medicines = [enrich_medicine(r) for r in rows]
    categories = ['全部', '感冒', '肠胃', '外用', '保健', '其他']
    current_category = request.args.get('category', '全部')

    if current_category != '全部':
        medicines = [m for m in medicines if m['category'] == current_category]

    expired_count = sum(1 for m in medicines if m['status'] == 'expired')
    expiring_count = sum(1 for m in medicines if m['status'] == 'expiring')

    # 按位置分组（用于智能药箱显示）
    locations = {}
    for m in medicines:
        loc = m.get('location', '未指定')
        if loc not in locations:
            locations[loc] = []
        locations[loc].append(m)

    return render_template(
        'index.html',
        medicines=medicines,
        categories=categories,
        current_category=current_category,
        expired_count=expired_count,
        expiring_count=expiring_count,
        total_count=len(medicines),
        locations=locations,
    )


@app.route('/scan')
def scan():
    return render_template('scan.html')


@app.route('/medicine/<int:mid>')
def medicine_detail(mid):
    conn = get_db()
    row = conn.execute('SELECT * FROM medicines WHERE id=?', (mid,)).fetchone()
    conn.close()
    if not row:
        return redirect(url_for('index'))
    return render_template('medicine_detail.html', medicine=enrich_medicine(row))


@app.route('/search')
def search():
    q = request.args.get('q', '').strip()
    results = []
    if q:
        conn = get_db()
        rows = conn.execute(
            """SELECT * FROM medicines
               WHERE status='active' AND (
                 name LIKE ? OR brand LIKE ? OR category LIKE ? OR notes LIKE ? OR location LIKE ?
               )
               ORDER BY
                 CASE WHEN name LIKE ? THEN 0 ELSE 1 END,
                 expiry_date ASC""",
            (f'%{q}%', f'%{q}%', f'%{q}%', f'%{q}%', f'%{q}%', f'%{q}%')
        ).fetchall()
        conn.close()
        results = [enrich_medicine(r) for r in rows]

    # 智能推荐：按症状找
    symptoms = {
        '退烧': '感冒', '止痛': '感冒', '感冒': '感冒', '发烧': '感冒',
        '拉肚子': '肠胃', '止泻': '肠胃', '胃痛': '肠胃', '肠胃': '肠胃',
        '外伤': '外用', '创口': '外用', '烫伤': '外用', '眼': '外用',
        '补': '保健', '维生素': '保健', '营养': '保健',
    }
    suggestions = []
    for keyword, cat in symptoms.items():
        if keyword in q:
            conn = get_db()
            count = conn.execute(
                "SELECT COUNT(*) FROM medicines WHERE status='active' AND category=?",
                (cat,)
            ).fetchone()[0]
            samples = conn.execute(
                "SELECT * FROM medicines WHERE status='active' AND category=? LIMIT 3",
                (cat,)
            ).fetchall()
            conn.close()
            suggestions.append({
                'keyword': keyword,
                'category': cat,
                'count': count,
                'samples': [enrich_medicine(s) for s in samples]
            })

    return render_template('search.html', q=q, results=results, suggestions=suggestions)


# ============== API 路由 ==============
@app.route('/api/scan', methods=['POST'])
def api_scan():
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': '没有上传图片'}), 400

    image = request.files['image']
    if image.filename == '':
        return jsonify({'success': False, 'error': '文件名为空'}), 400

    ext = image.filename.rsplit('.', 1)[-1].lower()
    if ext not in ALLOWED_EXT:
        return jsonify({'success': False, 'error': f'不支持的格式 {ext}'}), 400

    filename = secure_filename(image.filename)
    save_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
    save_path = os.path.join(UPLOAD_DIR, save_name)
    image.save(save_path)

    # 调用真实 API（如果有 key），否则 Mock
    ocr_result = real_ocr(save_path, filename)

    if ocr_result is None:
        # API 未配置或失败，降级 Mock
        ocr_result = mock_ocr(filename)
        ocr_result['source'] = 'mock'
    elif not ocr_result.get('success'):
        # API 调用出错，降级 Mock
        ocr_result = mock_ocr(filename)
        ocr_result['warning'] = 'AI 识别失败，已自动降级'
        ocr_result['source'] = 'mock_fallback'

    # 真实 API 成功时，跳过 Mock 分类（API 已经返回 category）
    if ocr_result.get('success') and not ocr_result.get('warning') and ocr_result.get('source') == 'mock':
        ocr_result['category'] = classify_medicine(
            ocr_result.get('name', ''),
            ocr_result.get('brand', '')
        )

    ocr_result['image_path'] = f'/uploads/{save_name}'
    return jsonify(ocr_result)


@app.route('/api/medicines', methods=['POST'])
def api_create_medicine():
    data = request.json
    required = ['name', 'category']
    for f in required:
        if not data.get(f):
            return jsonify({'success': False, 'error': f'缺少字段 {f}'}), 400

    conn = get_db()
    duplicate = conn.execute(
        """SELECT * FROM medicines
           WHERE status='active' AND name=? AND brand=? AND id != COALESCE(?, 0)""",
        (data.get('name', ''), data.get('brand', ''), data.get('ignore_duplicate_id'))
    ).fetchone()
    conn.close()

    if duplicate and not data.get('force_create'):
        return jsonify({
            'success': False,
            'duplicate': True,
            'existing': {
                'id': duplicate['id'],
                'name': duplicate['name'],
                'brand': duplicate['brand'],
                'spec': duplicate['spec'],
                'remaining_pct': duplicate['remaining_pct'],
                'location': duplicate['location'],
            },
            'message': f'已有相同的 {data.get("name")} ({data.get("brand")})，位置：{duplicate["location"]}，是否合并库存？'
        })

    conn = get_db()
    cursor = conn.execute(
        '''INSERT INTO medicines
           (name, brand, spec, category, location, expiry_date, remaining_pct, notes, image_path)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (
            data['name'],
            data.get('brand', ''),
            data.get('spec', ''),
            data['category'],
            data.get('location', '未指定'),
            data.get('expiry_date'),
            int(data.get('remaining_pct', 100)),
            data.get('notes', ''),
            data.get('image_path', ''),
        )
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return jsonify({'success': True, 'id': new_id, 'message': '入库成功'})


@app.route('/api/medicines/<int:mid>/merge', methods=['POST'])
def api_merge_medicine(mid):
    data = request.json
    add_pct = int(data.get('add_pct', 0))

    conn = get_db()
    conn.execute(
        '''UPDATE medicines
           SET remaining_pct = MIN(100, remaining_pct + ?),
               updated_at = CURRENT_TIMESTAMP
           WHERE id=?''',
        (add_pct, mid)
    )
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': '库存已合并'})


@app.route('/api/medicines/<int:mid>', methods=['PUT'])
def api_update_medicine(mid):
    data = request.json
    conn = get_db()
    conn.execute(
        '''UPDATE medicines
           SET name=?, brand=?, spec=?, category=?, location=?,
               expiry_date=?, remaining_pct=?, notes=?,
               updated_at=CURRENT_TIMESTAMP
           WHERE id=?''',
        (
            data.get('name'),
            data.get('brand', ''),
            data.get('spec', ''),
            data.get('category'),
            data.get('location', '未指定'),
            data.get('expiry_date'),
            int(data.get('remaining_pct', 100)),
            data.get('notes', ''),
            mid,
        )
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/medicines/<int:mid>/discard', methods=['POST'])
def api_discard_medicine(mid):
    conn = get_db()
    conn.execute(
        "UPDATE medicines SET status='discarded', updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (mid,)
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/stats')
def api_stats():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM medicines WHERE status='active'").fetchone()[0]
    expired = conn.execute(
        "SELECT COUNT(*) FROM medicines WHERE status='active' AND expiry_date < DATE('now')"
    ).fetchone()[0]
    expiring = conn.execute(
        "SELECT COUNT(*) FROM medicines WHERE status='active' AND expiry_date BETWEEN DATE('now') AND DATE('now', '+30 days')"
    ).fetchone()[0]
    conn.close()
    return jsonify({
        'total': total,
        'expired': expired,
        'expiring': expiring,
    })


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    from flask import send_from_directory
    return send_from_directory(UPLOAD_DIR, filename)


# ============== 启动 ==============
if __name__ == '__main__':
    init_db()
    print('=' * 50)
    print('🏠 智能药箱 Demo')
    print('=' * 50)
    print(f'📂 数据库: {DB_PATH}')
    print(f'📂 上传目录: {UPLOAD_DIR}')
    print('🌐 访问: http://localhost:5050')
    print('=' * 50)
    app.run(debug=True, port=5050)
