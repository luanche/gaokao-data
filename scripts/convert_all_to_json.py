"""
高考数据 - 全部 Excel 转 JSON 脚本
将 excel_data/03、重庆-2026高考志愿填报资料/ 下的所有 xlsx 文件
按类别转换成结构化的 JSON 文件，输出到 json_data/ 目录。
"""

import pandas as pd
import json
import os
import re
from collections import defaultdict

# ============== 配置 ==============
DATA_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                         "excel_data", "03、重庆-2026高考志愿填报资料")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "json_data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============== 工具函数 ==============

def sanitize(val):
    """将 NaN / NaT 转为 None，确保 JSON 可序列化"""
    if pd.isna(val):
        return None
    if isinstance(val, (float,)):
        if val != val:  # NaN
            return None
    return val

def row_to_dict(row, columns):
    """将一行数据转为 dict，处理 NaN"""
    d = {}
    for col in columns:
        d[col] = sanitize(row[col])
    return d

def save_json(data, filename, indent=2, encoding='utf-8'):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, 'w', encoding=encoding) as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)
    print(f"  ✓ 已保存: {path} ({len(data)} 条记录)")
    return path

def parse_int(v):
    """尝试将值转为 int，失败返回 None"""
    if v is None:
        return None
    try:
        return int(float(str(v).replace(',', '')))
    except (ValueError, TypeError):
        return None

def safe_float(v):
    if v is None:
        return None
    try:
        f = float(v)
        if f != f:  # NaN
            return None
        return f
    except:
        return None


# ================================================================
#  第一部分: 4-重庆高考历史数据 （2017-2024 历史数据）
# ================================================================

def convert_historical_enrollment_plans():
    """重庆_招生计划 (2017-2024)"""
    base = os.path.join(DATA_ROOT, "4-重庆高考历史数据", "重庆_招生计划")
    all_records = []
    for fname in sorted(os.listdir(base)):
        if not fname.endswith('.xlsx') or '副本' in fname:
            continue
        fp = os.path.join(base, fname)
        try:
            df = pd.read_excel(fp)
        except Exception as e:
            print(f"  ⚠ 读取失败: {fname} - {e}")
            continue
        year = re.search(r'(\d{4})', fname)
        year_str = year.group(1) if year else "未知"
        for _, row in df.iterrows():
            record = {
                "省份": sanitize(row.get("省份")),
                "年份": sanitize(row.get("年份")) or year_str,
                "科类": sanitize(row.get("科类")),
                "批次": sanitize(row.get("批次")),
                "院校代码": sanitize(row.get("院校代码")),
                "院校名称": sanitize(row.get("院校名称")),
                "专业代码": sanitize(row.get("专业代码")),
                "专业名称": sanitize(row.get("专业名称")),
                "专业备注": sanitize(row.get("专业备注")),
                "计划数": parse_int(row.get("计划数")),
                "学制": parse_int(row.get("学制")),
                "学费": parse_int(row.get("学费")),
                "选考要求": sanitize(row.get("选考要求")),
            }
            all_records.append(record)
    save_json(all_records, "historical_enrollment_plans.json")
    return all_records


def convert_historical_major_scores():
    """重庆_专业分数线 (2017-2023) — 注意不同年份列名略有差异"""
    base = os.path.join(DATA_ROOT, "4-重庆高考历史数据", "重庆_专业分数线")
    all_records = []
    for fname in sorted(os.listdir(base)):
        if not fname.endswith('.xlsx') or '副本' in fname:
            continue
        fp = os.path.join(base, fname)
        try:
            xl = pd.ExcelFile(fp)
        except Exception as e:
            print(f"  ⚠ 读取失败: {fname} - {e}")
            continue
        year_match = re.search(r'(\d{4})', fname)
        year_str = year_match.group(1) if year_match else "未知"

        for sheet_name in xl.sheet_names:
            df = pd.read_excel(fp, sheet_name=sheet_name)
            # 根据列名自动检测格式
            cols = list(df.columns)
            if '学校' in cols or '院校名称' in cols:
                # 2017 格式: 年份, 学校, 省份, 城市, 软科排名, _985, _211, 双一流, 科类, 批次,
                #           门类, 一级学科, 专业, 平均分, 最高分, 最低分, 最低分排名, ...
                for _, row in df.iterrows():
                    record = {
                        "年份": sanitize(row.get("年份")) or year_str,
                        "院校名称": sanitize(row.get("学校")),
                        "科类": sanitize(row.get("科类")),
                        "批次": sanitize(row.get("批次")),
                        "门类": sanitize(row.get("门类")),
                        "一级学科": sanitize(row.get("一级学科")),
                        "专业名称": sanitize(row.get("专业")),
                        "最低分": safe_float(row.get("最低分")),
                        "最低位次": parse_int(row.get("最低分排名")),
                        "最高分": safe_float(row.get("最高分")),
                        "平均分": safe_float(row.get("平均分")),
                        "省份": sanitize(row.get("省份")),
                        "城市": sanitize(row.get("城市")),
                        "软科排名": parse_int(row.get("软科排名")),
                        "985": sanitize(row.get("_985")),
                        "211": sanitize(row.get("_211")),
                        "双一流": sanitize(row.get("双一流")),
                        "办学性质": sanitize(row.get("办学性质")),
                        "学校归属": sanitize(row.get("学校归属")),
                        "学校代码": sanitize(row.get("全国统一招生代码")),
                        "招生类型": sanitize(row.get("招生类型")),
                        "学历类别": sanitize(row.get("学历类别")),
                        "生源地": sanitize(row.get("生源地")) or "重庆",
                    }
                    all_records.append(record)
            else:
                # 2018-2023 格式: 年份, 生源地, 科类, 批次, 院校名称, 专业名称, 专业备注, 最低分, 最低位次, 最高分, 平均分
                for _, row in df.iterrows():
                    record = {
                        "年份": sanitize(row.get("年份")) or year_str,
                        "生源地": sanitize(row.get("生源地")) or "重庆",
                        "科类": sanitize(row.get("科类")),
                        "批次": sanitize(row.get("批次")),
                        "院校名称": sanitize(row.get("院校名称")),
                        "专业名称": sanitize(row.get("专业名称")),
                        "专业备注": sanitize(row.get("专业备注")),
                        "最低分": safe_float(row.get("最低分")),
                        "最低位次": parse_int(row.get("最低位次")),
                        "最高分": safe_float(row.get("最高分")),
                        "平均分": safe_float(row.get("平均分")),
                    }
                    all_records.append(record)
    save_json(all_records, "historical_major_scores.json")
    return all_records


def convert_historical_toudang_lines():
    """重庆_投档线 (2017-2023)"""
    base = os.path.join(DATA_ROOT, "4-重庆高考历史数据", "重庆_投档线")
    all_records = []
    for fname in sorted(os.listdir(base)):
        if not fname.endswith('.xlsx') or '副本' in fname:
            continue
        fp = os.path.join(base, fname)
        try:
            xl = pd.ExcelFile(fp)
        except Exception as e:
            print(f"  ⚠ 读取失败: {fname} - {e}")
            continue
        year_match = re.search(r'(\d{4})', fname)
        year_str = year_match.group(1) if year_match else "未知"
        for sheet_name in xl.sheet_names:
            df = pd.read_excel(fp, sheet_name=sheet_name)
            for _, row in df.iterrows():
                record = {
                    "年份": sanitize(row.get("年份")) or year_str,
                    "生源地": sanitize(row.get("生源地")) or "重庆",
                    "院校名称": sanitize(row.get("学校")),
                    "省份": sanitize(row.get("省份")),
                    "城市": sanitize(row.get("城市")),
                    "软科排名": parse_int(row.get("软科排名")),
                    "985": sanitize(row.get("985")),
                    "211": sanitize(row.get("211")),
                    "双一流": sanitize(row.get("双一流")),
                    "科类": sanitize(row.get("科类")),
                    "批次": sanitize(row.get("批次")),
                    "专业组": sanitize(row.get("专业组")),
                    "选科要求": sanitize(row.get("选科要求")),
                    "最低分": safe_float(row.get("最低分")),
                    "最低分排名": parse_int(row.get("最低分排名")),
                    "省控线": parse_int(row.get("省控线")),
                    "办学性质": sanitize(row.get("办学性质")),
                    "学校归属": sanitize(row.get("学校归属")),
                    "学历类别": sanitize(row.get("学历类别")),
                }
                all_records.append(record)
    save_json(all_records, "historical_toudang_lines.json")
    return all_records


def convert_score_distribution():
    """一分一段表 — 多种格式"""
    base = os.path.join(DATA_ROOT, "4-重庆高考历史数据", "重庆市-一分一段表")
    all_records = []

    # 1) 重庆_一分一段_2022_2017.xlsx
    fp1 = os.path.join(base, "重庆_一分一段_2022_2017.xlsx")
    if os.path.exists(fp1):
        try:
            df = pd.read_excel(fp1, sheet_name="一分一段查询")
            for _, row in df.iterrows():
                record = {
                    "省份": sanitize(row.get("省份")),
                    "年份": sanitize(row.get("年份")),
                    "科类": sanitize(row.get("科类")),
                    "分数": sanitize(row.get("分数")),
                    "本段人数": parse_int(row.get("本段人数")),
                    "累计人数": parse_int(row.get("累计人数")),
                }
                all_records.append(record)
            print(f"  ✓ 读取: 重庆_一分一段_2022_2017.xlsx")
        except Exception as e:
            print(f"  ⚠ 读取失败: 重庆_一分一段_2022_2017.xlsx - {e}")

    # 2) 重庆市2024年高考-一分一段表-物理类.xlsx
    for cat, fname in [("物理类", "重庆市2024年高考-一分一段表-物理类.xlsx"),
                       ("历史类", "重庆市2024年高考-一分一段表-历史类.xlsx")]:
        fp = os.path.join(base, fname)
        if os.path.exists(fp):
            try:
                df = pd.read_excel(fp, sheet_name="Sheet1")
                # 列名可能是: ['2024年物理类含加分一分段表', 'Unnamed: 1', 'Unnamed: 2']
                col_score = df.columns[0]
                col_count = df.columns[1]
                col_cum = df.columns[2]
                for _, row in df.iterrows():
                    score = sanitize(row[col_score])
                    if score is None or str(score) in ('分数段', 'nan', ''):
                        continue
                    all_records.append({
                        "省份": "重庆",
                        "年份": "2024",
                        "科类": cat,
                        "分数": str(score).replace("及以上", "+"),
                        "本段人数": parse_int(row[col_count]),
                        "累计人数": parse_int(row[col_cum]),
                    })
                print(f"  ✓ 读取: {fname}")
            except Exception as e:
                print(f"  ⚠ 读取失败: {fname} - {e}")

    save_json(all_records, "historical_score_distribution.json")
    return all_records


def convert_province_control_lines():
    """省控线/批次线"""
    base = os.path.join(DATA_ROOT, "4-重庆高考历史数据", "重庆市-一分一段表")
    all_records = []

    # 1) 重庆_省控线_批次线_2022_2014.xlsx
    fp1 = os.path.join(base, "重庆_省控线_批次线_2022_2014.xlsx")
    if os.path.exists(fp1):
        try:
            df = pd.read_excel(fp1, sheet_name="省控线查询")
            for _, row in df.iterrows():
                record = {
                    "省份": sanitize(row.get("省份")),
                    "年份": sanitize(row.get("年份")),
                    "类别": sanitize(row.get("类别")),
                    "批次": sanitize(row.get("批次")),
                    "分数线": parse_int(row.get("分数线")),
                    "专业分": safe_float(row.get("专业分")),
                }
                all_records.append(record)
            print(f"  ✓ 读取: 重庆_省控线_批次线_2022_2014.xlsx")
        except Exception as e:
            print(f"  ⚠ 读取失败: 重庆_省控线_批次线_2022_2014.xlsx - {e}")

    # 2) 2014-2023年各地高考历年分数线(批次线).xlsx
    fp2 = os.path.join(base, "2014-2023年各地高考历年分数线(批次线).xlsx")
    if os.path.exists(fp2):
        try:
            df = pd.read_excel(fp2, sheet_name="各地高考历年分数线(批次线)")
            for _, row in df.iterrows():
                record = {
                    "地区": sanitize(row.get("地区")),
                    "年份": sanitize(row.get("年份")),
                    "考生类别": sanitize(row.get("考生类别")),
                    "批次": sanitize(row.get("批次")),
                    "分数线": parse_int(row.get("分数线")),
                }
                all_records.append(record)
            print(f"  ✓ 读取: 2014-2023年各地高考历年分数线(批次线).xlsx")
        except Exception as e:
            print(f"  ⚠ 读取失败: 2014-2023年各地高考历年分数线(批次线).xlsx - {e}")

    save_json(all_records, "province_control_lines.json")
    return all_records


# ================================================================
#  第二部分: 3-重庆录取数据22-25【持续更新】 (最新数据)
# ================================================================

def convert_latest_school_scores():
    """22-25年全国高校在重庆的院校录取分数"""
    base = os.path.join(DATA_ROOT, "3-重庆录取数据22-25【持续更新】")
    fp = os.path.join(base, "22-25年全国高校在重庆的院校录取分数.xlsx")
    all_records = []
    if os.path.exists(fp):
        df = pd.read_excel(fp, sheet_name="Sheet1")
        for _, row in df.iterrows():
            record = {
                "年份": sanitize(row.get("年份")),
                "院校名称": sanitize(row.get("院校名称")),
                "院校代码": str(sanitize(row.get("院校代码", "")) or ""),
                "科类": sanitize(row.get("科类")),
                "批次": sanitize(row.get("批次")),
                "招生类型": sanitize(row.get("招生类型")),
                "专业组": sanitize(row.get("专业组")),
                "选科要求": sanitize(row.get("选科要求")),
                "录取人数": parse_int(row.get("录取人数")),
                "最低分数": safe_float(row.get("最低分数")),
                "最低分位": parse_int(row.get("最低分位")),
                "批次线差": safe_float(row.get("批次线差")),
                "学校所在": sanitize(row.get("学校所在")),
                "学校性质": sanitize(row.get("学校性质")),
                "是否985": sanitize(row.get("是否985")),
                "是否211": sanitize(row.get("是否211")),
            }
            all_records.append(record)
        print(f"  ✓ 读取: 22-25年全国高校在重庆的院校录取分数.xlsx")
    save_json(all_records, "latest_school_scores.json")
    return all_records


def convert_latest_major_scores():
    """22-25年全国高校在重庆的专业录取分数"""
    base = os.path.join(DATA_ROOT, "3-重庆录取数据22-25【持续更新】")
    fp = os.path.join(base, "22-25年全国高校在重庆的专业录取分数.xlsx")
    all_records = []
    if os.path.exists(fp):
        df = pd.read_excel(fp, sheet_name="Sheet1")
        for _, row in df.iterrows():
            record = {
                "年份": sanitize(row.get("年份")),
                "院校名称": sanitize(row.get("院校名称")),
                "院校代码": str(sanitize(row.get("院校代码", "")) or ""),
                "科类": sanitize(row.get("科类")),
                "批次": sanitize(row.get("批次")),
                "专业名称": sanitize(row.get("专业")),
                "专业代码": sanitize(row.get("专业代码")),
                "所属专业组": sanitize(row.get("所属专业组")),
                "专业备注": sanitize(row.get("专业备注")),
                "选科要求": sanitize(row.get("选科要求")),
                "录取人数": parse_int(row.get("录取人数")),
                "最低分数": safe_float(row.get("最低分数")),
                "最低位次": parse_int(row.get("最低位次")),
                "学校所在": sanitize(row.get("学校所在")),
                "学校性质": sanitize(row.get("学校性质")),
                "是否985": sanitize(row.get("是否985")),
                "是否211": sanitize(row.get("是否211")),
            }
            all_records.append(record)
        print(f"  ✓ 读取: 22-25年全国高校在重庆的专业录取分数.xlsx")
    save_json(all_records, "latest_major_scores.json")
    return all_records


def convert_latest_enrollment_plans():
    """22-25年全国高校在重庆的招生计划"""
    base = os.path.join(DATA_ROOT, "3-重庆录取数据22-25【持续更新】")
    fp = os.path.join(base, "22-25年全国高校在重庆的招生计划.xlsx")
    all_records = []
    if os.path.exists(fp):
        df = pd.read_excel(fp, sheet_name="Sheet1")
        for _, row in df.iterrows():
            record = {
                "年份": sanitize(row.get("年份")),
                "院校名称": sanitize(row.get("院校名称")),
                "院校代码": str(sanitize(row.get("院校代码", "")) or ""),
                "科类": sanitize(row.get("科类")),
                "批次": sanitize(row.get("批次")),
                "招生类型": sanitize(row.get("招生类型")),
                "专业名称": sanitize(row.get("专业名称")),
                "专业代码": sanitize(row.get("专业代码")),
                "所属专业组": sanitize(row.get("所属专业组")),
                "专业备注": sanitize(row.get("专业备注")),
                "选科要求": sanitize(row.get("选科要求")),
                "招生人数": parse_int(row.get("招生人数")),
                "学制": sanitize(row.get("学制(年)")),
                "学费": parse_int(row.get("学费(元)")),
            }
            all_records.append(record)
        print(f"  ✓ 读取: 22-25年全国高校在重庆的招生计划.xlsx")
    save_json(all_records, "latest_enrollment_plans.json")
    return all_records


def convert_latest_score_distribution():
    """一分一段表 (2022-2025, 3-目录下)"""
    base = os.path.join(DATA_ROOT, "3-重庆录取数据22-25【持续更新】", "一分一段")
    all_records = []
    for fname in sorted(os.listdir(base)):
        if not fname.endswith('.xlsx') or '副本' in fname:
            continue
        fp = os.path.join(base, fname)
        year_match = re.search(r'(\d{4})', fname)
        year_str = year_match.group(1) if year_match else "未知"
        try:
            df = pd.read_excel(fp, sheet_name="Sheet1")
            for _, row in df.iterrows():
                record = {
                    "年份": sanitize(row.get("年份")) or year_str,
                    "科类": sanitize(row.get("科类")),
                    "批次": sanitize(row.get("批次")),
                    "控制线": parse_int(row.get("控制线(分)")),
                    "分数": sanitize(row.get("分数(分)")),
                    "本段人数": parse_int(row.get("本段人数(人)")),
                    "累计人数": parse_int(row.get("累计人数(人)")),
                    "排名区间": sanitize(row.get("排名区间")),
                    "历史同位次得分": sanitize(row.get("历史同位次考生得分")),
                }
                all_records.append(record)
            print(f"  ✓ 读取: {fname}")
        except Exception as e:
            print(f"  ⚠ 读取失败: {fname} - {e}")
    save_json(all_records, "latest_score_distribution.json")
    return all_records


def convert_combined_table():
    """22-25年重庆（一表联动）.xlsx — 综合大表，按行解析"""
    base = os.path.join(DATA_ROOT, "3-重庆录取数据22-25【持续更新】")
    fp = os.path.join(base, "22-25年重庆（一表联动）.xlsx")
    all_records = []
    if os.path.exists(fp):
        try:
            df = pd.read_excel(fp, sheet_name="重庆", header=None)
            # 第一行是合并表头，第二行开始是数据
            records = []
            for i in range(2, len(df)):
                row = df.iloc[i]
                # 只取有有效院校名称的行
                school = sanitize(row.iloc[6]) if len(row) > 6 else None
                if school is None or str(school).strip() == '' or str(school) == 'nan':
                    continue
                record = {
                    # --- 基本信息 ---
                    "考生类型": sanitize(row.iloc[0]),
                    "年份": sanitize(row.iloc[1]),
                    "生源地": sanitize(row.iloc[2]),
                    "批次": sanitize(row.iloc[3]),
                    "科类": sanitize(row.iloc[4]),
                    "院校代码": sanitize(row.iloc[5]),
                    "院校名称": school,
                    "专业代码": sanitize(row.iloc[7]),
                    "专业全称": sanitize(row.iloc[8]),
                    "专业名称": sanitize(row.iloc[9]),
                    "专业备注": sanitize(row.iloc[10]),
                    "专业层次": sanitize(row.iloc[11]),
                    "选科要求": sanitize(row.iloc[12]),
                    "计划人数": parse_int(row.iloc[13]),
                    "学制": sanitize(row.iloc[14]),
                    "学费": sanitize(row.iloc[15]),
                    "门类": sanitize(row.iloc[16]),
                    "专业类": sanitize(row.iloc[17]),
                    # --- 2025 年数据 ---
                    "2025_录取人数": parse_int(row.iloc[19]),
                    "2025_最低分": safe_float(row.iloc[20]),
                    "2025_最低位次": parse_int(row.iloc[21]),
                    "2025_平均分": safe_float(row.iloc[22]),
                    "2025_平均位次": parse_int(row.iloc[23]),
                    "2025_最高分": safe_float(row.iloc[24]),
                    "2025_最高位次": parse_int(row.iloc[25]),
                    # --- 2024 年数据 ---
                    "2024_录取人数": parse_int(row.iloc[28]),
                    "2024_最低分": safe_float(row.iloc[29]),
                    "2024_最低位次": parse_int(row.iloc[30]),
                    "2024_平均分": safe_float(row.iloc[31]),
                    "2024_平均位次": parse_int(row.iloc[32]),
                    "2024_最高分": safe_float(row.iloc[33]),
                    "2024_最高位次": parse_int(row.iloc[34]),
                    # --- 2023 年数据 ---
                    "2023_录取人数": parse_int(row.iloc[37]),
                    "2023_最低分": safe_float(row.iloc[38]),
                    "2023_最低位次": parse_int(row.iloc[39]),
                    "2023_平均分": safe_float(row.iloc[40]),
                    "2023_平均位次": parse_int(row.iloc[41]),
                    "2023_最高分": safe_float(row.iloc[42]),
                    "2023_最高位次": parse_int(row.iloc[43]),
                    # --- 院校基础信息 ---
                    "所在省": sanitize(row.iloc[46]),
                    "城市": sanitize(row.iloc[47]),
                    "城市水平标签": sanitize(row.iloc[48]),
                    "院校标签": sanitize(row.iloc[49]),
                    "院校水平": sanitize(row.iloc[50]),
                    "更名合并转设": sanitize(row.iloc[51]),
                    "隶属单位": sanitize(row.iloc[52]),
                    "类型": sanitize(row.iloc[53]),
                    "公私性质": sanitize(row.iloc[54]),
                    "本专科": sanitize(row.iloc[55]),
                    "保研率": safe_float(row.iloc[56]),
                    "院校排名": sanitize(row.iloc[57]),
                    "软科评级": sanitize(row.iloc[62]),
                    "软科排名": parse_int(row.iloc[63]),
                }
                records.append(record)
            save_json(records, "combined_table.json")
            print(f"  ✓ 读取: 22-25年重庆（一表联动）.xlsx")
            return records
        except Exception as e:
            print(f"  ⚠ 读取失败: 22-25年重庆（一表联动）.xlsx - {e}")
            import traceback
            traceback.print_exc()
    return all_records


# ================================================================
#  主流程
# ================================================================

def main():
    print("=" * 60)
    print("高考数据转换脚本 - Excel → JSON")
    print("=" * 60)

    print("\n📁 [第一部分] 4-重庆高考历史数据 (2017-2024)")
    print("-" * 50)
    print("\n--- 1. 招生计划 ---")
    convert_historical_enrollment_plans()
    print("\n--- 2. 专业分数线 ---")
    convert_historical_major_scores()
    print("\n--- 3. 投档线 ---")
    convert_historical_toudang_lines()
    print("\n--- 4. 一分一段表 ---")
    convert_score_distribution()
    print("\n--- 5. 省控线/批次线 ---")
    convert_province_control_lines()

    print("\n📁 [第二部分] 3-重庆录取数据22-25【持续更新】")
    print("-" * 50)
    print("\n--- 6. 院校录取分数 ---")
    convert_latest_school_scores()
    print("\n--- 7. 专业录取分数 ---")
    convert_latest_major_scores()
    print("\n--- 8. 招生计划 ---")
    convert_latest_enrollment_plans()
    print("\n--- 9. 一分一段表 ---")
    convert_latest_score_distribution()
    print("\n--- 10. 一表联动(综合大表) ---")
    convert_combined_table()

    # 汇总统计
    print("\n" + "=" * 60)
    print("✅ 转换完成!")
    print(f"输出目录: {OUTPUT_DIR}")
    total_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.json')]
    for f in sorted(total_files):
        size = os.path.getsize(os.path.join(OUTPUT_DIR, f))
        print(f"  {f} ({size/1024:.1f} KB)")


if __name__ == '__main__':
    main()
