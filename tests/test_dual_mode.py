"""
测试 AI 管家双模态交互与人格化设计
"""
import sys
from pathlib import Path

# 配置导入路径
project_root = Path(__file__).parent / 'src'
sys.path.insert(0, str(project_root))

from ai_assistant.pet_health_advisor import PetHealthAdvisor


def test_intent_detection():
    """测试意图识别功能"""
    print("=" * 60)
    print("测试1：意图识别 (_detect_intent)")
    print("=" * 60)
    
    advisor = PetHealthAdvisor()
    
    # 闲聊测试用例
    chat_inputs = [
        "你好",
        "在吗",
        "今天天气不错",
        "豆豆今天看起来很开心",
        "早上好"
    ]
    
    # 问诊测试用例
    consult_inputs = [
        "豆豆最近有点拉肚子",
        "它不吃东西了",
        "呕吐怎么办",
        "发烧了",
        "咳嗽厉害",
        "精神状态不好"
    ]
    
    print("\n>>> 闲聊模式测试:")
    for user_input in chat_inputs:
        intent = advisor._detect_intent(user_input)
        status = "✅" if intent == "chat" else "❌"
        print(f"{status} '{user_input}' -> {intent}")
    
    print("\n>>> 专业问诊模式测试:")
    for user_input in consult_inputs:
        intent = advisor._detect_intent(user_input)
        status = "✅" if intent == "consult" else "❌"
        print(f"{status} '{user_input}' -> {intent}")
    
    print("\n✅ 测试1完成\n")


def test_temperature_setting():
    """测试 temperature 参数传递"""
    print("=" * 60)
    print("测试2：Temperature 参数传递")
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
        "recent_records": []
    }
    
    # 注入上下文
    advisor.set_current_pet_context(pet_data)
    
    print("\n>>> 检查 send_request_stream() 方法签名...")
    import inspect
    sig = inspect.signature(advisor.client.send_request_stream)
    params = sig.parameters
    
    if 'temperature' in params:
        print("✅ send_request_stream() 包含 temperature 参数")
        print(f"   默认值: {params['temperature'].default}")
    else:
        print("❌ send_request_stream() 缺少 temperature 参数")
    
    print("\n✅ 测试2完成\n")


def test_consult_method():
    """测试 consult() 方法（需要 LLM 支持）"""
    print("=" * 60)
    print("测试3：双模态咨询接口 (consult)")
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
        "recent_records": []
    }
    
    # 注入上下文
    advisor.set_current_pet_context(pet_data)
    
    print("\n>>> 闲聊模式测试（需要 LLM 响应）:")
    print("输入: '你好呀'")
    print("预期: 轻松、亲切的简短回应，无医疗格式")
    try:
        response = advisor.consult("你好呀")
        print(f"回复长度: {len(response)} 字符")
        print(f"回复预览: {response[:100]}...")
        print("✅ 闲聊模式调用成功")
    except Exception as e:
        print(f"⚠️ 需要 LLM 服务: {e}")
    
    print("\n>>> 专业问诊模式测试（需要 LLM 响应）:")
    print("输入: '豆豆最近有点拉肚子'")
    print("预期: 结构化诊断，包含紧急程度、护理建议等")
    try:
        response = advisor.consult("豆豆最近有点拉肚子")
        print(f"回复长度: {len(response)} 字符")
        print(f"回复预览: {response[:100]}...")
        print("✅ 专业问诊模式调用成功")
    except Exception as e:
        print(f"⚠️ 需要 LLM 服务: {e}")
    
    print("\n✅ 测试3完成（注意：实际对话需要 LLM 响应）\n")


if __name__ == "__main__":
    try:
        test_intent_detection()
        test_temperature_setting()
        test_consult_method()
        
        print("\n" + "=" * 60)
        print("  所有测试完成！✅")
        print("=" * 60)
        print("\n💡 提示：现在可以运行 python main.py 体验双模态交互功能")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
