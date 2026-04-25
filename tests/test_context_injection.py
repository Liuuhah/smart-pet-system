"""
测试 AI 管家上下文注入优化方案
"""
import sys
from pathlib import Path

# 配置导入路径
project_root = Path(__file__).parent / 'src'
sys.path.insert(0, str(project_root))

from ai_assistant.pet_health_advisor import PetHealthAdvisor


def test_system_prompt_injection():
    """测试 System Prompt 注入功能"""
    print("=" * 60)
    print("测试1：System Prompt 注入")
    print("=" * 60)
    
    advisor = PetHealthAdvisor()
    
    # 模拟宠物数据
    pet_data = {
        "name": "豆豆",
        "species": "dog",
        "breed": "博美犬",
        "age": 3,
        "weight": 2.5,
        "gender": "male",
        "recent_records": [
            {"date": "2026-04-20", "type": "vaccine", "desc": "接种狂犬疫苗"}
        ]
    }
    
    # 注入上下文
    print("\n>>> 正在注入宠物上下文...")
    advisor.set_current_pet_context(pet_data)
    
    # 检查 system prompt 是否更新
    print(f"\n当前 System Prompt 长度: {len(advisor.client.system_prompt)} 字符")
    print(f"包含宠物名字: {'豆豆' in advisor.client.system_prompt}")
    print(f"包含品种信息: {'博美犬' in advisor.client.system_prompt}")
    print(f"包含年龄信息: {'3 岁' in advisor.client.system_prompt}")
    
    print("\n✅ 测试1完成\n")


def test_system_prompt_reset():
    """测试 System Prompt 重置功能"""
    print("=" * 60)
    print("测试2：System Prompt 重置")
    print("=" * 60)
    
    advisor = PetHealthAdvisor()
    
    # 先注入上下文
    pet_data = {
        "name": "豆豆",
        "species": "dog",
        "breed": "博美犬",
        "age": 3,
        "weight": 2.5,
        "gender": "male",
        "recent_records": []
    }
    
    print("\n>>> 注入宠物上下文...")
    advisor.set_current_pet_context(pet_data)
    print(f"注入后 System Prompt 长度: {len(advisor.client.system_prompt)} 字符")
    
    # 重置上下文
    print("\n>>> 重置上下文...")
    advisor.reset_context()
    print(f"重置后 System Prompt 长度: {len(advisor.client.system_prompt)} 字符")
    print(f"不再包含宠物名字: {'豆豆' not in advisor.client.system_prompt}")
    print(f"聊天历史已清空: {len(advisor.client.chat_history) == 0}")
    
    print("\n✅ 测试2完成\n")


def test_multiple_pets_switching():
    """测试多宠物切换场景"""
    print("=" * 60)
    print("测试3：多宠物切换（防止信息串台）")
    print("=" * 60)
    
    advisor = PetHealthAdvisor()
    
    # 第一只宠物：豆豆（博美犬）
    pet1 = {
        "name": "豆豆",
        "species": "dog",
        "breed": "博美犬",
        "age": 3,
        "weight": 2.5,
        "gender": "male",
        "recent_records": []
    }
    
    print("\n>>> 切换到宠物1：豆豆（博美犬）")
    advisor.set_current_pet_context(pet1)
    print(f"System Prompt 包含 '豆豆': {'豆豆' in advisor.client.system_prompt}")
    print(f"System Prompt 包含 '博美犬': {'博美犬' in advisor.client.system_prompt}")
    
    # 重置
    advisor.reset_context()
    
    # 第二只宠物：小花（布偶猫）
    pet2 = {
        "name": "小花",
        "species": "cat",
        "breed": "布偶猫",
        "age": 2,
        "weight": 4.5,
        "gender": "female",
        "recent_records": []
    }
    
    print("\n>>> 切换到宠物2：小花（布偶猫）")
    advisor.set_current_pet_context(pet2)
    print(f"System Prompt 包含 '小花': {'小花' in advisor.client.system_prompt}")
    print(f"System Prompt 包含 '布偶猫': {'布偶猫' in advisor.client.system_prompt}")
    print(f"System Prompt 不再包含 '豆豆': {'豆豆' not in advisor.client.system_prompt}")
    print(f"System Prompt 不再包含 '博美犬': {'博美犬' not in advisor.client.system_prompt}")
    
    # 清理
    advisor.reset_context()
    
    print("\n✅ 测试3完成\n")


if __name__ == "__main__":
    try:
        test_system_prompt_injection()
        test_system_prompt_reset()
        test_multiple_pets_switching()
        
        print("\n" + "=" * 60)
        print("  所有测试完成！✅")
        print("=" * 60)
        print("\n💡 提示：现在可以运行 python main.py 体验完整的上下文注入功能")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
