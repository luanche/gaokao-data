#!/usr/bin/env python3
"""
2026年物理类497分 → 等效495±8分 → 推荐院校和专业
排除北方省份、中外合作、土木工程
"""
import json
import os

# 统一路径解析
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "json_data")

def load(filename):
    with open(os.path.join(DATA_DIR, filename), 'r', encoding='utf-8') as f:
        return json.load(f)

def safe_int(v):
    try:
        return int(float(v))
    except:
        return None

# ==== 配置 ====
KELEI = "物理类"
SCORE_2026 = 497
RANK_2026 = 64996
BATCH = "本科批"

EQUIV = {2025: 495, 2024: 492, 2023: 451}
LO = 487
HI = 503

NORTH_PROVINCES = {
    "北京", "天津", "河北", "山西", "内蒙古",
    "辽宁", "吉林", "黑龙江",
    "山东", "河南",
    "陕西", "甘肃", "青海", "宁夏", "新疆"
}

schools = load("latest_school_scores.json")
majors = load("latest_major_scores.json")

candidates = []
for s in schools:
    if s.get('年份') != 2025: continue
    if s.get('科类') != KELEI: continue
    if s.get('批次') != BATCH: continue
    sc = s.get('最低分数')
    if sc is None: continue
    sc = float(sc)
    if not (LO <= sc <= HI): continue
    if s.get('学校所在', '') in NORTH_PROVINCES: continue
    zt = str(s.get('招生类型', ''))
    if '中外' in zt or ('合作' in zt and '中外' in zt): continue
    if '中外合作' in s.get('院校名称', ''): continue
    candidates.append(s)

candidates.sort(key=lambda x: float(x.get('最低分数', 0) or 0), reverse=True)

def get_school_history(school_name):
    history = {}
    for year in [2025, 2024, 2023]:
        for s in schools:
            if (s.get('年份') == year and
                s.get('院校名称') == school_name and
                s.get('科类') == KELEI and
                s.get('批次') == BATCH):
                history[year] = {
                    '最低分': s.get('最低分数'),
                    '最低位次': s.get('最低分位'),
                    '院校代码': s.get('院校代码')
                }
                break
    return history

def format_history(hist):
    parts = []
    for y in [2025, 2024, 2023]:
        if y in hist and hist[y]['最低分'] is not None:
            sc = float(hist[y]['最低分'])
            baseline = EQUIV.get(y, 495)
            diff = sc - baseline
            if diff > 0:
                trend = f"↑{abs(diff):.0f}"
            elif diff < 0:
                trend = f"↓{abs(diff):.0f}"
            else:
                trend = "="
            parts.append(f"{y}:{sc:.0f}({trend})")
        else:
            parts.append(f"{y}:--")
    return "  ".join(parts)

def get_major_history(school_name, major_name):
    history = {}
    for year in [2025, 2024, 2023]:
        for m in majors:
            if (m.get('年份') == year and
                m.get('院校名称') == school_name and
                m.get('专业名称') == major_name and
                m.get('科类') == KELEI and
                m.get('批次') == BATCH):
                history[year] = {'最低分': m.get('最低分数'), '最低位次': m.get('最低位次')}
                break
    return history

print("=" * 80)
print("  2026年高考志愿推荐（物理类497分）")
print(f"  等效495±8分（位次约64,996）")
print(f"  排除：北方省份 | 中外合作 | 土木工程")
print(f"  批次：{BATCH}")
print("=" * 80)
print(f"\n📊 位次换算：")
print(f"  2026年 {KELEI} {SCORE_2026}分 → 位次 {RANK_2026}")
print(f"  2025年等效 ≈ {EQUIV[2025]}分")
print(f"  2024年等效 ≈ {EQUIV[2024]}分")
print(f"  2023年等效 ≈ {EQUIV[2023]}分")
print(f"\n  匹配范围：{LO}-{HI}分")
print(f"  (↑分数上涨  ↓分数下跌  =持平  与各年等效分对比)")

chongci = [c for c in candidates if float(c['最低分数']) > 495]
wentuo = [c for c in candidates if float(c['最低分数']) == 495]
baodi = [c for c in candidates if float(c['最低分数']) < 495]

for label, items, limit in [
    ("🚀 冲刺院校", chongci, 20),
    ("✅ 稳妥院校", wentuo, 20),
    ("🛡️ 保底院校", baodi, 15),
]:
    if items:
        print(f"\n{'─'*80}")
        print(f"  {label}")
        print(f"  {'院校名称':<20} {'代码':<6} {'省份':<6} {'25分':<5} {'25位次':<8} {'历年趋势(25/24/23)':<34}")
        print(f"  {'─'*20} {'─'*6} {'─'*6} {'─'*5} {'─'*8} {'─'*34}")
        for s in items[:limit]:
            name = s.get('院校名称', '')
            hist = get_school_history(name)
            code = hist.get(2025, {}).get('院校代码', s.get('院校代码', ''))
            trend = format_history(hist)
            tags = ""
            if s.get('是否985') == '是': tags += "★985 "
            if s.get('是否211') == '是': tags += "▲211 "
            tag_str = f"({tags})" if tags else ""
            line = (f"  {str(name)[:18]:<20} {str(code)[:6]:<6} "
                    f"{str(s.get('学校所在',''))[:6]:<6} "
                    f"{str(int(s.get('最低分数',0)))[:5]:<5} "
                    f"{str(s.get('最低分位',''))[:8]:<8} {trend:<34}")
            if tag_str: line += f" {tag_str}"
            print(line)

print(f"\n{'='*80}")
print(f"  📚 专业推荐（排除土木工程、中外合作）")
print(f"{'='*80}")

school_names = set(s['院校名称'] for s in candidates)
recommended_majors = []
for m in majors:
    if m.get('年份') != 2025: continue
    if m.get('科类') != KELEI: continue
    if m.get('批次') != BATCH: continue
    if m.get('院校名称') not in school_names: continue
    sc = m.get('最低分数')
    if sc is None: continue
    sc = float(sc)
    if not (LO <= sc <= HI): continue
    mname = str(m.get('专业名称', ''))
    if '土木' in mname: continue
    remark = str(m.get('专业备注', ''))
    zt = str(m.get('招生类型', ''))
    if '中外' in remark or '中外' in mname or '中外' in zt: continue
    recommended_majors.append(m)

by_school = {}
for m in recommended_majors:
    by_school.setdefault(m['院校名称'], []).append(m)

for sname in sorted(by_school.keys()):
    major_list = by_school[sname]
    sch_hist = get_school_history(sname)
    code = sch_hist.get(2025, {}).get('院校代码', '')
    prov = next((s['学校所在'] for s in candidates if s['院校名称']==sname), '?')
    print(f"\n  📍 {sname[:18]:<18} 代码:{code:<6} {prov:<4} 院校: {format_history(sch_hist)}")
    major_list.sort(key=lambda x: float(x.get('最低分数', 0) or 0), reverse=True)
    for m in major_list:
        mname = m.get('专业名称', '')
        m_hist = get_major_history(sname, mname)
        m_trend = format_history(m_hist)
        cat = ""
        kw = mname
        if any(x in kw for x in ['计算机','软件','数据','人工智能','智能','电子','信息','通信','物联网','网络工程']):
            cat = "[计算机/电子信息]"
        elif any(x in kw for x in ['机械','自动化','电气','能源','动力','车辆','机器人']):
            cat = "[机械/自动化]"
        elif any(x in kw for x in ['会计','财务','金融','经济','贸易','管理','工商','市场','电商','国贸']):
            cat = "[经管]"
        elif any(x in kw for x in ['法学','法律']): cat = "[法学]"
        elif any(x in kw for x in ['外语','英语','日语','翻译','汉语']): cat = "[语言]"
        elif any(x in kw for x in ['数学','物理','化学','生物','统计','应用']): cat = "[理科]"
        elif any(x in kw for x in ['医学','药学','护理','临床','口腔','中医','中药','检验','康复']): cat = "[医药]"
        elif any(x in kw for x in ['师范','教育','小学','学前']): cat = "[师范]"
        print(f"      ├ {str(mname)[:22]:<22} {cat:<22} 25年:{str(int(m.get('最低分数',0))):>4}分 位次{str(m.get('最低位次',''))[:7]:>7}")
        if m_trend: print(f"      │  历年: {m_trend}")
    print(f"      └ 共{len(major_list)}个专业")

print(f"\n{'='*80}")
print(f"  统计：冲刺{len(chongci)}所 + 稳妥{len(wentuo)}所 + 保底{len(baodi)}所")
print(f"  共{len(candidates)}所院校，{len(recommended_majors)}个专业推荐")
print(f"{'='*80}")
