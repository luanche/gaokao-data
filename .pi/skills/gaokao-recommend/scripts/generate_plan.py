#!/usr/bin/env python3
"""
生成增强版志愿推荐JSON + HTML
从 combined_table.json 获取专业代码/历年分数/招生计划等全量信息
"""
import json
import os
import sys
import re
import hashlib
from collections import defaultdict

# 统一路径解析
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR))))
DATA_DIR = os.path.join(PROJECT_ROOT, "json_data")
OUT_DIR = os.path.join(PROJECT_ROOT, ".tmp")

def load(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def safe_int(v):
    try:
        return int(float(v))
    except:
        return None

# ─── 用户配置（可通过 --config <json文件> 覆盖） ───
DEFAULT_CONFIG = {
    "score_2026": 497,
    "kelei": "物理类",
    "batch": "本科批",
    "school_majors": {
        '1310': ['矿物加工工程', '应用化学', '智慧应急', '电气工程及其自动化', '测控技术与仪器', '网络工程'],
        '1433': ['生物技术', '生物科学（师范类）', '物理学（师范类）'],
        '1451': ['机械电子工程', '智能制造工程', '电子信息工程', '通信工程', '微电子科学与工程', '光电信息科学与工程', '人工智能', '自动化', '计算机科学与技术', '数据科学与大数据技术'],
        '1502': ['应用物理学', '生物技术', '生物信息学', '生物工程', '食品科学与工程', '金属材料工程', '无机非金属材料工程', '化学工程与工艺', '能源化学工程', '储能科学与工程', '测控技术与仪器', '人工智能', '稀土材料科学与工程'],
        '2166': ['化学工程与工艺', '制药工程', '生物工程'],
        '3629': ['自动化', '应用统计学', '无机非金属材料与工程'],
        '4168': ['信息与计算科学', '食品质量与安全', '通信工程', '材料化学', '制药工程', '应用统计学'],
        '4326': ['应用物理学', '化学工程与工艺'],
        '4525': ['软件工程', '食品科学与工程', '生物工程'],
        '4552': ['生物技术', '应用统计学', '食品科学与工程'],
        '4603': ['海洋科学', '生物科学', '生物技术', '生态学', '食品科学与工程', '食品质量与安全', '网络工程', '数学与应用数学（师范类）', '数据计算与应用', '智慧海洋技术'],
        '4612': ['生物科学'],
        '5009': ['生物科学（师范类）', '生物技术', '化学（师范类）', '数学与应用数学（师范类）', '物理学（师范类）', '食品质量与安全', '食品科学与工程', '物联网工程', '化学工程与工艺'],
        '5029': ['数学与应用数学（师范类）', '食品质量与安全', '药物分析', '药学', '应用化学', '化学（师范类）', '食品科学与工程', '信息与计算科学', '数据科学与大数据技术', '人工智能', '物联网工程'],
        '5129': ['数学与应用数学（师范类）', '冶金工程', '食品科学与工程'],
        '5179': ['生物科学（师范类）', '数学与应用数学（师范类）', '化学（师范类）'],
        '5307': ['信息与计算科学', '新能源材料与器件', '人工智能', '智能科学与技术'],
        '5310': ['化学（师范类）', '数学与应用数学（师范类）'],
        '6207': ['化学工程与工艺', '制药工程', '生物工程', '生物技术', '数学与应用数学', '应用化学', '食品科学与工程', '无机非金属材料与工程', '高分子材料与工程', '计算机科学与技术', '通信工程', '软件工程', '数据科学与大数据技术'],
        '6403': ['生物科学', '生物工程', '食品科学与工程', '数学与应用数学', '化学工程与工艺', '制药工程', '材料科学与工程', '高分子材料与工程', '新能源材料与器件', '智能材料与结构', '通信工程', '机械电子工程', '能源化学工程', '软件工程', '网络工程', '生态学', '电子信息工程', '机械设计制造及其自动化', '计算机科学与技术'],
        '6404': ['生物科学（师范类）', '新能源材料与器件'],
        '6524': ['数学与应用数学(师范类)', '物理学（师范类）', '化学（师范类）', '应用化学', '生物科学（师范类）', '应用统计学', '网络工程', '食品科学与工程', '通信工程', '预防医学', '大气科学', '数据科学与大数据技术', '能源与动力工程', '环境科学与工程', '环境科学', '资源循环科学与工程'],
        '6526': ['应用生物科学', '生物制药', '食品质量与安全', '食品科学与工程', '酿酒工程', '化学工程与工艺', '化学工程与工业生物工程', '应用化学', '物联网工程', '通信工程', '网络工程']
    },
    "school_names": {
        '1310': '华北科技学院', '1433': '山西师范大学', '1451': '山西电子科技学院',
        '1502': '内蒙古科技大学', '2166': '大连大学', '3629': '景德镇学院',
        '4168': '河南科技学院', '4326': '湖南工学院', '4525': '贺州学院',
        '4552': '百色学院', '4603': '海南热带海洋学院', '4612': '琼台师范学院',
        '5009': '重庆三峡学院', '5029': '重庆第二师范学院', '5129': '西昌学院',
        '5179': '阿坝师范学院', '5307': '曲靖师范学院', '5310': '玉溪师范学院',
        '6207': '西北民族大学', '6403': '北方民族大学', '6404': '宁夏师范大学',
        '6524': '喀什大学', '6526': '塔里木大学'
    }
}

cfg = DEFAULT_CONFIG

SIMILAR_GROUPS = {
    '电气信息类': ['电气工程及其自动化', '自动化', '测控技术与仪器', '电子信息工程', '通信工程', '微电子科学与工程', '光电信息科学与工程'],
    '计算机类': ['计算机科学与技术', '软件工程', '网络工程', '物联网工程', '数据科学与大数据技术', '人工智能', '智能科学与技术', '数据计算与应用'],
    '机械类': ['机械电子工程', '智能制造工程', '机械设计制造及其自动化'],
    '化工材料类': ['化学工程与工艺', '应用化学', '能源化学工程', '储能科学与工程', '材料科学与工程', '高分子材料与工程', '无机非金属材料工程', '稀土材料科学与工程', '新能源材料与器件', '智能材料与结构', '金属材料工程', '无机非金属材料与工程'],
    '生物食品类': ['生物科学', '生物技术', '生物工程', '生物信息学', '食品科学与工程', '食品质量与安全', '应用生物科学', '生物制药', '酿酒工程', '化学工程与工业生物工程', '生态学'],
    '师范类': ['数学与应用数学（师范类）', '数学与应用数学(师范类)', '物理学（师范类）', '化学（师范类）', '生物科学（师范类）'],
    '数理统计类': ['数学与应用数学', '信息与计算科学', '应用统计学', '应用物理学', '数据计算与应用'],
    '环境类': ['环境科学与工程', '环境科学', '资源循环科学与工程', '能源与动力工程'],
    '海洋类': ['海洋科学', '智慧海洋技术'],
    '医药类': ['药学', '药物分析', '预防医学'],
}

def main():
    global cfg
    os.makedirs(OUT_DIR, exist_ok=True)
    
    # ─── 解析 CLI 参数 ───
    cfg_args = {}
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == '--config' and i+1 < len(sys.argv):
            cfg_path = sys.argv[i+1]
            with open(cfg_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            i += 2
        elif sys.argv[i] == '--score' and i+1 < len(sys.argv):
            cfg_args['score_2026'] = int(sys.argv[i+1])
            i += 2
        elif sys.argv[i] == '--kelei' and i+1 < len(sys.argv):
            cfg_args['kelei'] = sys.argv[i+1]
            i += 2
        else:
            i += 1
    if cfg_args:
        cfg = {**cfg, **cfg_args}
    
    # ─── 加载数据 ───
    comb = load("combined_table.json")
    major_scores = load("latest_major_scores.json")
    plans_2026 = load("enrollment_plans_2026.json")
    dist_2026 = load("score_distribution_2026.json")
    dist_old = load("latest_score_distribution.json")
    
    SCHOOL_MAJORS = cfg["school_majors"]
    SCHOOL_NAMES = cfg["school_names"]
    SCORE_2026 = cfg["score_2026"]
    KELEI = cfg["kelei"]
    BATCH = cfg["batch"]
    KELEI_SHORT = "物理" if "物理" in KELEI else "历史"
    
    # ─── 查位次 ───
    score_str = str(SCORE_2026)
    rank_2026 = None
    for r in dist_2026:
        if KELEI_SHORT in str(r.get('科类', '')) and str(r.get('分数', '')) == score_str:
            rank_2026 = r.get('累计人数')
            break
    
    # ─── 查等效分 ───
    equiv = {}
    for y in [2025, 2024, 2023]:
        best = None
        for r in dist_old:
            if r.get('年份') == y and KELEI_SHORT in str(r.get('科类', '')) and r.get('批次') == BATCH:
                cum = r.get('累计人数')
                if cum and rank_2026:
                    diff = abs(cum - rank_2026)
                    if best is None or diff < best[1]:
                        best = (r.get('分数'), diff)
        if best:
            equiv[y] = int(str(best[0]).replace('+','').replace('-','').strip()[:3])
    
    print(f"2026: {SCORE_2026}分 → 位次 {rank_2026}")
    print(f"等效分: {equiv}")
    
    # ─── 构建索引 ───
    # combined_table 索引: (code, major_name, year) -> record
    comb_idx = {}
    for item in comb:
        code = str(item.get('院校代码'))
        major = item.get('专业名称')
        year = item.get('年份')
        if KELEI_SHORT in str(item.get('科类', '')) and item.get('批次') == BATCH:
            key = (code, major, year)
            is_hezuo = '中外合作' in str(item.get('专业备注', '')) or '中外合作' in str(item.get('专业全称', ''))
            if key not in comb_idx:
                comb_idx[key] = item
            else:
                existing = comb_idx[key]
                existing_hezuo = '中外合作' in str(existing.get('专业备注', '')) or '中外合作' in str(existing.get('专业全称', ''))
                if is_hezuo and not existing_hezuo:
                    continue
                elif not is_hezuo and existing_hezuo:
                    comb_idx[key] = item
    
    # latest_major_scores.json 索引（回退数据源）
    major_idx = {}
    for item in major_scores:
        code = str(item.get('院校代码'))
        major = item.get('专业名称')
        year = item.get('年份')
        if KELEI in str(item.get('科类', '')) and item.get('批次') == BATCH:
            key = (code, major, year)
            is_hezuo = '中外合作' in str(item.get('专业备注', ''))
            if key not in major_idx:
                major_idx[key] = item
            else:
                existing = major_idx[key]
                existing_hezuo = '中外合作' in str(existing.get('专业备注', ''))
                if is_hezuo and not existing_hezuo:
                    continue  # 已有非中外合作，跳过中外合作
                elif not is_hezuo and existing_hezuo:
                    major_idx[key] = item  # 用非中外合作覆盖中外合作
    
    # 2026计划索引: (code, major) -> 计划数据
    plan_idx = {}
    for item in plans_2026:
        code = str(item.get('院校代码'))
        major = item.get('专业名称')
        if KELEI_SHORT in str(item.get('科类', '')) and item.get('批次') == BATCH:
            key = (code, major)
            # 同一专业有多个招生类型（非中外合作/中外合作）时，优先保留非中外合作的
            existing = plan_idx.get(key)
            is_hezuo = '中外合作' in str(item.get('专业备注','')) or '中外合作' in str(item.get('专业名称',''))
            if existing:
                existing_hezuo = '中外合作' in str(existing.get('专业备注','')) or '中外合作' in str(existing.get('专业名称',''))
                if is_hezuo and not existing_hezuo:
                    continue  # 已有非中外合作，跳过中外合作
                elif not is_hezuo and existing_hezuo:
                    plan_idx[key] = item  # 用非中外合作覆盖中外合作
                # 两个都是非中外合作或两个都是中外合作，保留第一个
            else:
                plan_idx[key] = item
    
    # ─── 构建每个学校+专业的数据 ───
    def _normalize_major_name(major):
        """标准化专业名称，去掉（师范类）等后缀以便匹配"""
        # 去掉括号及内容（师范类、实验班等）
        import re
        # 先尝试精确的替换
        name = major
        # 去掉（师范类）后缀
        name = name.replace('（师范类）', '').replace('(师范类)', '')
        # 去掉括号内的其他修饰
        name = re.sub(r'[（(][^）)]*[）)]', '', name).strip()
        return name
    
    def find_comb(code, major, year):
        """从combined_table找数据（所有年份数据都在2025年的记录中）"""
        lookup_year = 2025
        
        # 1. 精确匹配
        if (code, major, lookup_year) in comb_idx:
            return comb_idx[(code, major, lookup_year)]
        
        # 2. 师范类名称归一化
        norm_versions = set()
        norm_versions.add(major)
        # 数学与应用数学(师范类) 转 数学与应用数学（师范类）
        if major == '数学与应用数学(师范类)':
            norm_versions.add('数学与应用数学（师范类）')
        # 去掉（师范类）后缀
        base = major.replace('（师范类）', '').replace('(师范类)', '')
        norm_versions.add(base)
        for v in norm_versions:
            if (code, v, lookup_year) in comb_idx:
                return comb_idx[(code, v, lookup_year)]
        
        # 3. 大类招生名称映射：检查comb_idx中该校所有专业名
        # 比如用户选"计算机科学与技术"，表中可能有"计算机类"
        base_simple = _normalize_major_name(major)
        for key, rec in comb_idx.items():
            if key[0] != code:
                continue
            comb_name = key[1]
            # 表中大类名称包含用户专业核心词（仅限以"类"结尾的大类名称）
            if (base_simple and comb_name and comb_name.endswith('类') and
                base_simple in comb_name):
                return rec
            # 师范类匹配：用户"化学（师范类）" → 表中"化学"
            if base_simple and comb_name == base_simple:
                return rec
            # 单独处理大类招生：计算机类→计算机科学与技术
            group_map = {
                '计算机类': ['计算机科学与技术', '软件工程', '网络工程', '物联网工程', '数据科学与大数据技术', '人工智能'],
                '电子信息类': ['电子信息工程', '通信工程', '微电子科学与工程', '光电信息科学与工程'],
                '机械类': ['机械电子工程', '机械设计制造及其自动化', '智能制造工程'],
                '材料类': ['材料科学与工程', '高分子材料与工程', '无机非金属材料工程', '新能源材料与器件', '智能材料与结构'],
                '化工与制药类': ['化学工程与工艺', '制药工程', '能源化学工程', '储能科学与工程'],
                '生物科学类': ['生物科学', '生物技术', '生物工程', '生物信息学', '生态学'],
                '生物工程类': ['生物工程', '生物制药'],
                '数学类': ['数学与应用数学', '信息与计算科学', '数据计算与应用'],
                '统计学类': ['应用统计学', '统计学'],
                '环境科学与工程类': ['环境科学与工程', '环境科学', '资源循环科学与工程'],
                '食品科学与工程类': ['食品科学与工程', '食品质量与安全'],
            }
            if comb_name in group_map and base_simple in group_map[comb_name]:
                return rec
        
        return None
    
    def find_exact_score(code, major, year):
        # 1. 先从combined_table查
        r = find_comb(code, major, year)
        if r:
            key = f'{year}_最低分'
            v = r.get(key)
            if v is not None:
                return int(v)
        # 2. 从latest_major_scores.json回退查找
        # 先试精确匹配
        if (code, major, year) in major_idx:
            v = major_idx[(code, major, year)].get('最低分数')
            if v is not None:
                return int(v)
        # 再试去掉（师范类）的匹配
        base = major.replace('（师范类）', '').replace('(师范类)', '')
        if base != major and (code, base, year) in major_idx:
            v = major_idx[(code, base, year)].get('最低分数')
            if v is not None:
                return int(v)
        # 再试大类匹配（仅限大类名称如"计算机类"，且用户专业核心词在大类名中）
        base_simple = _normalize_major_name(major)
        for key, rec in major_idx.items():
            if key[0] == code and key[2] == year:
                comb_name = key[1]
                if base_simple and comb_name and comb_name.endswith('类') and base_simple in comb_name:
                    v = rec.get('最低分数')
                    if v is not None:
                        return int(v)
                if base_simple and comb_name == base_simple:
                    v = rec.get('最低分数')
                    if v is not None:
                        return int(v)
        return None
    
    def estimate_score(code, major, year=2025):
        """估算分数"""
        s = find_exact_score(code, major, year)
        if s is not None:
            return s, False
        
        # 按相似专业组估算（取组内最低分）
        for gname, members in SIMILAR_GROUPS.items():
            if major in members:
                scores = []
                for gm in members:
                    if gm != major:
                        gs = find_exact_score(code, gm, year)
                        if gs is not None:
                            scores.append(gs)
                if scores:
                    return min(scores), True
        
        # 个别映射
        individual = {
            '智慧应急': '应用化学', '智能制造工程': '机械电子工程',
            '储能科学与工程': '能源化学工程', '稀土材料科学与工程': '无机非金属材料工程',
        }
        if major in individual:
            s = find_exact_score(code, individual[major], year)
            if s is not None:
                return s, True
        
        # 学校该年所有选中专业的最低分
        scores = []
        for m in SCHOOL_MAJORS.get(code, []):
            if m != major:
                gs = find_exact_score(code, m, year)
                if gs is not None:
                    scores.append(gs)
        if scores:
            return min(scores), True
        
        # 最后手段：查combined_table中该校所有专业的最低分
        all_school_scores = []
        for key, rec in comb_idx.items():
            if key[0] == code:
                s = rec.get(f'{year}_最低分')
                if s is not None:
                    all_school_scores.append(int(s))
        if all_school_scores:
            return min(all_school_scores), True
        
        return None, True
    
    # ─── 获取专业代码 ───
    def get_major_code(code, major):
        """获取专业代码，优先用2026年招生计划的最新代码"""
        # 1. 从2026招生计划精确匹配
        if (code, major) in plan_idx:
            pc = plan_idx[(code, major)].get('专业代码')
            if pc:
                return pc
        # 2. 归一化名称后匹配（去掉（师范类）等后缀）
        base = major.replace('（师范类）', '').replace('(师范类)', '')
        if base != major and (code, base) in plan_idx:
            pc = plan_idx[(code, base)].get('专业代码')
            if pc:
                return pc
        # 3. 从combined_table回退
        for y in [2025, 2024, 2023]:
            r = find_comb(code, major, y)
            if r and r.get('专业代码'):
                return r.get('专业代码')
        return None
    
    def get_plan_2026(code, major):
        """获取2026年该专业计划人数"""
        if (code, major) in plan_idx:
            return plan_idx[(code, major)].get('计划人数')
        return None
    
    def get_plan_detail(code, major):
        """获取2026年计划详细数据"""
        if (code, major) in plan_idx:
            p = plan_idx[(code, major)]
            return {
                '计划人数': p.get('计划人数'),
                '学制': p.get('学制'),
                '学费': p.get('学费'),
                '选科要求': p.get('选科要求'),
                '专业备注': re.sub(r'·?公众号山城学术圈', '', str(p.get('专业备注',''))).strip() if p.get('专业备注') else None,
                '专业层次': p.get('专业层次'),
                '门类': p.get('门类'),
                '专业类': p.get('专业类'),
            }
        return None
    
    # ─── 检测2026年校名变更 ───
    school_name_changes = {}
    for code in SCHOOL_MAJORS:
        hist_name = None
        plan_name = None
        for item in comb:
            if str(item.get('院校代码')) == code:
                hist_name = item.get('院校名称')
                break
        for item in plans_2026:
            if str(item.get('院校代码')) == code:
                plan_name = item.get('院校名称')
                break
        if hist_name and plan_name and hist_name != plan_name:
            school_name_changes[code] = {'旧名': hist_name, '新名': plan_name}
    
    def get_school_info(code):
        """获取学校信息"""
        for item in comb:
            if str(item.get('院校代码')) == code:
                info = {
                    '所在省': item.get('所在省'),
                    '城市': item.get('城市'),
                    '城市水平': item.get('城市水平标签'),
                    '院校标签': item.get('院校标签'),
                    '院校水平': item.get('院校水平'),
                    '隶属单位': item.get('隶属单位'),
                    '类型': item.get('类型'),
                    '公私性质': item.get('公私性质'),
                    '保研率': item.get('保研率'),
                    '软科排名': item.get('软科排名'),
                }
                # 校名变更信息
                if code in school_name_changes:
                    info['校名已更新'] = school_name_changes[code]
                return info
        return {}
    
    # ─── 生成每个条目 ───
    results = []
    for code in sorted(SCHOOL_MAJORS.keys(), key=lambda c: SCHOOL_NAMES.get(c, c)):
        name = SCHOOL_NAMES.get(code, code)
        school_info = get_school_info(code)
        
        for major in SCHOOL_MAJORS[code]:
            # 各年分数
            s25, est25 = estimate_score(code, major, 2025)
            s24, est24 = estimate_score(code, major, 2024)
            s23, est23 = estimate_score(code, major, 2023)
            
            # 判断是否为真正的新增专业：仅限精确名称匹配，大类映射不算（大类拆分出来的不叫新增）
            def _has_direct_exact(code, major, year):
                """只检查精确名称匹配，不做任何归一化/大类映射"""
                if (code, major, 2025) in comb_idx:
                    r = comb_idx[(code, major, 2025)]
                    if r.get(f'{year}_最低分') is not None:
                        return True
                if (code, major, year) in major_idx:
                    return True
                return False
            has_direct_2025 = _has_direct_exact(code, major, 2025)
            has_direct_2024 = _has_direct_exact(code, major, 2024)
            has_direct_2023 = _has_direct_exact(code, major, 2023)
            has_exact_2025 = find_exact_score(code, major, 2025) is not None
            has_exact_2024 = find_exact_score(code, major, 2024) is not None
            has_exact_2023 = find_exact_score(code, major, 2023) is not None
            # 新增专业：没有任何直接匹配
            is_new = not (has_direct_2025 or has_direct_2024 or has_direct_2023)
            # 大类拆分专业：有间接匹配（通过大类/归一化）但没有直接匹配
            is_split_from_dalei = is_new and (has_exact_2025 or has_exact_2024 or has_exact_2023)
            
            # 主分数
            primary_score = None
            ref_yr = 2025
            if s25 is not None:
                primary_score = s25
                ref_yr = 2025
            elif s24 is not None:
                primary_score = s24
                ref_yr = 2024
            elif s23 is not None:
                primary_score = s23
                ref_yr = 2023
            
            ref_score = equiv.get(ref_yr, 495)
            diff = (primary_score - ref_score) if primary_score else 0
            
            if diff >= 5:
                category = '冲刺'
            elif diff >= -4:
                category = '稳妥'
            else:
                category = '保底'
            
            # 专业代码
            major_code = get_major_code(code, major)
            
            # 2026计划详情
            plan_detail = get_plan_detail(code, major)
            plan_count = plan_detail['计划人数'] if plan_detail else get_plan_2026(code, major)
            
            # 专业全称和专业备注（去掉公众号推广信息）
            def _clean_note(t):
                if t: return re.sub(r'·?公众号山城学术圈', '', str(t)).strip()
                return t
            major_full = None
            major_note = None
            for y in [2025, 2024, 2023]:
                r = find_comb(code, major, y)
                if r:
                    if r.get('专业全称') and not major_full:
                        major_full = r.get('专业全称')
                    if r.get('专业备注') and not major_note:
                        major_note = _clean_note(r.get('专业备注'))
                    break
            # 如果历史备注是中外合作但2026计划是非中外合作的，清空历史备注（避免误导）
            if major_note and '中外合作' in major_note:
                p26 = plan_detail or {}
                if p26 and '中外合作' not in str(p26.get('专业备注','')) and '中外合作' not in str(p26.get('专业名称','')):
                    major_note = None
            
            # 备注
            reference = ''
            if is_new and is_split_from_dalei:
                reference = '⚠️ 大类拆分新专业（参考原大类分数）'
            elif is_new:
                reference = '⚠️ 新增专业（基于相近专业最低分估算）'
            
            # 历年分数详情
            scores_detail = {}
            for y in [2025, 2024, 2023]:
                r = find_comb(code, major, y)
                if r:
                    yr_key = str(y)
                    scores_detail[yr_key] = {
                        '最低分': r.get(f'{y}_最低分'),
                        '最低位次': r.get(f'{y}_最低位次'),
                        '平均分': r.get(f'{y}_平均分'),
                        '平均位次': r.get(f'{y}_平均位次'),
                        '最高分': r.get(f'{y}_最高分'),
                        '最高位次': r.get(f'{y}_最高位次'),
                        '录取人数': r.get(f'{y}_录取人数'),
                    }
            
            # 如果新增专业没有历史分数，填入估算分数
            if not scores_detail:
                est_scores = {2025: s25, 2024: s24, 2023: s23}
                for y in [2025, 2024, 2023]:
                    if est_scores[y] is not None:
                        scores_detail[str(y)] = {
                            '最低分': float(est_scores[y]),
                            '最低位次': None,
                            '平均分': None,
                            '最高分': None,
                            '录取人数': None,
                            '估算': True
                        }
            
            item = {
                '学校代码': code,
                '学校名称': name,
                '专业名称': major,
                '专业代码': major_code,
                '专业全称': major_full,
                '专业备注': major_note,
                '等效分': {str(k): v for k, v in equiv.items()},
                '历年分数': scores_detail,
                '2026计划': plan_detail or ( {'计划人数': plan_count} if plan_count else None ),
                '分差': diff,
                '类别': category,
                '是否新增': is_new,
                '大类拆分': is_split_from_dalei,
                '备注': reference,
                '学校信息': school_info
            }
            results.append(item)
    
    # ─── 排序 ───
    cat_order = {'冲刺': 0, '稳妥': 1, '保底': 2}
    results.sort(key=lambda r: (
        cat_order.get(r['类别'], 99),
        -(r['历年分数'].get('2025', {}).get('最低分') or 0) if '2025' in r.get('历年分数', {}) and r['历年分数']['2025'].get('最低分') else -(r['历年分数'].get('2024', {}).get('最低分') or 0),
        r['学校名称'],
        r['专业名称']
    ))
    
    # 为每条记录加上各年等效分字段
    for item in results:
        item['等效分2024'] = equiv.get(2024)
        item['等效分2023'] = equiv.get(2023)
    
    # ─── 输出 ───
    output = {
        '考生信息': {
            '年份': 2026,
            '分数': SCORE_2026,
            '位次': rank_2026,
            '科类': KELEI,
            '等效分': {str(k): v for k, v in equiv.items()},
            '省控线(本科批)': None
        },
        '分类说明': {
            '冲刺': '等效分差≥5分，略高于你的位次水平，可以冲一冲',
            '稳妥': '等效分差在-4~+4分之间，与你的位次匹配度较高',
            '保底': '等效分差≤-5分，低于你的位次水平，录取概率很高'
        },
        '分类汇总': {
            '冲刺': len([r for r in results if r['类别'] == '冲刺']),
            '稳妥': len([r for r in results if r['类别'] == '稳妥']),
            '保底': len([r for r in results if r['类别'] == '保底']),
            '总计': len(results)
        },
        '推荐列表': results
    }
    
    json_path = os.path.join(OUT_DIR, '志愿推荐.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n✓ JSON: {json_path} ({len(results)} 条)")
    
    # ─── 生成HTML ───
    html_path = os.path.join(OUT_DIR, '志愿推荐.html')
    generate_html(output, html_path)
    print(f"✓ HTML: {html_path}")


def generate_html(data, output_path):
    """生成交互式HTML页面"""
    json_data = json.dumps(data, ensure_ascii=False)
    # 生成数据指纹（用于检测数据更新后重置localStorage）
    fp_data = []
    for item in data['推荐列表'][:5]:
        fp_data.append((item['学校代码'], item['专业名称'],
                        item['历年分数'].get('2025',{}).get('最低分'),
                        item.get('专业代码')))
    data_fingerprint = hashlib.md5(str(fp_data).encode()).hexdigest()[:12]
    
    html = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>高考志愿规划表 - 2026</title>
<script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js"></script>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; background:#f0f2f5; color:#333; padding:16px; }
.container { max-width:1400px; margin:0 auto; }

/* ── 头部 ── */
.header { background:linear-gradient(135deg,#667eea,#764ba2); color:#fff; border-radius:12px; padding:20px 28px; margin-bottom:16px; }
.header h1 { font-size:22px; margin-bottom:8px; }
.header .info { display:flex; flex-wrap:wrap; gap:8px 16px; font-size:13px; }
.header .info span { background:rgba(255,255,255,.15); padding:3px 12px; border-radius:16px; }

/* ── 统计卡 ── */
.stats { display:flex; gap:12px; margin-bottom:16px; flex-wrap:wrap; }
.sc { flex:1; min-width:120px; background:#fff; border-radius:10px; padding:14px 18px; box-shadow:0 1px 3px rgba(0,0,0,.06); }
.sc .n { font-size:26px; font-weight:700; }
.sc .l { font-size:12px; color:#888; margin-top:3px; }
.sc.r .n { color:#e74c3c; } .sc.y .n { color:#f39c12; } .sc.g .n { color:#27ae60; } .sc.p .n { color:#667eea; }

/* ── 工具栏 ── */
.tbar { display:flex; gap:8px; margin-bottom:12px; flex-wrap:wrap; align-items:center; }
.tbar button,.tbar select { padding:7px 14px; border:1px solid #ddd; border-radius:8px; background:#fff; cursor:pointer; font-size:13px; }
.tbar button:hover { background:#f0f0f0; }
.tbar .bp { background:#667eea; color:#fff; border-color:#667eea; }
.tbar .bp:hover { background:#5a6fd6; }
.tbar .bd { background:#e74c3c; color:#fff; border-color:#e74c3c; }
.tbar .bd:hover { background:#c0392b; }
.tbar .sb { flex:1; min-width:180px; }
.tbar .sb input { width:100%; padding:7px 14px; border:1px solid #ddd; border-radius:8px; font-size:13px; }

/* ── 三栏 ── */
.cols { display:flex; gap:12px; align-items:flex-start; }
.col { flex:1; min-width:0; display:flex; flex-direction:column; }
.ch { padding:10px 14px; border-radius:10px 10px 0 0; font-weight:600; font-size:14px; display:flex; justify-content:space-between; align-items:center; }
.ch.cr { background:#fde8e8; color:#c0392b; }
.ch.cy { background:#fef5e7; color:#d68910; }
.ch.cg { background:#e8f8f5; color:#1e8449; }
.cb { background:#fff; border-radius:0 0 10px 10px; box-shadow:0 1px 4px rgba(0,0,0,.08); min-height:50px; padding:4px; }
.cb.cr { border:2px solid #fde8e8; border-top:none; }
.cb.cy { border:2px solid #fef5e7; border-top:none; }
.cb.cg { border:2px solid #e8f8f5; border-top:none; }

/* ── 卡片 ── */
.card { padding:10px; margin:4px; border-radius:8px; border:1px solid #eee; cursor:grab; background:#fff; }
.card:hover { box-shadow:0 2px 8px rgba(0,0,0,.08); }
.card.del { opacity:.35; background:#f7f7f7; text-decoration:line-through; }
.card .hdr { display:flex; justify-content:space-between; align-items:flex-start; gap:6px; margin-bottom:4px; }
.card .nm { font-weight:600; font-size:13px; color:#2c3e50; }
.card .mj { font-size:12px; color:#555; margin-top:1px; }
.card .cd { font-size:10px; color:#999; font-weight:400; margin-left:4px; }
.card .diff { font-size:11px; padding:1px 8px; border-radius:10px; white-space:nowrap; flex-shrink:0; }
.card .dfp { background:#fde8e8; color:#e74c3c; }
.card .dfn { background:#e8f8f5; color:#27ae60; }
.card .dfz { background:#fef5e7; color:#f39c12; }
.card .row { display:flex; gap:12px; margin:6px 0; }
.card .row .it { display:flex; flex-direction:column; align-items:center; }
.card .row .it .y { font-size:9px; color:#bbb; }
.card .row .it .v { font-size:13px; font-weight:600; color:#333; }
.card .row .it .v.est { color:#b7950b; position:relative; } .card .row .it .v.est sup { font-size:9px; color:#b7950b; }
.card .row .it .v.ms { color:#bbb; }
.card .tag { display:inline-block; font-size:10px; padding:1px 6px; border-radius:8px; margin-right:3px; }
.card .tg-new { background:#eaf0fb; color:#2980b9; }
.card .tg-upd { background:#fef9e7; color:#b7950b; }
.card .ftr { display:flex; justify-content:space-between; align-items:center; margin-top:6px; padding-top:6px; border-top:1px solid #f0f0f0; }
.card .ftr .dh { color:#ccc; font-size:11px; }
.card .ftr button { padding:2px 10px; border:1px solid #ddd; border-radius:4px; background:#fff; cursor:pointer; font-size:11px; }
.card .ftr button:hover { background:#f0f0f0; }
.card .ftr .db { color:#e74c3c; border-color:#f5c6cb; }
.card .ftr .db:hover { background:#fde8e8; }
.card .ftr .rb { color:#27ae60; border-color:#c3e6cb; }
.card .ftr .rb:hover { background:#e8f8f5; }

/* ── 已删除区 ── */
.dz { margin-top:20px; }
.dz h3 { font-size:13px; color:#999; margin-bottom:6px; display:flex; align-items:center; gap:6px; }
.dz .dc { font-size:11px; background:#eee; padding:1px 7px; border-radius:10px; }
.db { background:#fff; border-radius:10px; box-shadow:0 1px 4px rgba(0,0,0,.08); min-height:40px; padding:4px; border:2px dashed #ddd; }
.emp { text-align:center; padding:20px 10px; color:#bbb; font-size:12px; }

.sg { opacity:.3; background:#e8f0fe !important; border:2px dashed #667eea !important; }
.scs { box-shadow:0 4px 16px rgba(0,0,0,.12) !important; }

@media (max-width:900px) { .cols { flex-direction:column; } }
</style>
</head>
<body>
<div class="container">
  <div class="header" id="hdr"></div>
  <div class="stats" id="sts"></div>
  <div class="tbar">
    <button class="bp" onclick="exp()">📋 导出</button>
    <button onclick="rs()">🔄 重置</button>
    <button class="bd" onclick="cd()">🗑️ 清空已删</button>
    <div class="sb"><input id="q" placeholder="🔍 搜索学校或专业..." oninput="flt()"></div>
    <select id="fn" onchange="flt()">
      <option value="all">全部</option>
      <option value="new">仅新增专业</option>
      <option value="old">仅原有专业</option>
    </select>
  </div>
  <div style="display:flex;gap:12px;margin-bottom:8px;font-size:12px;color:#666;flex-wrap:wrap;">
    <span>🆕 = 新增专业</span>
    <span style="color:#b7950b;">分数<sup>估</sup> = 基于相近专业估算</span>
    <span style="color:#bbb;">-- = 无历年数据</span>
    <span>⏫/⏬/➡️ = 与等效分对比（高/低/持平）</span>
  </div>
  <div class="cols" id="cols"></div>
  <div class="dz" id="dz"></div>
</div>
<script>
const D = """ + json_data + r""";
const DATA_VERSION = 'REPLACE_ME';
let P = [], R = [], S = {};

function init() {
  const s = localStorage.getItem('gk');
  var ver = 'v0';
  if (s) { try { const o = JSON.parse(s); ver = o.v||'v0'; P = o.p||[]; R = o.r||[]; } catch(e) { def(); } }
  // 数据版本变化时重置（HTML已重新生成）
  if (ver !== DATA_VERSION) { def(); }
  rnd();
}
function def() { P = D.推荐列表.map((x,i) => ({...x,_id:i})); R = []; }
function sv() {
  localStorage.setItem('gk', JSON.stringify({v:DATA_VERSION,p:P,r:R}));
}

function rnd() {
  // header
  const ii = D.考生信息;
  document.getElementById('hdr').innerHTML = `<h1>🎓 2026年高考志愿规划表</h1><div class="info">
    <span>📅 2026</span><span>📊 ${ii.分数}分</span><span>📍 ${ii.位次.toLocaleString()}名</span>
    <span>🔄 25等效: ${ii.等效分['2025']}分</span><span>🔄 24等效: ${ii.等效分['2024']}分</span><span>🔄 23等效: ${ii.等效分['2023']}分</span>
  </div>`;
  
  // stats
  const c = {冲刺:0,稳妥:0,保底:0}; P.forEach(x => { if (c[x.类别]!==undefined) c[x.类别]++; });
  document.getElementById('sts').innerHTML = [
    ['r','🚀 冲刺',c.冲刺],['y','✅ 稳妥',c.稳妥],['g','🛡️ 保底',c.保底],['p','📌 总计',P.length]
  ].map(([cls,lb,n]) => `<div class="sc ${cls}"><div class="n">${n}</div><div class="l">${lb}</div></div>`).join('');
  
  // columns
  const cats = ['冲刺','稳妥','保底'];
  const clsMap = {冲刺:'cr',稳妥:'cy',保底:'cg'};
  document.getElementById('cols').innerHTML = cats.map(c => `
    <div class="col">
      <div class="ch ${clsMap[c]}">${c}</div>
      <div class="cb ${clsMap[c]}" id="col-${c}"></div>
    </div>`).join('');
  cats.forEach(c => {
    const el = document.getElementById('col-'+c);
    el.innerHTML = '';
    const items = P.filter(x => x.类别 === c);
    if (!items.length) el.innerHTML = '<div class="emp">（空）</div>';
    else items.forEach(x => el.appendChild(cd2(x)));
  });
  
  // deleted
  const dz = document.getElementById('dz');
  if (!R.length) { dz.innerHTML = ''; }
  else {
    dz.innerHTML = `<h3>🗑️ 已删除 <span class="dc">${R.length}</span></h3><div class="db" id="col-del"></div>`;
    R.forEach(x => document.getElementById('col-del').appendChild(cd2(x, true)));
  }
  
  // sortables
  Object.values(S).forEach(s => s.destroy()); S = {};
  cats.forEach(c => {
    const el = document.getElementById('col-'+c);
    if (!el) return;
    S[c] = new Sortable(el, {
      group:'plan', animation:200, ghostClass:'sg', chosenClass:'scs',
      onEnd: () => { up(); sv(); }
    });
  });
  const de = document.getElementById('col-del');
  if (de) {
    S.del = new Sortable(de, {
      group:{name:'plan',pull:false,put:true}, animation:200, ghostClass:'sg',
      onAdd: ev => {
        const id = parseInt(ev.item.dataset.id);
        const i = P.findIndex(p => p._id === id);
        if (i>=0) { R.push(P[i]); P.splice(i,1); sv(); rnd(); }
      }
    });
  }
  sv();
}

function cd2(x, isDel) {
  const d = document.createElement('div');
  d.className = 'card' + (isDel ? ' del' : '');
  d.dataset.id = x._id;
  
  const df = x.分差;
  const dc = df>0?'dfp':df<0?'dfn':'dfz';
  const dl = df>0?'⏫ +'+df:df<0?'⏬ '+df:'➡️ '+df;
  const s25 = x.历年分数?.['2025'];
  const s24 = x.历年分数?.['2024'];
  const s23 = x.历年分数?.['2023'];
  const si = x.学校信息||{};
  const nc = si.校名已更新;
  const p26 = x['2026计划']||{};
  const extras = [];
  if (si.城市) extras.push(`📍 ${si.城市}`);
  if (p26.计划人数) extras.push(`📋 招${p26.计划人数}人`);
  if (p26.学费) extras.push(`💰 ${p26.学费}`);
  if (p26.学制) extras.push(`⏱ ${p26.学制}年`);
  if (p26.选科要求) extras.push(`🧪 选科:${p26.选科要求}`);
  if (si.保研率) extras.push(`📈 保研${(si.保研率*100).toFixed(1)}%`);
  if (si.院校标签) extras.push(`🏷 ${si.院校标签}`);
  // 招生要求（体检/视力等）- 去掉公众号等无关信息
  const cleanNote = (s) => (s||'').replace(/·?公众号山城学术圈/g,'').trim();
  const reqNotes = [];
  const nn1 = cleanNote(x.专业备注);
  if (nn1) reqNotes.push(nn1);
  const nn2 = cleanNote(p26.专业备注);
  if (nn2 && nn2 !== nn1) reqNotes.push(nn2);
  const reqStr = reqNotes.filter(Boolean).join('；');
  
  function svv(y,d,isEst) {
    if (!d) return '<span class="v ms">--</span>';
    const cls = isEst ? ' est' : '';
    const sup = isEst ? '<sup>估</sup>' : '';
    return `<span class="v${cls}">${d}${sup}</span>`;
  }
  
  d.innerHTML = `
    <div class="hdr"><div>
      <div class="nm">${x.学校名称}<span class="cd">${x.学校代码}</span><span class="cd">${x.专业代码||''}</span>
        ${x.是否新增?'<span class="tag tg-new">🆕</span>':''}
        ${x.大类拆分?'<span class="tag tg-upd">📦 大类拆分</span>':''}
        ${nc?`<span class="tag tg-upd">${nc.旧名}→${nc.新名}</span>`:''}
      </div>
      <div class="mj">${x.专业名称}</div>
    </div><div><span class="diff ${dc}">${dl}</span></div></div>
    <div class="row">
      <div class="it"><span class="y">2025</span>${svv(2025,s25?.最低分,s25?.估算)}</div>
      <div class="it"><span class="y">2024</span>${svv(2024,s24?.最低分,s24?.估算)}</div>
      <div class="it"><span class="y">2023</span>${svv(2023,s23?.最低分,s23?.估算)}</div>
      <div class="it"><span class="y">等效</span><span class="v">${x.等效分?.['2025']||'--'}分</span></div>
    </div>
    ${extras.length ? `<div style="font-size:11px;color:#888;display:flex;flex-wrap:wrap;gap:4px 10px;">${extras.map(e => `<span>${e}</span>`).join('')}</div>` : ''}
    ${reqStr ? `<div style="font-size:10px;color:#c0392b;background:#fde8e8;border-radius:4px;padding:3px 6px;margin-top:3px;">⚠️ ${reqStr}</div>` : ''}
    <div class="ftr">
      <span class="dh">⠿ 拖拽调整</span>
      ${isDel
        ? `<button class="rb" onclick="rs2(${x._id})">↩️ 恢复</button>`
        : `<button class="db" onclick="dl2(${x._id})">✕ 删除</button>`
      }
    </div>`;
  return d;
}

function up() {
  const np = [];
  ['冲刺','稳妥','保底'].forEach(c => {
    const el = document.getElementById('col-'+c);
    if (!el) return;
    el.querySelectorAll('.card').forEach(card => {
      const id = parseInt(card.dataset.id);
      const it = P.find(p => p._id === id);
      if (it) np.push(it);
    });
  });
  P = np;
}
function dl2(id) { const i = P.findIndex(p => p._id === id); if (i>=0) { R.push(P[i]); P.splice(i,1); rnd(); } }
function rs2(id) { const i = R.findIndex(p => p._id === id); if (i>=0) { P.push(R[i]); R.splice(i,1); rnd(); } }
function rs() { if (confirm('重置所有排序和删除？')) { def(); rnd(); } }
function cd() { if (confirm(`清空已删除的 ${R.length} 个？`)) { R = []; rnd(); } }

function flt() {
  const q = document.getElementById('q').value.trim().toLowerCase();
  const f = document.getElementById('fn').value;
  document.querySelectorAll('.card').forEach(c => {
    const id = parseInt(c.dataset.id);
    const it = [...P, ...R].find(p => p._id === id);
    if (!it) return void (c.style.display = '');
    let s = true;
    if (q) s = it.学校名称.toLowerCase().includes(q) || it.专业名称.toLowerCase().includes(q);
    if (f==='new' && !it.是否新增) s = false;
    if (f==='old' && it.是否新增) s = false;
    c.style.display = s ? '' : 'none';
  });
}

function exp() {
  const ii = D.考生信息;
  let ls = [
    '# 高考志愿表 (2026年)', `# 考生: ${ii.分数}分 位次${ii.位次}`,
    `# 等效分: 2025≈${ii.等效分['2025']} | 2024≈${ii.等效分['2024']} | 2023≈${ii.等效分['2023']}`,
    '', '| # | 学校 | 专业 | 代码 | 类别 | 25分 | 24分 | 23分 | 等25 | 等24 | 等23 | 分差 | 26计划 | 城市 | 备注 |',
    '|---|------|------|------|------|------|------|------|------|------|------|------|--------|------|------|'
  ];
  P.forEach((x,i) => {
    const s25 = x.历年分数?.['2025']?.最低分 ?? '-';
    const s24 = x.历年分数?.['2024']?.最低分 ?? '-';
    const s23 = x.历年分数?.['2023']?.最低分 ?? '-';
    const d = x.分差>0?'+'+x.分差:x.分差;
    const pn = x['2026计划']?.计划人数 ?? '-';
    const cy = x.学校信息?.城市 ?? '';
    const nt = x.是否新增 ? '新增' : '';
    ls.push(`| ${i+1} | ${x.学校名称} | ${x.专业名称} | ${x.专业代码||'-'} | ${x.类别} | ${s25} | ${s24} | ${s23} | ${x.等效分?.['2025']||'-'} | ${x.等效分2024||'-'} | ${x.等效分2023||'-'} | ${d} | ${pn} | ${cy} | ${nt} |`);
  });
  ls.push('', `共 ${P.length} 个，已删 ${R.length} 个。`);
  const b = new Blob([ls.join('\\n')], {type:'text/plain;charset=utf-8'});
  const a = document.createElement('a'); a.href = URL.createObjectURL(b); a.download = '高考志愿表_2026.txt'; a.click();
}

init();
</script>
</body>
</html>"""
    
    # 替换数据指纹占位符
    html = html.replace("REPLACE_ME", data_fingerprint)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)


if __name__ == '__main__':
    main()
