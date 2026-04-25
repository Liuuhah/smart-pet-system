# Phase 2 & 3 备选模块设计文档

## 📋 说明

本文档记录了**暂不实现**但**未来可扩展**的模块设计。  
这些模块已设计好数据结构和接口，可以在后续阶段快速实现。

---

## ⏳ Phase 2：待实现模块（下学期或毕业后）

### **模块3：智能喂食调度系统**

#### **功能描述**
- 定时喂食任务管理
- 多宠物喂食计划协调
- 任务优先级调度
- 执行日志记录

#### **数据结构选型**

**1. 最小堆 - 喂食任务优先队列**

```python
import heapq
from datetime import datetime


class FeedingTask:
    """喂食任务（用于优先队列）"""
    
    def __init__(self, timestamp, pet_id, food_type, portion, task_id):
        self.timestamp = timestamp      # 执行时间戳
        self.pet_id = pet_id            # 宠物ID
        self.food_type = food_type      # main/snack/supplement
        self.portion = portion          # 份量（克）
        self.task_id = task_id          # 任务唯一ID
        self.status = "pending"         # pending/executed/cancelled
    
    def __lt__(self, other):
        """堆比较依据（按时间戳）"""
        return self.timestamp < other.timestamp
    
    def __str__(self):
        from datetime import datetime
        time_str = datetime.fromtimestamp(self.timestamp).strftime("%Y-%m-%d %H:%M")
        return f"[{time_str}] {self.pet_id}: {self.food_type} {self.portion}g"


class SmartFeedingScheduler:
    """智能喂食调度器（最小堆 + BST）"""
    
    def __init__(self):
        # 最小堆：按时间排序的待执行任务
        self.task_queue = []
        
        # BST：每个宠物的喂食计划树
        self.pet_schedules = {}  # {pet_id: FeedingPlanBST}
        
        # 哈希表：快速查找任务
        self.task_map = {}  # {task_id: FeedingTask}
        
        # 计数器：生成唯一任务ID
        self.task_counter = 0
    
    def add_feeding_plan(self, pet_id, schedule_list):
        """
        添加喂食计划
        
        Args:
            pet_id: 宠物ID
            schedule_list: [(time_str, food_type, portion), ...]
                          例如：[("08:00", "main", 50), ("18:00", "main", 50)]
        """
        if pet_id not in self.pet_schedules:
            self.pet_schedules[pet_id] = FeedingPlanBST()
        
        for time_str, food_type, portion in schedule_list:
            timestamp = self._time_to_timestamp(time_str)
            self.pet_schedules[pet_id].insert(timestamp, food_type, portion)
            self._schedule_task(pet_id, timestamp, food_type, portion)
    
    def _schedule_task(self, pet_id, timestamp, food_type, portion):
        """将喂食任务加入优先队列"""
        self.task_counter += 1
        task = FeedingTask(
            timestamp=timestamp,
            pet_id=pet_id,
            food_type=food_type,
            portion=portion,
            task_id=f"task_{self.task_counter}"
        )
        
        heapq.heappush(self.task_queue, task)
        self.task_map[task.task_id] = task
    
    def get_next_feeding_tasks(self, count=5):
        """获取接下来N个喂食任务（O(log n)）"""
        next_tasks = []
        temp_queue = list(self.task_queue)
        
        for _ in range(min(count, len(temp_queue))):
            if temp_queue:
                task = heapq.heappop(temp_queue)
                if task.status == "pending":
                    next_tasks.append(task)
        
        return next_tasks
    
    def execute_feeding(self, task_id):
        """执行喂食任务（模拟硬件操作）"""
        if task_id not in self.task_map:
            return False
        
        task = self.task_map[task_id]
        if task.status != "pending":
            return False
        
        print(f"[硬件模拟] 为宠物{task.pet_id}喂食：")
        print(f"  - 食物类型：{task.food_type}")
        print(f"  - 份量：{task.portion}克")
        
        task.status = "executed"
        return True
    
    def _time_to_timestamp(self, time_str):
        """将"HH:MM"转换为今日时间戳"""
        today = datetime.now().strftime("%Y-%m-%d")
        dt = datetime.strptime(f"{today} {time_str}", "%Y-%m-%d %H:%M")
        return dt.timestamp()
```

**选型理由：**
- ✅ 总是取出最近的喂食任务（最小时间戳）
- ✅ 动态插入/删除任务，堆效率O(log n)
- ✅ 实时性要求高，不能延迟

---

**2. BST - 喂食计划管理**

```python
class FeedingPlanBSTNode:
    """喂食计划BST节点"""
    
    def __init__(self, timestamp, food_type, portion):
        self.timestamp = timestamp
        self.food_type = food_type
        self.portion = portion
        self.left = None
        self.right = None


class FeedingPlanBST:
    """喂食计划二叉搜索树（按时间排序）"""
    
    def __init__(self):
        self.root = None
    
    def insert(self, timestamp, food_type, portion):
        """插入喂食计划 O(log n)"""
        new_node = FeedingPlanBSTNode(timestamp, food_type, portion)
        
        if not self.root:
            self.root = new_node
            return
        
        current = self.root
        while True:
            if timestamp < current.timestamp:
                if current.left is None:
                    current.left = new_node
                    break
                current = current.left
            else:
                if current.right is None:
                    current.right = new_node
                    break
                current = current.right
    
    def get_range(self, start_time, end_time):
        """查询时间段内的喂食计划（范围查询）O(k + log n)"""
        result = []
        self._inorder_range(self.root, start_time, end_time, result)
        return result
    
    def _inorder_range(self, node, start, end, result):
        """中序遍历获取范围内的节点"""
        if node is None:
            return
        
        if node.timestamp > start:
            self._inorder_range(node.left, start, end, result)
        
        if start <= node.timestamp <= end:
            result.append({
                "time": node.timestamp,
                "food_type": node.food_type,
                "portion": node.portion
            })
        
        if node.timestamp < end:
            self._inorder_range(node.right, start, end, result)
```

**选型理由：**
- ✅ 支持范围查询（如"查询本周的喂食计划"）
- ✅ 有序存储，便于展示时间线
- ✅ 平衡BST保证O(log n)操作

---

#### **核心代码文件（待创建）**
```
smart_pet_system/
├── data_structures/
│   ├── min_heap.py            # 最小堆实现
│   └── bst.py                 # 二叉搜索树实现
├── modules/
│   └── feeding_scheduler.py   # 喂食调度主模块
└── tests/
    └── test_feeding_scheduler.py
```

---

### **模块4：食物库存管理系统**

#### **功能描述**
- 食物余量监测
- 低库存提醒
- 补货历史记录
- 消耗统计

#### **数据结构选型**

**栈 - 补货历史记录**

```python
from datetime import datetime


class FoodInventory:
    """食物库存管理（栈结构）"""
    
    def __init__(self, capacity=1000):  # 容量：克
        self.capacity = capacity
        self.current_stock = 0
        self.refill_history = []  # 补货历史（栈）
    
    def refill(self, amount, food_type="main"):
        """
        补货（压栈）
        
        时间复杂度：O(1)
        """
        if self.current_stock + amount > self.capacity:
            raise ValueError(f"库存溢出！当前{self.current_stock}g，尝试添加{amount}g")
        
        self.current_stock += amount
        self.refill_history.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "amount": amount,
            "food_type": food_type,
            "total_after": self.current_stock
        })
        
        print(f"[库存] 补货{amount}g {food_type}，当前库存：{self.current_stock}g")
    
    def consume(self, amount):
        """
        消耗食物
        
        时间复杂度：O(1)
        """
        if amount > self.current_stock:
            raise ValueError(f"库存不足！需要{amount}g，当前{self.current_stock}g")
        
        self.current_stock -= amount
        
        # 检查是否需要提醒补货
        if self.current_stock < self.capacity * 0.2:  # 低于20%
            print(f"[警告] 库存不足20%！当前：{self.current_stock}g")
            return "low_stock_warning"
        
        return "ok"
    
    def get_stock_level(self):
        """获取库存水平 O(1)"""
        percentage = (self.current_stock / self.capacity) * 100
        return {
            "current": self.current_stock,
            "capacity": self.capacity,
            "percentage": percentage,
            "status": "low" if percentage < 20 else "normal"
        }
    
    def get_refill_history(self, count=10):
        """获取最近N次补货记录（栈顶N个）O(1)"""
        return self.refill_history[-count:]
```

**选型理由：**
- ✅ 补货记录是LIFO场景（最近的最重要）
- ✅ 用户通常只关心最近几次补货
- ✅ push/pop都是O(1)，效率最高

---

#### **核心代码文件（待创建）**
```
smart_pet_system/
├── data_structures/
│   └── stack.py                 # 栈实现（可选，可用list代替）
├── modules/
│   └── food_inventory.py        # 库存管理主模块
└── tests/
    └── test_food_inventory.py
```

---

## 🔮 Phase 3：未来扩展模块（商业化阶段）

### **模块5：宠物社交网络**

#### **功能描述**
- 宠物交友匹配
- 附近宠物发现
- 线下聚会组织
- 经验分享社区

#### **数据结构选型**

**图结构 - 社交关系网络**

```python
from collections import deque


class PetSocialGraph:
    """宠物社交图（邻接表实现）"""
    
    def __init__(self):
        self.graph = {}  # {pet_id: [(friend_id, friendship_level)]}
    
    def add_friendship(self, pet1, pet2, level=1):
        """
        添加宠物友谊关系
        
        Args:
            pet1: 宠物1 ID
            pet2: 宠物2 ID
            level: 友谊等级（1-5）
        """
        if pet1 not in self.graph:
            self.graph[pet1] = []
        if pet2 not in self.graph:
            self.graph[pet2] = []
        
        self.graph[pet1].append((pet2, level))
        self.graph[pet2].append((pet1, level))  # 无向图
    
    def find_nearby_pets(self, pet_id, max_distance=3):
        """
        BFS查找附近N度以内的宠物朋友
        
        时间复杂度：O(V + E)
        
        Args:
            pet_id: 起始宠物ID
            max_distance: 最大搜索距离
            
        Returns:
            list: 附近的宠物ID列表
        """
        if pet_id not in self.graph:
            return []
        
        visited = set()
        queue = deque([(pet_id, 0)])
        nearby = []
        
        while queue:
            current, distance = queue.popleft()
            
            if distance > max_distance:
                break
            
            if current not in visited:
                visited.add(current)
                if current != pet_id:  # 不包括自己
                    nearby.append(current)
                
                for friend, _ in self.graph.get(current, []):
                    if friend not in visited:
                        queue.append((friend, distance + 1))
        
        return nearby
    
    def recommend_friends(self, pet_id, min_common_friends=2):
        """
        基于共同好友推荐新朋友
        
        Args:
            pet_id: 宠物ID
            min_common_friends: 最少共同好友数
            
        Returns:
            dict: {recommended_pet_id: common_friends_count}
        """
        if pet_id not in self.graph:
            return {}
        
        # 获取直接好友
        direct_friends = set(friend for friend, _ in self.graph[pet_id])
        
        # 统计二度好友的共同好友数
        friend_of_friend_count = {}
        for friend in direct_friends:
            for foaf, _ in self.graph.get(friend, []):
                if foaf != pet_id and foaf not in direct_friends:
                    friend_of_friend_count[foaf] = friend_of_friend_count.get(foaf, 0) + 1
        
        # 过滤出共同好友数足够的
        recommendations = {
            pet: count 
            for pet, count in friend_of_friend_count.items() 
            if count >= min_common_friends
        }
        
        # 按共同好友数排序
        return dict(sorted(recommendations.items(), key=lambda x: x[1], reverse=True))
```

**选型理由：**
- ✅ 社交关系天然适合用图表示
- ✅ BFS算法查找"朋友的朋友"效率高
- ✅ 邻接表适合稀疏图（宠物社交网络通常稀疏）

---

#### **核心代码文件（待创建）**
```
smart_pet_system/
├── data_structures/
│   └── graph.py                 # 图结构实现
├── modules/
│   └── pet_social_network.py    # 社交网络主模块
└── tests/
    └── test_social_network.py
```

---

### **模块6：硬件通信模块**

#### **功能描述**
- 连接真实智能喂食器
- 远程控制喂食/喂水
- 设备状态监控
- OTA固件升级

#### **技术方案**

**方案A：MQTT协议（推荐）**
```python
import paho.mqtt.client as mqtt


class HardwareController:
    """硬件控制器（MQTT）"""
    
    def __init__(self, broker="localhost", port=1883):
        self.client = mqtt.Client()
        self.client.connect(broker, port)
    
    def send_feeding_command(self, device_id, pet_id, portion):
        """发送喂食命令"""
        topic = f"devices/{device_id}/commands"
        payload = {
            "action": "feed",
            "pet_id": pet_id,
            "portion": portion
        }
        self.client.publish(topic, json.dumps(payload))
    
    def subscribe_device_status(self, device_id, callback):
        """订阅设备状态"""
        topic = f"devices/{device_id}/status"
        self.client.subscribe(topic)
        self.client.on_message = callback
```

**方案B：HTTP API**
```python
import requests


class HardwareAPI:
    """硬件API控制器"""
    
    def __init__(self, base_url="http://feeder.local/api"):
        self.base_url = base_url
    
    def trigger_feeding(self, device_id, portion):
        """触发喂食"""
        url = f"{self.base_url}/devices/{device_id}/feed"
        response = requests.post(url, json={"portion": portion})
        return response.json()
    
    def get_device_status(self, device_id):
        """获取设备状态"""
        url = f"{self.base_url}/devices/{device_id}/status"
        response = requests.get(url)
        return response.json()
```

---

## 📊 模块依赖关系图

```
Phase 1 (已完成)
├─ 宠物档案管理
│  ├─ 双向链表 ✓
│  └─ 哈希表 ✓
└─ AI健康顾问
   └─ LLM集成 ✓

Phase 2 (待实现)
├─ 智能喂食调度
│  ├─ 最小堆 ○
│  └─ BST ○
└─ 库存管理
   └─ 栈 ○

Phase 3 (未来扩展)
├─ 宠物社交网络
│  └─ 图结构 ○
└─ 硬件通信
   └─ MQTT/HTTP ○
```

---

## 🎯 实现优先级建议

### **高优先级（本学期后）**
1. ⭐⭐⭐⭐⭐ 智能喂食调度系统
   - 核心价值：自动化喂食
   - 难度：中等
   - 数据结构：最小堆 + BST

2. ⭐⭐⭐⭐ 库存管理
   - 核心价值：避免断粮
   - 难度：简单
   - 数据结构：栈

### **中优先级（毕业后）**
3. ⭐⭐⭐ 硬件通信模块
   - 核心价值：连接真实设备
   - 难度：较高（需要硬件知识）
   - 技术：MQTT/HTTP

### **低优先级（商业化阶段）**
4. ⭐⭐ 宠物社交网络
   - 核心价值：增加用户粘性
   - 难度：中等
   - 数据结构：图

---

## 💡 快速启动指南

当你准备实现Phase 2或Phase 3时：

1. **阅读本文档**：了解数据结构和接口设计
2. **参考Phase 1代码**：学习项目结构和编码风格
3. **从单元测试开始**：先写测试，再实现功能
4. **逐步集成**：先独立测试模块，再与现有系统集成

---

**祝未来开发顺利！** 🚀
