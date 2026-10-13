# 🏠 智能药箱 Demo

## 一句话定位
> 第一版服务 25-30 岁独居/合租白领。解决一件事：你家抽屉里那堆不知道过期没、找不到、重复买的药，让你能"3 分钟拍完、随时查到、永不吃过期"。

## 🚀 快速开始

### 1. 安装依赖
```bash
cd medicine-box-demo
pip install -r requirements.txt
```

### 2. 启动
```bash
python app.py
```

### 3. 访问
打开浏览器：http://localhost:5000

首次启动会自动创建 SQLite 数据库 + 填充 7 条示例药品数据。

## 📂 项目结构

```
medicine-box-demo/
├── app.py                  # Flask 主程序（472 行）
├── requirements.txt        # 依赖（Flask）
├── medicine_box.db         # SQLite 数据库（自动生成）
├── README.md               # 本文件
├── templates/
│   ├── index.html          # 首页 - 库存总览
│   ├── scan.html           # 拍照入库页（核心流程）
│   ├── medicine_detail.html # 药品详情页
│   └── search.html         # 搜索页
├── static/
│   └── style.css           # 自定义样式
└── uploads/                # 上传图片（自动生成）
```

## 🎯 核心功能

| 功能 | 路径 | 状态 |
|------|------|------|
| 库存总览（分类筛选 + 过期预警） | `/` | ✅ |
| 拍照入库（OCR + LLM 分类 + 重复检测） | `/scan` | ✅ |
| 药品详情（编辑剩余 + 标记丢弃） | `/medicine/<id>` | ✅ |
| 智能搜索（"我家有没有 X"） | `/search` | ✅ |

## 🤖 AI 能力（Mock 模式，无需 API Key）

### 1. OCR 识别（Mock）
- 根据上传文件名的关键词匹配药品库
- 15% 概率模拟"识别失败"（文件名包含 "fail"）
- 10% 概率模拟"识别不完整"（缺有效期）

### 2. LLM 分类（Mock）
- 基于关键词规则匹配：感冒 / 肠胃 / 外用 / 保健 / 其他

### 3. 重复检测
- 入库前自动检测同品牌药品
- 提示"合并库存"或"新建"

### 4. 过期预警
- 已过期：红色
- 30 天内：黄色
- 正常：绿色

## 🧪 异常处理演示

**演示 1：识别失败**
- 上传文件名包含 "fail" 的图片（如 `fail_test.jpg`）
- 系统提示"识别失败"，引导手动录入

**演示 2：识别不完整**
- 上传文件名包含 "999" 的图片（如 `感冒灵.jpg`）
- 随机 10% 概率触发"有效期识别失败"提示

**演示 3：重复药品**
- 上传维生素 C 相关图片
- 系统提示"已有 1 个维生素 C，是否合并？"

## 🎬 演示脚本（5 分钟）

```
1. (30s) 首页展示：
   - 看到 7 个示例药品
   - 顶部红色 banner：1 个已过期
   - 顶部黄色 banner：1 个即将过期

2. (1min) 搜索演示：
   - 搜索"退烧"
   - 找到布洛芬

3. (1min) 正常识别：
   - 上传"布洛芬.jpg"
   - OCR 成功 → 自动分类"感冒"
   - 入库成功

4. (1min) 异常处理：
   - 上传"fail_test.jpg"
   - 识别失败 → 提示手动录入
   - 手动填入正确信息 → 入库成功

5. (1min) 重复检测：
   - 上传"维生素.jpg"
   - 检测到已有维生素 C
   - 选择"合并库存"
   - 库存百分比上升

6. 总结：边界声明 - 不做症状推荐、诊断
```

## 🔧 切换到真实 API（可选）

### 百度 OCR
设置环境变量：
```bash
export BAIDU_OCR_API_KEY="your_key"
```

### OpenAI / Qwen LLM
在 `app.py` 中修改 `classify_medicine` 函数调用真实 API。

## 📋 边界声明

本 Demo 严格遵守产品边界：
- ✅ 只做：库存管理、过期提醒、重复检测、查询
- ❌ 不做：症状推荐、疾病诊断、处方药管理、用药建议

所有 AI 输出限定为"事实呈现"（如"这盒药 2024-12 到期"），不做"行动建议"（如"建议你吃这个"）。

## 📊 数据流（核心流程）

```
用户上传图片 
  → POST /api/scan 
  → OCR 识别（药品名/品牌/规格/有效期）
  → LLM 分类（感冒/肠胃/外用/保健）
  → 重复检测
  → 用户确认表单（可编辑）
  → POST /api/medicines
  → 写入 SQLite
  → 跳回首页，库存更新
```

---

## 🚀 部署上线

### 方案 A：Railway 一键部署（推荐）

1. 把项目推到 GitHub：
```bash
git init
git add .
git commit -m "init"
# 在 GitHub 创建 repo，然后：
git remote add origin https://github.com/yourname/medicine-box-demo.git
git push -u origin main
```

2. 到 [railway.app](https://railway.app) 用 GitHub 登录

3. 点击 "New Project" → "Deploy from GitHub repo" → 选这个项目

4. 在 Variables 里设置环境变量：
   - `MINIMAX_API_KEY` = 你的真实 Key

5. Railway 自动检测 Python + gunicorn，给你一个 https://xxx.up.railway.app URL

### 方案 B：Render 部署

1. 推 GitHub（同上）
2. 到 [render.com](https://render.com) 用 GitHub 登录
3. New Web Service → 选 repo
4. 设置：
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT`
5. 添加环境变量 `MINIMAX_API_KEY`

### 方案 C：本地公网暴露（ngrok）

```bash
# 启动 Flask
python3 app.py

# 另一个终端
ngrok http 5050
# 得到 https://xxx.ngrok-free.app
```

### ⚠️ SQLite 在云平台注意事项

Railway/Render 免费版重启会丢数据。如果需要持久化：
- Railway: 加 Volume 挂载到 `/app/data`
- Render: 用 Persistent Disk（需付费）
- 或者换 PostgreSQL（免费层用 Neon/Supabase）

**笔试场景下数据丢失无所谓**，重启后重新入库即可。

---

## 🔑 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `MINIMAX_API_KEY` | 否 | 没填则降级 Mock OCR |
| `MINIMAX_API_BASE` | 否 | 默认 `https://api.minimaxi.com/v1` |
| `MINIMAX_MODEL` | 否 | 默认 `MiniMax-M3` |
| `PORT` | 自动 | Railway/Render 会自动注入 |
| `DB_PATH` | 否 | SQLite 数据库路径，默认 `data/medicine_box.db` |
