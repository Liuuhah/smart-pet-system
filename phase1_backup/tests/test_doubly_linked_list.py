"""
双向链表单元测试

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

from data_structures.doubly_linked_list import HealthRecordNode, DoublyLinkedList


class TestHealthRecordNode(unittest.TestCase):
    """健康记录节点测试"""
    
    def test_create_node_success(self):
        """测试正常创建节点"""
        node = HealthRecordNode("2026-04-15", "vaccine", "接种狂犬疫苗", "medium")
        
        self.assertEqual(node.date, "2026-04-15")
        self.assertEqual(node.event_type, "vaccine")
        self.assertEqual(node.description, "接种狂犬疫苗")
        self.assertEqual(node.severity, "medium")
        self.assertIsNotNone(node.record_id)
        self.assertIsInstance(node.details, dict)
        self.assertEqual(node.details, {})
    
    def test_create_node_with_details(self):
        """测试创建带详细信息的节点"""
        details = {"hospital": "爱心宠物医院", "vet_name": "张医生"}
        node = HealthRecordNode("2026-04-15", "checkup", "体检", "low", details)
        
        self.assertEqual(node.details["hospital"], "爱心宠物医院")
        self.assertEqual(node.details["vet_name"], "张医生")
    
    def test_date_validation_valid(self):
        """测试有效日期格式"""
        valid_dates = [
            "2026-04-15",
            "2026-01-01",
            "2026-12-31",
            "2000-02-29"  # 闰年
        ]
        
        for date in valid_dates:
            node = HealthRecordNode(date, "test", "测试")
            self.assertEqual(node.date, date)
    
    def test_date_validation_invalid_format(self):
        """测试无效日期格式"""
        invalid_dates = [
            "2026/04/15",
            "20260415",
            "04-15-2026",
            "2026-4-15",
            "not-a-date"
        ]
        
        for date in invalid_dates:
            with self.assertRaises(ValueError):
                HealthRecordNode(date, "test", "测试")
    
    def test_date_validation_invalid_date(self):
        """测试不存在的日期"""
        invalid_dates = [
            "2026-13-01",  # 13月
            "2026-04-31",  # 4月31日
            "2026-02-30",  # 2月30日
            "2026-00-15"   # 0月
        ]
        
        for date in invalid_dates:
            with self.assertRaises(ValueError):
                HealthRecordNode(date, "test", "测试")
    
    def test_severity_validation(self):
        """测试严重程度校验"""
        # 有效值
        for severity in ["low", "medium", "high", "critical"]:
            node = HealthRecordNode("2026-04-15", "test", "测试", severity)
            self.assertEqual(node.severity, severity)
        
        # 无效值
        with self.assertRaises(ValueError):
            HealthRecordNode("2026-04-15", "test", "测试", "invalid")
    
    def test_details_isolation(self):
        """测试 details 字典隔离"""
        shared_details = {"hospital": "测试医院"}
        node1 = HealthRecordNode("2026-04-15", "test", "测试1", details=shared_details)
        node2 = HealthRecordNode("2026-04-16", "test", "测试2", details=shared_details)
        
        # 修改 node1 的 details
        node1.details["vet"] = "张医生"
        
        # node2 不应受影响
        self.assertNotIn("vet", node2.details)
        # 原始字典也不应受影响
        self.assertNotIn("vet", shared_details)
    
    def test_node_string_representation(self):
        """测试节点的字符串表示"""
        node = HealthRecordNode("2026-04-15", "vaccine", "接种狂犬疫苗", "medium")
        str_repr = str(node)
        
        self.assertIn("2026-04-15", str_repr)
        self.assertIn("vaccine", str_repr)
        self.assertIn("接种狂犬疫苗", str_repr)
        self.assertIn("medium", str_repr)
    
    def test_node_default_severity(self):
        """测试默认严重程度为 low"""
        node = HealthRecordNode("2026-04-15", "test", "测试")
        self.assertEqual(node.severity, "low")


class TestDoublyLinkedList(unittest.TestCase):
    """双向链表测试"""
    
    def setUp(self):
        """每个测试前的准备工作"""
        self.timeline = DoublyLinkedList()
        
        # 创建测试数据
        self.test_records = [
            ("2026-01-15", "vaccine", "接种狂犬疫苗", "medium"),
            ("2026-02-20", "checkup", "常规体检", "low"),
            ("2026-03-10", "illness", "感冒发烧", "high"),
        ]
    
    def test_empty_list(self):
        """测试空链表"""
        self.assertTrue(self.timeline.is_empty())
        self.assertEqual(self.timeline.get_size(), 0)
        self.assertIsNone(self.timeline.head)
        self.assertIsNone(self.timeline.tail)
    
    def test_append_single_node(self):
        """测试添加单个节点"""
        node = HealthRecordNode("2026-04-15", "test", "测试")
        self.timeline.append(node)
        
        self.assertFalse(self.timeline.is_empty())
        self.assertEqual(self.timeline.get_size(), 1)
        self.assertEqual(self.timeline.head, node)
        self.assertEqual(self.timeline.tail, node)
        self.assertIsNone(node.prev)
        self.assertIsNone(node.next)
    
    def test_append_multiple_nodes(self):
        """测试添加多个节点"""
        for date, event_type, desc, severity in self.test_records:
            node = HealthRecordNode(date, event_type, desc, severity)
            self.timeline.append(node)
        
        self.assertEqual(self.timeline.get_size(), 3)
        
        # 验证链表连接
        self.assertIsNone(self.timeline.head.prev)
        self.assertIsNone(self.timeline.tail.next)
        
        # 验证指针关系
        current = self.timeline.head
        count = 0
        while current:
            count += 1
            if current.next:
                self.assertEqual(current.next.prev, current)
            current = current.next
        
        self.assertEqual(count, 3)
    
    def test_append_invalid_type(self):
        """测试添加非节点类型"""
        with self.assertRaises(TypeError):
            self.timeline.append("不是节点")
        
        with self.assertRaises(TypeError):
            self.timeline.append(123)
    
    def test_traverse_forward(self):
        """测试正向遍历"""
        for date, event_type, desc, severity in self.test_records:
            node = HealthRecordNode(date, event_type, desc, severity)
            self.timeline.append(node)
        
        records = self.timeline.traverse_forward()
        
        self.assertEqual(len(records), 3)
        # 验证顺序（从早到晚）
        self.assertEqual(records[0]["date"], "2026-01-15")
        self.assertEqual(records[1]["date"], "2026-02-20")
        self.assertEqual(records[2]["date"], "2026-03-10")
    
    def test_traverse_forward_empty(self):
        """测试空链表正向遍历"""
        records = self.timeline.traverse_forward()
        self.assertEqual(records, [])
    
    def test_traverse_backward(self):
        """测试反向遍历"""
        for date, event_type, desc, severity in self.test_records:
            node = HealthRecordNode(date, event_type, desc, severity)
            self.timeline.append(node)
        
        # 获取最近 2 条
        records = self.timeline.traverse_backward(2)
        
        self.assertEqual(len(records), 2)
        # 验证顺序（从新到旧）
        self.assertEqual(records[0]["date"], "2026-03-10")
        self.assertEqual(records[1]["date"], "2026-02-20")
    
    def test_traverse_backward_count_exceeds_size(self):
        """测试 count 超过链表长度"""
        for date, event_type, desc, severity in self.test_records:
            node = HealthRecordNode(date, event_type, desc, severity)
            self.timeline.append(node)
        
        # 请求 10 条，实际只有 3 条
        records = self.timeline.traverse_backward(10)
        
        self.assertEqual(len(records), 3)
    
    def test_traverse_backward_zero_or_negative(self):
        """测试 count 为 0 或负数"""
        for date, event_type, desc, severity in self.test_records:
            node = HealthRecordNode(date, event_type, desc, severity)
            self.timeline.append(node)
        
        self.assertEqual(self.timeline.traverse_backward(0), [])
        self.assertEqual(self.timeline.traverse_backward(-1), [])
    
    def test_delete_by_record_id_success(self):
        """测试删除存在的记录"""
        nodes = []
        for date, event_type, desc, severity in self.test_records:
            node = HealthRecordNode(date, event_type, desc, severity)
            self.timeline.append(node)
            nodes.append(node)
        
        # 删除中间节点
        target_id = nodes[1].record_id
        result = self.timeline.delete_by_record_id(target_id)
        
        self.assertTrue(result)
        self.assertEqual(self.timeline.get_size(), 2)
        
        # 验证链表连接正确
        self.assertEqual(self.timeline.head.next, self.timeline.tail)
        self.assertEqual(self.timeline.tail.prev, self.timeline.head)
    
    def test_delete_head_node(self):
        """测试删除头节点"""
        nodes = []
        for date, event_type, desc, severity in self.test_records:
            node = HealthRecordNode(date, event_type, desc, severity)
            self.timeline.append(node)
            nodes.append(node)
        
        old_head_id = nodes[0].record_id
        result = self.timeline.delete_by_record_id(old_head_id)
        
        self.assertTrue(result)
        self.assertEqual(self.timeline.get_size(), 2)
        self.assertNotEqual(self.timeline.head.record_id, old_head_id)
        self.assertIsNone(self.timeline.head.prev)
    
    def test_delete_tail_node(self):
        """测试删除尾节点"""
        nodes = []
        for date, event_type, desc, severity in self.test_records:
            node = HealthRecordNode(date, event_type, desc, severity)
            self.timeline.append(node)
            nodes.append(node)
        
        old_tail_id = nodes[2].record_id
        result = self.timeline.delete_by_record_id(old_tail_id)
        
        self.assertTrue(result)
        self.assertEqual(self.timeline.get_size(), 2)
        self.assertNotEqual(self.timeline.tail.record_id, old_tail_id)
        self.assertIsNone(self.timeline.tail.next)
    
    def test_delete_only_node(self):
        """测试删除唯一节点"""
        node = HealthRecordNode("2026-04-15", "test", "测试")
        self.timeline.append(node)
        
        result = self.timeline.delete_by_record_id(node.record_id)
        
        self.assertTrue(result)
        self.assertEqual(self.timeline.get_size(), 0)
        self.assertIsNone(self.timeline.head)
        self.assertIsNone(self.timeline.tail)
        self.assertTrue(self.timeline.is_empty())
    
    def test_delete_nonexistent_id(self):
        """测试删除不存在的 ID"""
        node = HealthRecordNode("2026-04-15", "test", "测试")
        self.timeline.append(node)
        
        result = self.timeline.delete_by_record_id("nonexistent_id")
        
        self.assertFalse(result)
        self.assertEqual(self.timeline.get_size(), 1)
    
    def test_find_by_date(self):
        """测试按日期查找"""
        # 添加两条相同日期的记录
        node1 = HealthRecordNode("2026-04-15", "vaccine", "疫苗1")
        node2 = HealthRecordNode("2026-04-15", "checkup", "体检")
        node3 = HealthRecordNode("2026-04-16", "feeding", "喂食")
        
        self.timeline.append(node1)
        self.timeline.append(node2)
        self.timeline.append(node3)
        
        results = self.timeline.find_by_date("2026-04-15")
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["type"], "vaccine")
        self.assertEqual(results[1]["type"], "checkup")
    
    def test_find_by_type(self):
        """测试按类型查找"""
        for date, event_type, desc, severity in self.test_records:
            node = HealthRecordNode(date, event_type, desc, severity)
            self.timeline.append(node)
        
        results = self.timeline.find_by_type("vaccine")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["type"], "vaccine")
    
    def test_find_by_date_range(self):
        """测试按时间范围查找"""
        for date, event_type, desc, severity in self.test_records:
            node = HealthRecordNode(date, event_type, desc, severity)
            self.timeline.append(node)
        
        results = self.timeline.find_by_date_range("2026-02-01", "2026-03-31")
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["date"], "2026-02-20")
        self.assertEqual(results[1]["date"], "2026-03-10")
    
    def test_find_by_severity(self):
        """测试按严重程度查找"""
        for date, event_type, desc, severity in self.test_records:
            node = HealthRecordNode(date, event_type, desc, severity)
            self.timeline.append(node)
        
        results = self.timeline.find_by_severity("high")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["severity"], "high")
    
    def test_clear(self):
        """测试清空链表"""
        for date, event_type, desc, severity in self.test_records:
            node = HealthRecordNode(date, event_type, desc, severity)
            self.timeline.append(node)
        
        self.timeline.clear()
        
        self.assertTrue(self.timeline.is_empty())
        self.assertEqual(self.timeline.get_size(), 0)
        self.assertIsNone(self.timeline.head)
        self.assertIsNone(self.timeline.tail)
    
    def test_string_representation(self):
        """测试字符串表示"""
        node = HealthRecordNode("2026-04-15", "test", "测试")
        self.timeline.append(node)
        
        str_repr = str(self.timeline)
        
        self.assertIn("1 条记录", str_repr)
        self.assertIn("2026-04-15", str_repr)
        self.assertIn("test", str_repr)
    
    def test_empty_string_representation(self):
        """测试空链表的字符串表示"""
        str_repr = str(self.timeline)
        self.assertIn("暂无记录", str_repr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
