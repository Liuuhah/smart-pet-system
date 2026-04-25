"""
测试强制提取功能的兜底归档策略
"""
import sys
from pathlib import Path

# 配置导入路径
project_root = Path(__file__).parent / 'src'
sys.path.insert(0, str(project_root))

from ai_assistant.chat_compress_client import ChatCompressClient

def test_force_extraction_with_short_dialogue():
    """测试短对话的强制提取（应触发兜底归档）"""
    print("=" * 60)
    print("测试1：短对话强制提取（信息不足场景）")
    print("=" * 60)
    
    client = ChatCompressClient()
    
    # 模拟一轮简短对话
    client.add_to_history('user', '你好')
    client.add_to_history('assistant', '你好！有什么可以帮助你的吗？')
    
    print(f"\n当前对话历史条数: {len(client.chat_history)}")
    print("\n>>> 执行强制提取...")
    
    result = client.extract_summary_now()
    
    print(f"\n返回结果: {result}")
    print("\n✅ 测试完成！请检查 D:\\chat-log\\log.txt 文件是否生成了简短问诊记录。")


def test_force_extraction_with_no_dialogue():
    """测试无对话的强制提取"""
    print("\n" + "=" * 60)
    print("测试2：无对话强制提取（空历史场景）")
    print("=" * 60)
    
    client = ChatCompressClient()
    
    print(f"\n当前对话历史条数: {len(client.chat_history)}")
    print("\n>>> 执行强制提取...")
    
    result = client.extract_summary_now()
    
    print(f"\n返回结果: {result}")
    print("\n✅ 测试完成！请检查日志文件是否有相应记录。")


def test_force_extraction_with_normal_dialogue():
    """测试正常对话的强制提取（应成功提取 5W）"""
    print("\n" + "=" * 60)
    print("测试3：正常对话强制提取（应成功提取 5W）")
    print("=" * 60)
    
    client = ChatCompressClient()
    
    # 模拟一段包含宠物信息的对话
    client.add_to_history('user', '我家狗狗小白最近总是呕吐，它是一只2岁的金毛犬，体重25公斤。')
    client.add_to_history('assistant', '根据您的描述，小白可能是肠胃不适。建议先禁食12小时观察，如果症状持续请立即就医。可能的原因包括食物不耐受、肠胃炎等。')
    
    print(f"\n当前对话历史条数: {len(client.chat_history)}")
    print("\n>>> 执行强制提取...")
    
    result = client.extract_summary_now()
    
    print(f"\n返回结果: {result}")
    print("\n✅ 测试完成！请检查日志文件是否生成了 5W 提取结果。")


if __name__ == "__main__":
    try:
        test_force_extraction_with_short_dialogue()
        test_force_extraction_with_no_dialogue()
        test_force_extraction_with_normal_dialogue()
        
        print("\n" + "=" * 60)
        print("所有测试完成！✅")
        print("=" * 60)
        print("\n📝 请检查以下文件确认归档是否成功：")
        print("   - D:\\chat-log\\log.txt")
        print("\n💡 提示：")
        print("   - 测试1 应生成'简短问诊记录（兜底归档）'")
        print("   - 测试2 应生成'暂无对话记录'的提示")
        print("   - 测试3 应生成标准的 5W 提取结果")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
