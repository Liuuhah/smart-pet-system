"""
测试 AI 咨询子模式与精准存档功能
"""
import sys
from pathlib import Path

# 配置导入路径
project_root = Path(__file__).parent / 'src'
sys.path.insert(0, str(project_root))

from ai_assistant.pet_health_advisor import PetHealthAdvisor


def test_history_display():
    """测试历史记录显示功能"""
    print("=" * 60)
    print("测试1：历史记录显示 (/list)")
    print("=" * 60)
    
    advisor = PetHealthAdvisor()
    
    # 模拟几轮对话
    advisor.client.add_to_history('user', '我的狗狗最近食欲不振')
    advisor.client.add_to_history('assistant', '建议观察一下是否有其他症状...')
    advisor.client.add_to_history('user', '它还有点拉肚子')
    advisor.client.add_to_history('assistant', '可能是肠胃问题，建议就医检查...')
    
    # 测试显示
    display = advisor.get_history_display()
    print(f"\n{display}")
    
    print("\n✅ 测试1完成\n")


def test_parse_round_numbers():
    """测试轮次表达式解析"""
    print("=" * 60)
    print("测试2：轮次表达式解析")
    print("=" * 60)
    
    advisor = PetHealthAdvisor()
    
    test_cases = [
        ("1,3,5", [1, 3, 5]),
        ("1-3", [1, 2, 3]),
        ("1,3-5,8", [1, 3, 4, 5, 8]),
        ("5-3", [3, 4, 5]),  # 自动交换
        ("abc", []),  # 无效输入
    ]
    
    for expression, expected in test_cases:
        result = advisor._parse_round_numbers(expression)
        status = "✅" if result == expected else "❌"
        print(f"{status} 表达式 '{expression}' -> {result} (期望: {expected})")
    
    print("\n✅ 测试2完成\n")


def test_build_temp_context():
    """测试临时上下文构建"""
    print("=" * 60)
    print("测试3：临时上下文构建")
    print("=" * 60)
    
    advisor = PetHealthAdvisor()
    
    # 模拟 5 轮对话
    for i in range(1, 6):
        advisor.client.add_to_history('user', f'第{i}轮用户问题')
        advisor.client.add_to_history('assistant', f'第{i}轮AI回复')
    
    # 测试提取第 1、3、5 轮
    temp_messages, warnings = advisor._build_temp_context([1, 3, 5])
    print(f"提取轮次: [1, 3, 5]")
    print(f"消息数量: {len(temp_messages)}")
    print(f"警告信息: {warnings if warnings else '无'}")
    
    for i, msg in enumerate(temp_messages):
        role = msg.get('role')
        content = msg.get('content', '')[:30]
        print(f"  [{i}] {role}: {content}...")
    
    # 测试超出范围
    print("\n测试超出范围:")
    temp_messages, warnings = advisor._build_temp_context([1, 10])
    print(f"提取轮次: [1, 10]")
    print(f"警告信息: {warnings}")
    
    print("\n✅ 测试3完成\n")


def test_extract_summary_by_rounds():
    """测试精准提取摘要（需要 LLM 支持）"""
    print("=" * 60)
    print("测试4：精准提取摘要 (/archive)")
    print("=" * 60)
    
    advisor = PetHealthAdvisor()
    
    # 模拟 3 轮对话
    advisor.client.add_to_history('user', '我的猫咪呕吐了')
    advisor.client.add_to_history('assistant', '建议观察呕吐物的颜色和频率...')
    advisor.client.add_to_history('user', '是黄色的液体')
    advisor.client.add_to_history('assistant', '可能是胆汁，建议禁食12小时...')
    advisor.client.add_to_history('user', '好的，谢谢')
    advisor.client.add_to_history('assistant', '不客气，如有恶化请及时就医')
    
    # 测试精准提取第 1、2 轮
    print("\n尝试提取第 1、2 轮对话...")
    result = advisor.extract_summary_by_rounds("1,2")
    print(f"结果: {result}")
    
    print("\n✅ 测试4完成（注意：实际提取需要 LLM 响应）\n")


if __name__ == "__main__":
    try:
        test_history_display()
        test_parse_round_numbers()
        test_build_temp_context()
        test_extract_summary_by_rounds()
        
        print("\n" + "=" * 60)
        print("  所有测试完成！✅")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
