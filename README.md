# 🏠 智能药箱 Demo v1

> **第一版服务 25-30 岁独居/合租白领**。解决一件事：让你随时知道"我家有什么药、放在哪、还能不能吃"。

## 🌐 在线 Demo

**https://youngpeoplemedicine-production.up.railway.app**

无需任何配置，浏览器直接打开。

## 📂 项目文档

| 文档 | 作用 |
|------|------|
| **[PRODUCT.md](./PRODUCT.md)** | 产品说明（题目要求 ①） |
| **[RUN.md](./RUN.md)** | 简单运行说明（题目要求 ②） |
| **[RETROSPECTIVE.md](./RETROSPECTIVE.md)** | 复盘（题目要求 ③） |

## ⚡ 快速开始（30 秒）

```bash
# 1. 克隆
git clone https://github.com/qyu233333-lqy/youngpeoplemedicine.git
cd youngpeoplemedicine

# 2. 装依赖
pip install -r requirements.txt

# 3. 跑
python3 app.py

# 4. 浏览器打开 http://localhost:5050
```

完整说明见 **[RUN.md](./RUN.md)**。

## 🎯 一句话定位

> **"对于平时很少管理药品、需要时才打开药箱的年轻人，智能药箱第一版解决：让你不用翻抽屉、不用打开手机 App，看一眼药箱屏幕就知道答案。"**

## 🌟 核心洞察

1. **形态决策**：题目说"用户很少管理、需要时才打开"→ App 形态是错的 → **带屏幕的智能药箱**才是正确解
2. **多模态入库**：拍照 OCR + 快速添加（5 秒）+ 条码扫描 → 给用户最优路径
3. **边界即护城河**：不做症状推荐、不做诊断 → 别人想做不敢做，我们守边界就是守信任

## 🔑 关键能力

- 🔍 **找药**：输入症状（"退烧"）→ 显示位置（"抽屉A·第1格"）
- ⚡ **快速添加**：5 秒入库，45 个常见 OTC 药品库
- 📷 **拍照入库**：MiniMax M3.1 视觉模型真实识别
- ⏰ **过期预警**：30 天/7 天/1 天分级提醒
- 🔁 **重复检测**：同品牌入库前提示合并

## 🤖 AI 集成

- **OCR 视觉识别**：MiniMax M3.1 Flash Preview（支持图像）
- **LLM 自动分类**：结构化输出感冒/肠胃/外用/保健
- **降级方案**：API 失败 → Mock 模式（基于关键词）

## 📊 技术栈

- **后端**：Python 3.11 + Flask + SQLite
- **前端**：Tailwind CSS（CDN）+ 原生 JavaScript
- **部署**：Railway + Gunicorn
- **AI**：MiniMax API（OpenAI 兼容接口）

## ⏱️ 投入时间

约 4 小时（含产品思考 + 代码 + 部署 + 文档）

详细复盘见 **[RETROSPECTIVE.md](./RETROSPECTIVE.md)**

## 📁 文件结构

```
medicine-box-demo/
├── PRODUCT.md            ← 产品说明
├── RUN.md                ← 简单运行说明
├── RETROSPECTIVE.md      ← 复盘
├── README.md             ← 本文件
├── app.py                ← Flask 主程序
├── requirements.txt      ← 依赖
├── Procfile              ← Railway 启动
├── railway.toml          ← Railway 配置
├── runtime.txt           ← Python 版本
├── .env.example          ← 环境变量模板
├── .gitignore
├── start.sh              ← 本地启动脚本
├── static/style.css
├── templates/            ← 5 个 HTML 模板
│   ├── index.html        ← 智能药箱屏幕（首页）
│   ├── scan.html         ← 拍照入库
│   ├── quick_add.html    ← 快速添加
│   ├── search.html       ← 找药
│   └── medicine_detail.html
└── uploads/              ← 用户上传图片
```

## 📞 链接

- 🌐 **在线 Demo**：https://youngpeoplemedicine-production.up.railway.app
- 💻 **GitHub 仓库**：https://github.com/qyu233333-lqy/youngpeoplemedicine

---

## 📝 提交清单

按题目要求（03 提交内容与规则）：

| 项 | 文件 | 状态 |
|---|------|------|
| ① 产品说明 | `PRODUCT.md` | ✅ |
| ② 部署 Demo | Railway URL | ✅ |
| ② 源代码 | `app.py` + `templates/` | ✅ |
| ② 简单运行说明 | `RUN.md` | ✅ |
| ③ 复盘 | `RETROSPECTIVE.md` | ✅ |
| AI/Coding 工具 | `RETROSPECTIVE.md` 第六节 | ✅ |
| 实际投入时间 | `RETROSPECTIVE.md` / `PRODUCT.md` | ✅ |
