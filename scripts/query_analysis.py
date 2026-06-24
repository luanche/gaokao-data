"""
高考数据查询分析脚本
提供多维度查询功能，支持按院校、专业、分数、位次、年份、科类等维度分析。
"""

import json
import os
import sys
from collections import defaultdict, Counter
from datetime import datetime

# ============== 配置 ==============
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "json_data")

# ============== 数据加载 ==============
_cache = {}

def load(filename):
    """按需加载 JSON 数据（带缓存）"""
    if filename in _cache:
        return _cache[filename]
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        print(f"⚠ 文件不存在: {path}")
        return []
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    _cache[filename] = data
    print(f"  ✓ 已加载: {filename} ({len(data)} 条)")
    return data


def load_all():
    """延迟加载所有数据集（惰性求值）"""
    return {
        "historical_enrollment_plans": lambda: load("historical_enrollment_plans.json"),
        "historical_major_scores": lambda: load("historical_major_scores.json"),
        "historical_toudang_lines": lambda: load("historical_toudang_lines.json"),
        "historical_score_distribution": lambda: load("historical_score_distribution.json"),
        "province_control_lines": lambda: load("province_control_lines.json"),
        "latest_school_scores": lambda: load("latest_school_scores.json"),
        "latest_major_scores": lambda: load("latest_major_scores.json"),
        "latest_enrollment_plans": lambda: load("latest_enrollment_plans.json"),
        "latest_score_distribution": lambda: load("latest_score_distribution.json"),
        "combined_table": lambda: load("combined_table.json"),
    }


# ================================================================
#  查询工具函数
# ================================================================

def safe_int(v):
    if v is None:
        return None
    try:
        return int(v)
    except (ValueError, TypeError):
        return None


def match_str(val, keyword):
    """模糊匹配字符串（忽略大小写）"""
    if val is None or keyword is None:
        return False
    return keyword.lower() in str(val).lower()


def filter_records(records, **filters):
    """
    通用过滤：对 records 进行多条件过滤。
    filters 格式: field_name=(value_or_list, mode='eq'|'in'|'gte'|'lte'|'gt'|'lt'|'contains')
    简化写法: field_name=value  等价于 (value, 'eq')
              field_name=[a,b]  等价于 (a,b,'in')
    支持: eq, in, gte, lte, contains (模糊), ne (不等于)
    """
    results = []
    for r in records:
        ok = True
        for field, condition in filters.items():
            val = r.get(field)
            if isinstance(condition, (list, tuple)):
                if len(condition) == 2:
                    target, mode = condition
                else:
                    target, mode = condition[0], 'eq'
            else:
                target, mode = condition, 'eq'

            if mode == 'eq':
                if str(val) != str(target):
                    ok = False
                    break
            elif mode == 'ne':
                if str(val) == str(target):
                    ok = False
                    break
            elif mode == 'in':
                if val not in target:
                    ok = False
                    break
            elif mode == 'contains':
                if not match_str(val, target):
                    ok = False
                    break
            elif mode in ('gte', 'ge'):
                if val is None or float(val) < float(target):
                    ok = False
                    break
            elif mode in ('lte', 'le'):
                if val is None or float(val) > float(target):
                    ok = False
                    break
            elif mode == 'gt':
                if val is None or float(val) <= float(target):
                    ok = False
                    break
            elif mode == 'lt':
                if val is None or float(val) >= float(target):
                    ok = False
                    break
        if ok:
            results.append(r)
    return results


def group_and_aggregate(records, group_field, agg_field=None, agg_func='count'):
    """
    分组聚合统计
    agg_func: 'count', 'sum', 'avg', 'min', 'max'
    """
    groups = defaultdict(list)
    for r in records:
        key = r.get(group_field, "未知")
        groups[key].append(r)

    result = {}
    for key, items in groups.items():
        if agg_field is None or agg_func == 'count':
            result[key] = len(items)
        else:
            values = [float(r[agg_field]) for r in items if r[agg_field] is not None]
            if not values:
                result[key] = None
            elif agg_func == 'sum':
                result[key] = sum(values)
            elif agg_func == 'avg':
                result[key] = round(sum(values) / len(values), 2)
            elif agg_func == 'min':
                result[key] = min(values)
            elif agg_func == 'max':
                result[key] = max(values)
            elif agg_func == 'median':
                sorted_vals = sorted(values)
                n = len(sorted_vals)
                if n % 2 == 0:
                    result[key] = (sorted_vals[n//2-1] + sorted_vals[n//2]) / 2
                else:
                    result[key] = sorted_vals[n//2]
    return result


def print_table(data_dict, title=None, top_n=None, key_name="项目", val_name="数值", sort_by_value=True):
    """打印键值对表格"""
    if title:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")

    items = list(data_dict.items())
    if sort_by_value:
        items.sort(key=lambda x: x[1] if isinstance(x[1], (int, float)) else 0, reverse=True)
    if top_n:
        items = items[:top_n]

    print(f"  {'':<4} {key_name:<30} {val_name:<15}")
    print(f"  {'-'*4} {'-'*30} {'-'*15}")
    for i, (k, v) in enumerate(items, 1):
        key_str = str(k)[:30]
        if isinstance(v, float):
            val_str = f"{v:.2f}"
        else:
            val_str = str(v)
        print(f"  {i:<4} {key_str:<30} {val_str:<15}")
    print(f"  共 {len(items)} 项")


# ================================================================
#  📊 查询模块
# ================================================================

class QueryEngine:
    def __init__(self):
        self._data = {}
        self._loaders = load_all()

    @property
    def data(self):
        return self._data

    def get(self, name):
        """惰性加载指定数据集"""
        if name not in self._data:
            if name in self._loaders:
                self._data[name] = self._loaders[name]()
            else:
                self._data[name] = []
        return self._data[name]

    # ---------- 1. 按院校查询 ----------

    def query_school(self, school_name, years=None, kelei=None):
        """查询某院校所有年份的录取数据"""
        print(f"\n{'='*60}")
        print(f"  🏫 院校查询: {school_name}")
        print(f"{'='*60}")

        # 从最新院校录取分数查询
        records = self.get("latest_school_scores")
        results = filter_records(records, 院校名称=(school_name, "contains"))
        if years:
            results = filter_records(results, 年份=(years, 'in') if isinstance(years, list) else (years, 'eq'))

        if kelei:
            results = filter_records(results, 科类=(kelei, 'contains'))

        if results:
            print(f"\n  院校录取分数 (共{len(results)}条):")
            print(f"  {'年份':<6} {'科类':<6} {'批次':<14} {'最低分':<8} {'最低位次':<10} {'录取人数':<8}")
            print(f"  {'-'*6} {'-'*6} {'-'*14} {'-'*8} {'-'*10} {'-'*8}")
            for r in results[:30]:
                print(f"  {r.get('年份',''):<6} {str(r.get('科类',''))[:6]:<6} "
                      f"{str(r.get('批次',''))[:14]:<14} {str(r.get('最低分数',''))[:8]:<8} "
                      f"{str(r.get('最低分位',''))[:10]:<10} {str(r.get('录取人数',''))[:8]:<8}")
            if len(results) > 30:
                print(f"  ... 还有 {len(results)-30} 条")

        # 查询专业录取分数
        print(f"\n  专业录取分数 (近3年):")
        major_records = self.get("latest_major_scores")
        major_results = filter_records(major_records, 院校名称=(school_name, "contains"))
        for year in ['2025', '2024', '2023']:
            yr = filter_records(major_results, 年份=(year, 'eq'))
            if yr:
                by_major = group_and_aggregate(yr, '专业名称', '最低分数', 'avg')
                print(f"    [{year}年] 共 {len(yr)} 条记录, {len(by_major)} 个专业")
                top_majors = sorted(by_major.items(), key=lambda x: x[1] or 0, reverse=True)[:10]
                for maj, score in top_majors:
                    print(f"      {maj[:20]:<22} 平均最低分: {score}")

        # 历史数据
        hist_major = self.get("historical_major_scores")
        hist_results = filter_records(hist_major, 院校名称=(school_name, "contains"))
        if hist_results:
            by_year = group_and_aggregate(hist_results, '年份', '最低分', 'avg')
            print(f"\n  历史年度最低分趋势:")
            for y in sorted(by_year.keys()):
                print(f"    {y}年: 平均最低分 {by_year[y]}")

        return results

    # ---------- 2. 按专业查询 ----------

    def query_major(self, major_name, years=None, kelei=None):
        """查询某专业所有院校的录取数据"""
        print(f"\n{'='*60}")
        print(f"  📚 专业查询: {major_name}")
        print(f"{'='*60}")

        results = []
        # 从最新专业录取分数查
        records = self.get("latest_major_scores")
        results = filter_records(records, 专业名称=(major_name, "contains"))
        if years:
            results = filter_records(results, 年份=(years, 'in') if isinstance(years, list) else (years, 'eq'))
        if kelei:
            results = filter_records(results, 科类=(kelei, "contains"))

        if not results:
            # 也查历史数据
            hist = self.get("historical_major_scores")
            results = filter_records(hist, 专业名称=(major_name, "contains"))
            if years:
                results = filter_records(results, 年份=(years, 'in') if isinstance(years, list) else (years, 'eq'))
            if kelei:
                results = filter_records(results, 科类=(kelei, "contains"))

        if results:
            print(f"\n  📊 共 {len(results)} 条记录")
            # 按年份/院校汇总
            for year in sorted(set(r.get('年份') for r in results), reverse=True):
                yr_records = [r for r in results if r.get('年份') == year]
                print(f"\n  [{year}年] 共 {len(yr_records)} 个录取记录:")
                top = sorted(yr_records,
                           key=lambda x: float(x.get('最低分数', 0) or 0), reverse=True)[:15]
                for r in top:
                    school = r.get('院校名称', '')
                    score = r.get('最低分数', '')
                    rank = r.get('最低位次', '')
                    kl = r.get('科类', '')
                    print(f"    {school[:24]:<24} {kl[:4]:<4} 最低分:{score:<6} 位次:{rank}")
        else:
            print("  ⚠ 未找到相关记录")

        return results

    # ---------- 3. 按分数/位次查询 ----------

    def query_by_score(self, min_score=None, max_score=None, rank_max=None,
                       year="2025", kelei="物理类", batch="本科批"):
        """按分数段/位次段查询可报院校"""
        print(f"\n{'='*60}")
        if min_score and max_score:
            print(f"  🎯 分数段查询: {min_score}-{max_score}分 ({year} {kelei} {batch})")
        elif rank_max:
            print(f"  🎯 位次查询: 前{rank_max}名 ({year} {kelei} {batch})")
        print(f"{'='*60}")

        records = self.get("latest_school_scores")
        filters = {
            '年份': (year, 'eq'),
            '科类': (kelei, 'contains'),
            '批次': (batch, 'contains'),
        }
        if min_score:
            filters['最低分数'] = (min_score, 'gte')
        if max_score:
            filters['最低分数'] = (max_score, 'lte')
        if min_score and max_score:
            filters['最低分数'] = (min_score, 'gte')
            # 需要同时过滤两个条件，用复合逻辑
        if rank_max:
            filters['最低分位'] = (rank_max, 'lte')

        results = filter_records(records, **filters)

        # 对于同时有 min_score 和 max_score，需要额外处理
        if min_score and max_score:
            results = [r for r in results if r.get('最低分数') is not None
                       and min_score <= r['最低分数'] <= max_score]

        if results:
            print(f"\n  符合条件的院校: {len(results)} 所")
            results.sort(key=lambda r: float(r.get('最低分数', 0) or 0), reverse=True)
            print(f"  {'院校名称':<24} {'批次':<12} {'最低分':<8} {'最低位次':<10} {'批次线差':<8}")
            print(f"  {'-'*24} {'-'*12} {'-'*8} {'-'*10} {'-'*8}")
            for r in results[:50]:
                print(f"  {str(r.get('院校名称',''))[:24]:<24} {str(r.get('批次',''))[:12]:<12} "
                      f"{str(r.get('最低分数',''))[:8]:<8} {str(r.get('最低分位',''))[:10]:<10} "
                      f"{str(r.get('批次线差',''))[:8]:<8}")
            if len(results) > 50:
                print(f"  ... 还有 {len(results)-50} 所")
        else:
            print("  ⚠ 未找到符合条件的院校")

        return results

    # ---------- 4. 位次转换 ----------

    def query_rank_conversion(self, score, year_from, year_to, kelei="物理类"):
        """同位次分数转换：给定某年分数，查其他年份同等位次对应的分数"""
        print(f"\n{'='*60}")
        print(f"  🔄 同位次转换: {year_from}年 {kelei} {score}分")
        print(f"{'='*60}")

        dist = self.get("latest_score_distribution")
        if not dist:
            dist = self.get("historical_score_distribution")

        # 找到该年该科类的位次
        from_records = filter_records(dist, 年份=(year_from, 'eq'), 科类=(kelei, 'contains'))
        target_rank = None
        for r in from_records:
            s = r.get('分数')
            if s is not None:
                score_val = str(s).replace('+', '')
                try:
                    if '-' in str(s):
                        low, high = str(s).split('-')
                        if int(low) <= int(score) <= int(high):
                            target_rank = r.get('累计人数')
                            break
                    elif int(score_val) <= int(score):
                        target_rank = r.get('累计人数')
                        if int(score_val) == int(score):
                            break
                except:
                    pass

        if not target_rank:
            # 尝试精确匹配
            for r in from_records:
                s = r.get('分数')
                if str(s) == str(score) or str(s) == f"{score}":
                    target_rank = r.get('累计人数')
                    break

        if not target_rank:
            print(f"  ⚠ 未找到 {year_from}年 {kelei} {score}分对应的位次")
            return

        print(f"  {year_from}年 {score}分 → 位次: {target_rank}")

        # 在目标年份找同等位次的分数
        to_records = filter_records(dist, 年份=(year_to, 'eq'), 科类=(kelei, 'contains'))
        result_score = "未找到"
        for r in to_records:
            cum = r.get('累计人数')
            if cum and target_rank <= cum:
                result_score = r.get('分数')
                break

        print(f"  {year_to}年同等位次 → 分数: {result_score}")
        print(f"  (位次 {target_rank} 在 {year_to}年对应分数段 {result_score})")

        return {"year_from": year_from, "score_from": score,
                "rank": target_rank, "year_to": year_to, "score_to": result_score}

    # ---------- 5. 热门专业分析 ----------

    def query_popular_majors(self, year="2025", kelei="物理类", top_n=20):
        """分析热门专业（按报考人数/院校数量）"""
        print(f"\n{'='*60}")
        print(f"  🔥 热门专业分析 ({year} {kelei})")
        print(f"{'='*60}")

        records = self.get("latest_major_scores")
        records = filter_records(records, 年份=(year, 'eq'), 科类=(kelei, 'contains'))

        if not records:
            print("  ⚠ 未找到数据")
            return

        # 按专业统计开设院校数
        by_major = defaultdict(set)
        for r in records:
            major = r.get('专业名称', '未知')
            school = r.get('院校名称', '')
            by_major[major].add(school)

        # 按院校数量排序
        major_pop = {k: len(v) for k, v in by_major.items()}
        print_table(major_pop, f"开设院校最多的专业 Top{top_n}",
                    top_n=top_n, key_name="专业名称", val_name="开设院校数")

        # 按录取人数统计（如果有）
        if records[0].get('录取人数') is not None:
            by_major_count = defaultdict(int)
            for r in records:
                major = r.get('专业名称', '未知')
                cnt = r.get('录取人数')
                if cnt:
                    by_major_count[major] += cnt
            sorted_majors = sorted(by_major_count.items(), key=lambda x: x[1], reverse=True)[:top_n]
            print(f"\n  录取人数最多的专业 Top{top_n}:")
            print(f"  {'':<4} {'专业名称':<24} {'录取人数':<10}")
            print(f"  {'-'*4} {'-'*24} {'-'*10}")
            for i, (maj, cnt) in enumerate(sorted_majors, 1):
                print(f"  {i:<4} {maj[:24]:<24} {cnt:<10}")

        return by_major

    # ---------- 6. 985/211 院校分析 ----------

    def query_elite_schools(self, year="2025", kelei="物理类", batch="本科批"):
        """查询 985/211 院校录取数据"""
        print(f"\n{'='*60}")
        print(f"  🎓 985/211 院校录取分析 ({year} {kelei} {batch})")
        print(f"{'='*60}")

        records = self.get("latest_school_scores")
        results = filter_records(records,
                                 年份=(year, 'eq'),
                                 科类=(kelei, 'contains'),
                                 批次=(batch, 'contains'))
        # 分开统计
        for tag, label in [('是否985', '985院校'), ('是否211', '211院校')]:
            tagged = [r for r in results if r.get(tag) == '是']
            if tagged:
                print(f"\n  📌 {label} ({len(tagged)} 所):")
                tagged.sort(key=lambda r: float(r.get('最低分数', 0) or 0), reverse=True)
                print(f"  {'院校名称':<24} {'最低分':<8} {'最低位次':<10} {'批次':<12}")
                print(f"  {'-'*24} {'-'*8} {'-'*10} {'-'*12}")
                for r in tagged[:30]:
                    print(f"  {str(r.get('院校名称',''))[:24]:<24} "
                          f"{str(r.get('最低分数',''))[:8]:<8} "
                          f"{str(r.get('最低分位',''))[:10]:<10} "
                          f"{str(r.get('批次',''))[:12]:<12}")
                if len(tagged) > 30:
                    print(f"  ... 还有 {len(tagged)-30} 所")

        return results

    # ---------- 7. 不同批次对比 ----------

    def query_batch_comparison(self, year="2025", kelei="物理类"):
        """对比不同批次的录取数据"""
        print(f"\n{'='*60}")
        print(f"  📊 批次对比 ({year} {kelei})")
        print(f"{'='*60}")

        records = self.get("latest_school_scores")
        records = filter_records(records, 年份=(year, 'eq'), 科类=(kelei, 'contains'))

        by_batch = group_and_aggregate(records, '批次', '最低分数', 'avg')
        print_table(by_batch, "各批次平均最低分", key_name="批次", val_name="平均最低分")

        by_batch_count = group_and_aggregate(records, '批次')
        print_table(by_batch_count, "各批次院校数量", key_name="批次", val_name="院校数量")

        return by_batch

    # ---------- 8. 省份地域分析 ----------

    def query_province_analysis(self, year="2025", kelei="物理类"):
        """分析各省份高校在重庆的录取情况"""
        print(f"\n{'='*60}")
        print(f"  🌏 省份地域分析 ({year} {kelei})")
        print(f"{'='*60}")

        records = self.get("latest_school_scores")
        records = filter_records(records, 年份=(year, 'eq'), 科类=(kelei, 'contains'))

        by_province = group_and_aggregate(records, '学校所在', '最低分数', 'avg')
        print_table(by_province, "各省高校平均最低分", top_n=30,
                    key_name="省份/地区", val_name="平均最低分")

        by_province_count = group_and_aggregate(records, '学校所在')
        print_table(by_province_count, "各省高校数量", top_n=30,
                    key_name="省份/地区", val_name="院校数")

        return by_province

    # ---------- 9. 省控线查询 ----------

    def query_control_line(self, province="重庆", years=None):
        """查询省控线/批次线"""
        print(f"\n{'='*60}")
        print(f"  📏 省控线查询: {province}")
        print(f"{'='*60}")

        records = self.get("province_control_lines")
        results = filter_records(records, 地区=(province, 'contains'))
        # 也查重庆专项的
        results2 = filter_records(records, 省份=(province, 'contains'))
        all_results = results + results2

        if years:
            all_results = [r for r in all_results if str(r.get('年份')) in
                          [str(y) for y in (years if isinstance(years, list) else [years])]]

        if all_results:
            all_results.sort(key=lambda r: (str(r.get('年份', '')), str(r.get('批次', ''))))
            print(f"\n  {'年份':<6} {'类别/考生类别':<12} {'批次':<20} {'分数线':<8}")
            print(f"  {'-'*6} {'-'*12} {'-'*20} {'-'*8}")
            for r in all_results:
                year = r.get('年份', '')
                cat = r.get('类别') or r.get('考生类别', '')
                batch = r.get('批次', '')
                score = r.get('分数线', '')
                print(f"  {str(year):<6} {str(cat)[:12]:<12} {str(batch)[:20]:<20} {str(score):<8}")
        else:
            print("  ⚠ 未找到数据")

    # ---------- 10. 综合报告 ----------

    def summary_report(self, year="2025"):
        """生成年度数据总览报告"""
        print(f"\n{'='*60}")
        print(f"  📈 {year}年重庆高考录取数据总览")
        print(f"{'='*60}")

        school_records = self.get("latest_school_scores")
        school_records = filter_records(school_records, 年份=(year, 'eq'))

        if not school_records:
            print(f"  ⚠ 未找到 {year} 年的数据")
            return

        # 基本统计
        total_schools = len(set(r.get('院校名称') for r in school_records))
        total_records = len(school_records)
        print(f"\n  院校总数: {total_schools}")
        print(f"  录取记录: {total_records}")

        # 科类分布
        by_kelei = group_and_aggregate(school_records, '科类')
        print_table(by_kelei, "科类分布", key_name="科类", val_name="记录数")

        # 批次分布
        by_batch = group_and_aggregate(school_records, '批次')
        print_table(by_batch, "批次分布", key_name="批次", val_name="记录数")

        # 最低分区间
        scores = [r.get('最低分数') for r in school_records if r.get('最低分数') is not None]
        if scores:
            print(f"\n  最低分统计:")
            print(f"    最高最低分: {max(scores):.0f}")
            print(f"    最低最低分: {min(scores):.0f}")
            print(f"    平均最低分: {sum(scores)/len(scores):.1f}")

        # 985/211 统计
        for tag, label in [('是否985', '985'), ('是否211', '211')]:
            count_yes = len([r for r in school_records if r.get(tag) == '是'])
            print(f"  {label}院校录取记录: {count_yes}")

        # 民办/公办
        by_nature = group_and_aggregate(school_records, '学校性质')
        print_table(by_nature, "学校性质分布", key_name="性质", val_name="记录数")

    # ---------- 11. 自由查询 ----------

    def custom_query(self, dataset, conditions, sort_by=None, limit=50):
        """
        自由查询
        dataset: 数据集名称 (如 'latest_school_scores', 'latest_major_scores')
        conditions: 过滤条件 dict, 格式同 filter_records
        sort_by: (field, reverse) 排序
        limit: 返回条数
        """
        records = self.get(dataset)
        if not records:
            print(f"⚠ 未知数据集: {dataset}")
            print(f"   可用数据集: {list(self._loaders.keys())}")
            return

        results = filter_records(records, **conditions)

        if sort_by:
            field, reverse = sort_by
            results.sort(key=lambda r: r.get(field) or 0, reverse=reverse)

        print(f"\n{'='*60}")
        print(f"  🔍 自定义查询: {dataset}")
        print(f"  条件: {conditions}")
        print(f"  结果: {len(results)} 条")
        print(f"{'='*60}")

        if results:
            # 显示前几条
            show = results[:limit]
            keys = list(show[0].keys())
            # 只显示非 None 的字段
            display_keys = [k for k in keys[:10]]  # 最多10列
            print(f"  字段: {', '.join(display_keys)}")
            print()
            for i, r in enumerate(show, 1):
                parts = [f"{k}={r.get(k)}" for k in display_keys if r.get(k) is not None]
                print(f"  {i}. {' | '.join(parts)}")
                if i >= 20:
                    print(f"  ... (共 {len(results)} 条, 显示前20条)")
                    break

        return results


# ================================================================
#  CLI 交互
# ================================================================

def show_help():
    print("""
📖 高考数据查询脚本 - 使用帮助

用法:
  python3 query_analysis.py <命令> [参数]

命令:
  school <名称>         查询院校录取数据
  major <专业名>        查询专业录取数据
  score <最低分> [最高分] 按分数段查询可报院校
  rank <位次>           按位次查询可报院校
  convert <年份> <分数> <目标年份>  同位次分数转换
  popular [年份]        热门专业分析
  elite [年份]          985/211院校分析
  batch [年份]          批次对比分析
  province [年份]       省份地域分析
  control [省份]        省控线查询
  summary [年份]        年度数据总览
  custom <数据集> <字段=值,...>  自由查询
  help                  显示此帮助

示例:
  python3 query_analysis.py school 清华大学
  python3 query_analysis.py major 计算机
  python3 query_analysis.py score 600 650
  python3 query_analysis.py rank 5000
  python3 query_analysis.py convert 2025 650 2024
  python3 query_analysis.py popular 2025
  python3 query_analysis.py elite
  python3 query_analysis.py summary 2025
  python3 query_analysis.py control 重庆
  python3 query_analysis.py custom latest_school_scores 年份=2025,科类=物理类
""")


def main():
    qe = QueryEngine()

    if len(sys.argv) < 2:
        show_help()
        return

    cmd = sys.argv[1]

    if cmd == 'help':
        show_help()

    elif cmd == 'school':
        if len(sys.argv) < 3:
            print("用法: python3 query_analysis.py school <院校名称> [年份] [科类]")
            return
        name = sys.argv[2]
        year = sys.argv[3] if len(sys.argv) > 3 else None
        kelei = sys.argv[4] if len(sys.argv) > 4 else None
        qe.query_school(name, year, kelei)

    elif cmd == 'major':
        if len(sys.argv) < 3:
            print("用法: python3 query_analysis.py major <专业名称> [年份] [科类]")
            return
        name = sys.argv[2]
        year = sys.argv[3] if len(sys.argv) > 3 else None
        kelei = sys.argv[4] if len(sys.argv) > 4 else None
        qe.query_major(name, year, kelei)

    elif cmd == 'score':
        if len(sys.argv) < 3:
            print("用法: python3 query_analysis.py score <最低分> [最高分] [年份] [科类] [批次]")
            return
        min_s = int(sys.argv[2])
        max_s = int(sys.argv[3]) if len(sys.argv) > 3 else None
        year = sys.argv[4] if len(sys.argv) > 4 else "2025"
        kelei = sys.argv[5] if len(sys.argv) > 5 else "物理类"
        batch = sys.argv[6] if len(sys.argv) > 6 else "本科批"
        qe.query_by_score(min_score=min_s, max_score=max_s,
                         year=year, kelei=kelei, batch=batch)

    elif cmd == 'rank':
        if len(sys.argv) < 3:
            print("用法: python3 query_analysis.py rank <位次> [年份] [科类] [批次]")
            return
        rank = int(sys.argv[2])
        year = sys.argv[3] if len(sys.argv) > 3 else "2025"
        kelei = sys.argv[4] if len(sys.argv) > 4 else "物理类"
        batch = sys.argv[5] if len(sys.argv) > 5 else "本科批"
        qe.query_by_score(rank_max=rank, year=year, kelei=kelei, batch=batch)

    elif cmd == 'convert':
        if len(sys.argv) < 5:
            print("用法: python3 query_analysis.py convert <年份> <分数> <目标年份> [科类]")
            return
        year = sys.argv[2]
        score = int(sys.argv[3])
        to_year = sys.argv[4]
        kelei = sys.argv[5] if len(sys.argv) > 5 else "物理类"
        qe.query_rank_conversion(score, year, to_year, kelei)

    elif cmd == 'popular':
        year = sys.argv[2] if len(sys.argv) > 2 else "2025"
        qe.query_popular_majors(year)

    elif cmd == 'elite':
        year = sys.argv[2] if len(sys.argv) > 2 else "2025"
        qe.query_elite_schools(year)

    elif cmd == 'batch':
        year = sys.argv[2] if len(sys.argv) > 2 else "2025"
        qe.query_batch_comparison(year)

    elif cmd == 'province':
        year = sys.argv[2] if len(sys.argv) > 2 else "2025"
        qe.query_province_analysis(year)

    elif cmd == 'control':
        province = sys.argv[2] if len(sys.argv) > 2 else "重庆"
        qe.query_control_line(province)

    elif cmd == 'summary':
        year = sys.argv[2] if len(sys.argv) > 2 else "2025"
        qe.summary_report(year)

    elif cmd == 'custom':
        if len(sys.argv) < 4:
            print("用法: python3 query_analysis.py custom <数据集> <字段=值,字段=值,...>")
            return
        dataset = sys.argv[2]
        cond_str = sys.argv[3]
        conditions = {}
        for pair in cond_str.split(','):
            if '=' in pair:
                k, v = pair.split('=', 1)
                conditions[k.strip()] = v.strip()
        qe.custom_query(dataset, conditions)

    else:
        print(f"未知命令: {cmd}")
        show_help()


if __name__ == '__main__':
    main()
