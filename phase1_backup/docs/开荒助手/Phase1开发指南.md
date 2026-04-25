# Phase 1 开发指南 - 宠物档案管理 + AI健康顾问

## 📋 当前阶段目标

**时间：** 第10-13周  
**任务：** 实现宠物档案管理和AI健康顾问两个核心模块  
**交付物：** 
- ✅ 可运行的Python程序
- ✅ 完整的单元测试
- ✅ 数据结构选型分析报告

---

## 🏗️ 项目结构

```
smart_pet_system/
├── data_structures/           # 数据结构实现
│   ├── __init__.py
│   ├── doubly_linked_list.py  # 双向链表
│   └── hash_table.py          # 哈希表封装
├── modules/                   # 业务模块
│   ├── __init__.py
│   └── pet_profile_manager.py # 宠物档案管理
├── ai_assistant/              # AI助手
│   ├── __init__.py
│   ├── pet_health_advisor.py  # AI健康顾问
│   └── prompts.py             # Prompt模板
├── tests/                     # 单元测试
│   ├── __init__.py
│   ├── test_doubly_linked_list.py
│   ├── test_hash_table.py
│   ├── test_pet_profile.py
│   └── test_ai_advisor.py
├── main.py                    # 主程序入口
├── requirements.txt           # 依赖列表（空，只用标准库）
└── README.md                  # 模块说明
```

---

## 🚀 快速开始

### **第1步：创建项目目录**

```powershell
cd f:\administrator\desktop\llm-test-trae
mkdir smart_pet_system
cd smart_pet_system

# 创建子目录
mkdir data_structures
mkdir modules
mkdir ai_assistant
mkdir tests

# 创建__init__.py文件
New-Item data_structures\__init__.py
New-Item modules\__init__.py
New-Item ai_assistant\__init__.py
New-Item tests\__init__.py
New-Item main.py
```

### **第2步：复制已有代码**

```powershell
# 复制LLM客户端
Copy-Item "..\practice03\chat_compress_client.py" "ai_assistant\"
Copy-Item "..\practice03\tools.py" "ai_assistant\"
```

---

## 📝 模块1：双向链表实现

### **文件：** `data_structures/doubly_linked_list.py`

```python
"""
双向链表实现 - 用于存储宠物健康记录时间线

作者：刘同学
日期：2026-04-15
课程：《数据结构》项目
"""


class HealthRecordNode:
    """健康记录节点"""
    
    def __init__(self, date, event_type, description, details=None):
        """
        初始化节点
        
        Args:
            date: 日期字符串 (YYYY-MM-DD)
            event_type: 事件类型 (vaccine/checkup/illness/feeding)
            description: 事件描述
            details: 详细信息字典（可选）
        """
        self.date = date
        self.event_type = event_type
        self.description = description
        self.details = details or {}
        self.prev = None
        self.next = None
    
    def __str__(self):
        return f"[{self.date}] {self.event_type}: {self.description}"


class DoublyLinkedList:
    """双向链表实现"""
    
    def __init__(self):
        """初始化空链表"""
        self.head = None
        self.tail = None
        self.size = 0
    
    def append(self, node):
        """
        在尾部添加节点（最新记录）
        
        时间复杂度：O(1)
        
        Args:
            node: HealthRecordNode对象
        """
        if not isinstance(node, HealthRecordNode):
            raise TypeError("必须传入HealthRecordNode对象")
        
        if not self.head:
            # 空链表
            self.head = self.tail = node
        else:
            # 非空链表，添加到尾部
            node.prev = self.tail
            self.tail.next = node
            self.tail = node
        
        self.size += 1
    
    def traverse_forward(self):
        """
        从前向后遍历（时间正序）
        
        时间复杂度：O(n)
        
        Returns:
            list: 包含所有记录的字典列表
        """
        records = []
        current = self.head
        while current:
            records.append({
                "date": current.date,
                "type": current.event_type,
                "desc": current.description,
                "details": current.details
            })
            current = current.next
        return records
    
    def traverse_backward(self, count=5):
        """
        从后向前遍历N个节点（查看最近记录）
        
        时间复杂度：O(count)
        
        Args:
            count: 要获取的记录数量
            
        Returns:
            list: 最近count条记录的字典列表
        """
        records = []
        current = self.tail
        while current and len(records) < count:
            records.append({
                "date": current.date,
                "type": current.event_type,
                "desc": current.description,
                "details": current.details
            })
            current = current.prev
        return records
    
    def delete_by_date(self, date):
        """
        删除指定日期的记录
        
        时间复杂度：O(n)
        
        Args:
            date: 要删除的日期字符串
            
        Returns:
            bool: 是否成功删除
        """
        current = self.head
        while current:
            if current.date == date:
                # 调整前驱节点的next指针
                if current.prev:
                    current.prev.next = current.next
                else:
                    # 删除的是头节点
                    self.head = current.next
                
                # 调整后继节点的prev指针
                if current.next:
                    current.next.prev = current.prev
                else:
                    # 删除的是尾节点
                    self.tail = current.prev
                
                self.size -= 1
                return True
            current = current.next
        return False
    
    def is_empty(self):
        """判断链表是否为空"""
        return self.size == 0
    
    def get_size(self):
        """获取链表大小"""
        return self.size
    
    def __str__(self):
        """字符串表示"""
        if self.is_empty():
            return "Empty Timeline"
        
        records = self.traverse_forward()
        lines = [f"Health Timeline ({self.size} records):"]
        for i, record in enumerate(records, 1):
            lines.append(f"  {i}. {record['date']} - {record['type']}: {record['desc']}")
        return "\n".join(lines)
```

---

## 📝 模块2：哈希表封装

### **文件：** `data_structures/hash_table.py`

```python
"""
哈希表封装 - 用于快速检索宠物档案

作者：刘同学
日期：2026-04-15
课程：《数据结构》项目
"""


class PetProfile:
    """宠物档案类"""
    
    def __init__(self, pet_id, name, breed, age, weight):
        """
        初始化宠物档案
        
        Args:
            pet_id: 宠物唯一ID
            name: 宠物名字
            breed: 品种
            age: 年龄（岁）
            weight: 体重（公斤）
        """
        self.pet_id = pet_id
        self.name = name
        self.breed = breed
        self.age = age
        self.weight = weight
        self.allergies = []  # 过敏源列表
        self.medications = []  # 药物清单
        self.health_timeline = None  # 关联的健康时间线（DoublyLinkedList）
    
    def __str__(self):
        return f"{self.name} ({self.breed}, {self.age}岁, {self.weight}kg)"


class PetProfileManager:
    """
    宠物档案管理器（基于字典实现的哈希表）
    
    Python的dict底层就是哈希表实现，提供O(1)的查找效率
    """
    
    def __init__(self):
        """初始化空的宠物档案管理器"""
        self.profiles = {}  # {pet_id: PetProfile}
    
    def add_pet(self, pet_profile):
        """
        添加宠物档案
        
        时间复杂度：O(1)
        
        Args:
            pet_profile: PetProfile对象
            
        Raises:
            ValueError: 如果pet_id已存在
        """
        if not isinstance(pet_profile, PetProfile):
            raise TypeError("必须传入PetProfile对象")
        
        if pet_profile.pet_id in self.profiles:
            raise ValueError(f"宠物ID {pet_profile.pet_id} 已存在")
        
        self.profiles[pet_profile.pet_id] = pet_profile
    
    def get_pet(self, pet_id):
        """
        快速获取宠物档案
        
        时间复杂度：O(1)
        
        Args:
            pet_id: 宠物ID
            
        Returns:
            PetProfile对象或None
        """
        return self.profiles.get(pet_id)
    
    def remove_pet(self, pet_id):
        """
        删除宠物档案
        
        时间复杂度：O(1)
        
        Args:
            pet_id: 宠物ID
            
        Returns:
            bool: 是否成功删除
        """
        if pet_id in self.profiles:
            del self.profiles[pet_id]
            return True
        return False
    
    def get_all_pets(self):
        """
        获取所有宠物档案
        
        时间复杂度：O(n)
        
        Returns:
            list: PetProfile对象列表
        """
        return list(self.profiles.values())
    
    def search_by_name(self, name):
        """
        按名字搜索宠物（线性扫描）
        
        时间复杂度：O(n)
        
        Args:
            name: 宠物名字（支持部分匹配）
            
        Returns:
            list: 匹配的PetProfile对象列表
        """
        results = []
        name_lower = name.lower()
        for pet in self.profiles.values():
            if name_lower in pet.name.lower():
                results.append(pet)
        return results
    
    def get_pet_count(self):
        """获取宠物数量"""
        return len(self.profiles)
    
    def is_empty(self):
        """判断是否为空"""
        return len(self.profiles) == 0
    
    def __str__(self):
        """字符串表示"""
        if self.is_empty():
            return "No pets registered"
        
        lines = [f"Registered Pets ({self.get_pet_count()}):"]
        for pet in self.profiles.values():
            lines.append(f"  - ID: {pet.pet_id}, {pet}")
        return "\n".join(lines)
```

---

## 📝 模块3：宠物档案管理主模块

### **文件：** `modules/pet_profile_manager.py`

```python
"""
宠物档案管理主模块

整合双向链表和哈希表，提供完整的宠物档案管理功能

作者：刘同学
日期：2026-04-15
课程：《数据结构》项目
"""

import sys
import os

# 添加父目录到路径，以便导入data_structures
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_structures.doubly_linked_list import DoublyLinkedList, HealthRecordNode
from data_structures.hash_table import PetProfile, PetProfileManager


class SmartPetProfileSystem:
    """
    智能宠物档案系统
    
    结合双向链表（健康记录）和哈希表（快速检索）
    """
    
    def __init__(self):
        """初始化系统"""
        self.profile_manager = PetProfileManager()
    
    def register_pet(self, pet_id, name, breed, age, weight):
        """
        注册新宠物
        
        Args:
            pet_id: 宠物ID
            name: 名字
            breed: 品种
            age: 年龄
            weight: 体重
            
        Returns:
            PetProfile对象
        """
        pet = PetProfile(pet_id, name, breed, age, weight)
        pet.health_timeline = DoublyLinkedList()  # 每个宠物有自己的健康时间线
        self.profile_manager.add_pet(pet)
        print(f"✓ 成功注册宠物：{pet}")
        return pet
    
    def add_health_record(self, pet_id, date, event_type, description, details=None):
        """
        添加健康记录
        
        Args:
            pet_id: 宠物ID
            date: 日期
            event_type: 事件类型
            description: 描述
            details: 详细信息
            
        Returns:
            bool: 是否成功
        """
        pet = self.profile_manager.get_pet(pet_id)
        if not pet:
            print(f"✗ 错误：找不到宠物ID {pet_id}")
            return False
        
        record = HealthRecordNode(date, event_type, description, details)
        pet.health_timeline.append(record)
        print(f"✓ 已为 {pet.name} 添加健康记录：{description}")
        return True
    
    def view_recent_records(self, pet_id, count=5):
        """
        查看最近的健康记录
        
        Args:
            pet_id: 宠物ID
            count: 记录数量
            
        Returns:
            list: 记录列表
        """
        pet = self.profile_manager.get_pet(pet_id)
        if not pet:
            print(f"✗ 错误：找不到宠物ID {pet_id}")
            return []
        
        records = pet.health_timeline.traverse_backward(count)
        print(f"\n{pet.name} 的最近{len(records)}条健康记录：")
        for i, record in enumerate(records, 1):
            print(f"  {i}. [{record['date']}] {record['type']}: {record['desc']}")
        
        return records
    
    def view_full_timeline(self, pet_id):
        """
        查看完整健康时间线
        
        Args:
            pet_id: 宠物ID
            
        Returns:
            list: 完整记录列表
        """
        pet = self.profile_manager.get_pet(pet_id)
        if not pet:
            print(f"✗ 错误：找不到宠物ID {pet_id}")
            return []
        
        print(f"\n{pet.name} 的完整健康时间线：")
        print(pet.health_timeline)
        
        return pet.health_timeline.traverse_forward()
    
    def search_pets(self, keyword):
        """
        搜索宠物
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            list: 匹配的宠物列表
        """
        results = self.profile_manager.search_by_name(keyword)
        if results:
            print(f"\n找到 {len(results)} 只匹配的宠物：")
            for pet in results:
                print(f"  - {pet}")
        else:
            print(f"未找到名字包含 '{keyword}' 的宠物")
        
        return results
    
    def show_all_pets(self):
        """显示所有宠物"""
        print(f"\n{self.profile_manager}")
    
    def remove_pet(self, pet_id):
        """
        删除宠物
        
        Args:
            pet_id: 宠物ID
            
        Returns:
            bool: 是否成功
        """
        success = self.profile_manager.remove_pet(pet_id)
        if success:
            print(f"✓ 已删除宠物ID {pet_id}")
        else:
            print(f"✗ 错误：找不到宠物ID {pet_id}")
        return success
```

---

## 📝 模块4：AI健康顾问

### **文件：** `ai_assistant/pet_health_advisor.py`

```python
"""
AI宠物健康顾问

集成LLM客户端，提供智能化健康建议

作者：刘同学
日期：2026-04-15
课程：《数据结构》项目
"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_assistant.chat_compress_client import ChatCompressClient
from data_structures.hash_table import PetProfile


class PetHealthAdvisor:
    """宠物健康AI顾问"""
    
    def __init__(self):
        """初始化AI顾问"""
        self.llm_client = ChatCompressClient()
        print("✓ AI健康顾问已初始化")
    
    def analyze_feeding_plan(self, pet_profile, current_plan):
        """
        分析喂食计划是否合理
        
        Args:
            pet_profile: PetProfile对象
            current_plan: 当前喂食计划描述
            
        Returns:
            str: AI分析结果
        """
        prompt = f"""请分析以下宠物的喂食计划是否科学：

宠物信息：
- 名字：{pet_profile.name}
- 品种：{pet_profile.breed}
- 年龄：{pet_profile.age}岁
- 体重：{pet_profile.weight}公斤

当前喂食计划：
{current_plan}

请给出：
1. 喂食次数是否合理
2. 每次份量是否合适
3. 营养搭配建议
4. 需要注意的事项

请用中文回答，控制在300字以内。"""
        
        print(f"\n[AI分析] 正在分析 {pet_profile.name} 的喂食计划...")
        response = self.llm_client.send_request(prompt)
        return response
    
    def diagnose_symptoms(self, pet_profile, symptoms):
        """
        根据症状初步诊断
        
        Args:
            pet_profile: PetProfile对象
            symptoms: 症状描述
            
        Returns:
            str: AI诊断建议
        """
        prompt = f"""宠物出现以下症状，请给出专业建议：

宠物信息：
- 品种：{pet_profile.breed}
- 年龄：{pet_profile.age}岁

症状描述：
{symptoms}

请给出：
1. 可能的原因（列出3种可能性）
2. 紧急程度评估（紧急/一般/观察）
3. 家庭护理建议
4. 是否需要立即就医

注意：这只是AI初步建议，不能替代兽医诊断。

请用中文回答，控制在400字以内。"""
        
        print(f"\n[AI诊断] 正在分析 {pet_profile.name} 的症状...")
        response = self.llm_client.send_request(prompt)
        return response
    
    def recommend_supplements(self, pet_profile):
        """
        推荐保健品
        
        Args:
            pet_profile: PetProfile对象
            
        Returns:
            str: AI推荐结果
        """
        prompt = f"""根据以下宠物信息，推荐适合的保健品：

- 品种：{pet_profile.breed}
- 年龄：{pet_profile.age}岁
- 体重：{pet_profile.weight}公斤

请推荐：
1. 适合该年龄段的基础保健品
2. 针对该品种的特殊需求
3. 服用方法和剂量
4. 注意事项

注意：仅推送信息，不自动添加到喂食器。

请用中文回答，控制在300字以内。"""
        
        print(f"\n[AI推荐] 正在为 {pet_profile.name} 推荐保健品...")
        response = self.llm_client.send_request(prompt)
        return response
    
    def generate_care_guide(self, pet_profile):
        """
        生成护理指南
        
        Args:
            pet_profile: PetProfile对象
            
        Returns:
            str: AI生成的护理指南
        """
        prompt = f"""为以下宠物生成全面的护理指南：

- 品种：{pet_profile.breed}
- 年龄：{pet_profile.age}岁
- 体重：{pet_profile.weight}公斤

请包括：
1. 日常护理要点
2. 饮食建议
3. 运动需求
4. 常见疾病预防
5. 季节性注意事项

请用中文回答，控制在500字以内。"""
        
        print(f"\n[AI指南] 正在为 {pet_profile.name} 生成护理指南...")
        response = self.llm_client.send_request(prompt)
        return response
```

---

## 🎮 主程序入口

### **文件：** `main.py`

```python
"""
智能宠物喂食管理系统 - 主程序

Phase 1: 宠物档案管理 + AI健康顾问

作者：刘同学
日期：2026-04-15
课程：《数据结构》项目
"""

import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.pet_profile_manager import SmartPetProfileSystem
from ai_assistant.pet_health_advisor import PetHealthAdvisor


def show_menu():
    """显示主菜单"""
    print("\n" + "="*60)
    print("  智能宠物喂食管理系统 - Phase 1")
    print("="*60)
    print("1. 注册新宠物")
    print("2. 查看所有宠物")
    print("3. 搜索宠物")
    print("4. 添加健康记录")
    print("5. 查看最近健康记录")
    print("6. 查看完整健康时间线")
    print("7. AI分析喂食计划")
    print("8. AI症状诊断")
    print("9. AI推荐保健品")
    print("10. AI生成护理指南")
    print("0. 退出")
    print("="*60)


def main():
    """主函数"""
    system = SmartPetProfileSystem()
    advisor = PetHealthAdvisor()
    
    print("\n欢迎使用智能宠物喂食管理系统！")
    print("提示：先注册宠物，然后可以添加健康记录和使用AI功能\n")
    
    while True:
        show_menu()
        choice = input("\n请选择操作 (0-10): ").strip()
        
        if choice == '0':
            print("\n感谢使用，再见！👋")
            break
        
        elif choice == '1':
            # 注册新宠物
            pet_id = input("请输入宠物ID: ").strip()
            name = input("请输入宠物名字: ").strip()
            breed = input("请输入品种: ").strip()
            age = float(input("请输入年龄（岁）: ").strip())
            weight = float(input("请输入体重（公斤）: ").strip())
            
            try:
                system.register_pet(pet_id, name, breed, age, weight)
            except ValueError as e:
                print(f"错误：{e}")
        
        elif choice == '2':
            # 查看所有宠物
            system.show_all_pets()
        
        elif choice == '3':
            # 搜索宠物
            keyword = input("请输入搜索关键词: ").strip()
            system.search_pets(keyword)
        
        elif choice == '4':
            # 添加健康记录
            pet_id = input("请输入宠物ID: ").strip()
            date = input("请输入日期 (YYYY-MM-DD): ").strip()
            print("事件类型：vaccine(疫苗) / checkup(体检) / illness(生病) / feeding(喂食)")
            event_type = input("请输入事件类型: ").strip()
            description = input("请输入描述: ").strip()
            
            system.add_health_record(pet_id, date, event_type, description)
        
        elif choice == '5':
            # 查看最近健康记录
            pet_id = input("请输入宠物ID: ").strip()
            count = int(input("要查看几条记录？(默认5): ").strip() or "5")
            system.view_recent_records(pet_id, count)
        
        elif choice == '6':
            # 查看完整健康时间线
            pet_id = input("请输入宠物ID: ").strip()
            system.view_full_timeline(pet_id)
        
        elif choice == '7':
            # AI分析喂食计划
            pet_id = input("请输入宠物ID: ").strip()
            pet = system.profile_manager.get_pet(pet_id)
            if not pet:
                print(f"错误：找不到宠物ID {pet_id}")
                continue
            
            plan = input("请输入当前喂食计划（如：每天2次，每次50克）: ").strip()
            result = advisor.analyze_feeding_plan(pet, plan)
            print(f"\n{result}")
        
        elif choice == '8':
            # AI症状诊断
            pet_id = input("请输入宠物ID: ").strip()
            pet = system.profile_manager.get_pet(pet_id)
            if not pet:
                print(f"错误：找不到宠物ID {pet_id}")
                continue
            
            symptoms = input("请描述症状: ").strip()
            result = advisor.diagnose_symptoms(pet, symptoms)
            print(f"\n{result}")
        
        elif choice == '9':
            # AI推荐保健品
            pet_id = input("请输入宠物ID: ").strip()
            pet = system.profile_manager.get_pet(pet_id)
            if not pet:
                print(f"错误：找不到宠物ID {pet_id}")
                continue
            
            result = advisor.recommend_supplements(pet)
            print(f"\n{result}")
        
        elif choice == '10':
            # AI生成护理指南
            pet_id = input("请输入宠物ID: ").strip()
            pet = system.profile_manager.get_pet(pet_id)
            if not pet:
                print(f"错误：找不到宠物ID {pet_id}")
                continue
            
            result = advisor.generate_care_guide(pet)
            print(f"\n{result}")
        
        else:
            print("无效选择，请重新输入")


if __name__ == "__main__":
    main()
```

---

## ✅ 下一步行动

### **本周任务（第10周）**
1. ✅ 创建项目目录结构
2. ✅ 实现双向链表（doubly_linked_list.py）
3. ✅ 实现哈希表封装（hash_table.py）
4. ✅ 编写单元测试

### **下周任务（第11周）**
1. ✅ 实现宠物档案管理模块
2. ✅ 集成AI健康顾问
3. ✅ 完成主程序
4. ✅ 端到端测试

---

**加油！你可以的！** 💪
