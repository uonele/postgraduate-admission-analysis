#!/usr/bin/env python3
"""
从已拉取的官网页面中提取招聘名单数据，清洗后保存到 raw_data 目录。
按公司分目录存储。
"""
import os
import re

# 已拉取的文件映射: (step_id, 公司, 文件名)
FETCHED_FILES = [
    # === 豫信电科 [2026年] ===
    (32, "豫信电科_2026", "投资类_拟复试人员名单_20260412.md"),
    (33, "豫信电科_2026", "研发类_第二批拟初试名单_20260412.md"),
    (34, "豫信电科_2026", "研发类_第二批拟笔试人员名单_20260402.md"),
    (35, "豫信电科_2026", "投资类_拟初面人员名单_20260329.md"),
    (36, "豫信电科_2026", "研发类_第一批拟录用名单_20260326.md"),
    (37, "豫信电科_2026", "投资类_拟笔试人员名单_20260324.md"),
    (38, "豫信电科_2026", "研发类_第一批拟复试名单_20260315.md"),
    (39, "豫信电科_2026", "研发类_第一批拟初试名单_20260306.md"),
    (40, "豫信电科_2026", "研发类_第一批拟笔试人员名单_20260303.md"),

    # === 豫信电子科技集团（河南）有限 [2024年] ===
    (75, "豫信河南_2024", "拟录用人员名单_20250121.md"),
    (76, "豫信河南_2024", "复试人员名单_20241115.md"),
    (77, "豫信河南_2024", "初试人员名单_20241022.md"),
    (78, "豫信河南_2024", "笔试人员名单_20241009.md"),
    (79, "豫信河南_2024", "招聘公告_20240909.md"),

    # === 河南电子口岸有限 [2025年] ===
    (80, "河南电子口岸_2025", "拟录用人员_20250805.md"),
    (81, "河南电子口岸_2025", "拟复试人员名单_20250705.md"),
    (82, "河南电子口岸_2025", "拟初面人员名单_20250623.md"),
    (83, "河南电子口岸_2025", "拟笔试人员名单_20250617.md"),
    (84, "河南电子口岸_2025", "招聘公告_20250520.md"),

    # === 河南智能医学科技有限 [2025年] ===
    (88, "河南智能医学_2025", "拟录用人员名单_20260105.md"),
    (89, "河南智能医学_2025", "拟复面人员名单_20251124.md"),
    (90, "河南智能医学_2025", "拟初面人员名单_20251013.md"),
    (91, "河南智能医学_2025", "拟笔试人员名单_20250924.md"),
    (92, "河南智能医学_2025", "招聘公告_20250812.md"),

    # === 河南信息产业投资有限 [2025年] ===
    (93, "河南信产投资_2025", "业务财务岗_拟录用人员_20250909.md"),
    (94, "河南信产投资_2025", "拟录用人员_20250728.md"),
    (95, "河南信产投资_2025", "拟复试人员名单_20250710.md"),
    (96, "河南信产投资_2025", "拟初面人员名单_20250627.md"),
    (97, "河南信产投资_2025", "拟笔试人员名单_20250618.md"),
    (98, "河南信产投资_2025", "招聘公告_20250513.md"),
]

BASE_STEPS_DIR = os.path.expanduser(
    "~/.gemini/antigravity/brain/a11a0b78-3e3b-4074-8735-52aa3d096240/.system_generated/steps"
)
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw_data")


def extract_clean_content(raw_text: str) -> str:
    """从原始抓取内容中提取招聘正文部分，去掉导航栏等噪音"""
    lines = raw_text.split('\n')

    # 找到标题行 (以 "# 豫信" 或 "# 河南" 开头的行)
    start_idx = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('# ') and ('豫信' in stripped or '河南' in stripped):
            start_idx = i
            break
        # 也匹配 "根据公司招聘工作安排" 这样的正文开头
        if '根据公司招聘工作安排' in stripped or '根据招聘工作安排' in stripped:
            start_idx = i
            break

    # 找到结尾 (公示期限 或 咨询电话 之后，或 "上一篇/下一篇" 之前)
    end_idx = len(lines)
    for i in range(start_idx, len(lines)):
        stripped = lines[i].strip()
        if stripped.startswith('[上一篇') or stripped.startswith('[下一篇'):
            end_idx = i
            break
        if stripped.startswith('[集团概况]') and i > start_idx + 10:
            end_idx = i
            break

    # 提取 Title 和 Source
    header = ""
    for line in lines[:10]:
        if line.startswith('Title:') or line.startswith('Source:'):
            header += line + '\n'

    clean_lines = [header.strip(), '', '---', '']
    clean_lines.extend(lines[start_idx:end_idx])

    return '\n'.join(clean_lines)


def main():
    saved_count = 0
    failed_count = 0

    for step_id, company_dir, filename in FETCHED_FILES:
        src_path = os.path.join(BASE_STEPS_DIR, str(step_id), "content.md")
        dst_dir = os.path.join(OUTPUT_DIR, company_dir)
        dst_path = os.path.join(dst_dir, filename)

        if not os.path.exists(src_path):
            print(f"❌ 文件不存在: step {step_id} -> {filename}")
            failed_count += 1
            continue

        os.makedirs(dst_dir, exist_ok=True)

        with open(src_path, 'r', encoding='utf-8') as f:
            raw = f.read()

        clean = extract_clean_content(raw)

        with open(dst_path, 'w', encoding='utf-8') as f:
            f.write(clean)

        print(f"✅ 已保存: {company_dir}/{filename} ({len(clean)} 字符)")
        saved_count += 1

    print(f"\n📊 总计: 成功 {saved_count} 个, 失败 {failed_count} 个")
    print(f"📁 输出目录: {OUTPUT_DIR}")


if __name__ == '__main__':
    main()
