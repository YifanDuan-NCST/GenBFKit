#!/usr/bin/env python3
"""
GenBFKit 时间尺度对齐模板 - 快速启动脚本
"""

import os
import sys
import subprocess

def print_menu():
    """打印菜单"""
    print("\n" + "=" * 60)
    print("GenBFKit 时间尺度对齐模板 (TSAT)")
    print("=" * 60)
    print("\n请选择要执行的操作:")
    print("  1. 运行核心演示 (time_scale_alignment_template.py)")
    print("  2. 运行所有示例 (usage_examples.py)")
    print("  3. 部署到数据库 (deploy_tsat.py)")
    print("  4. 查看快速参考 (quick_reference.py 中的示例)")
    print("  5. 查看文档")
    print("  0. 退出")

def run_demo():
    """运行核心演示"""
    print("\n运行核心演示...")
    subprocess.run([sys.executable, "time_scale_alignment_template.py"])

def run_examples():
    """运行所有示例"""
    print("\n运行所有示例...")
    subprocess.run([sys.executable, "usage_examples.py"])

def deploy():
    """部署到数据库"""
    print("\n部署到数据库...")
    print("提示: 需要先配置 config_time_alignment.json 中的数据库连接信息")
    response = input("是否继续? (y/n): ").strip().lower()
    if response == 'y':
        subprocess.run([sys.executable, "deploy_tsat.py"])
    else:
        print("已取消部署")

def show_docs():
    """显示文档列表"""
    print("\n可用文档:")
    docs = [
        ("README_TSAT.md", "完整技术文档"),
        ("SUMMARY_TSAT.md", "技术方案总结"),
        ("DELIVERY_CHECKLIST.md", "交付清单"),
        ("PROJECT_SUMMARY.md", "项目总结"),
        ("FIX_Usage_Examples.md", "使用样例修复说明"),
        ("REMOVE_Quality_Control.md", "质量控制删除说明"),
        ("README.md", "本目录说明")
    ]
    for i, (file, desc) in enumerate(docs, 1):
        print(f"  {i}. {file} - {desc}")

    choice = input("\n请输入文档编号查看内容 (或按 Enter 返回): ").strip()
    if choice and choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(docs):
            doc_file = docs[idx][0]
            print(f"\n--- {doc_file} ---")
            try:
                with open(doc_file, 'r', encoding='utf-8') as f:
                    print(f.read()[:1000])  # 只显示前1000字符
                print("\n(内容已截断，完整内容请查看文件)")
            except Exception as e:
                print(f"读取文件失败: {e}")

def show_quick_reference():
    """显示快速参考"""
    print("\n快速参考 - 常用代码片段:")
    print("\n1. 基础使用:")
    print("""
from time_scale_alignment_template import (
    TimeScaleAlignmentTemplate,
    TimeAlignmentConfig,
    InterpolationMethod
)

config = TimeAlignmentConfig(
    target_frequency="1S",
    default_interpolation=InterpolationMethod.LINEAR
)

tsat = TimeScaleAlignmentTemplate(config)
result = tsat.align_time_series(timestamps, values)
""")

    print("\n2. PostgreSQL 集成:")
    print("""
from postgresql_alignment_manager import PostgreSQLAlignmentManager

with PostgreSQLAlignmentManager(db_config, alignment_config) as manager:
    results = manager.align_table_data(table_name)
""")

    print("\n3. 查看更多示例:")
    print("   - 运行: python quick_reference.py")
    print("   - 查看: usage_examples.py")

def main():
    """主函数"""
    while True:
        print_menu()
        choice = input("\n请输入选项 (0-5): ").strip()

        if choice == '0':
            print("\n感谢使用 GenBFKit 时间尺度对齐模板!")
            break
        elif choice == '1':
            run_demo()
        elif choice == '2':
            run_examples()
        elif choice == '3':
            deploy()
        elif choice == '4':
            show_quick_reference()
        elif choice == '5':
            show_docs()
        else:
            print("\n无效选项，请重新选择")

        input("\n按 Enter 继续...")

if __name__ == "__main__":
    main()
