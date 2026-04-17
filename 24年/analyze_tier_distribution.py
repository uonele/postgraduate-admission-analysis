#!/usr/bin/env python3
"""
分析各公司各阶段的 985/211/海外/双非 人数分布。
从 raw_data 目录解析每个名单文件，交叉比对各阶段人员流动。
"""
import os
import re
from collections import defaultdict

# ==================== 985 院校列表 ====================
UNIVERSITIES_985 = {
    "北京大学", "清华大学", "中国人民大学", "北京师范大学",
    "北京航空航天大学", "北京理工大学", "中国农业大学", "中央民族大学",
    "复旦大学", "上海交通大学", "同济大学", "华东师范大学",
    "南京大学", "东南大学", "浙江大学", "中国科学技术大学", "厦门大学",
    "山东大学", "中国海洋大学", "武汉大学", "华中科技大学",
    "中南大学", "湖南大学", "国防科技大学", "中山大学", "华南理工大学",
    "四川大学", "电子科技大学", "重庆大学",
    "西安交通大学", "西北工业大学", "西北农林科技大学",
    "吉林大学", "哈尔滨工业大学", "大连理工大学", "东北大学",
    "南开大学", "天津大学", "兰州大学",
}

# ==================== 211 院校列表 (不含985) ====================
UNIVERSITIES_211_ONLY = {
    "北京交通大学", "北京工业大学", "北京科技大学", "北京化工大学",
    "北京邮电大学", "北京林业大学", "北京中医药大学", "北京外国语大学",
    "中国传媒大学", "中央财经大学", "对外经济贸易大学", "中国政法大学",
    "华北电力大学", "中国地质大学", "中国矿业大学",
    "中国石油大学", "天津医科大学", "河北工业大学", "太原理工大学",
    "内蒙古大学", "辽宁大学", "大连海事大学", "延边大学", "东北师范大学",
    "哈尔滨工程大学", "东北农业大学", "东北林业大学",
    "华东理工大学", "东华大学", "上海财经大学", "上海外国语大学", "上海大学",
    "苏州大学", "南京航空航天大学", "南京理工大学",
    "河海大学", "江南大学", "南京农业大学", "中国药科大学", "南京师范大学",
    "安徽大学", "合肥工业大学", "福州大学", "南昌大学",
    "郑州大学", "河南大学",
    "武汉理工大学", "华中农业大学", "华中师范大学", "中南财经政法大学",
    "湖南师范大学", "暨南大学", "华南师范大学", "广西大学", "海南大学",
    "西南交通大学", "西南财经大学", "四川农业大学",
    "贵州大学", "云南大学", "西藏大学",
    "西安电子科技大学", "长安大学", "西北大学", "陕西师范大学",
    "青海大学", "宁夏大学", "新疆大学", "石河子大学",
}

# 海外名校关键词
OVERSEAS_KEYWORDS = [
    "新加坡", "香港", "伦敦", "英国", "阿尔伯塔", "澳大利亚", "新南威尔士",
    "莫纳什", "匹兹堡", "诺丁汉", "马来西亚", "UCL", "利物浦",
    "伯明翰", "墨尔本", "悉尼", "剑桥", "牛津", "哈佛", "斯坦福",
    "耶鲁", "麻省", "哥伦比亚", "芝加哥", "宾夕法尼亚",
]


def classify_university(uni_name):
    """分类大学: 985/211/overseas/shuangfei"""
    for u985 in UNIVERSITIES_985:
        if u985 in uni_name or uni_name in u985:
            return "985"
    for u211 in UNIVERSITIES_211_ONLY:
        if u211 in uni_name or uni_name in u211:
            return "211"
    for kw in OVERSEAS_KEYWORDS:
        if kw in uni_name:
            return "overseas"
    # 特殊匹配
    if "中国石油大学" in uni_name or "中国矿业大学" in uni_name or "中国地质大学" in uni_name:
        return "211"
    return "shuangfei"


def parse_name_list(filepath):
    """从清洗后的名单文件中解析出人员列表 [{name, gender, edu, university}]"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    people = []
    lines = content.split('\n')

    # 找到正文开始（跳过头部）
    start = 0
    for i, line in enumerate(lines):
        if line.strip() == '序号':
            start = i
            break

    # 判断列头
    headers = []
    for j in range(start, min(start + 6, len(lines))):
        h = lines[j].strip()
        if h in ['序号', '姓名', '性别', '学历', '毕业院校']:
            headers.append(h)
        else:
            break

    has_edu = '学历' in headers
    num_fields = len(headers)

    # 解析人员
    data_lines = lines[start + num_fields:]
    i = 0
    while i < len(data_lines):
        line = data_lines[i].strip()
        # 遇到非数字开头的行且不是空行，可能是结尾
        if not line:
            i += 1
            continue

        # 尝试解析为序号
        try:
            seq = int(line)
        except ValueError:
            # 可能是结尾文字
            if '公示' in line or '咨询' in line or '监督' in line or '时间' in line:
                break
            i += 1
            continue

        # 读取后续字段
        if has_edu:
            # 序号、姓名、性别、学历、毕业院校
            if i + 4 < len(data_lines):
                name = data_lines[i + 1].strip()
                gender = data_lines[i + 2].strip()
                edu = data_lines[i + 3].strip()
                uni = data_lines[i + 4].strip()
                # 有时学历和院校之间有空行
                if not uni and i + 5 < len(data_lines):
                    uni = data_lines[i + 5].strip()
                    i += 1
                people.append({
                    'name': name, 'gender': gender,
                    'edu': edu, 'university': uni
                })
                i += 5
            else:
                break
        else:
            # 序号、姓名、性别、毕业院校
            if i + 3 < len(data_lines):
                name = data_lines[i + 1].strip()
                gender = data_lines[i + 2].strip()
                uni = data_lines[i + 3].strip()
                people.append({
                    'name': name, 'gender': gender,
                    'edu': '', 'university': uni
                })
                i += 4
            else:
                break

    return people


def analyze_company(company_dir, company_label):
    """分析一个公司目录下的所有阶段数据"""
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw_data", company_dir)
    if not os.path.exists(base):
        return None

    files = sorted(os.listdir(base))
    stages = {}

    for f in files:
        if not f.endswith('.md'):
            continue
        filepath = os.path.join(base, f)
        people = parse_name_list(filepath)

        # 确定阶段名
        stage = f.replace('.md', '')
        stages[stage] = people

    return stages


def print_tier_stats(people, stage_name):
    """统计并打印一个阶段的层级分布"""
    stats = {"985": [], "211": [], "overseas": [], "shuangfei": []}

    for p in people:
        tier = classify_university(p['university'])
        stats[tier].append(p)

    total = len(people)
    n985 = len(stats["985"])
    n211 = len(stats["211"])
    noverseas = len(stats["overseas"])
    nshuangfei = len(stats["shuangfei"])

    print(f"\n  📊 【{stage_name}】共 {total} 人")
    print(f"     👑 985院校: {n985}人 ({n985/total*100:.1f}%)" if total > 0 else "")

    if stats["985"]:
        uni_count = defaultdict(int)
        for p in stats["985"]:
            uni_count[p['university']] += 1
        unis = sorted(uni_count.items(), key=lambda x: -x[1])
        print(f"        → {', '.join(f'{u}({c}人)' for u, c in unis)}")

    print(f"     ✨ 211院校(非985): {n211}人 ({n211/total*100:.1f}%)" if total > 0 else "")
    if stats["211"]:
        uni_count = defaultdict(int)
        for p in stats["211"]:
            uni_count[p['university']] += 1
        unis = sorted(uni_count.items(), key=lambda x: -x[1])
        print(f"        → {', '.join(f'{u}({c}人)' for u, c in unis)}")

    print(f"     🌍 海外院校: {noverseas}人 ({noverseas/total*100:.1f}%)" if total > 0 else "")
    if stats["overseas"]:
        uni_count = defaultdict(int)
        for p in stats["overseas"]:
            uni_count[p['university']] += 1
        unis = sorted(uni_count.items(), key=lambda x: -x[1])
        print(f"        → {', '.join(f'{u}({c}人)' for u, c in unis)}")

    print(f"     ⬜ 双非院校: {nshuangfei}人 ({nshuangfei/total*100:.1f}%)" if total > 0 else "")

    return {"985": n985, "211": n211, "overseas": noverseas, "shuangfei": nshuangfei, "total": total,
            "985_list": stats["985"], "211_list": stats["211"], "overseas_list": stats["overseas"]}


def compute_eliminated(prev_people, curr_people):
    """计算被淘汰的人员（在prev中但不在curr中的）"""
    curr_names = {p['name'] for p in curr_people}
    return [p for p in prev_people if p['name'] not in curr_names]


def main():
    companies = [
        ("豫信电科_2026", "豫信电科 [2026年]"),
        ("豫信河南_2024", "豫信电子科技集团（河南）有限 [2024年]"),
        ("河南电子口岸_2025", "河南电子口岸有限 [2025年]"),
        ("河南智能医学_2025", "河南智能医学科技有限 [2025年]"),
        ("河南信产投资_2025", "河南信息产业投资有限 [2025年]"),
    ]

    all_results = {}

    for company_dir, label in companies:
        print(f"\n{'='*70}")
        print(f"🏢 {label}")
        print(f"{'='*70}")

        stages = analyze_company(company_dir, label)
        if not stages:
            print("  ❌ 无数据")
            continue

        # 按阶段顺序排列
        stage_keys = sorted(stages.keys())
        print(f"  📂 找到 {len(stage_keys)} 个阶段文件:")
        for sk in stage_keys:
            print(f"     - {sk}: {len(stages[sk])}人")

        # 分析每个阶段的层级分布
        for sk in stage_keys:
            print_tier_stats(stages[sk], sk)

        # 计算各阶段淘汰人员
        print(f"\n  {'─'*50}")
        print(f"  📉 各阶段淘汰人员层级分析:")

        ordered_stages = stage_keys  # 按文件名排序，即按时间排序
        for i in range(1, len(ordered_stages)):
            prev_stage = ordered_stages[i - 1]
            curr_stage = ordered_stages[i]
            eliminated = compute_eliminated(stages[prev_stage], stages[curr_stage])
            if eliminated:
                print(f"\n  ❌ {prev_stage} → {curr_stage} 淘汰 {len(eliminated)} 人:")
                print_tier_stats(eliminated, f"淘汰({prev_stage}→{curr_stage})")

        all_results[company_dir] = stages

    # === 汇总横向对比 ===
    print(f"\n\n{'='*70}")
    print(f"📊 五大公司各阶段 985/211/海外/双非 汇总")
    print(f"{'='*70}")

    for company_dir, label in companies:
        if company_dir not in all_results:
            continue
        stages = all_results[company_dir]
        stage_keys = sorted(stages.keys())

        print(f"\n🏢 {label}")
        print(f"{'阶段':<40} {'总人数':>6} {'985':>6} {'211':>6} {'海外':>6} {'双非':>6}")
        print(f"{'─'*76}")

        for sk in stage_keys:
            people = stages[sk]
            total = len(people)
            n985 = sum(1 for p in people if classify_university(p['university']) == "985")
            n211 = sum(1 for p in people if classify_university(p['university']) == "211")
            nov = sum(1 for p in people if classify_university(p['university']) == "overseas")
            nsf = sum(1 for p in people if classify_university(p['university']) == "shuangfei")
            print(f"{sk:<40} {total:>6} {n985:>6} {n211:>6} {nov:>6} {nsf:>6}")


if __name__ == '__main__':
    main()
