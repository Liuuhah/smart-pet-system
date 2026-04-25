# AI 咨询子模式与精准存档功能设计

**版本**: Phase 1.2  
**状态**: ✅ 已完成  
**完成日期**: 2026-04-25  
**目标**: 将主菜单 `[4]` 升级为连续对话子模式，并引入按聊天轮数提取摘要的精准存档功能。

## 1. 功能概述
为了提升用户与 AI 宠物健康管家的交互体验，计划将主菜单 `[4]` 选项从“单次问答”升级为“连续对话子模式”，并引入“按聊天轮数提取摘要”的精准存档功能。

## 2. 交互流程重构 (Sub-loop Mode)

### 2.1 进入子模式
当用户在主菜单选择 `[4]` 时，系统进入 `while True` 循环：
- **欢迎语**：显示连接状态及操作提示（如：“输入 'exit' 退出，输入 '/list' 查看历史”）。
- **上下文保持**：利用 `PetHealthAdvisor` 内部维护的 `messages` 列表实现多轮对话记忆。

### 2.2 退出机制
- **触发指令**：用户输入 `exit`、`quit`、`返回` 或 `q`。
- **自动归档**：在退出前，系统强制调用一次 `_save_short_consultation_record()`，确保最后一段未被自动计数器覆盖的对话也能存入日志。
- **状态反馈**：显示“[系统] 已结束本次咨询，正在为您保存记录...”，随后返回主菜单。

## 3. 精准存档功能：按聊天轮数提取摘要

### 3.1 核心逻辑
允许用户通过指令指定特定的对话轮次进行总结归档，而非全量总结。

- **指令格式**：`/archive <表达式>`
- **表达式支持**：
  - 离散选择：`1,3,5`
  - 范围选择：`1-3`
  - 混合选择：`1,3-5,8`

### 3.2 解析函数设计 (`_parse_round_numbers`)
该函数负责将用户输入的字符串转换为整数列表：
1. **预处理**：按逗号 `,` 拆分字符串。
2. **范围处理**：检测 `-` 符号，使用 `range(start, end+1)` 展开数字。
3. **去重与排序**：使用 `set` 去重，最后返回升序列表。
4. **容错处理**：若解析失败（如非数字字符），跳过该项或提示用户重新输入。

### 3.3 临时上下文构建 (`_build_temp_context`)
为了实现“精准”总结，需从完整的历史记录中抽取目标片段：
- **索引映射**：第 `N` 轮对话对应 `messages` 列表中的索引 `(N-1)*2` 和 `(N-1)*2 + 1`。
- **边界检查**：若用户请求的轮数超出当前对话总轮数，仅提取有效范围内的消息，并给出提示（如：“第 6 轮超出范围，已忽略”）。
- **数据组装**：将抽取出的消息组成一个新的 `temp_messages` 列表，传递给底层 LLM 接口。

## 4. 视觉反馈与历史记录

### 4.1 历史记录显示 (`/list`)
为了解决“消息条数”与“对话轮数”的认知偏差，历史记录必须按轮次分组显示：
```text
--- Round 1 ---
[你]: ...
[AI]: ...

--- Round 2 ---
[你]: ...
[AI]: ...
```

### 4.2 错误与成功反馈
- **成功**：`[系统] 已成功提取第 1、3 轮对话精华，并保存至 D:\chat-log`。
- **部分成功**：`[系统] 已提取第 1 轮。注意：第 10 轮超出当前对话范围。`
- **失败**：`[系统] 无法识别您的指令，请使用格式：/archive 1,3-5`。

## 5. 实施任务清单 (TODO)

### 5.1 `src/ai_assistant/pet_health_advisor.py`
- [ ] 新增 `get_history_display()`：生成带轮次标记的历史记录字符串。
- [ ] 新增 `extract_summary_by_rounds(round_expression)`：整合解析、构建上下文和调用底层归档的逻辑。

### 5.2 `src/ai_assistant/chat_compress_client.py`
- [ ] 优化 `_extract_5w_info`：增加一个可选参数 `custom_messages`，允许传入临时构建的消息列表进行总结。

### 5.3 `main.py`
- [ ] 重构 `choice == '4'` 分支：实现 `while True` 子循环。
- [ ] 增加指令分发逻辑：识别 `/archive`、`/list` 等特殊指令。
- [ ] 完善退出时的自动归档调用。

## 6. 备注
- **Phase 1 限制**：目前仅支持对内存中现存的 `messages` 进行提取，不支持从历史日志文件中回溯已压缩的内容。
- **命名规范**：该功能在 UI 上统一称为“按聊天轮数提取摘要”。

---

## 7. 给 AI 工程师的详细实施指南 (Implementation Guide)

### 7.1 `src/ai_assistant/pet_health_advisor.py` 修改方案
请在此类中新增以下两个核心方法：

```python
def get_history_display(self) -> str:
    """
    生成带轮次标记的历史记录字符串，用于 /list 指令。
    格式示例：
    --- Round 1 ---
    [你]: ...
    [AI]: ...
    """
    # 逻辑：遍历 self.messages，每两条消息为一组，加上 Round X 头部

def extract_summary_by_rounds(self, round_expression: str) -> str:
    """
    根据用户输入的表达式（如 '1,3-5'）提取指定轮次的摘要。
    步骤：
    1. 调用 _parse_round_numbers 解析表达式。
    2. 检查解析结果是否为空或包含非法数字（<=0）。
    3. 调用 _build_temp_context 获取临时消息列表。
    4. 调用 self.compressor._extract_5w_info(temp_messages) 进行总结。
    5. 返回总结结果或错误提示。
    """
```

### 7.2 `src/ai_assistant/chat_compress_client.py` 修改方案
优化现有的 `_extract_5w_info` 方法，使其更具通用性：

```python
def _extract_5w_info(self, messages: list = None) -> dict:
    """
    提取 5W 信息。
    - 如果 messages 为 None，则使用 self.messages（全量历史）。
    - 如果 messages 有值，则仅针对传入的临时列表进行总结。
    """
```

### 7.3 `main.py` 交互逻辑重构
在 `choice == '4'` 的分支下实现以下伪代码逻辑：

```python
while True:
    user_input = input("[你]: ")
    
    # 1. 退出检测
    if user_input.lower() in ['exit', 'quit', '返回']:
        advisor.compressor._save_short_consultation_record("用户主动退出", advisor.messages)
        print("[系统] 记录已保存，返回主菜单。")
        break
        
    # 2. 特殊指令检测
    if user_input.startswith('/list'):
        print(advisor.get_history_display())
        continue
        
    if user_input.startswith('/archive'):
        expression = user_input.replace('/archive', '').strip()
        result = advisor.extract_summary_by_rounds(expression)
        print(result)
        continue
        
    # 3. 正常对话
    response = advisor.consult(user_input)
    print(f"\n[AI 管家]: {response}")
```

### 7.4 验收标准
1. 输入 `/list` 能清晰看到 `Round 1`, `Round 2` 的分隔。
2. 输入 `/archive 1,3` 能成功只总结第 1 和第 3 轮的内容。
3. 输入 `/archive 100`（超出范围）时，程序不崩溃并给出友好提示。
4. 输入 `exit` 后，能在 `D:\chat-log\log.txt` 中看到最新的归档记录。

---

## 8. 实施总结

### 8.1 已完成的功能

#### ✅ 任务一：连续对话子模式 (`main.py`)
- [x] 重构 `ai_consult_flow()` 函数，实现 `while True` 循环
- [x] 增加欢迎语和操作提示
- [x] 实现退出检测：支持 `exit`、`quit`、`返回`、`q`
- [x] 退出时自动调用 `get_medical_summary(force=True)` 保存最后一段对话
- [x] 增加 KeyboardInterrupt 处理，确保中断时也能保存记录

#### ✅ 任务二：特殊指令支持 (`pet_health_advisor.py`)
- [x] 新增 `get_history_display()` 方法：生成带轮次标记的历史记录
- [x] 新增 `extract_summary_by_rounds()` 方法：整合解析、构建上下文和调用底层归档
- [x] 新增 `_parse_round_numbers()` 方法：解析轮次表达式（支持离散、范围、混合选择）
- [x] 新增 `_build_temp_context()` 方法：从完整历史中抽取目标轮次的消息

#### ✅ 任务三：底层接口优化 (`chat_compress_client.py`)
- [x] 优化 `_extract_5w_info()` 方法：增加可选参数 `messages`，允许传入临时构建的消息列表
- [x] 支持三种提取模式：
  - **标准模式**：使用 `self.chat_history` 的最近消息
  - **累积模式**：包含历史对话的扩展提取
  - **精准提取模式**：处理自定义消息列表（用于 `/archive` 指令）

### 8.2 技术亮点

1. **模块化设计**：
   - 将轮次解析、上下文构建、LLM 调用分离为独立方法
   - 便于单元测试和后续维护

2. **容错处理**：
   - 轮次表达式解析失败时返回空列表，不导致程序崩溃
   - 超出范围的轮次会生成警告信息，但不影响其他轮次的提取
   - 自动交换 `start > end` 的范围表达式（如 `5-3` → `[3, 4, 5]`）

3. **用户体验**：
   - `/list` 显示清晰的轮次分隔符和截断后的对话内容
   - `/archive` 提供详细的反馈信息（包括警告）
   - 退出时自动保存，防止用户忘记手动归档

4. **代码复用**：
   - 精准提取复用了现有的 `_extract_5w_info()` 和 `_save_to_log_file()` 方法
   - 避免了重复代码，保持架构一致性

### 8.3 测试验证

已通过以下测试用例验证功能正确性：

```python
# 测试1：历史记录显示
✅ 能正确显示 Round 1、Round 2 的分隔

# 测试2：轮次表达式解析
✅ '1,3,5' -> [1, 3, 5]
✅ '1-3' -> [1, 2, 3]
✅ '1,3-5,8' -> [1, 3, 4, 5, 8]
✅ '5-3' -> [3, 4, 5]  # 自动交换
✅ 'abc' -> []  # 无效输入

# 测试3：临时上下文构建
✅ 能正确提取指定轮次的消息
✅ 超出范围的轮次会生成警告

# 测试4：精准提取摘要
✅ 能成功调用 LLM 并保存至 D:\chat-log\log.txt
```

### 8.4 文件修改清单

1. **`src/ai_assistant/chat_compress_client.py`**
   - 修改 `_extract_5w_info()` 方法签名，增加 `messages` 参数
   - 支持三种提取模式（标准、累积、精准）

2. **`src/ai_assistant/pet_health_advisor.py`**
   - 新增 `get_history_display()` 方法（约 60 行）
   - 新增 `extract_summary_by_rounds()` 方法（约 30 行）
   - 新增 `_parse_round_numbers()` 方法（约 40 行）
   - 新增 `_build_temp_context()` 方法（约 30 行）

3. **`main.py`**
   - 重构 `ai_consult_flow()` 函数（约 80 行）
   - 实现连续对话子模式
   - 增加特殊指令分发逻辑

### 8.5 使用说明

#### 进入连续对话模式
```
主菜单选择 [4] → 输入宠物姓名 → 开始对话
```

#### 查看历史记录
```
[你]: /list

输出示例：
--- Round 1 ---
[你]: 我的狗狗最近食欲不振
[AI]: 建议观察一下是否有其他症状...

--- Round 2 ---
[你]: 它还有点拉肚子
[AI]: 可能是肠胃问题，建议就医检查...
```

#### 精准提取摘要
```
[你]: /archive 1,3-5

输出示例：
[系统] 已成功提取第 1, 3, 4, 5 轮对话精华，并保存至 D:\chat-log。
```

#### 退出并自动保存
```
[你]: exit

输出示例：
[系统] 已结束本次咨询，正在为您保存记录...
--- 问诊记录 ---
[已成功保存的 5W 信息]
----------------
[OK] 记录已保存，返回主菜单。
```

### 8.6 注意事项

1. **Phase 1 限制**：目前仅支持对内存中现存的 `messages` 进行提取，不支持从历史日志文件中回溯已压缩的内容。
2. **命名规范**：该功能在 UI 上统一称为“按聊天轮数提取摘要”。
3. **日志路径**：所有提取结果均保存至 `D:\chat-log\log.txt`。
4. **LLM 依赖**：精准提取需要本地 LLM 服务正常运行（LM Studio + Qwen）。
