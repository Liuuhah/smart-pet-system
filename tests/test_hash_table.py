"""
哈希表（宠物档案管理）单元测试

作者：刘同学
日期：2026-04-16
课程：《数据结构》项目 - Phase 1
"""

import sys
import os
import unittest
from pathlib import Path

# 配置导入路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from data_structures.hash_table import PetProfile, PetProfileManager


class TestPetProfile(unittest.TestCase):
    """宠物档案类测试"""
    
    def test_create_profile_success(self):
        """测试正常创建宠物档案"""
        pet = PetProfile("pet001", "小白", "金毛犬", 2, 25.5, "male")
        
        self.assertEqual(pet.pet_id, "pet001")
        self.assertEqual(pet.name, "小白")
        self.assertEqual(pet.breed, "金毛犬")
        self.assertEqual(pet.age, 2)
        self.assertEqual(pet.weight, 25.5)
        self.assertEqual(pet.gender, "male")
        self.assertEqual(pet.status, "active")
        self.assertIsNotNone(pet.created_at)
        self.assertIsInstance(pet.allergies, list)
        self.assertIsInstance(pet.medications, list)
        self.assertIsNone(pet.health_timeline)
    
    def test_default_gender(self):
        """测试默认性别为 unknown"""
        pet = PetProfile("pet001", "小白", "金毛犬", 2, 25.5)
        self.assertEqual(pet.gender, "unknown")
    
    def test_age_validation_negative(self):
        """测试负数年龄校验"""
        with self.assertRaises(ValueError):
            PetProfile("pet001", "小白", "金毛犬", -1, 25.5)
    
    def test_weight_validation_negative(self):
        """测试负数体重校验"""
        with self.assertRaises(ValueError):
            PetProfile("pet001", "小白", "金毛犬", 2, -5.0)
    
    def test_gender_validation(self):
        """测试性别校验"""
        # 有效值
        for gender in ["male", "female", "unknown"]:
            pet = PetProfile("pet001", "小白", "金毛犬", 2, 25.5, gender)
            self.assertEqual(pet.gender, gender)
        
        # 无效值
        with self.assertRaises(ValueError):
            PetProfile("pet001", "小白", "金毛犬", 2, 25.5, "invalid")
    
    def test_string_representation(self):
        """测试字符串表示"""
        pet = PetProfile("pet001", "小白", "金毛犬", 2, 25.5, "male")
        str_repr = str(pet)
        
        self.assertIn("小白", str_repr)
        self.assertIn("金毛犬", str_repr)
        self.assertIn("2岁", str_repr)
        self.assertIn("25.5kg", str_repr)
        self.assertIn("公", str_repr)
    
    def test_female_gender_string(self):
        """测试母性别的字符串表示"""
        pet = PetProfile("pet002", "小花", "布偶猫", 1, 4.2, "female")
        str_repr = str(pet)
        
        self.assertIn("母", str_repr)
    
    def test_zero_age_weight(self):
        """测试年龄和体重为 0 的情况"""
        pet = PetProfile("pet001", "新生", "金毛犬", 0, 0.5)
        self.assertEqual(pet.age, 0)
        self.assertEqual(pet.weight, 0.5)


class TestPetProfileManager(unittest.TestCase):
    """宠物档案管理器测试"""
    
    def setUp(self):
        """每个测试前的准备工作"""
        self.manager = PetProfileManager()
        
        # 创建测试宠物
        self.test_pets = [
            PetProfile("pet001", "小白", "金毛犬", 2, 25.5, "male"),
            PetProfile("pet002", "小花", "布偶猫", 1, 4.2, "female"),
            PetProfile("pet003", "旺财", "中华田园犬", 3, 15.0, "male"),
        ]
    
    def test_empty_manager(self):
        """测试空管理器"""
        self.assertTrue(self.manager.is_empty())
        self.assertEqual(self.manager.get_pet_count(), 0)
        self.assertEqual(self.manager.get_all_pets(), [])
    
    def test_add_pet_success(self):
        """测试成功添加宠物"""
        pet = PetProfile("pet001", "小白", "金毛犬", 2, 25.5)
        self.manager.add_pet(pet)
        
        self.assertFalse(self.manager.is_empty())
        self.assertEqual(self.manager.get_pet_count(), 1)
        self.assertEqual(self.manager.get_pet("pet001"), pet)
    
    def test_add_pet_duplicate_id(self):
        """测试添加重复 ID"""
        pet1 = PetProfile("pet001", "小白", "金毛犬", 2, 25.5)
        pet2 = PetProfile("pet001", " duplicate", "金毛犬", 3, 30.0)
        
        self.manager.add_pet(pet1)
        
        with self.assertRaises(ValueError):
            self.manager.add_pet(pet2)
    
    def test_add_pet_invalid_type(self):
        """测试添加非 PetProfile 类型"""
        with self.assertRaises(TypeError):
            self.manager.add_pet("不是 PetProfile")
        
        with self.assertRaises(TypeError):
            self.manager.add_pet(123)
    
    def test_get_pet_exists(self):
        """测试获取存在的宠物"""
        pet = PetProfile("pet001", "小白", "金毛犬", 2, 25.5)
        self.manager.add_pet(pet)
        
        result = self.manager.get_pet("pet001")
        
        self.assertEqual(result, pet)
        self.assertEqual(result.name, "小白")
    
    def test_get_pet_not_exists(self):
        """测试获取不存在的宠物"""
        result = self.manager.get_pet("pet999")
        self.assertIsNone(result)
    
    def test_remove_pet_success(self):
        """测试成功删除宠物"""
        pet = PetProfile("pet001", "小白", "金毛犬", 2, 25.5)
        self.manager.add_pet(pet)
        
        result = self.manager.remove_pet("pet001")
        
        self.assertTrue(result)
        self.assertEqual(self.manager.get_pet_count(), 0)
        self.assertIsNone(self.manager.get_pet("pet001"))
    
    def test_remove_pet_not_exists(self):
        """测试删除不存在的宠物"""
        result = self.manager.remove_pet("pet999")
        self.assertFalse(result)
    
    def test_update_pet_success(self):
        """测试成功更新宠物信息"""
        pet = PetProfile("pet001", "小白", "金毛犬", 2, 25.5)
        self.manager.add_pet(pet)
        
        # 更新年龄和体重
        self.manager.update_pet("pet001", age=3, weight=28.0)
        
        updated_pet = self.manager.get_pet("pet001")
        self.assertEqual(updated_pet.age, 3)
        self.assertEqual(updated_pet.weight, 28.0)
    
    def test_update_pet_not_exists(self):
        """测试更新不存在的宠物"""
        with self.assertRaises(ValueError):
            self.manager.update_pet("pet999", age=3)
    
    def test_update_pet_invalid_field(self):
        """测试更新不存在的字段"""
        pet = PetProfile("pet001", "小白", "金毛犬", 2, 25.5)
        self.manager.add_pet(pet)
        
        with self.assertRaises(AttributeError):
            self.manager.update_pet("pet001", invalid_field="test")
    
    def test_update_pet_negative_age(self):
        """测试更新负数年龄"""
        pet = PetProfile("pet001", "小白", "金毛犬", 2, 25.5)
        self.manager.add_pet(pet)
        
        with self.assertRaises(ValueError):
            self.manager.update_pet("pet001", age=-1)
    
    def test_update_pet_negative_weight(self):
        """测试更新负数体重"""
        pet = PetProfile("pet001", "小白", "金毛犬", 2, 25.5)
        self.manager.add_pet(pet)
        
        with self.assertRaises(ValueError):
            self.manager.update_pet("pet001", weight=-5.0)
    
    def test_update_pet_invalid_gender(self):
        """测试更新非法性别"""
        pet = PetProfile("pet001", "小白", "金毛犬", 2, 25.5)
        self.manager.add_pet(pet)
        
        with self.assertRaises(ValueError):
            self.manager.update_pet("pet001", gender="invalid")
    
    def test_update_pet_invalid_status(self):
        """测试更新非法状态"""
        pet = PetProfile("pet001", "小白", "金毛犬", 2, 25.5)
        self.manager.add_pet(pet)
        
        with self.assertRaises(ValueError):
            self.manager.update_pet("pet001", status="invalid")
    
    def test_update_pet_status(self):
        """测试更新宠物状态"""
        pet = PetProfile("pet001", "小白", "金毛犬", 2, 25.5)
        self.manager.add_pet(pet)
        
        # 更新为 inactive
        self.manager.update_pet("pet001", status="inactive")
        self.assertEqual(self.manager.get_pet("pet001").status, "inactive")
        
        # 更新为 lost
        self.manager.update_pet("pet001", status="lost")
        self.assertEqual(self.manager.get_pet("pet001").status, "lost")
    
    def test_get_all_pets(self):
        """测试获取所有宠物"""
        for pet in self.test_pets:
            self.manager.add_pet(pet)
        
        all_pets = self.manager.get_all_pets()
        
        self.assertEqual(len(all_pets), 3)
        self.assertIn(self.test_pets[0], all_pets)
        self.assertIn(self.test_pets[1], all_pets)
        self.assertIn(self.test_pets[2], all_pets)
    
    def test_search_by_name_exact(self):
        """测试精确名字搜索"""
        for pet in self.test_pets:
            self.manager.add_pet(pet)
        
        results = self.manager.search_by_name("小白")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "小白")
    
    def test_search_by_name_partial(self):
        """测试模糊名字搜索"""
        for pet in self.test_pets:
            self.manager.add_pet(pet)
        
        results = self.manager.search_by_name("小")
        
        self.assertEqual(len(results), 2)  # 小白、小花
    
    def test_search_by_name_case_insensitive(self):
        """测试名字搜索不区分大小写"""
        pet = PetProfile("pet001", "Bailey", "金毛犬", 2, 25.5)
        self.manager.add_pet(pet)
        
        results1 = self.manager.search_by_name("bai")
        results2 = self.manager.search_by_name("BAI")
        results3 = self.manager.search_by_name("Bai")
        
        self.assertEqual(len(results1), 1)
        self.assertEqual(len(results2), 1)
        self.assertEqual(len(results3), 1)
    
    def test_search_by_name_no_result(self):
        """测试名字搜索无结果"""
        for pet in self.test_pets:
            self.manager.add_pet(pet)
        
        results = self.manager.search_by_name("不存在的名字")
        
        self.assertEqual(results, [])
    
    def test_search_by_breed_exact(self):
        """测试精确品种搜索"""
        for pet in self.test_pets:
            self.manager.add_pet(pet)
        
        results = self.manager.search_by_breed("金毛犬")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].breed, "金毛犬")
    
    def test_search_by_breed_partial(self):
        """测试模糊品种搜索"""
        for pet in self.test_pets:
            self.manager.add_pet(pet)
        
        results = self.manager.search_by_breed("猫")
        
        self.assertEqual(len(results), 1)  # 布偶猫
    
    def test_search_by_breed_case_insensitive(self):
        """测试品种搜索不区分大小写"""
        pet = PetProfile("pet001", "小白", "Golden Retriever", 2, 25.5)
        self.manager.add_pet(pet)
        
        results = self.manager.search_by_breed("golden")
        
        self.assertEqual(len(results), 1)
    
    def test_get_active_pets(self):
        """测试获取活跃宠物"""
        pet1 = PetProfile("pet001", "小白", "金毛犬", 2, 25.5)
        pet2 = PetProfile("pet002", "小花", "布偶猫", 1, 4.2)
        pet3 = PetProfile("pet003", "旺财", "中华田园犬", 3, 15.0)
        
        self.manager.add_pet(pet1)
        self.manager.add_pet(pet2)
        self.manager.add_pet(pet3)
        
        # 将 pet2 设为 inactive
        self.manager.update_pet("pet002", status="inactive")
        
        active_pets = self.manager.get_active_pets()
        
        self.assertEqual(len(active_pets), 2)
        self.assertIn(pet1, active_pets)
        self.assertIn(pet3, active_pets)
        self.assertNotIn(pet2, active_pets)
    
    def test_clear(self):
        """测试清空管理器"""
        for pet in self.test_pets:
            self.manager.add_pet(pet)
        
        self.manager.clear()
        
        self.assertTrue(self.manager.is_empty())
        self.assertEqual(self.manager.get_pet_count(), 0)
        self.assertEqual(self.manager.get_all_pets(), [])
    
    def test_string_representation(self):
        """测试字符串表示"""
        pet = PetProfile("pet001", "小白", "金毛犬", 2, 25.5)
        self.manager.add_pet(pet)
        
        str_repr = str(self.manager)
        
        self.assertIn("1 只", str_repr)
        self.assertIn("pet001", str_repr)
        self.assertIn("小白", str_repr)
    
    def test_empty_string_representation(self):
        """测试空管理器的字符串表示"""
        str_repr = str(self.manager)
        self.assertIn("暂无宠物档案", str_repr)
    
    def test_status_icon_mapping(self):
        """测试状态图标映射"""
        pet1 = PetProfile("pet001", "小白", "金毛犬", 2, 25.5)
        pet2 = PetProfile("pet002", "小花", "布偶猫", 1, 4.2)
        pet3 = PetProfile("pet003", "旺财", "中华田园犬", 3, 15.0)
        
        self.manager.add_pet(pet1)
        self.manager.add_pet(pet2)
        self.manager.add_pet(pet3)
        
        self.manager.update_pet("pet002", status="inactive")
        self.manager.update_pet("pet003", status="lost")
        
        str_repr = str(self.manager)
        
        self.assertIn("🟢", str_repr)  # active
        self.assertIn("⚫", str_repr)  # inactive
        self.assertIn("🔴", str_repr)  # lost


if __name__ == '__main__':
    unittest.main(verbosity=2)
