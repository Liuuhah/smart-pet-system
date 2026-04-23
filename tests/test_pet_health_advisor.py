"""
AI 宠物健康顾问模块单元测试

作者：刘同学
日期：2026-04-16
课程：《数据结构》项目 - Phase 1

测试目标：
- 验证 PetHealthAdvisor 的核心业务逻辑
- 测试 Mock LLM 客户端的集成
- 验证异常处理和降级策略
- 确保接口隔离设计的正确性
"""

import sys
import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# 配置导入路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root))

from ai_assistant.pet_health_advisor import PetHealthAdvisor


class TestPetHealthAdvisor(unittest.TestCase):
    """智能宠物健康顾问测试"""
    
    @patch('ai_assistant.pet_health_advisor.ChatCompressClient')
    def setUp(self, mock_client_class):
        """每个测试前的准备工作"""
        # 持久化 Mock，避免在测试方法执行时失效
        self.mock_client_instance = MagicMock()
        mock_client_class.return_value = self.mock_client_instance
        
        # 预设 Mock 返回值
        self.mock_client_instance.send_request_stream.return_value = ("Mocked AI Response", 1.5)
        
        self.advisor = PetHealthAdvisor()
        
        # 准备测试数据
        self.dog_profile = {
            "name": "小白",
            "species": "dog",
            "breed": "金毛犬",
            "age": 2,
            "weight": 25.5,
            "gender": "male",
            "recent_records": [
                {"date": "2026-04-15", "type": "checkup", "desc": "常规体检"}
            ]
        }
        
        self.cat_profile = {
            "name": "小花",
            "species": "cat",
            "breed": "布偶猫",
            "age": 1,
            "weight": 4.2,
            "gender": "female"
        }
    
    # ==================== 【A】核心功能测试 ====================
    
    def test_analyze_feeding_plan_success(self):
        """测试成功分析喂养计划"""
        response = self.advisor.analyze_feeding_plan(self.dog_profile)
        
        # 验证返回非空字符串
        self.assertIsInstance(response, str)
        self.assertTrue(len(response) > 0)
        
        # 验证 Mock 被正确调用
        self.mock_client_instance.send_request_stream.assert_called_once()
    
    def test_diagnose_symptoms_success(self):
        """测试成功诊断症状"""
        symptoms = "呕吐、腹泻、食欲不振"
        response = self.advisor.diagnose_symptoms(self.cat_profile, symptoms)
        
        # 验证返回非空字符串
        self.assertIsInstance(response, str)
        self.assertTrue(len(response) > 0)
        
        # 验证 Mock 被正确调用
        self.mock_client_instance.send_request_stream.assert_called_once()
    
    def test_generate_health_report_success(self):
        """测试成功生成健康报告"""
        response = self.advisor.generate_health_report(self.dog_profile)
        
        # 验证返回非空字符串
        self.assertIsInstance(response, str)
        self.assertTrue(len(response) > 0)
        
        # 验证 Mock 被正确调用
        self.mock_client_instance.send_request_stream.assert_called_once()
    
    def test_format_pet_profile_for_llm(self):
        """测试宠物档案格式化"""
        formatted = self.advisor.format_pet_profile_for_llm(self.dog_profile)
        
        # 验证包含关键字段
        self.assertIn("名字: 小白", formatted)
        self.assertIn("物种: dog", formatted)
        self.assertIn("年龄: 2 岁", formatted)
        self.assertIn("体重: 25.5 kg", formatted)
    
    # ==================== 【B】异常处理测试 ====================
    
    def test_validate_pet_profile_missing_fields(self):
        """测试校验缺少必要字段的宠物档案"""
        incomplete_profile = {"name": "小白"}  # 缺少 species, age, weight
        
        with self.assertRaises(ValueError):
            self.advisor._validate_pet_profile(incomplete_profile, required_fields=["name", "species", "age"])
    
    def test_diagnose_symptoms_empty_input(self):
        """测试诊断空症状输入"""
        with self.assertRaises(ValueError):
            self.advisor.diagnose_symptoms(self.dog_profile, "")
        
        with self.assertRaises(ValueError):
            self.advisor.diagnose_symptoms(self.dog_profile, "   ")
    
    def test_analyze_feeding_plan_missing_required_fields(self):
        """测试喂养计划分析缺少必要字段"""
        incomplete_profile = {"name": "小白"}  # 缺少 species, age, weight
        
        with self.assertRaises(ValueError):
            self.advisor.analyze_feeding_plan(incomplete_profile)
    
    # ==================== 【C】降级策略测试 ====================
    
    def test_fallback_feeding_advice_triggered(self):
        """测试 LLM 失败时触发降级策略"""
        # 模拟 LLM 调用失败
        self.mock_client_instance.send_request_stream.side_effect = Exception("Network Error")
        
        response = self.advisor.analyze_feeding_plan(self.dog_profile)
        
        # 验证返回降级建议（包含基础关键词）
        self.assertIsInstance(response, str)
        self.assertIn("喂养建议", response)
        self.assertIn("注意", response)
    
    def test_fallback_diagnosis_advice_triggered(self):
        """测试症状诊断降级策略"""
        # 直接调用降级方法
        response = self.advisor._fallback_diagnosis_advice("呕吐、腹泻")
        
        # 验证包含紧急程度和就医建议
        self.assertIn("紧急程度", response)
        self.assertIn("就医", response)
        self.assertIn("家庭护理", response)
    
    def test_fallback_with_urgent_symptoms(self):
        """测试紧急症状的降级建议"""
        response = self.advisor._fallback_diagnosis_advice("昏迷、抽搐")
        
        # 验证识别为高紧急程度
        self.assertIn("高", response)
        self.assertIn("立即", response)
    
    # ==================== 【D】Prompt 构建测试 ====================
    
    def test_build_feeding_plan_prompt_structure(self):
        """测试喂养计划 Prompt 结构"""
        prompt = self.advisor._build_feeding_plan_prompt(self.dog_profile)
        
        # 验证包含关键信息
        self.assertIn("小白", prompt)
        self.assertIn("金毛犬", prompt)
        self.assertIn("2 岁", prompt)
        self.assertIn("25.5 kg", prompt)
        
        # 验证包含任务要求
        self.assertIn("每日喂食量建议", prompt)
        self.assertIn("喂食频率", prompt)
        self.assertIn("营养配比", prompt)
    
    def test_build_diagnosis_prompt_structure(self):
        """测试诊断 Prompt 结构"""
        symptoms = "发烧、咳嗽"
        prompt = self.advisor._build_diagnosis_prompt(self.cat_profile, symptoms)
        
        # 验证包含症状和免责声明
        self.assertIn(symptoms, prompt)
        self.assertIn("仅供参考", prompt)
        self.assertIn("不能替代专业兽医诊断", prompt)
    
    def test_build_health_report_prompt_with_records(self):
        """测试健康报告 Prompt 包含历史记录"""
        prompt = self.advisor._build_health_report_prompt(self.dog_profile)
        
        # 验证包含健康记录
        self.assertIn("常规体检", prompt)
        self.assertIn("2026-04-15", prompt)
        
        # 验证包含报告结构要求
        self.assertIn("整体评估", prompt)
        self.assertIn("风险提示", prompt)
        self.assertIn("改进建议", prompt)
    
    # ==================== 【E】边界情况测试 ====================
    
    def test_analyze_feeding_plan_without_records(self):
        """测试没有健康记录的喂养计划分析"""
        profile_no_records = {
            "name": "旺财",
            "species": "dog",
            "breed": "中华田园犬",
            "age": 3,
            "weight": 15.0
        }
        
        response = self.advisor.analyze_feeding_plan(profile_no_records)
        
        # 验证仍能正常返回
        self.assertIsInstance(response, str)
        self.assertTrue(len(response) > 0)
    
    def test_different_species_handling(self):
        """测试不同物种的处理"""
        bird_profile = {
            "name": "小鹦",
            "species": "other",
            "breed": "鹦鹉",
            "age": 1,
            "weight": 0.1
        }
        
        response = self.advisor.analyze_feeding_plan(bird_profile)
        
        # 验证能处理其他物种
        self.assertIsInstance(response, str)
    
    def test_life_stage_classification(self):
        """测试生命阶段分类"""
        # 幼宠
        young_pet = {"name": "宝宝", "species": "dog", "breed": "泰迪", "age": 0.5, "weight": 2.0}
        prompt_young = self.advisor._build_feeding_plan_prompt(young_pet)
        self.assertIn("幼年", prompt_young)
        
        # 成宠
        adult_pet = {"name": "壮壮", "species": "dog", "breed": "哈士奇", "age": 3, "weight": 20.0}
        prompt_adult = self.advisor._build_feeding_plan_prompt(adult_pet)
        self.assertIn("成年", prompt_adult)
        
        # 老宠
        old_pet = {"name": "老黄", "species": "dog", "breed": "金毛", "age": 10, "weight": 28.0}
        prompt_old = self.advisor._build_feeding_plan_prompt(old_pet)
        self.assertIn("老年", prompt_old)
    
    # ==================== 【F】集成测试 ====================
    
    def test_full_workflow_integration(self):
        """测试完整工作流程"""
        # 1. 分析喂养计划
        feeding = self.advisor.analyze_feeding_plan(self.dog_profile)
        self.assertTrue(len(feeding) > 0)
        
        # 2. 诊断症状
        diagnosis = self.advisor.diagnose_symptoms(self.dog_profile, "轻微咳嗽")
        self.assertTrue(len(diagnosis) > 0)
        
        # 3. 生成健康报告
        report = self.advisor.generate_health_report(self.dog_profile)
        self.assertTrue(len(report) > 0)
        
        # 验证所有调用都使用了 Mock
        self.assertEqual(self.mock_client_instance.send_request_stream.call_count, 3)


if __name__ == '__main__':
    unittest.main(verbosity=2)
