#!/usr/bin/env python3
"""自动统计 checklist.md 中的检查项进度"""

import re
from pathlib import Path


def count_checklist_items(content: str) -> dict:
    """统计检查清单中的项目数"""
    # 匹配模块标题
    module_pattern = r"##\s+\d+\.\s+(.+?)\n"
    modules = re.findall(module_pattern, content)

    stats = []
    total_checked = 0
    total_unchecked = 0

    # 按模块分割内容
    sections = re.split(r"##\s+\d+\.\s+", content)[1:]

    for i, section in enumerate(sections):
        module_name = modules[i] if i < len(modules) else f"模块{i+1}"

        checked = len(re.findall(r"(?im)^\s*- \[x\]", section))
        unchecked = len(re.findall(r"(?m)^\s*- \[ \]", section))
        total = checked + unchecked

        if total > 0:
            percentage = round(checked / total * 100, 1)
            stats.append(
                {
                    "name": module_name,
                    "total": total,
                    "checked": checked,
                    "unchecked": unchecked,
                    "percentage": percentage,
                }
            )
            total_checked += checked
            total_unchecked += unchecked

    return {
        "modules": stats,
        "total_checked": total_checked,
        "total_unchecked": total_unchecked,
        "total": total_checked + total_unchecked,
        "overall_percentage": (
            round(total_checked / (total_checked + total_unchecked) * 100, 1)
            if (total_checked + total_unchecked) > 0
            else 0
        ),
    }


def print_stats(stats: dict):
    """打印统计结果"""
    print("\n" + "=" * 80)
    print("检查清单进度统计".center(80))
    print("=" * 80)
    print(f"\n{'模块':<30} {'总项':>8} {'通过':>8} {'未通过':>8} {'通过率':>10}")
    print("-" * 80)

    for module in stats["modules"]:
        print(
            f"{module['name']:<30} {module['total']:>8} {module['checked']:>8} {module['unchecked']:>8} {module['percentage']:>9}%"
        )

    print("-" * 80)
    print(
        f"{'总计':<30} {stats['total']:>8} {stats['total_checked']:>8} {stats['total_unchecked']:>8} {stats['overall_percentage']:>9}%"
    )
    print("=" * 80)

    if stats["overall_percentage"] == 100:
        print("\n🎉 所有检查项已通过！")
    elif stats["overall_percentage"] >= 80:
        print(f"\n✅ 进度良好，还剩 {stats['total_unchecked']} 项待完成")
    else:
        print(f"\n⚠️  进度较慢，还有 {stats['total_unchecked']} 项待完成")


if __name__ == "__main__":
    checklist_path = Path("docs/checklist.md")
    if not checklist_path.exists():
        # 尝试相对于脚本位置查找
        checklist_path = Path(__file__).parent.parent / "docs/checklist.md"

    if not checklist_path.exists():
        print(f"错误: 找不到文件 {checklist_path}")
        exit(1)

    content = checklist_path.read_text(encoding="utf-8")
    stats = count_checklist_items(content)
    print_stats(stats)
