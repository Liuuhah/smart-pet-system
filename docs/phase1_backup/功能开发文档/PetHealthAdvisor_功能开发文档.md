# 智能宠物健康顾问模块 (PetHealthAdvisor) 功能开发文档

**版本**: Phase 1.0  
**状态**: 待开发  
**目标**: 将 `chat_compress_client.py` 的高级通信与记忆管理功能集成至 `pet_health_advisor.py`，实现具备“医疗模式”的专业 AI 健康顾问。

---

## 1. 核心架构设计：组合模式 (Composition)

### 1.1 设计理念
采用**组合模式**而非继承或代码复制。`PetHealthAdvisor`（业务大脑）内部实例化一个 `ChatCompressClient`（通信引擎），通过调用其方法实现底层通信和记忆管理。

### 1.2 模块职责划分
| 模块 | 职责 | 关键特性 |
| :--- | :--- | :--- |
| **PetHealthAdvisor** | 业务逻辑、人设锁定、数据组装 | 负责“说什么”，处理 DTO 数据，定义医疗场景下的 Prompt。 |
| **ChatCompressClient** | LLM 通信、消息预处理、记忆压缩 | 负责“怎么说”，处理流式输出、上下文清理、5W 信息提取。 |

---

## 2. 详细开发任务清单

### 任务一：微调底层通信引擎 (`chat_compress_client.py`)

**目标**：使其能被外部模块安全调用，不产生冲突。

1.  **增加配置开关**：
    *   在 `__init__` 中增加 `auto_compress_enabled = True`。
    *   修改 `_compress_chat_history`，仅在开关开启且达到阈值时自动运行。
2.  **暴露核心接口**：
    *   确保 `send_request_stream(messages)` 方法可以被外部直接调用并返回生成器。
    *   确保 `_clean_message_sequence(messages)` 方法是公开的（去掉下划线前缀或保留但提供调用入口）。
3.  **保留通用工具**：
    *   保留天气查询等通用工具函数，作为 Advisor 的辅助能力。

### 任务二：重构健康顾问 (`pet_health_advisor.py`)

**目标**：接入通信引擎，实现“医疗模式”。

1.  **实例化客户端**：
    ```python
    from .chat_compress_client import ChatCompressClient

    class PetHealthAdvisor:
        def __init__(self):
            self.client = ChatCompressClient()
            self.client.auto_compress_enabled = False  # 强制开启医疗模式
            self.system_prompt = "你是一名专业的宠物医生..."
    ```
2.  **实现手动压缩接口**：
    *   新增方法 `compress_memory()`：调用 `self.client._compress_chat_history()`。
    *   新增方法 `get_medical_summary()`：调用 `self.client._extract_5w_info()` 并返回结果。
3.  **重写 `ask()` 方法**：
    *   不再直接请求 API，而是组装好 `messages` 后，调用 `self.client.send_request_stream(messages)`。
    *   在发送前，必须调用 `self.client._clean_message_sequence()` 过滤连续角色消息。

### 任务三：主程序交互增强 (`main.py`)

**目标**：让用户能感知到高级功能的运作。

1.  **增加菜单选项**：
    *   `[4] 手动压缩记忆`：触发 Advisor 的 `compress_memory()`。
    *   `[5] 查看病历摘要`：触发 Advisor 的 `get_medical_summary()` 并打印。
2.  **优化对话循环**：
    *   在对话开始前提示用户：“当前为医疗模式，建议每 10-15 轮对话后手动压缩一次。”

---

## 3. 关键技术规范

### 3.1 消息序列清理规范
*   **问题**：本地模型（如 LM Studio）不支持连续的 `user` 或 `assistant` 消息。
*   **方案**：在发送给 LLM 前，遍历消息列表，若发现连续相同角色，则合并内容并用 `\n` 分隔。

### 3.2 5W 病历提取规范
*   **触发时机**：手动触发或对话达到一定长度。
*   **提取要素**：Who (宠物名), What (症状/行为), When (时间), Where (部位/环境), Why (可能诱因)。
*   **存储位置**：项目根目录下的 `logs/medical_records/`。

### 3.3 资源释放规范
*   **原则**：所有涉及文件读写或网络连接的操作，必须使用 `try...finally` 确保资源关闭。
*   **示例**：保存病历时，确保文件句柄正确关闭。

---

## 4. 验收标准 (Definition of Done)

1.  **无冲突运行**：启动 `main.py` 进入健康顾问模块，不会弹出第二个交互窗口。
2.  **医疗模式生效**：对话过程中不会自动丢失之前的病情描述（因为关闭了自动压缩）。
3.  **手动压缩成功**：点击“手动压缩”后，控制台显示“记忆已压缩”，且后续对话依然流畅。
4.  **病历归档成功**：点击“查看病历”后，能在 `logs/` 目录下找到包含 5W 信息的文本文件。
5.  **代码规范性**：所有新代码符合 PEP8 规范，注释使用中文。

---

## 5. 给 AI 工程师的提示词 (Prompt)

> “请根据上述《功能开发文档》，对 `src/ai_assistant/pet_health_advisor.py` 进行重构。要求使用组合模式实例化 `ChatCompressClient`，并确保在‘医疗模式’下（关闭自动压缩）依然能通过手动按钮完成记忆管理和 5W 病历提取。请重点处理消息序列的清理逻辑，确保兼容本地 LLM。”
