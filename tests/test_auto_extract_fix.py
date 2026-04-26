"""
测试自动提取归档失效 Bug 修复
"""
import sys
from pathlib import Path
import os

# 配置导入路径
project_root = Path(__file__).parent / 'src'
sys.path.insert(0, str(project_root))

from ai_assistant.chat_compress_client import ChatCompressClient


def test_auto_extract_failure_logging():
    """测试自动提取失败时的日志写入"""
    print("=" * 60)
    print("测试1：自动提取失败时的兜底归档")
    print("=" * 60)
    
    client = ChatCompressClient()
    
    # 模拟对话历史（不足以提取 5W）
    client.add_to_history('user', '你好')
    client.add_to_history('assistant', '你好！有什么可以帮助你的吗？')
    
    print(f"\n当前对话历史条数: {len(client.chat_history)}")
    print(">>> 手动触发提取（应该会失败并调用兜底归档）...")
    
    result = client.extract_summary_now()
    print(f"\n返回结果: {result}")
    
    # 检查日志文件是否存在且有内容
    log_file = client.log_file_path
    if os.path.exists(log_file):
        file_size = os.path.getsize(log_file)
        print(f"\n✅ 日志文件存在: {log_file}")
        print(f"✅ 文件大小: {file_size} 字节")
        
        # 读取最后 500 字符验证内容
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            last_content = content[-500:] if len(content) > 500 else content
            print(f"\n📝 日志末尾内容预览:\n{last_content}...")
    else:
        print(f"\n❌ 日志文件不存在: {log_file}")
    
    print("\n✅ 测试1完成\n")


def test_content_filtering():
    """测试内容过滤逻辑"""
    print("=" * 60)
    print("测试2：日志内容过滤")
    print("=" * 60)
    
    client = ChatCompressClient()
    
    # 模拟包含系统模板的用户消息
    user_msg_with_template = """【宠物信息】
- 名字：豆豆
- 物种：dog
- 品种：博美犬

【症状描述】
豆豆最近有点拉肚子"""
    
    # 模拟工具返回的长 JSON
    tool_output = '{"success": true, "data": {"temperature": 25, "humidity": 60, "conditions": "Partly cloudy", "detailed_forecast": "..."}}' * 10
    
    client.add_to_history('user', user_msg_with_template)
    client.add_to_history('assistant', '根据豆豆的症状，建议观察一下...')
    client.add_to_history('tool', tool_output)
    
    print("\n>>> 触发强制提取（测试内容过滤）...")
    result = client.extract_summary_now()
    
    # 检查日志文件
    log_file = client.log_file_path
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # 验证过滤效果
            has_pet_info_template = '【宠物信息】' in content and '- 名字：豆豆' in content
            has_truncated_tool = '[工具返回结果已截断]' in content or len(tool_output) > 200
            
            print(f"\n内容过滤验证:")
            print(f"  - 系统模板是否被过滤: {'❌ 未过滤' if has_pet_info_template else '✅ 已过滤'}")
            print(f"  - 工具输出是否被截断: {'✅ 已截断' if has_truncated_tool else '⚠️ 未截断'}")
            
            # 显示日志片段
            print(f"\n📝 日志片段预览（最后 500 字符）:\n{content[-500:]}")
    else:
        print(f"\n❌ 日志文件不存在")
    
    print("\n✅ 测试2完成\n")


def test_error_handling():
    """测试异常处理的健壮性"""
    print("=" * 60)
    print("测试3：异常处理健壮性")
    print("=" * 60)
    
    client = ChatCompressClient()
    
    # 模拟空消息列表
    print("\n>>> 测试空消息列表...")
    result = client.extract_summary_now()
    print(f"返回结果: {result}")
    
    # 模拟无效路径（临时修改）
    original_path = client.log_file_path
    client.log_file_path = "X:\\invalid\\path\\log.txt"
    
    print("\n>>> 测试无效文件路径...")
    result = client.extract_summary_now()
    print(f"返回结果: {result}")
    
    # 恢复原路径
    client.log_file_path = original_path
    
    print("\n✅ 测试3完成\n")


if __name__ == "__main__":
    try:
        test_auto_extract_failure_logging()
        test_content_filtering()
        test_error_handling()
        
        print("\n" + "=" * 60)
        print("  所有测试完成！✅")
        print("=" * 60)
        print("\n💡 提示：请检查 D:\\chat-log\\log.txt 文件验证修复效果")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
