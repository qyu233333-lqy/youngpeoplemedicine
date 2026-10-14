# 简单运行说明

## 🚀 方式 A：直接访问已部署的公网 Demo（最快）

**Demo 已在 Railway 部署，浏览器直接打开**：

```
https://youngpeoplemedicine-production.up.railway.app
```

无需任何配置，自动包含：
- ✅ 智能药箱屏幕主界面
- ✅ 8 个预填示例药品（含过期 + 即将过期）
- ✅ "🔍 找药"功能
- ✅ "⚡ 快速添加"功能（45 个常见 OTC 药品）
- ✅ "📷 拍照入库"功能（含 OCR 异常处理）

---

## 🛠️ 方式 B：本地运行（5 步）

### 第 1 步：克隆代码

```bash
git clone https://github.com/qyu233333-lqy/youngpeoplemedicine.git
cd youngpeoplemedicine
```

### 第 2 步：安装依赖

需要 Python 3.11+：

```bash
pip install -r requirements.txt
```

依赖包：
- Flask 3.0.0
- Werkzeug 3.0.1
- requests 2.31.0
- gunicorn 21.2.0

### 第 3 步：（可选）配置 MiniMax API

如果想让 OCR 用真实 AI 识别（而不是 Mock），创建 `.env` 文件：

```bash
cp .env.example .env
```

然后编辑 `.env`：

```bash
MINIMAX_API_KEY=sk-cp-你的完整key
```

**不填也能跑**——会降级到 Mock OCR（基于文件名匹配）。

### 第 4 步：启动

```bash
python3 app.py
```

或者用一键脚本：

```bash
chmod +x start.sh
./start.sh
```

看到这行就是启动成功：

```
🏠 智能药箱 Demo
🌐 访问: http://localhost:5050
```

### 第 5 步：打开浏览器

```
http://localhost:5050
```

---

## 🚂 方式 C：自己部署到 Railway（10 分钟）

### 第 1 步：推到 GitHub

```bash
git init
git add .
git commit -m "智能药箱 v1"
# 在 GitHub 创建 repo，然后：
git remote add origin https://github.com/你的用户名/medicine-box.git
git push -u origin main
```

### 第 2 步：Railway 部署

1. 打开 https://railway.app
2. 用 GitHub 登录
3. **New Project** → **Deploy from GitHub repo** → 选你的 repo
4. 等 2-3 分钟自动构建

### 第 3 步：设置环境变量

在 Railway 项目 → **Variables** 标签 → 添加：

```
MINIMAX_API_KEY = 你的完整 key
```

Railway 会自动重新部署。

### 第 4 步：生成公网 URL

在 Railway 项目 → **Settings** → **Networking** → **Generate Domain**

---

## ✅ 部署/启动后验证清单

打开 Demo URL 后，依次测试：

- [ ] **首页** - 看到智能药箱屏幕（黑色边框 + LED 灯 + 蓝色 header）
- [ ] **过期 banner** - 顶部有红色"1过期"+ 黄色"1即将过期"
- [ ] **药品列表** - 看到 8 个药品，每个显示📍位置（抽屉A·第1格等）
- [ ] **🔍 找药** - 点击搜索 → 输入"退烧" → 返回布洛芬 + 位置
- [ ] **⚡ 快速添加** - 点击 → 搜"布洛芬" → 选品牌 → 选位置 → 入库
- [ ] **📷 拍照入库** - 点击 → 上传图片 → OCR 识别
- [ ] **异常演示** - 上传文件名含 `fail` 的图片 → 触发识别失败

---

## 🐛 常见问题

### Q1: 启动报 "ModuleNotFoundError: No module named 'flask'"
→ 没装依赖：`pip install -r requirements.txt`

### Q2: 端口被占用
→ 改 app.py 最后一行：`port=int(os.environ.get('PORT', 5050))` 改为其他端口

### Q3: OCR 不工作
→ 检查 `.env` 里 `MINIMAX_API_KEY` 是否正确；没填也能跑（Mock 模式）

### Q4: 数据库错误
→ 删除 `data/medicine_box.db`，重启会自动重建

### Q5: Railway 部署失败
→ 看 Logs 标签；常见是 Python 版本不对，已在 runtime.txt 固定 3.11.6

---

## 📞 联系

- GitHub 仓库：https://github.com/qyu233333-lqy/youngpeoplemedicine
- 在线 Demo：https://youngpeoplemedicine-production.up.railway.app
