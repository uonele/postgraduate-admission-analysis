#!/usr/bin/env python3
"""
自动为全景总览表中的所有大学名称添加 985/211/海外名校 标签。
"""
import re
import os

# ==================== 985 院校列表 ====================
UNIVERSITIES_985 = {
    "北京大学", "清华大学", "中国人民大学", "北京师范大学",
    "北京航空航天大学", "北京理工大学", "中国农业大学", "中央民族大学",
    "复旦大学", "上海交通大学", "同济大学", "华东师范大学",
    "南京大学", "东南大学",
    "浙江大学",
    "中国科学技术大学",
    "厦门大学",
    "山东大学", "中国海洋大学",
    "武汉大学", "华中科技大学",
    "中南大学", "湖南大学", "国防科技大学",
    "中山大学", "华南理工大学",
    "四川大学", "电子科技大学",
    "重庆大学",
    "西安交通大学", "西北工业大学", "西北农林科技大学",
    "吉林大学",
    "哈尔滨工业大学",
    "大连理工大学",
    "东北大学",
    "南开大学", "天津大学",
    "兰州大学",
}

# ==================== 211 院校列表 (不含985) ====================
UNIVERSITIES_211_ONLY = {
    # 北京
    "北京交通大学", "北京工业大学", "北京科技大学", "北京化工大学",
    "北京邮电大学", "北京林业大学", "北京中医药大学", "北京外国语大学",
    "中国传媒大学", "中央财经大学", "对外经济贸易大学", "中国政法大学",
    "华北电力大学", "中国地质大学", "中国矿业大学",
    "中国地质大学（武汉）", "中国地质大学（北京）",
    "中国矿业大学（徐州）", "中国矿业大学（北京）",
    "中国石油大学", "中国石油大学（华东）", "中国石油大学（北京）",
    # 天津
    "天津医科大学",
    # 河北
    "河北工业大学",
    # 山西
    "太原理工大学",
    # 内蒙古
    "内蒙古大学",
    # 辽宁
    "辽宁大学", "大连海事大学",
    # 吉林
    "延边大学", "东北师范大学",
    # 黑龙江
    "哈尔滨工程大学", "东北农业大学", "东北林业大学",
    # 上海
    "华东理工大学", "东华大学", "上海财经大学", "上海外国语大学", "上海大学",
    # 江苏
    "苏州大学", "南京航空航天大学", "南京理工大学",
    "河海大学", "江南大学", "南京农业大学", "中国药科大学", "南京师范大学",
    # 安徽
    "安徽大学", "合肥工业大学",
    # 福建
    "福州大学",
    # 江西
    "南昌大学",
    # 河南
    "郑州大学", "河南大学",
    # 湖北
    "武汉理工大学", "华中农业大学", "华中师范大学", "中南财经政法大学",
    # 湖南
    "湖南师范大学",
    # 广东
    "暨南大学", "华南师范大学",
    # 广西
    "广西大学",
    # 海南
    "海南大学",
    # 四川
    "西南交通大学", "西南财经大学", "四川农业大学",
    # 贵州
    "贵州大学",
    # 云南
    "云南大学",
    # 西藏
    "西藏大学",
    # 陕西
    "西安电子科技大学", "长安大学", "西北大学", "陕西师范大学",
    # 甘肃 (兰州大学已在985)
    # 青海
    "青海大学",
    # 宁夏
    "宁夏大学",
    # 新疆
    "新疆大学", "石河子大学",
}

# ==================== 海外名校列表(QS前100/知名校) ====================
UNIVERSITIES_OVERSEAS = {
    "新加坡南洋理工大学", "新加坡国立大学",
    "香港理工大学", "香港大学", "香港中文大学", "香港科技大学", "香港浸会大学",
    "伦敦大学学院", "伦敦大学学院（UCL）",
    "伦敦玛丽女王大学",
    "英国伯明翰大学", "英国利物浦大学",
    "阿尔伯塔大学",
    "澳大利亚国立大学",
    "新南威尔士大学",
    "莫纳什大学",
    "匹兹堡大学",
    "诺丁汉大学",
    "马来西亚理科大学", "马来西亚城市大学",
}


def get_tag(uni_name: str) -> str:
    """返回大学的标签前缀"""
    # 精确匹配
    if uni_name in UNIVERSITIES_985:
        return "👑**[985]**"
    if uni_name in UNIVERSITIES_211_ONLY:
        return "✨**[211]**"
    if uni_name in UNIVERSITIES_OVERSEAS:
        return "🌍**[海外名校]**"

    # 模糊匹配 (处理带括号等变体)
    for u985 in UNIVERSITIES_985:
        if u985 in uni_name or uni_name in u985:
            return "👑**[985]**"
    for u211 in UNIVERSITIES_211_ONLY:
        if u211 in uni_name or uni_name in u211:
            return "✨**[211]**"
    for uov in UNIVERSITIES_OVERSEAS:
        if uov in uni_name or uni_name in uov:
            return "🌍**[海外名校]**"

    return ""


def process_line(line: str) -> str:
    """处理一行文本，为大学名称添加标签"""

    # 已经有标签的不重复添加
    # 匹配 "大学名(数字)" 或 "大学名-人名" 或 "大学名，" 等格式
    # 常见模式: "XXX大学(1)" "XXX学院(1)" "XXX大学-张三(男)"

    # 模式1: "院校名(✖ N人)" 或 "院校名(N人)" 或 "院校名(N)"
    def replace_uni_with_count(match):
        prefix = match.group(1)  # 前面可能的空格等
        uni = match.group(2)     # 大学名
        suffix = match.group(3)  # (✖ N人) 等
        # 检查前面是否已有标签
        check_before = line[:match.start()]
        if '**]**' in check_before[-20:] if len(check_before) >= 20 else check_before:
            return match.group(0)  # 已有标签，跳过
        tag = get_tag(uni)
        if tag:
            return f"{prefix}{tag}{uni}{suffix}"
        return match.group(0)

    # 模式2: "院校名-人名(性别)" 用于录用名单
    def replace_uni_with_name(match):
        prefix = match.group(1)
        uni = match.group(2)
        suffix = match.group(3)
        tag = get_tag(uni)
        if tag:
            return f"{prefix}{tag}{uni}{suffix}"
        return match.group(0)

    # 跳过已经完全标记的行
    if line.count('👑') + line.count('✨') + line.count('🌍') > 3:
        return line  # 已有大量标签，可能不需要再处理

    # 处理 "大学名(N)" 格式, 但避免重复标签
    # 先处理含有"(✖"的
    result = re.sub(
        r'(，|｜\s*|：\s*|^|\| )([^\s,，｜👑✨🌍\*\[（]+(?:大学|学院|研究所|研究院)(?:（[^）]+）)?)\s*(\(✖?\s*\d+人?\))',
        replace_uni_with_count, line
    )

    # 处理 "大学名-人名" 格式
    result = re.sub(
        r'(，|^|\| )([^\s,，｜👑✨🌍\*\[（]+(?:大学|学院|研究所|研究院)(?:（[^）]+）)?)([-—][^\s,，]+)',
        replace_uni_with_name, result
    )

    return result


def main():
    filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "五大公司2024-2025年度全链路招考录取全景总览表.md")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    new_lines = []
    changed = 0

    for line in lines:
        new_line = process_line(line)
        if new_line != line:
            changed += 1
            print(f"  🏷️  修改: {line[:80]}...")
        new_lines.append(new_line)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))

    print(f"\n✅ 处理完成，共修改 {changed} 行")

    # 统计所有出现的大学
    all_unis = set()
    for line in new_lines:
        # 匹配大学/学院名
        matches = re.findall(r'([^\s,，｜\*\[\]（）()👑✨🌍]+(?:大学|学院|研究所|研究院)(?:（[^）]+）)?)', line)
        for m in matches:
            clean = m.strip('，,｜ ')
            if len(clean) > 2:
                all_unis.add(clean)

    print(f"\n📊 文档中出现的所有院校 ({len(all_unis)} 所):")
    tagged = 0
    untagged = 0
    for uni in sorted(all_unis):
        tag = get_tag(uni)
        if tag:
            print(f"  {tag} {uni}")
            tagged += 1
        else:
            print(f"  ⬜ {uni}")
            untagged += 1
    print(f"\n已标注: {tagged} 所, 未标注(双非): {untagged} 所")


if __name__ == '__main__':
    main()
