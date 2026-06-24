#!/usr/bin/env python3
"""
高考志愿推荐引擎 — 支持2026年分数自动换算，参考23-25年历年数据推荐
"""
import json
import os
import sys

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))), "json_data")

def load(filename):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def safe_int(v):
    try:
        return int(float(v))
    except:
        return None

def find_rank_from_score(dist_data, year, kelei, score):
    for r in dist_data:
        if r.get('年份') != year:
            continue
        if kelei not in str(r.get('科类', '')):
            continue
        s = str(r.get('分数', ''))
        cum = r.get('累计人数')
        if not cum:
            continue
        if '+' in s or '及以上' in s:
            sv = safe_int(s.replace('+', '').replace('及以上', ''))
            if sv and sv <= score:
                return cum
        elif '-' in s:
            parts = s.split('-')
            try:
                if int(parts[1]) >= score >= int(parts[0]):
                    return cum
            except:
                pass
        else:
            sv = safe_int(s)
            if sv and sv == score:
                return cum
    return None

def find_score_from_rank(dist_data, year, kelei, rank):
    for r in dist_data:
        if r.get('年份') != year:
            continue
        if kelei not in str(r.get('科类', '')):
            continue
        cum = r.get('累计人数')
        if cum and rank <= cum:
            return r.get('分数', '')
    return None

def get_school_history(schools_data, school_name, kelei, batch):
    """获取某院校近三年（2023-2025）最低分"""
    history = {}
    for year in [2025, 2024, 2023]:
        for s in schools_data:
            if (s.get('年份') == year and 
                s.get('院校名称') == school_name and
                s.get('科类') == kelei and
                s.get('批次') == batch):
                history[year] = {
                    '最低分': s.get('最低分数'),
                    '最低位次': s.get('最低分位')
                }
                break
    return history

def get_major_history(majors_data, school_name, major_name, kelei, batch):
    """获取某专业近三年（2023-2025）最低分"""
    history = {}
    for year in [2025, 2024, 2023]:
        for m in majors_data:
            if (m.get('年份') == year and
                m.get('院校名称') == school_name and
                m.get('专业名称') == major_name and
                m.get('科类') == kelei and
                m.get('批次') == batch):
                history[year] = {
                    '最低分': m.get('最低分数'),
                    '最低位次': m.get('最低位次')
                }
                break
    return history

def format_history(h, equiv_scores, ref_score):
    """格式化历史数据，用每年各自的等效分对比显示趋势"""
    parts = []
    for y in [2025, 2024, 2023]:
        if y in h and h[y]['最低分'] is not None:
            sc = float(h[y]['最低分'])
            # 用该年自己的等效分作对比基准
            baseline = equiv_scores.get(y, ref_score)
            diff = sc - baseline
            if diff > 0:
                trend = f"↑{abs(diff):.0f}"
            elif diff < 0:
                trend = f"↓{abs(diff):.0f}"
            else:
                trend = "="
            parts.append(f"{y}:{sc:.0f}({trend})")
        elif y in h:
            parts.append(f"{y}:--")
    return "  ".join(parts)

def main():
    schools = load("latest_school_scores.json")
    majors = load("latest_major_scores.json")
    control_lines = load("province_control_lines.json")
    dist_old = load("latest_score_distribution.json")
    dist_2026 = load("score_distribution_2026.json")

    print("=" * 60)
    print("  🎯 高考志愿推荐助手（参考23-25年历史数据）")
    print("=" * 60)

    # 0. 年份
    year_input = input("\n📌 你的考试年份 (2026 或 2025，回车默认2026): ").strip()
    user_year = safe_int(year_input) or 2026
    
    # 1. 科类
    kelei_input = input("\n📌 你的科类 (1=物理类, 2=历史类, 直接回车默认物理类): ").strip()
    kelei = "物理类" if kelei_input in ("", "1") else "历史类"

    # 2. 分数
    score_input = input("\n📌 你的分数: ").strip()
    score = safe_int(score_input)
    if not score:
        print("⚠ 分数无效")
        return
    
    dist_current = dist_2026 if user_year == 2026 else dist_old
    rank = find_rank_from_score(dist_current, user_year, kelei, score)
    if not rank:
        print(f"⚠ 未在{user_year}年一分一段表中找到对应位次")
        rank = "未知"

    equiv_scores = {}
    if rank and rank != "未知":
        for y in [2025, 2024, 2023]:
            score_str = find_score_from_rank(dist_old, y, kelei, rank)
            if score_str:
                if '-' in str(score_str):
                    equiv_scores[y] = safe_int(str(score_str).split('-')[0])
                else:
                    equiv_scores[y] = safe_int(str(score_str).replace('+', '').replace('及以上', ''))

    ref_year = 2025
    ref_score = equiv_scores.get(2025, score)
    
    batch_input = input(f"\n📌 批次 (1=本科批, 2=专科批, 3=本科提前批B段, 回车默认本科批): ").strip()
    batch_map = {"1": "本科批", "2": "专科批", "3": "本科提前批B段"}
    batch = batch_map.get(batch_input, "本科批")

    range_input = input(f"\n📌 分数上下浮动范围 (默认 5 分，建议3-10): ").strip()
    score_range = safe_int(range_input) or 5

    pref_985 = input("\n📌 是否只看985/211院校？(y/n, 回车不限制): ").strip().lower()
    only_elite = pref_985 == 'y'

    region = input("\n📌 偏好省份/地区 (如 重庆、北京、四川，回车不限制): ").strip()
    major_pref = input("\n📌 感兴趣的专业方向 (如 计算机、医学、师范，回车不限制): ").strip()

    city_pref = input("\n📌 偏好城市类型 (1=一线城市, 2=新一线, 3=二三线, 回车不限制): ").strip()
    city_map = {"1": ["北京", "上海", "广州", "深圳"],
                "2": ["成都", "杭州", "重庆", "武汉", "南京", "西安", "长沙", "天津", "苏州", "郑州"],
                "3": []}

    print(f"\n{'='*60}")
    print(f"  🔍 正在查询中... 请稍候")
    print(f"{'='*60}")

    # ==================== 换算结果 ====================
    print(f"\n{'='*60}")
    print(f"  📊 位次换算结果")
    print(f"{'='*60}")
    print(f"  {user_year}年 {kelei} {score}分 → 位次 {rank}")
    if equiv_scores:
        print(f"  同等位次在往年相当于：")
        for y in sorted(equiv_scores.keys(), reverse=True):
            arrow = " 🎯" if y == 2025 else ""
            print(f"    {y}年 ≈ {equiv_scores[y]}分{arrow}")
    print(f"  ─────────────────────────────")
    print(f"  将用{ref_year}年等效 {ref_score}分 ±{score_range}分 去匹配学校")

    lo_score = ref_score - score_range
    hi_score = ref_score + score_range

    # ==================== 查找院校 ====================
    candidates = []
    for s in schools:
        if s.get('年份') != 2025: continue
        if s.get('科类') != kelei: continue
        if s.get('批次') != batch: continue
        sc = s.get('最低分数')
        if sc is None: continue
        sc = float(sc)
        if not (lo_score <= sc <= hi_score): continue
        if only_elite:
            is985 = s.get('是否985') == '是'
            is211 = s.get('是否211') == '是'
            if not (is985 or is211): continue
        if region and region not in str(s.get('学校所在', '')): continue
        if city_pref in ("1", "2"):
            if not any(c in str(s.get('学校所在', '')) for c in city_map[city_pref]): continue
        candidates.append(s)
    candidates.sort(key=lambda x: float(x.get('最低分数', 0) or 0), reverse=True)

    # ==================== 查找专业 ====================
    recommended_majors = []
    school_names = set(s.get('院校名称') for s in candidates)
    for m in majors:
        if m.get('年份') != 2025: continue
        if m.get('科类') != kelei: continue
        if m.get('批次') != batch: continue
        if m.get('院校名称') not in school_names: continue
        sc = m.get('最低分数')
        if sc is None: continue
        sc = float(sc)
        if not (lo_score <= sc <= hi_score): continue
        if major_pref and major_pref not in str(m.get('专业名称', '')): continue
        recommended_majors.append(m)
    recommended_majors.sort(key=lambda x: float(x.get('最低分数', 0) or 0), reverse=True)

    # ==================== 输出 ====================
    print(f"\n{'='*60}")
    print(f"  🏫 推荐结果（附23-25年历史分数线参考）")
    print(f"  批次: {batch}  |  匹配分数范围: {lo_score}-{hi_score}分")
    if only_elite: print(f"  筛选: 仅985/211院校")
    if region: print(f"  地域: {region}")
    if major_pref: print(f"  专业方向: {major_pref}")
    print(f"{'='*60}")
    print(f"  (↑分数上涨  ↓分数下跌  =持平  对比{ref_score}分)")

    chongci = [c for c in candidates if float(c.get('最低分数', 0)) > ref_score]
    wentuo = [c for c in candidates if float(c.get('最低分数', 0)) == ref_score]
    baodi = [c for c in candidates if float(c.get('最低分数', 0)) < ref_score]

    sections = [
        ("🚀 冲刺院校 (分数略高于你，可以冲一冲)", chongci[:15]),
        ("✅ 稳妥院校 (分数与你匹配，录取概率大)", wentuo[:15]),
        ("🛡️ 保底院校 (分数低于你，作为保底选择)", baodi[:10]),
    ]

    for title, items in sections:
        if items:
            print(f"\n  {title}")
            print(f"  {'院校名称':<22} {'省份':<6} {'25分':<6} {'25位次':<8} {'历年趋势(25/24/23)':<24}")
            print(f"  {'-'*22} {'-'*6} {'-'*6} {'-'*8} {'-'*24}")
            for s in items:
                name = s.get('院校名称', '')
                hist = get_school_history(schools, name, kelei, batch)
                trend = format_history(hist, equiv_scores, ref_score)
                tags = ""
                if s.get('是否985') == '是': tags += "985 "
                if s.get('是否211') == '是': tags += "211"
                tag_str = f"({tags})" if tags else ""

                line = f"  {str(name)[:22]:<22} {str(s.get('学校所在',''))[:6]:<6} " \
                       f"{str(s.get('最低分数',''))[:6]:<6} {str(s.get('最低分位',''))[:8]:<8} {trend:<24}"
                if tag_str:
                    line += f" {tag_str}"
                print(line)

    # ==================== 专业推荐（含历年） ====================
    if recommended_majors:
        print(f"\n  📚 推荐专业（共 {len(recommended_majors)} 个，附历年分数）")
        by_school = {}
        for m in recommended_majors:
            by_school.setdefault(m.get('院校名称', '未知'), []).append(m)

        for sname in sorted(by_school.keys()):
            majors_list = by_school[sname]
            # 显示该院校历史最低分趋势
            sch_hist = get_school_history(schools, sname, kelei, batch)
            if sch_hist:
                sch_trend = format_history(sch_hist, equiv_scores, ref_score)
            else:
                sch_trend = ""
            
            print(f"\n  📍 {sname[:20]:<20} 院校分数线: {sch_trend}")
            
            majors_list.sort(key=lambda x: float(x.get('最低分数', 0) or 0), reverse=True)
            for m in majors_list[:5]:
                major_name = m.get('专业名称', '')
                m_hist = get_major_history(majors, sname, major_name, kelei, batch)
                m_trend = format_history(m_hist, equiv_scores, ref_score)
                print(f"      ├ {str(major_name)[:20]:<20} "
                      f"25年:最低{str(m.get('最低分数','')):<6} "
                      f"位次{str(m.get('最低位次','')):<8}")
                if m_trend:
                    print(f"      │  历年: {m_trend}")
            if len(majors_list) > 5:
                print(f"      └ ... 还有 {len(majors_list)-5} 个专业")
    else:
        print(f"\n  📚 未匹配到符合条件的专业，建议放宽筛选条件")

    print(f"\n{'='*60}")
    print(f"  💡 报考建议")
    print(f"{'='*60}")
    if chongci:
        print(f"  • 冲刺 {len(chongci)} 所院校：选2-3所分数略高的尝试")
    if wentuo:
        print(f"  • 稳妥 {len(wentuo)} 所院校：这是你的主力志愿区")
    if baodi:
        print(f"  • 保底 {len(baodi)} 所院校：确保有学可上")
    print(f"  • 建议采用 '冲-稳-保' 策略，比例约为 3:4:3")
    print(f"  • 历年趋势解读：↑表示该院校分数逐年上涨（更热门），↓表示下跌（可能更好考）")
    print(f"  • 以上推荐基于{ref_year}年录取数据换算，实际填报请以官方为准")

    try:
        result_file = os.path.join(os.path.dirname(__file__), "..", "last_recommendation.txt")
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write(f"年份: {user_year}, 分数: {score}, 科类: {kelei}, 位次: {rank}\n")
            f.write(f"等效: {equiv_scores}\n")
            f.write(f"推荐院校({len(candidates)}所): {[s.get('院校名称') for s in candidates]}\n")
    except:
        pass

    print(f"\n{'='*60}")

if __name__ == '__main__':
    main()
