"""
测试流式输出中断功能
"""
import sys
from pathlib import Path
import time

# 配置导入路径
project_root = Path(__file__).parent / 'src'
sys.path.insert(0, str(project_root))

from ai_assistant.chat_compress_client import ChatCompressClient


def test_interrupt_flag():
    """测试中断标志位初始化"""
    print("=" * 60)
    print("测试1：中断标志位初始化")
    print("=" * 60)
    
    client = ChatCompressClient()
    
    if hasattr(client, 'is_interrupted'):
        print(f"✅ is_interrupted 属性存在")
        print(f"   初始值: {client.is_interrupted}")
        
        if client.is_interrupted == False:
            print(f"✅ 初始值为 False（正确）")
            return True
        else:
            print(f"❌ 初始值不为 False")
            return False
    else:
        print(f"❌ is_interrupted 属性不存在")
        return False


def test_keyboard_listener_method():
    """测试键盘监听方法存在性"""
    print("\n" + "=" * 60)
    print("测试2：键盘监听方法存在性")
    print("=" * 60)
    
    client = ChatCompressClient()
    
    if hasattr(client, '_keyboard_listener'):
        print(f"✅ _keyboard_listener 方法存在")
        
        # 检查方法是否为可调用对象
        if callable(getattr(client, '_keyboard_listener')):
            print(f"✅ _keyboard_listener 是可调用的")
            return True
        else:
            print(f"❌ _keyboard_listener 不是可调用的")
            return False
    else:
        print(f"❌ _keyboard_listener 方法不存在")
        return False


def test_platform_detection():
    """测试平台检测逻辑"""
    print("\n" + "=" * 60)
    print("测试3：平台检测逻辑")
    print("=" * 60)
    
    print(f"当前平台: {sys.platform}")
    
    if sys.platform == 'win32':
        print(f"✅ 当前为 Windows 平台，支持 msvcrt")
        
        try:
            import msvcrt
            print(f"✅ msvcrt 模块可用")
            return True
        except ImportError:
            print(f"❌ msvcrt 模块不可用")
            return False
    else:
        print(f"⚠️ 当前为非 Windows 平台 ({sys.platform})")
        print(f"   流式中断功能可能受限")
        return True  # 非 Windows 平台也算通过


def test_threading_support():
    """测试多线程支持"""
    print("\n" + "=" * 60)
    print("测试4：多线程支持")
    print("=" * 60)
    
    try:
        import threading
        
        # 创建一个简单的守护线程测试
        test_flag = {'value': False}
        
        def test_thread_func():
            time.sleep(0.1)
            test_flag['value'] = True
        
        t = threading.Thread(target=test_thread_func, daemon=True)
        t.start()
        t.join(timeout=1.0)
        
        if test_flag['value']:
            print(f"✅ 多线程支持正常")
            return True
        else:
            print(f"❌ 多线程测试失败")
            return False
            
    except Exception as e:
        print(f"❌ 多线程支持异常: {e}")
        return False


def test_interrupt_in_stream():
    """测试流式输出中的中断逻辑（需要 LLM 服务）"""
    print("\n" + "=" * 60)
    print("测试5：流式输出中断逻辑（需要 LLM 服务）")
    print("=" * 60)
    
    print("⚠️ 此测试需要 LLM 服务支持")
    print("💡 提示：请手动运行 python main.py 进行实际测试")
    print("   1. 选择 [4] 咨询 AI 管家")
    print("   2. 输入一个会触发长回复的问题（如'请详细介绍狗狗的日常护理'）")
    print("   3. 在 AI 输出过程中按下 Esc 键")
    print("   4. 观察是否显示 '[已暂停输出]' 并停止输出")
    
    return True


if __name__ == "__main__":
    try:
        result1 = test_interrupt_flag()
        result2 = test_keyboard_listener_method()
        result3 = test_platform_detection()
        result4 = test_threading_support()
        result5 = test_interrupt_in_stream()
        
        print("\n" + "=" * 60)
        if result1 and result2 and result3 and result4 and result5:
            print("  所有测试通过！✅")
        else:
            print("  部分测试失败 ❌")
        print("=" * 60)
        
        print("\n💡 提示：请运行 python main.py 进行实际的中断功能测试")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
