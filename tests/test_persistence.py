"""
测试宠物档案持久化功能
"""
import sys
from pathlib import Path
import os
import json

# 配置导入路径
project_root = Path(__file__).parent / 'src'
sys.path.insert(0, str(project_root))

from modules.pet_profile_manager import SmartPetProfileSystem, PETS_FILE


def test_persistence_basic():
    """测试基本持久化功能"""
    print("=" * 60)
    print("测试1：基本持久化（注册、添加记录、重启验证）")
    print("=" * 60)
    
    # 第一次运行：注册宠物并添加记录
    print("\n>>> 第1次运行：注册宠物并添加记录...")
    system1 = SmartPetProfileSystem()
    
    # 注册新宠物
    system1.register_pet("test001", "测试猫", "波斯猫", 2, 4.5, "female", "cat")
    
    # 添加健康记录
    system1.add_health_record("test001", "2026-04-20", "vaccine", "接种狂犬疫苗", severity="medium")
    system1.add_health_record("test001", "2026-04-25", "checkup", "常规体检", severity="low")
    
    # 检查文件是否存在
    if PETS_FILE.exists():
        print(f"\n✅ 数据文件已创建: {PETS_FILE}")
        
        # 读取文件内容
        with open(PETS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"✅ 文件中包含 {len(data)} 只宠物")
            
            # 显示 JSON 结构预览
            if data:
                pet = data[0]
                print(f"   - 宠物ID: {pet['pet_id']}")
                print(f"   - 姓名: {pet['name']}")
                print(f"   - 健康记录数: {len(pet['health_records'])}")
    else:
        print(f"\n❌ 数据文件未创建: {PETS_FILE}")
        return False
    
    # 第二次运行：验证数据是否保留
    print("\n>>> 第2次运行：验证数据是否保留...")
    system2 = SmartPetProfileSystem()
    
    # 查看宠物列表
    pets = system2.show_all_pets()
    
    # 验证测试猫是否存在
    test_pet = system2.profile_manager.get_pet("test001")
    if test_pet:
        print(f"\n✅ 数据持久化成功！")
        print(f"   - 找到宠物: {test_pet.name} ({test_pet.breed})")
        print(f"   - 年龄: {test_pet.age} 岁")
        print(f"   - 体重: {test_pet.weight} kg")
        
        # 验证健康记录
        records = test_pet.health_timeline.traverse_forward()
        print(f"   - 健康记录数: {len(records)}")
        for record in records:
            print(f"     * [{record['date']}] {record['type']}: {record['desc']}")
        
        return True
    else:
        print(f"\n❌ 数据持久化失败！找不到测试猫")
        return False


def test_update_and_delete():
    """测试更新和删除操作的持久化"""
    print("\n" + "=" * 60)
    print("测试2：更新和删除操作的持久化")
    print("=" * 60)
    
    system = SmartPetProfileSystem()
    
    # 注册新宠物
    print("\n>>> 注册新宠物...")
    system.register_pet("test002", "测试狗", "金毛犬", 3, 25.0, "male", "dog")
    
    # 更新信息
    print("\n>>> 更新宠物信息...")
    system.update_pet_info("test002", age=4, weight=27.0)
    
    # 验证更新
    pet = system.profile_manager.get_pet("test002")
    if pet and pet.age == 4 and pet.weight == 27.0:
        print(f"✅ 更新成功：年龄={pet.age}, 体重={pet.weight}")
    else:
        print(f"❌ 更新失败")
        return False
    
    # 删除宠物
    print("\n>>> 删除宠物...")
    system.remove_pet("test002")
    
    # 验证删除
    pet = system.profile_manager.get_pet("test002")
    if not pet:
        print(f"✅ 删除成功")
        
        # 检查文件中是否还有该宠物
        if PETS_FILE.exists():
            with open(PETS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                remaining_ids = [p['pet_id'] for p in data]
                if "test002" not in remaining_ids:
                    print(f"✅ 文件中已移除该宠物")
                    return True
                else:
                    print(f"❌ 文件中仍存在该宠物")
                    return False
    else:
        print(f"❌ 删除失败")
        return False


def test_error_handling():
    """测试异常处理"""
    print("\n" + "=" * 60)
    print("测试3：异常处理健壮性")
    print("=" * 60)
    
    # 测试1：删除数据文件夹后重新初始化
    print("\n>>> 测试：删除数据文件夹后重新初始化...")
    
    # 临时重命名数据文件夹
    data_dir = PETS_FILE.parent
    backup_dir = data_dir.parent / "data_backup"
    
    if data_dir.exists():
        data_dir.rename(backup_dir)
        print(f"   - 已临时移动数据文件夹")
    
    try:
        # 创建新系统（应该能正常初始化）
        system = SmartPetProfileSystem()
        print(f"✅ 系统在无数据文件时正常初始化")
        
        # 注册一只宠物（应该能自动创建文件夹）
        system.register_pet("test003", "新宠物", "品种", 1, 1.0)
        
        if PETS_FILE.exists():
            print(f"✅ 系统自动创建了数据文件夹和文件")
        else:
            print(f"❌ 系统未创建数据文件")
            return False
        
    except Exception as e:
        print(f"❌ 系统初始化失败: {e}")
        return False
    finally:
        # 恢复数据文件夹
        if backup_dir.exists():
            if data_dir.exists():
                import shutil
                shutil.rmtree(data_dir)
            backup_dir.rename(data_dir)
            print(f"   - 已恢复数据文件夹")
    
    return True


def cleanup_test_data():
    """清理测试数据"""
    print("\n" + "=" * 60)
    print("清理测试数据")
    print("=" * 60)
    
    if PETS_FILE.exists():
        # 读取现有数据
        with open(PETS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 过滤掉测试宠物
        original_data = [p for p in data if not p['pet_id'].startswith('test')]
        
        # 写回文件
        with open(PETS_FILE, 'w', encoding='utf-8') as f:
            json.dump(original_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 已清理测试数据，保留 {len(original_data)} 只真实宠物")
    else:
        print(f"⚠️ 数据文件不存在，无需清理")


if __name__ == "__main__":
    try:
        result1 = test_persistence_basic()
        result2 = test_update_and_delete()
        result3 = test_error_handling()
        
        print("\n" + "=" * 60)
        if result1 and result2 and result3:
            print("  所有测试通过！✅")
        else:
            print("  部分测试失败 ❌")
        print("=" * 60)
        
        # 清理测试数据
        cleanup_test_data()
        
        print("\n💡 提示：可以查看 data/pets.json 文件验证书写格式")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
