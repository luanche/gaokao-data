# 🎓 重庆高考志愿填报数据分析

> 2025-2026年重庆高考录取数据查询、志愿推荐与招生计划分析工具

---

## 📦 数据来源

原始 Excel 数据放在 `excel_data/` 目录下，来源于网络收集的重庆高考历史录取数据。

**如果你想重新生成 JSON**，需要先从夸克网盘下载最新数据：

1. 打开：https://pan.quark.cn/s/f5bdc51dea3a
2. 下载数据，覆盖到 `excel_data/` 目录
3. 运行转换脚本重新生成 JSON

---

## 🚀 快速开始

### 安装依赖

```bash
pip install openpyxl pandas
```

### 下载数据并转成 JSON（可选）

如果你下载了最新的 Excel 数据，运行：

```bash
python3 scripts/convert_all_to_json.py
```

这会把 `excel_data/` 下所有 `.xlsx` 文件转换成结构化 JSON，输出到 `json_data/` 目录。

### 查询分析

```bash
python3 scripts/query_analysis.py help
```

### 志愿推荐（交互式）

```bash
python3 .pi/skills/gaokao-recommend/scripts/recommend.py
```

或者在 pi（AI 编程助手）中对我说：

> 使用 gaokao-recommend 帮我推荐学校和专业

### 定制推荐（直接修改配置）

```bash
python3 custom_recommend.py
```

快速为一个固定分数/偏好生成推荐，直接在脚本里修改配置即可。

### 生成交互式志愿规划网页

```bash
python3 .pi/skills/gaokao-recommend/scripts/generate_plan.py
```

基于一表联动数据，为选定院校和专业生成增强版 JSON 和可拖拽排序的 HTML 志愿表。

---

## 📊 项目结构

```
gaokao-data/
├── excel_data/                          # 原始 Excel 数据（需自行下载）
│   └── 03、重庆-2026高考志愿填报资料/
│       ├── 3-重庆录取数据22-25【持续更新】/      # 2022-2025年最新数据
│       │   ├── 22-25年全国高校在重庆的院校录取分数.xlsx
│       │   ├── 22-25年全国高校在重庆的专业录取分数.xlsx
│       │   ├── 22-25年全国高校在重庆的招生计划.xlsx
│       │   ├── 22-25年重庆（一表联动）.xlsx
│       │   └── 一分一段/
│       └── 4-重庆高考历史数据/               # 2017-2024年历史数据
│           ├── 重庆_招生计划/
│           ├── 重庆_专业分数线/
│           ├── 重庆_投档线/
│           └── 重庆市-一分一段表/
├── json_data/                           # 转换后的 JSON 数据
│   ├── score_distribution_2026.json     # 2026年一分一段表
│   ├── enrollment_plans_2026.json       # 2026年招生计划（27142条）
│   ├── latest_school_scores.json        # 2022-2025院校录取分数
│   ├── latest_major_scores.json         # 2022-2025专业录取分数
│   ├── latest_enrollment_plans.json     # 2022-2025招生计划
│   ├── latest_score_distribution.json   # 2022-2025一分一段表
│   ├── combined_table.json              # 一表联动综合数据
│   └── province_control_lines.json      # 省控线/批次线
├── custom_recommend.py                  # 定制推荐脚本（固定配置）
├── scripts/                             # 脚本工具
│   ├── convert_all_to_json.py           # Excel → JSON 转换（含2026计划）
│   └── query_analysis.py               # 多维度查询分析
├── .pi/skills/gaokao-recommend/         # AI 技能（志愿推荐）
│   ├── SKILL.md
│   ├── scripts/
│   │   ├── recommend.py                 # 交互式志愿推荐
│   │   └── generate_plan.py             # 生成增强版JSON+HTML志愿表
└── README.md
```

> 注：已清理 2017-2021 年历史大数据文件（`historical_*`），仅保留 2022-2025 近三年录取数据 + 2026年招生计划及一分一段表。

---

## 🔍 查询脚本使用案例

### 1️⃣ 查某个学校

想知道 **重庆大学** 近几年的录取分数线：

```bash
python3 scripts/query_analysis.py school 重庆大学
```

想知道 **重庆文理学院** 2025年物理类的录取情况：

```bash
python3 scripts/query_analysis.py school 重庆文理学院 2025 物理类
```

### 2️⃣ 查某个专业

想知道 **计算机科学与技术** 2025年有哪些学校在重庆招生：

```bash
python3 scripts/query_analysis.py major 计算机 2025 物理类
```

### 3️⃣ 按分数找学校

物理类 **490-500分** 能上哪些本科院校：

```bash
python3 scripts/query_analysis.py score 490 500 2025 物理类 本科批
```

### 4️⃣ 按位次找学校

位次 **前5000名** 能上哪些学校：

```bash
python3 scripts/query_analysis.py rank 5000 2025 物理类 本科批
```

### 5️⃣ 同位次分数换算

想知道2025年的 **650分** 相当于2024年的多少分：

```bash
python3 scripts/query_analysis.py convert 2025 650 2024
```

### 6️⃣ 热门专业排名

2025年物理类开设院校最多的专业：

```bash
python3 scripts/query_analysis.py popular 2025
```

### 7️⃣ 985/211院校分析

2025年985和211院校在重庆的录取情况：

```bash
python3 scripts/query_analysis.py elite 2025
```

### 8️⃣ 省控线查询

查重庆近几年的省控线：

```bash
python3 scripts/query_analysis.py control 重庆
```

### 9️⃣ 年度数据总览

2025年重庆高考录取数据概览：

```bash
python3 scripts/query_analysis.py summary 2025
```

---

## 🧠 AI 志愿推荐技能（gaokao-recommend）

这是本项目最强的功能——只要告诉你的分数，就能自动推荐学校和专业。支持 **2023-2025年三年数据对比** + **2026年官方招生计划**。

### 交互式推荐

```bash
python3 .pi/skills/gaokao-recommend/scripts/recommend.py
```

系统提供 **两种模式**：

#### 模式1：推荐模式
| 问题 | 说明 |
|------|------|
| 模式选择 | 推荐模式(1) 或 招生计划查询模式(2) |
| 考试年份 | 2026 或 2025（默认2026） |
| 科类 | 物理类 / 历史类 |
| 分数 | 你的高考分数 |
| 批次 | 本科批 / 专科批 / 本科提前批B段 |
| 浮动范围 | 上下浮动多少分（默认±5） |
| 是否只看985/211 | 可选 |
| 偏好省份/地区 | 如重庆、四川等，可选 |
| 专业方向 | 如计算机、医学、师范，可选 |
| 城市类型 | 一线/新一线，可选 |

#### 模式2：招生计划查询模式
| 问题 | 说明 |
|------|------|
| 科类 | 物理类 / 历史类 |
| 批次 | 本科批 / 专科批 / 本科提前批等 |
| 查询方式 | 按院校名称 / 按专业关键词 / 列出所有院校 |

### 核心功能：2026年分数自动换算

```
你的2026年分数
    ↓
查2026年一分一段表 → 得到位次
    ↓
用位次找2025/2024/2023年的等效分
    ↓
参考23-25年三年数据推荐学校+专业
    ↓
展示各院校/专业2026年计划招生人数
```

每条推荐都附带 **历年趋势**（按你的排名在各年的等效分对比，不是简单地比原始分数）以及 **2026年计划人数**：
```
你的排名64,996在各年等效分：2025年≈495  2024年≈492  2023年≈451

四川外国语大学历年：
  2025年:500(↑5)  ← 500 vs 495(你的等效) = 高5分
  2024年:507(↑15) ← 507 vs 492(你的等效) = 高15分
  2023年:462(↑11) ← 462 vs 451(你的等效) = 高11分
  2026年计划招生: 85人（物理类本科批）
```

趋势标记含义：
- `↑5` = 比该年等效分高5分（冲刺）
- `↓3` = 比该年等效分低3分（保底）
- `=` = 持平（稳妥）

### 使用示例

你只需说：
> "我2026年物理类497分，帮我推荐"

系统就会：
1. 算出去年等效 **495分**（位次64,996）
2. 找出 **冲刺66所、稳妥18所、保底74所** 院校
3. 列出各院校 **327个专业** 的详细数据
4. 每条都标注23-25年涨跌趋势
5. 每条都显示该院校/专业 **2026年计划招生人数**

### 定制推荐脚本

如果你有一个固定分数和偏好，可以直接修改 `custom_recommend.py` 中的配置快速运行：
```bash
python3 custom_recommend.py
```
脚本顶部 `SCORE_2026`、`RANK_2026`、`EQUIV`、`排除省份`、`排除专业` 等均可直接修改，适合反复微调。

---

## 🗺️ 一键生成交互式志愿规划网页

基于 `combined_table.json`（一表联动）和 `enrollment_plans_2026.json`（2026招生计划），可以为选定院校和专业生成增强版 JSON 和可拖拽排序的 HTML 网页。

### 运行

```bash
cd /root/projects/gaokao-data && python3 .pi/skills/gaokao-recommend/scripts/generate_plan.py
```

输出文件：
- `.tmp/志愿推荐.json` — 增强版JSON数据
- `.tmp/志愿推荐.html` — 交互式志愿规划网页（直接在浏览器打开）

### 数据增强
每条数据包含：
- **专业代码** — 从 combined_table 精确匹配
- **2023-2025三年详细分数** — 最低分/位次、平均分/位次、最高分、录取人数
- **2026年招生计划** — 计划人数、学制、学费、选科要求、专业层次、门类、专业类
- **学校详细信息** — 所在省、城市、城市水平标签、院校标签、是否985/211、隶属单位、类型、公私性质

### 网页功能
1. **三栏布局** — 冲刺/稳妥/保底分栏展示，颜色区分
2. **拖拽排序** — SortableJS 实现，同栏可拖拽调整优先级
3. **删除/恢复** — 删除到回收区，可恢复
4. **搜索筛选** — 按学校/专业名称搜索，按新增/原有专业筛选
5. **导出志愿表** — 导出 Markdown 格式表格
6. **另存为HTML** — 保存当前排序状态为独立HTML文件
7. **自动保存** — 所有操作保存在浏览器 localStorage

---

## 📋 数据字段说明

### 院校录取分数（latest_school_scores.json）

| 字段 | 说明 |
|------|------|
| 年份 | 2022-2025 |
| 院校名称 | 全国高校名称 |
| 科类 | 物理类 / 历史类 |
| 批次 | 本科批、专科批、本科提前批等 |
| 最低分数 | 最低录取分 |
| 最低分位 | 最低录取位次 |
| 批次线差 | 最低分 - 省控线 |
| 学校所在 | 省份/直辖市 |
| 是否985 | 是/否 |
| 是否211 | 是/否 |

### 专业录取分数（latest_major_scores.json）

| 字段 | 说明 |
|------|------|
| 年份 | 2022-2025 |
| 院校名称 | 全国高校名称 |
| 专业名称 | 招生专业 |
| 专业备注 | 专业备注信息 |
| 最低分数 | 该专业最低录取分 |
| 最低位次 | 该专业最低录取位次 |

### 2026年招生计划（enrollment_plans_2026.json）

| 字段 | 说明 |
|------|------|
| 年份 | 2026 |
| 批次 | 本科批、专科批、本科提前批等 |
| 科类 | 物理类 / 历史类 |
| 院校代码 | 院校代码 |
| 院校名称 | 招生院校 |
| 专业代码 | 专业代码 |
| 专业全称 | 专业完整名称 |
| 专业名称 | 专业简称 |
| 专业备注 | 备注信息（办学地点等） |
| 选科要求 | 选考科目要求 |
| 专业层次 | 本科/专科 |
| 计划人数 | 2026年计划招生人数 |
| 学制 | 学习年限 |
| 学费 | 学费标准 |
| 门类 | 学科门类 |
| 专业类 | 专业类别 |
| 是否新增 | 是否为2026年新增专业 |

---

## 📊 数据统计

| 数据文件 | 记录数 |
|----------|--------|
| `score_distribution_2026.json` | 物理类504条 + 历史类484条 |
| `enrollment_plans_2026.json` | **27,142条**（物理类18,868 + 历史类8,274） |
| `latest_school_scores.json` | **14,988条** |
| `latest_major_scores.json` | **89,443条** |
| `latest_enrollment_plans.json` | **96,622条** |
| `latest_score_distribution.json` | 3,888条 |
| `combined_table.json` | 一表联动综合数据 |
| `province_control_lines.json` | 6,748条 |

---

## ⚠️ 注意事项

1. **2026年一分一段表** 和 **2026年招生计划** 已内置在 `json_data/`，不需要重新下载
2. 其他 JSON 数据是转换好的，可以直接使用
3. 如需更新数据，从夸克网盘下载 Excel 后运行 `convert_all_to_json.py`
4. 已清理 2017-2021 年历史大数据（`historical_*` 文件），仅保留 2022-2025 近三年数据 + 2026 年招生计划
5. 所有数据仅供志愿填报参考，请以重庆市教育考试院官方数据为准

---

## 🔗 链接

- 夸克网盘数据下载：https://pan.quark.cn/s/f5bdc51dea3a
- 重庆市教育考试院：https://www.cqksy.cn
- 2026年一分一段表（物理类）：https://www.cqksy.cn/uploadFile/infopub/2026/ptgk/yfd/lk.htm
- 2026年一分一段表（历史类）：https://www.cqksy.cn/uploadFile/infopub/2026/ptgk/yfd/wk.htm
