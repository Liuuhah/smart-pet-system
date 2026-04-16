"""
宠物档案管理模块单元测试

作者：刘同学
日期：2026-04-16
课程：《数据结构》项目 - Phase 1

测试目标：
- 验证 SmartPetProfileSystem 的业务逻辑整合
- 测试双向链表和哈希表的协同工作
- 验证异常处理和边界情况
- 验证资源释放的严谨性
"""

import sys
import os
import unittest
from pathlib import Path

# 配置导入路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from modules.pet_profile_manager import SmartPetProfileSystem


class TestSmartPetProfileSystem(unittest.TestCase):
    """智能宠物档案系统测试"""
    
    def setUp(self):
        """每个测试前的准备工作"""
        self.system = SmartPetProfileSystem()
        
        # 注册测试宠物
        self.pet1 = self.system.register_pet("pet001", "小白", "金毛犬", 2, 25.5, "male")
        self.pet2 = self.system.register_pet("pet002", "小花", "布偶猫", 1, 4.2, "female")
        
        # 为 pet001 添加健康记录
        self.system.add_health_record("pet001", "2026-01-15", "vaccine", "接种狂犬疫苗", severity="medium")
        self.system.add_health_record("pet001", "2026-02-20", "checkup", "常规体检", severity="low")
        self.system.add_health_record("pet001", "2026-03-10", "illness", "感冒发烧", severity="high")
    
    # ==================== 【A】正常流程测试 ====================
    
    def test_register_pet_success(self):
        """测试成功注册宠物"""
        pet = self.system.register_pet("pet003", "旺财", "中华田园犬", 3, 15.0, "male")
        
        # 验证返回值
        self.assertIsNotNone(pet)
        self.assertEqual(pet.pet_id, "pet003")
        self.assertEqual(pet.name, "旺财")
        self.assertEqual(pet.breed, "中华田园犬")
        self.assertEqual(pet.age, 3)
        self.assertEqual(pet.weight, 15.0)
        self.assertEqual(pet.gender, "male")
        
        # 验证健康时间线已初始化
        self.assertIsNotNone(pet.health_timeline)
        self.assertTrue(pet.health_timeline.is_empty())
        
        # 验证宠物数量
        self.assertEqual(self.system.get_pet_count(), 3)
    
    def test_add_health_record_success(self):
        """测试成功添加健康记录"""
        # 记录添加前的数量
        pet = self.system.profile_manager.get_pet("pet001")
        initial_size = pet.health_timeline.get_size()
        
        # 添加新记录
        result = self.system.add_health_record("pet001", "2026-04-15", "checkup", "复查")
        
        # 验证返回值
        self.assertTrue(result)
        
        # 验证链表大小增加
        self.assertEqual(pet.health_timeline.get_size(), initial_size + 1)
    
    def test_view_recent_records(self):
        """测试查看最近记录"""
        records = self.system.view_recent_records("pet001", count=2)
        
        # 验证返回数量
        self.assertEqual(len(records), 2)
        
        # 验证顺序（从新到旧）
        self.assertEqual(records[0]["date"], "2026-03-10")
        self.assertEqual(records[0]["type"], "illness")
        self.assertEqual(records[1]["date"], "2026-02-20")
        self.assertEqual(records[1]["type"], "checkup")
    
    def test_view_full_timeline(self):
        """测试查看完整时间线"""
        records = self.system.view_full_timeline("pet001")
        
        # 验证返回数量
        self.assertEqual(len(records), 3)
        
        # 验证顺序（从早到晚）
        self.assertEqual(records[0]["date"], "2026-01-15")
        self.assertEqual(records[0]["type"], "vaccine")
        self.assertEqual(records[1]["date"], "2026-02-20")
        self.assertEqual(records[1]["type"], "checkup")
        self.assertEqual(records[2]["date"], "2026-03-10")
        self.assertEqual(records[2]["type"], "illness")
    
    def test_update_pet_info_success(self):
        """测试更新宠物信息"""
        # 更新前
        pet_before = self.system.profile_manager.get_pet("pet001")
        self.assertEqual(pet_before.age, 2)
        self.assertEqual(pet_before.weight, 25.5)
        
        # 更新
        result = self.system.update_pet_info("pet001", age=3, weight=28.0)
        
        # 验证返回值
        self.assertTrue(result)
        
        # 验证更新生效
        pet_after = self.system.profile_manager.get_pet("pet001")
        self.assertEqual(pet_after.age, 3)
        self.assertEqual(pet_after.weight, 28.0)
    
    def test_remove_pet_success(self):
        """测试删除宠物"""
        initial_count = self.system.get_pet_count()
        
        # 删除 pet002
        result = self.system.remove_pet("pet002")
        
        # 验证返回值
        self.assertTrue(result)
        
        # 验证宠物数量减少
        self.assertEqual(self.system.get_pet_count(), initial_count - 1)
        
        # 验证宠物已不存在
        self.assertIsNone(self.system.profile_manager.get_pet("pet002"))
    
    # ==================== 【B】异常处理测试 ====================
    
    def test_register_duplicate_id(self):
        """测试重复 ID 注册"""
        with self.assertRaises(ValueError):
            self.system.register_pet("pet001", "重复", "测试", 1, 1.0)
    
    def test_add_record_nonexistent_pet(self):
        """测试给不存在的宠物添加记录"""
        result = self.system.add_health_record("pet999", "2026-04-15", "test", "测试")
        self.assertFalse(result)
    
    def test_add_record_invalid_date(self):
        """测试非法日期格式"""
        result = self.system.add_health_record("pet001", "2026/13/45", "test", "测试")
        self.assertFalse(result)
    
    def test_view_records_nonexistent_pet(self):
        """测试查看不存在宠物的记录"""
        records = self.system.view_recent_records("pet999")
        self.assertEqual(records, [])
    
    def test_update_nonexistent_pet(self):
        """测试更新不存在的宠物"""
        result = self.system.update_pet_info("pet999", age=5)
        self.assertFalse(result)
    
    def test_remove_nonexistent_pet(self):
        """测试删除不存在的宠物"""
        result = self.system.remove_pet("pet999")
        self.assertFalse(result)
    
    # ==================== 【C】边界情况测试 ====================
    
    def test_empty_system_operations(self):
        """测试空系统下的操作"""
        empty_system = SmartPetProfileSystem()
        
        # 获取数量
        self.assertEqual(empty_system.get_pet_count(), 0)
        
        # 显示所有宠物（应返回空列表）
        all_pets = empty_system.show_all_pets()
        self.assertEqual(all_pets, [])
    
    def test_view_empty_timeline(self):
        """测试查看刚注册宠物的空时间线"""
        pet = self.system.register_pet("pet003", "新宠物", "测试犬", 1, 5.0)
        
        # 查看空时间线
        records = self.system.view_recent_records("pet003")
        self.assertEqual(records, [])
        
        # 查看完整时间线
        full_records = self.system.view_full_timeline("pet003")
        self.assertEqual(full_records, [])
    
    def test_single_record_operations(self):
        """测试只有一条记录时的遍历"""
        # 创建一个只有一条记录的宠物
        pet = self.system.register_pet("pet003", "新宠物", "测试犬", 1, 5.0)
        self.system.add_health_record("pet003", "2026-04-15", "vaccine", "接种疫苗")
        
        # 正向遍历
        forward_records = self.system.view_full_timeline("pet003")
        self.assertEqual(len(forward_records), 1)
        self.assertEqual(forward_records[0]["date"], "2026-04-15")
        
        # 反向遍历
        backward_records = self.system.view_recent_records("pet003", count=5)
        self.assertEqual(len(backward_records), 1)
        self.assertEqual(backward_records[0]["date"], "2026-04-15")
    
    def test_remove_pet_clears_timeline(self):
        """测试删除宠物后，健康时间线是否被正确清空（验证资源释放）"""
        # 获取 pet001 的时间线引用
        pet_before = self.system.profile_manager.get_pet("pet001")
        timeline_ref = pet_before.health_timeline
        
        # 验证时间线有记录
        self.assertEqual(timeline_ref.get_size(), 3)
        
        # 删除宠物
        self.system.remove_pet("pet001")
        
        # 验证宠物已删除
        pet_after = self.system.profile_manager.get_pet("pet001")
        self.assertIsNone(pet_after)
        
        # 验证时间线已被清空并置为 None
        # 注意：timeline_ref 仍然指向原来的对象，但其内部已被清空
        self.assertEqual(timeline_ref.get_size(), 0)
        
        # 验证 pet 对象的 health_timeline 属性已被置为 None
        # （这里需要重新获取，但宠物已删除，所以通过 profile_manager 获取不到）
        # 我们通过检查删除逻辑来验证：如果资源释放正确，应该不会有内存泄漏
    
    # ==================== 【D】搜索功能测试 ====================
    
    def test_search_by_name_exact(self):
        """测试精确名字搜索"""
        results = self.system.search_by_name("小白")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "小白")
    
    def test_search_by_name_partial(self):
        """测试模糊名字搜索"""
        results = self.system.search_by_name("小")
        
        # 应该匹配 "小白" 和 "小花"
        self.assertEqual(len(results), 2)
    
    def test_search_by_breed_partial(self):
        """测试模糊品种搜索"""
        results = self.system.search_by_breed("猫")
        
        # 应该匹配 "布偶猫"
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].breed, "布偶猫")
    
    def test_search_no_results(self):
        """测试搜索无结果"""
        # 按名字搜索
        name_results = self.system.search_by_name("不存在的名字")
        self.assertEqual(name_results, [])
        
        # 按品种搜索
        breed_results = self.system.search_by_breed("不存在的品种")
        self.assertEqual(breed_results, [])
    
    # ==================== 【E】综合集成测试 ====================
    
    def test_full_workflow(self):
        """测试完整工作流程"""
        # 1. 创建新系统
        system = SmartPetProfileSystem()
        
        # 2. 注册宠物
        pet = system.register_pet("pet100", "测试宠", "测试犬", 1, 5.0)
        self.assertEqual(system.get_pet_count(), 1)
        
        # 3. 添加多条记录
        system.add_health_record("pet100", "2026-01-01", "vaccine", "疫苗1")
        system.add_health_record("pet100", "2026-02-01", "checkup", "体检1")
        system.add_health_record("pet100", "2026-03-01", "illness", "生病1")
        
        # 4. 查看记录
        recent = system.view_recent_records("pet100", count=2)
        self.assertEqual(len(recent), 2)
        self.assertEqual(recent[0]["date"], "2026-03-01")  # 最新的
        
        full = system.view_full_timeline("pet100")
        self.assertEqual(len(full), 3)
        self.assertEqual(full[0]["date"], "2026-01-01")  # 最早的
        
        # 5. 搜索宠物
        results = system.search_by_name("测试")
        self.assertEqual(len(results), 1)
        
        # 6. 更新信息
        system.update_pet_info("pet100", age=2, weight=6.0)
        updated_pet = system.profile_manager.get_pet("pet100")
        self.assertEqual(updated_pet.age, 2)
        
        # 7. 删除宠物
        system.remove_pet("pet100")
        self.assertEqual(system.get_pet_count(), 0)
        
        # 8. 验证删除后无法操作
        self.assertFalse(system.add_health_record("pet100", "2026-04-01", "test", "测试"))
    
    def test_multiple_pets_independent_timelines(self):
        """测试多个宠物的时间线独立"""
        # 为两个宠物添加不同数量的记录
        self.system.add_health_record("pet001", "2026-04-01", "test", "记录1")
        self.system.add_health_record("pet002", "2026-04-01", "test", "记录1")
        self.system.add_health_record("pet002", "2026-04-02", "test", "记录2")
        
        # 获取各自的记录数量
        pet1 = self.system.profile_manager.get_pet("pet001")
        pet2 = self.system.profile_manager.get_pet("pet002")
        
        self.assertEqual(pet1.health_timeline.get_size(), 4)  # 3 + 1
        self.assertEqual(pet2.health_timeline.get_size(), 2)  # 0 + 2


if __name__ == '__main__':
    unittest.main(verbosity=2)
