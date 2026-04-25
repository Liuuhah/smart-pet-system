"""
智能宠物喂食管理系统 - 主程序入口

作者：刘同学
日期：2026-04-16
课程：《数据结构》项目 - Phase 1

模块职责：
- 提供菜单驱动的命令行交互界面 (CLI)
- 整合档案管理模块与 AI 健康顾问
- 处理用户输入校验与异常捕获

架构设计：
- 采用模块化导入，确保在 Windows/Linux/macOS 下路径兼容
- 实现健壮的错误处理机制，防止因非法输入或 LLM 服务不可用导致程序崩溃
"""

import sys
from pathlib import Path

# ==================== 路径配置 ====================
# 将 src 目录和项目根目录加入搜索路径，确保跨平台兼容性
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root))

from modules.pet_profile_manager import SmartPetProfileSystem
from ai_assistant.pet_health_advisor import PetHealthAdvisor


def print_header():
    """打印系统欢迎横幅"""
    print("\n" + "=" * 50)
    print("   欢迎进入智能宠物喂食管理系统 (Phase 1)")
    print("=" * 50)
    print("   [1] 注册新宠物")
    print("   [2] 查看宠物列表")
    print("   [3] 添加健康记录")
    print("   [4] 咨询 AI 管家")
    print("   [5] 手动压缩记忆 (建议在对话 10-15 轮后执行)")
    print("   [6] 提取 AI 管家对话摘要")
    print("   [0] 退出系统")
    print("-" * 50)


def register_pet_flow(system):
    """[1] 注册新宠物的交互流程
    
    工程规范说明：
    - 输入校验：对数值型输入进行 try-except 捕获，防止非数字导致崩溃。
    - 封装原则：通过 system.get_pet_count() 获取状态，严禁直接访问底层哈希表。
    - 用户体验：提供清晰的选项映射，并在成功后展示完整摘要。
    """
    print("\n>>> 正在注册新宠物...")
    try:
        # 1. 基础信息录入
        name = input("请输入宠物姓名: ").strip()
        if not name:
            print("[ERR] 姓名不能为空！")
            return

        # 2. 物种选择
        species_map = {"1": "dog", "2": "cat", "3": "other"}
        print("请选择物种: 1.狗狗  2.猫咪  3.其他")
        species_choice = input("请输入选项编号: ").strip()
        species = species_map.get(species_choice, "unknown")

        # 3. 品种与性别录入
        breed = input("请输入品种: ").strip()
        
        gender_map = {"1": "male", "2": "female"}
        gender_choice = input("请选择性别: 1.公  2.母: ").strip()
        gender = gender_map.get(gender_choice, "unknown")
        if gender == "unknown":
            print("[WARN] 未识别的性别选项，已默认设为 '未知'")
        
        # 4. 数值型输入校验（健壮性核心）
        try:
            age = float(input("请输入年龄(岁): "))
            weight = float(input("请输入体重(kg): "))
        except ValueError:
            print("[ERR] 年龄和体重必须是数字！")
            return

        # 5. 调用核心业务逻辑（遵循封装原则）
        pet_count = system.get_pet_count()
        pet_id = f"pet_{pet_count + 1:03d}"
        system.register_pet(pet_id, name, breed, age, weight, gender=gender, species=species)
        
    except Exception as e:
        print(f"[ERR] 注册过程中发生未知错误：{e}")


def list_pets_flow(system):
    """[2] 查看宠物列表的交互流程"""
    print("\n>>> 当前系统中的所有宠物：")
    pets = system.show_all_pets()
    if not pets:
        print("  暂无宠物档案，请先注册。")


def add_record_flow(system):
    """[3] 添加健康记录的交互流程"""
    print("\n>>> 正在添加健康记录...")
    
    # 1. 选择宠物
    pet_name = input("请输入宠物姓名: ").strip()
    matches = system.search_by_name(pet_name)
    if not matches:
        print(f"[ERR] 找不到名为 '{pet_name}' 的宠物。")
        return
    target_pet = matches[0]
    pet_id = target_pet.pet_id
    
    # 2. 录入记录信息
    try:
        date = input("请输入日期 (YYYY-MM-DD): ").strip()
        print("事件类型: 1.疫苗  2.体检  3.生病  4.喂养")
        type_map = {"1": "vaccine", "2": "checkup", "3": "illness", "4": "feeding"}
        type_choice = input("请选择类型编号: ").strip()
        event_type = type_map.get(type_choice, "other")
        
        desc = input("请输入详细描述: ").strip()
        
        # 3. 调用业务逻辑
        system.add_health_record(pet_id, date, event_type, desc)
    except Exception as e:
        print(f"[ERR] 记录添加失败：{e}")


def ai_consult_flow(system, advisor):
    """[4] 咨询 AI 管家的交互流程（连续对话子模式）
    
    功能特性：
    - 进入 while True 循环，支持多轮对话
    - 特殊指令：/list 查看历史、/archive 精准提取摘要
    - 退出时自动归档最后一段对话
    """
    print("\n>>> 正在连接 AI 管家...")
    pet_name = input("请输入您要咨询的宠物姓名: ").strip()
    
    # 根据姓名查找宠物（模糊匹配）
    matches = system.search_by_name(pet_name)
    if not matches:
        print(f"[ERR] 找不到名为 '{pet_name}' 的宠物，请检查姓名是否正确。")
        return
    
    # 默认取第一个匹配的宠物
    target_pet = matches[0]
    print(f"\n已选中宠物：{target_pet}")
    
    # 准备发送给 AI 的数据字典（接口隔离原则）
    pet_data = {
        "name": target_pet.name,
        "species": target_pet.species,
        "breed": target_pet.breed,
        "age": target_pet.age,
        "weight": target_pet.weight,
        "gender": target_pet.gender,
        "recent_records": target_pet.health_timeline.traverse_backward(5)
    }
    
    # 【关键步骤】注入宠物上下文到 System Prompt
    advisor.set_current_pet_context(pet_data)
    
    # 进入连续对话子模式
    print("\n" + "=" * 60)
    print("   AI 宠物健康管家 - 连续对话模式")
    print("=" * 60)
    print("   输入 'exit' 或 'quit' 退出")
    print("   输入 '/list' 查看历史记录")
    print("   输入 '/archive <轮次>' 精准提取摘要（如 /archive 1,3-5）")
    print("=" * 60)
    
    while True:
        try:
            user_input = input("\n[你]: ").strip()
            
            if not user_input:
                continue
            
            # 1. 退出检测
            if user_input.lower() in ['exit', 'quit', '返回', 'q']:
                print("\n[系统] 已结束本次咨询，正在为您保存记录...")
                # 强制保存最后一段对话
                summary = advisor.get_medical_summary(force=True)
                if summary:
                    print(f"\n--- 问诊记录 ---\n{summary}\n----------------")
                print("[OK] 记录已保存，返回主菜单。")
                
                # 【关键步骤】重置上下文，防止信息串台
                advisor.reset_context()
                break
            
            # 2. 特殊指令检测
            if user_input.startswith('/list'):
                history_display = advisor.get_history_display()
                print(f"\n{history_display}")
                continue
            
            if user_input.startswith('/archive'):
                expression = user_input[len('/archive'):].strip()
                if not expression:
                    print("[系统] 请指定轮次，格式：/archive 1,3-5")
                    continue
                result = advisor.extract_summary_by_rounds(expression)
                print(result)
                continue
            
            # 3. 正常对话
            print("\n🤖 AI 管家思考中...")
            
            # 根据问题类型自动选择分析策略
            if any(keyword in user_input for keyword in ["吃", "喂", "粮", "饭"]):
                response = advisor.analyze_feeding_plan(pet_data)
            else:
                # 默认使用症状诊断或综合建议
                response = advisor.diagnose_symptoms(pet_data, user_input)
            
            print(f"\n[AI 管家]: {response}")
            
        except RuntimeError as e:
            print(f"[WARN] AI 服务暂时不可用，请稍后重试。({e})")
        except KeyboardInterrupt:
            print("\n\n[系统] 检测到中断信号，正在保存记录...")
            advisor.get_medical_summary(force=True)
            print("[OK] 记录已保存，返回主菜单。")
            
            # 【关键步骤】重置上下文
            advisor.reset_context()
            break
        except Exception as e:
            print(f"[ERR] 咨询过程中发生未知错误：{e}")


def main():
    """主程序入口"""
    print("正在初始化系统组件...")
    
    try:
        # 初始化核心模块
        system = SmartPetProfileSystem()
        advisor = PetHealthAdvisor()
        print("[OK] 系统初始化完成！\n")
    except Exception as e:
        print(f"[ERR] 系统启动失败：{e}")
        return

    while True:
        print_header()
        choice = input("请输入您的选择: ").strip()

        if choice == '1':
            register_pet_flow(system)
        elif choice == '2':
            list_pets_flow(system)
        elif choice == '3':
            add_record_flow(system)
        elif choice == '4':
            ai_consult_flow(system, advisor)
        elif choice == '5':
            print("\n>>> 正在执行记忆压缩...")
            try:
                advisor.compress_memory()
                print("[OK] 已为您清理了冗余的对话细节，保留了关键信息。这有助于 AI 在长对话中保持清醒。")
            except Exception as e:
                print(f"[ERR] 压缩失败：{e}")
        elif choice == '6':
            print("\n>>> 正在提取 AI 管家对话摘要...")
            try:
                summary = advisor.get_medical_summary(force=True)
                if summary:
                    print(f"\n--- 对话摘要 ---\n{summary}\n----------------")
                    print("[OK] 已成功提取本次问诊精华，并保存至 D:\\chat-log 目录。您可以随时查阅宠物的健康档案。")
                else:
                    print("暂无可提取的对话摘要（建议至少进行一轮有效问诊）。")
            except Exception as e:
                print(f"[ERR] 提取失败：{e}")
        elif choice == '0':
            print("\n感谢使用智能宠物喂食管理系统，再见！👋")
            break
        else:
            print("[ERR] 无效的选择，请输入 0-6 之间的数字。")


if __name__ == "__main__":
    main()
