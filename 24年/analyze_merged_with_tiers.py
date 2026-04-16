import urllib.request
import re
import collections
from bs4 import BeautifulSoup
import time

U_985 = ['清华大学', '北京大学', '复旦大学', '中国人民大学', '上海交通大学', '浙江大学', '中国科学技术大学', '南京大学', '武汉大学', '同济大学', '中国农业大学', '国防科技大学', '南开大学', '天津大学', '大连理工大学', '吉林大学', '哈尔滨工业大学', '东南大学', '北京航空航天大学', '北京理工大学', '中央民族大学', '北京师范大学', '中国海洋大学', '西安交通大学', '厦门大学', '山东大学', '华中科技大学', '中南大学', '湖南大学', '中山大学', '华南理工大学', '重庆大学', '四川大学', '电子科技大学', '西北工业大学', '西北农林科技大学', '兰州大学', '东北大学', '华东师范大学']

U_211 = ['郑州大学', '河南大学', '长安大学', '中国矿业大学', '北京科技大学', '西南大学', '河海大学', '南京航空航天大学', '南京理工大学', '哈尔滨工程大学', '北京邮电大学', '南昌大学', '苏州大学', '辽宁大学', '福州大学', '暨南大学', '华东理工大学', '西南交通大学', '中国药科大学', '中南财经政法大学', '湖南师范大学', '东北师范大学', '西北大学', '东华大学', '北京交通大学', '太原理工大学', '合肥工业大学', '华北电力大学', '北京化工大学', '中国传媒大学', '中国政法大学', '对外经济贸易大学', '中国石油大学', '上海外国语大学', '江南大学', '南京师范大学', '华中农业大学', '中央财经大学', '武汉理工大学']

U_OS = ['南洋理工', '匹兹堡', '新南威尔士', '莫纳什', '香港理工', '悉尼大学', '墨尔本', '伦敦', '哥伦比亚', '帝国理工', '爱丁堡', '曼彻斯特', '多伦多', '宾夕法尼亚']

def detect_tier(s):
    if not s or s == '-' or s == '无数据': return 0, ""
    for k in U_985:
        if s.startswith(k):
            if '学院' in s and '学院' not in k: continue
            if '继续教育' in s or '分校' in s: continue
            return 1000, "👑**[985]**"
    for k in U_211:
        if s.startswith(k):
            if '学院' in s and '学院' not in k: continue
            if '继续教育' in s or '分校' in s: continue
            return 500, "✨**[211]**"
    for k in U_OS:
        if k in s: return 600, "🌍**[海外名校]**"
    return 0, ""

def clean_role(r):
    if not r: return '未知岗位'
    for p in ['豫信河南-', '登封公司-', '本部-', '豫信电科-']:
        r = r.replace(p, '')
    return r.strip()

md_file = '/Users/wuwenle/Desktop/考研/24年/豫信电科全网招聘汇总_分类版.md'
target_comps = ['豫信电科', '豫信电子科技集团（河南）有限', '河南电子口岸有限', '河南智能医学科技有限', '河南信息产业投资有限']

urls_by_comp = collections.defaultdict(list)
with open(md_file, 'r', encoding='utf-8') as f:
    current_comp = None
    for line in f:
        line = line.strip()
        if line.startswith('## 🏢 '):
            m = re.search(r'## 🏢 (.+?) \(', line)
            if m: current_comp = m.group(1).strip()
        elif line.startswith('- [') and current_comp in target_comps:
            m = re.search(r'\[(.*?)\]\((.*?)\)', line)
            if m: urls_by_comp[current_comp].append({'title': m.group(1), 'url': m.group(2)})

STAGE_RANKS = {'初筛': 0, '笔试': 1, '初试': 2, '初面': 2, '复试': 3, '复面': 3, '终面': 3, '录用': 4}

def get_stage_rank(title):
    rank = 1 
    stage_name = '未知阶段'
    for k, v in STAGE_RANKS.items():
        if k in title:
            if v > rank:
                rank = v
                stage_name = k
    return rank, stage_name

def get_cohort(title):
    m = re.search(r'(20\d{2}年)', title)
    return m.group(1) if m else '未知批次'

def normalize_header(th):
    th = th.replace(' ', '').replace('\n', '')
    if '姓名' in th: return 'name'
    if '性别' in th: return 'sex'
    if '年龄' in th: return 'age'
    if '学历' in th: return 'degree'
    if '学校' in th or '院校' in th: return 'school'
    if '专业' in th: return 'major'
    if '岗位' in th or '职位' in th: return 'role'
    return None

def fetch_table_data(url, default_role='未知岗位'):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    records = []
    try:
        html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')
        tables = soup.find_all('table')
        if not tables: return records
        for table in tables:
            rows = table.find_all('tr')
            if not rows: continue
            header_cells = rows[0].find_all(['th', 'td'])
            headers = [normalize_header(c.get_text(strip=True)) for c in header_cells]
            if 'name' not in headers:
                if len(rows) > 1:
                    header_cells = rows[1].find_all(['th', 'td'])
                    headers = [normalize_header(c.get_text(strip=True)) for c in header_cells]
                    rows = rows[1:]
            if 'name' not in headers: continue
            for row in rows[1:]:
                cells = row.find_all('td')
                if not cells or len(cells) < len(headers): continue
                rec = {}
                for h, c in zip(headers, cells):
                    if h: rec[h] = c.get_text(strip=True).replace('\n', '').replace('\r', '')
                if rec.get('name'):
                    if 'role' not in rec or not rec['role']:
                        rec['role'] = default_role
                    records.append(rec)
    except Exception as e: print(f"Error fetching {url}: {e}")
    time.sleep(0.5)
    return records

def get_role_from_title(title):
    if '投资' in title: return '投资类'
    if '研发' in title: return '研发类'
    if '财务' in title: return '财务类'
    if '市场' in title: return '市场类'
    return '未知岗位'

all_stats = []
for comp in target_comps:
    print(f"Processing {comp} ...")
    items = urls_by_comp[comp]
    cohorts = collections.defaultdict(list)
    for it in items:
        cohort = get_cohort(it['title'])
        rank, sname = get_stage_rank(it['title'])
        if rank > 0: cohorts[cohort].append({'title': it['title'], 'url': it['url'], 'rank': rank, 'sname': sname})
            
    for cohort, citems in cohorts.items():
        citems.sort(key=lambda x: x['rank'])
        candidates = {} 
        for it in citems:
            def_role = get_role_from_title(it['title'])
            recs = fetch_table_data(it['url'], def_role)
            for r in recs:
                name = r['name'].replace(' ', '')
                if name not in candidates:
                    candidates[name] = {
                        'name': name, 'sex': '无数据', 'age': '无数据', 'degree': '无数据',
                        'school': '无数据', 'major': '无数据', 'role': '未知岗位',
                        'max_rank': 0, 'max_stage': '初筛阶段'
                    }
                c = candidates[name]
                if it['rank'] > c['max_rank']:
                    c['max_rank'] = it['rank']
                    c['max_stage'] = it['sname']
                for field in ['sex', 'age', 'degree', 'school', 'major']:
                    rv = r.get(field, '')
                    if rv and rv != '-' and rv != '无' and rv != 'None' and rv != '未知岗位':
                        c[field] = rv
                
                new_role = clean_role(r.get('role', ''))
                if new_role and new_role != '未知岗位':
                    if not new_role.endswith('类'):
                        c['role'] = new_role
                    elif c['role'] == '未知岗位':
                        c['role'] = new_role
        if candidates: all_stats.append({'comp': comp, 'cohort': cohort, 'candidates': list(candidates.values())})


md = []
md.append("# 🌟 五大公司招考录取全景总览表 (含985/211标识)\n")
md.append("> 结合全流程数据生成。被淘汰的 985/211 及海外名校出身的候选人已置顶显示，以便直观对比岗位的学历筛选尺度。\n\n")
md.append("---\n\n")

def agg_field(lst, f):
    vals = [x[f] for x in lst if x[f] and x[f] != '无数据' and x[f] != '未知岗位']
    return collections.Counter(vals)

def format_school_list(lst):
    sch_counts = agg_field(lst, 'school')
    if not sch_counts: return "无人/空缺"
    
    sch_items = []
    for k, v in sch_counts.items():
        score, badge = detect_tier(k)
        sch_items.append({'name': k, 'count': v, 'score': score, 'badge': badge})
        
    sch_items.sort(key=lambda x: (-x['score'], -x['count'], x['name']))
    return "，".join([f"{x['badge']}{x['name']}(✖ {x['count']}人)".strip() for x in sch_items[:10]])

def format_simple_list(counts):
    if not counts: return "无"
    return "，".join([f"{k} ✖ {v}人" for k,v in sorted(counts.items(), key=lambda x: -x[1])[:5]])

def create_macro_view(comp, cohort, cands):
    hired = [c for c in cands if c['max_rank'] == 4]
    not_hired = [c for c in cands if c['max_rank'] < 4]
    md.append(f"## 🏢 公司：{comp} [{cohort}]\n")
    md.append(f"### 1. 【宏观概况】录用漏斗 (总参与人数: {len(cands)} 人)")
    
    h_sex = format_simple_list(agg_field(hired, 'sex'))
    h_deg = format_simple_list(agg_field(hired, 'degree'))
    h_sch = format_school_list(hired)
    
    n_sex = format_simple_list(agg_field(not_hired, 'sex'))
    n_deg = format_simple_list(agg_field(not_hired, 'degree'))
    n_sch = format_school_list(not_hired)
    
    md.append("| 对比维度 | ✅ 录用人员画像 | ❌ 淘汰人员画像 |")
    md.append("|---|---|---|")
    md.append(f"| **人数统计** | **录用人数**: {len(hired)} 人 | **淘汰人数**: {len(not_hired)} 人 |")
    md.append(f"| **性别配比** | {h_sex} | {n_sex} |")
    md.append(f"| **学历偏向** | {h_deg} | {n_deg} |")
    md.append(f"| **院校组成** | {h_sch} | {n_sch} |")
    md.append("\n")

def format_role_cell(lst):
    if not lst: return "*(空缺)*"
    sex = dict_str(agg_field(lst, 'sex'))
    deg = dict_str(agg_field(lst, 'degree'))
    sch = format_school_list(lst)
    return f"**人数**: {len(lst)} ｜ **性别**: {sex} ｜ **学历**: {deg} ｜ **院校**: {sch}"

def dict_str(counts):
    if not counts: return "无"
    return "，".join([f"{k} x{v}" for k,v in sorted(counts.items(), key=lambda x: -x[1])[:5]])

for stat in all_stats:
    comp = stat['comp']
    cohort = stat['cohort']
    cands = stat['candidates']
    
    create_macro_view(comp, cohort, cands)
    
    roles = collections.defaultdict(list)
    for c in cands: roles[c['role']].append(c)
        
    md.append(f"### 2. 【岗位拆解】阶段追踪数据")
    for r_name in sorted(roles.keys()):
        if r_name == "未知岗位" and len(roles) > 1: continue 
        role_cands = roles[r_name]
        in_writ = [c for c in role_cands if c['max_rank'] == 1]
        in_intv = [c for c in role_cands if c['max_rank'] == 2]
        in_fint = [c for c in role_cands if c['max_rank'] == 3]
        in_hire = [c for c in role_cands if c['max_rank'] == 4]
        
        md.append(f"#### 🎯 `[岗位]` {r_name} *(参与人数: {len(role_cands)}人)*")
        
        md.append("| 阶段 | 平均年龄 | 画像组成 (人数/性别/学历/院校) |")
        md.append("|---|---|---|")
        
        stages = [
            ("✅ 录用", in_hire),
            ("❌ 复试淘汰", in_fint),
            ("❌ 初面淘汰", in_intv),
            ("❌ 笔试淘汰", in_writ)
        ]
        
        for stage_title, lst in stages:
            if not lst and stage_title != "✅ 录用": continue
            ages = [int(x['age']) for x in lst if x['age'].isdigit()]
            avg_age = f"{sum(ages)/len(ages):.1f}岁" if ages else "未知"
            md.append(f"| **{stage_title}** | {avg_age} | {format_role_cell(lst)} |")
            
        md.append("\n---\n")

out_path = '/Users/wuwenle/Desktop/考研/24年/五大公司2024-2025年度全链路招考录取全景总览表.md'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write("\n".join(md))

print(f"Finished. Check out: {out_path}")
