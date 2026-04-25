import os
import json
import time
import http.client
from urllib.parse import urlparse
import re
from .tools import tools

class ChatCompressClient:
    def __init__(self):
        self.config = self._load_config()
        self.base_url = self.config.get('BASE_URL')
        self.model = self.config.get('MODEL')
        self.token = self.config.get('TOKEN')
        self._parse_base_url()
        self.chat_history = []
        self.tools = self._register_tools()
        
        # 压缩配置
        self.max_rounds = 5  # 最大对话轮数
        self.max_context_tokens = 262144  # 最大上下文token数
        self.compress_ratio = 0.7  # 压缩前70%的内容
        
        # 压缩控制标志
        self.skip_next_compress = False  # 单次跳过标志（只对下一次有效）
        self.auto_compress_enabled = True  # 全局自动压缩开关
        
        # 关键信息提取配置
        self.auto_extract_enabled = True  # 自动提取开关
        self.skip_next_extract = False    # 单次跳过标志
        self.extract_interval = 5         # 提取间隔（每5轮对话）
        self.log_file_path = r"D:\chat-log\log.txt"  # 日志文件路径
        
        # 累积式提取相关状态（独立计数器方案）
        self.extract_message_counter = 0  # 5W 提取消息计数器，每收到一条用户消息累加 1
        
        # 日志模式配置
        self.debug_mode = False  # 全局日志模式开关
        
        # System Prompt 配置（用于上下文注入）
        self.base_system_prompt = """你是一位经验丰富的宠物兽医助手，具有以下专业能力：
1. 宠物健康诊断：根据症状提供初步诊断建议
2. 喂养计划制定：根据年龄、体重、品种制定个性化喂养方案
3. 健康管理咨询：提供预防保健、疫苗接种等建议

【重要原则】
- 如果用户提到宠物的基本信息，请基于这些信息给出专业建议
- 始终保持温和专业的语气，避免引起宠物主人恐慌
- 对于紧急情况，务必建议立即就医
- 你不是真正的医生，仅提供参考建议，不能替代专业兽医诊断"""
        self.system_prompt = self.base_system_prompt  # 当前生效的 system prompt
    
    def _register_tools(self):
        """注册可用工具"""
        tools_list = [
            {
                "type": "function",
                "function": {
                    "name": "list_directory",
                    "description": "列出指定目录下的所有文件和子目录，包括文件的基本属性（大小、修改时间等）",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "directory_path": {
                                "type": "string",
                                "description": "要列出的目录路径"
                            }
                        },
                        "required": ["directory_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "rename_file",
                    "description": "修改某个目录下某个文件的名字",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "directory_path": {
                                "type": "string",
                                "description": "文件所在目录路径"
                            },
                            "old_filename": {
                                "type": "string",
                                "description": "旧文件名"
                            },
                            "new_filename": {
                                "type": "string",
                                "description": "新文件名"
                            }
                        },
                        "required": ["directory_path", "old_filename", "new_filename"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "delete_file",
                    "description": "删除某个目录下某个文件",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "directory_path": {
                                "type": "string",
                                "description": "文件所在目录路径"
                            },
                            "filename": {
                                "type": "string",
                                "description": "要删除的文件名"
                            }
                        },
                        "required": ["directory_path", "filename"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_file",
                    "description": "在某个目录下新建一个文件，并且写入内容",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "directory_path": {
                                "type": "string",
                                "description": "要创建文件的目录路径"
                            },
                            "filename": {
                                "type": "string",
                                "description": "要创建的文件名"
                            },
                            "content": {
                                "type": "string",
                                "description": "要写入文件的内容"
                            }
                        },
                        "required": ["directory_path", "filename"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "读取某个目录下面的某个文件的内容",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "directory_path": {
                                "type": "string",
                                "description": "文件所在目录路径"
                            },
                            "filename": {
                                "type": "string",
                                "description": "要读取的文件名"
                            }
                        },
                        "required": ["directory_path", "filename"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "curl",
                    "description": "通过HTTP请求访问网页，并返回网页内容。\n\n【重要提示】\n- 查询wttr.in天气时：\n  1. 必须使用英文城市名（如Chengdu、Beijing），不要使用中文\n  2. 必须添加 format=j1 参数获取JSON格式数据\n  3. 完整格式：https://wttr.in/{城市英文名}?format=j1\n  示例：https://wttr.in/Chengdu?format=j1\n  \n- 天气数据已经由工具格式化好，直接使用该数据回答用户\n- 不要重复调用此工具获取相同城市的天气\n- 如果需要查询其他城市或日期的天气，请明确说明\n\n【禁止行为】\n- 不要重复调用相同的URL\n- 不要对返回的数据进行二次格式化\n- 不要添加原始数据中没有的信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "要访问的网页URL"
                            }
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_chat_history",
                    "description": "搜索聊天历史记录。聊天记录保存在日志文件中，每5轮对话会自动提取关键信息。当用户询问之前的对话内容、历史记录时使用此工具。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "搜索关键词或查询描述。示例：'第一条历史'、'篮球相关'、'查找历史'、'我之前说过什么'。如果是通用查询（如'查找历史'、'第一条记录'），请传入用户的原始问题。如果是特定关键词搜索，请传入具体的搜索词。"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "anythingllm_query",
                    "description": "查询本地文档仓库/知识库。当用户提到'文档仓库'、'文件仓库'、'知识库'、'查找文档'等关键词时使用此工具。可以回答关于已上传文档的问题。\n\n重要提示：\n- 只返回与用户问题直接相关的文档内容\n- 如果检索到多个文档，优先展示最相关的1-2个\n- 对于明显不相关的文档（如文学作品与技术问题），不要展示\n- 如果答案已经足够完整，不需要列出所有来源文档",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "要查询的问题，例如：'公司请假政策是什么？'、'项目文档在哪里？'"
                            }
                        },
                        "required": ["message"]
                    }
                }
            }
        ]
        return tools_list
    
    def execute_tool(self, tool_name, tool_args):
        """执行工具调用"""
        if tool_name == "list_directory":
            return tools.list_directory(tool_args.get("directory_path"))
        elif tool_name == "rename_file":
            return tools.rename_file(
                tool_args.get("directory_path"),
                tool_args.get("old_filename"),
                tool_args.get("new_filename")
            )
        elif tool_name == "delete_file":
            return tools.delete_file(
                tool_args.get("directory_path"),
                tool_args.get("filename")
            )
        elif tool_name == "create_file":
            return tools.create_file(
                tool_args.get("directory_path"),
                tool_args.get("filename"),
                tool_args.get("content", "")
            )
        elif tool_name == "read_file":
            return tools.read_file(
                tool_args.get("directory_path"),
                tool_args.get("filename")
            )
        elif tool_name == "curl":
            return tools.curl(
                tool_args.get("url")
            )
        elif tool_name == "search_chat_history":
            return tools.search_chat_history(
                tool_args.get("query"),
                debug=self.debug_mode
            )
        elif tool_name == "anythingllm_query":
            return tools.anythingllm_query(
                tool_args.get("message"),
                debug=self.debug_mode
            )
        return {"error": f"未知工具: {tool_name}"}
    
    def _load_config(self):
        config = {}
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        if not os.path.exists(env_path):
            print(f"错误: 在 {env_path} 未找到 .env 文件")
            print("请将 env.example 复制为 .env 并填写配置信息")
            exit(1)
        
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip().strip('"')
        
        return config
    
    def _parse_base_url(self):
        parsed = urlparse(self.base_url)
        self.host = parsed.netloc
        self.path = parsed.path.rstrip('/')
    
    def _estimate_tokens(self, text):
        """估算文本的token数量（粗略估算：中文约1字符=1token，英文约4字符=1token）"""
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        other_chars = len(text) - chinese_chars
        # 中文1字符≈1token，其他字符4字符≈1token
        estimated_tokens = chinese_chars + (other_chars // 4)
        return estimated_tokens
    
    def _get_context_tokens(self):
        """计算当前聊天历史的总token数"""
        total_tokens = 0
        for msg in self.chat_history:
            if 'content' in msg and isinstance(msg['content'], str):
                total_tokens += self._estimate_tokens(msg['content'])
            elif 'tool_calls' in msg:
                total_tokens += self._estimate_tokens(json.dumps(msg['tool_calls']))
            elif 'content' in msg and isinstance(msg['content'], dict):
                total_tokens += self._estimate_tokens(json.dumps(msg['content']))
        return total_tokens
    
    def _count_rounds(self):
        """计算对话轮数（一轮=user+assistant）"""
        user_count = sum(1 for msg in self.chat_history if msg.get('role') == 'user')
        return user_count
    
    def _should_compress(self):
        """检查是否需要压缩聊天记录"""
        # 优先检查全局自动压缩开关
        if not self.auto_compress_enabled:
            return False
        
        # 检查单次跳过标志
        if self.skip_next_compress:
            self.skip_next_compress = False  # 重置标志
            print("\n[压缩跳过] 用户选择跳过本次压缩")
            return False
        
        rounds = self._count_rounds()
        context_tokens = self._get_context_tokens()
        
        should_compress_by_rounds = rounds > self.max_rounds
        should_compress_by_tokens = context_tokens > self.max_context_tokens
        
        if should_compress_by_rounds or should_compress_by_tokens:
            reason = []
            if should_compress_by_rounds:
                reason.append(f"对话轮数({rounds})超过限制({self.max_rounds})")
            if should_compress_by_tokens:
                reason.append(f"上下文长度({context_tokens} tokens)超过限制({self.max_context_tokens} tokens)")
            print(f"\n[压缩触发] {'; '.join(reason)}")
            return True
        
        return False
    
    def _compress_chat_history(self):
        """压缩聊天历史记录：前70%内容进行LLM总结，后30%保留原文"""
        if len(self.chat_history) < 3:
            print("[压缩跳过] 聊天记录太少，无需压缩")
            return
        
        # 计算分割点：前70%的内容
        total_messages = len(self.chat_history)
        compress_count = int(total_messages * self.compress_ratio)
        keep_count = total_messages - compress_count
        
        # 确保至少保留最近的一轮对话（user + assistant）
        if keep_count < 2:
            keep_count = 2
            compress_count = total_messages - keep_count
        
        print(f"[压缩开始] 总共{total_messages}条消息，压缩前{compress_count}条，保留后{keep_count}条")
        
        # 提取需要压缩的部分
        messages_to_compress = self.chat_history[:compress_count]
        messages_to_keep = self.chat_history[compress_count:]
        
        # 构建需要压缩的文本
        compress_text = ""
        for msg in messages_to_compress:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            if isinstance(content, dict):
                content = json.dumps(content, ensure_ascii=False)
            compress_text += f"{role}: {content}\n\n"
        
        # 调用LLM进行总结
        print("[压缩中] 正在调用LLM总结历史对话...")
        summary = self._summarize_conversation(compress_text)
        
        if summary:
            # 创建压缩后的摘要消息（改为 user 角色，避免连续 system 导致 Jinja 模板错误）
            compressed_message = {
                'role': 'user',
                'content': f"【之前的对话摘要】\n{summary}\n\n请基于以上背景继续对话。"
            }
            
            # 更新聊天历史：摘要 + 保留的最近消息
            self.chat_history = [compressed_message] + messages_to_keep
            
            print(f"[压缩完成] 从{total_messages}条消息压缩为{len(self.chat_history)}条消息")
            print(f"[压缩效果] 保留了最近{keep_count}条原始消息")
        else:
            print("[压缩失败] LLM总结失败，保持原聊天记录")
    
    def _clean_message_sequence(self, messages):
        """清理消息序列，避免连续相同角色的消息导致 LM Studio Jinja 模板错误
        
        LM Studio 要求：
        1. 不能有两个连续的 system 消息
        2. 不能有两个连续的 user 消息  
        3. 不能有两个连续的 assistant 消息
        
        处理策略：合并连续的同角色消息
        """
        if not messages:
            return []
        
        cleaned = []
        
        for msg in messages:
            role = msg.get('role')
            
            # 跳过空的 system 消息
            if role == 'system' and not msg.get('content', '').strip():
                continue
            
            # 如果当前消息与前一个消息角色相同
            if cleaned and cleaned[-1].get('role') == role:
                if role in ['user', 'assistant', 'system']:
                    # 合并连续的同角色消息
                    prev_content = cleaned[-1].get('content', '')
                    curr_content = msg.get('content', '')
                    if isinstance(curr_content, dict):
                        curr_content = json.dumps(curr_content)
                    cleaned[-1]['content'] = prev_content + '\n\n' + str(curr_content)
                    print(f"[消息清理] 合并两个连续的 {role} 消息")
            else:
                # 创建消息的副本，避免修改原始数据
                cleaned.append(msg.copy())
        
        return cleaned
    
    def _summarize_conversation(self, conversation_text):
        """调用LLM对对话内容进行总结"""
        try:
            print(f"[调试] 开始调用LLM总结...")
            print(f"[调试] 需要总结的文本长度: {len(conversation_text)} 字符")
            
            if self.base_url.startswith('https://'):
                conn = http.client.HTTPSConnection(self.host)
            else:
                conn = http.client.HTTPConnection(self.host)
            
            headers = {
                'Content-Type': 'application/json'
            }
            if self.token:
                headers['Authorization'] = f'Bearer {self.token}'
            
            prompt = f"""请对以下对话历史进行简洁的总结，提取关键信息和上下文。

要求：
1. 用中文输出总结
2. 控制在200字以内
3. 包含用户的主要信息和问题
4. 直接输出总结内容，不要有任何思考过程或额外说明

对话历史：
{conversation_text}

总结："""
            
            data = {
                'model': self.model,
                'messages': [
                    {'role': 'system', 'content': '你是一个专业的对话总结助手。请直接输出总结内容，不要输出任何思考过程。'},
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': 512,
                'temperature': 0.3,
                'stream': False
            }
            
            # 输出请求原文（方便调试）
            print(f"\n{'='*60}")
            print(f"[请求原文] 发送给LLM的数据:")
            print(json.dumps(data, ensure_ascii=False, indent=2))
            print(f"{'='*60}\n")
            
            print(f"[调试] 发送请求到: {self.base_url}/chat/completions")
            print(f"[调试] 使用模型: {self.model}")
            print(f"[调试] stream参数: False")
            
            conn.request('POST', f'{self.path}/chat/completions', json.dumps(data), headers)
            response = conn.getresponse()
            
            print(f"[调试] 响应状态码: {response.status}")
            print(f"[调试] 响应头: {dict(response.getheaders())}")
            
            raw_response = response.read().decode()
            print(f"[调试] 原始响应内容（前500字符）: {raw_response[:500]}")
            
            response_data = json.loads(raw_response)
            print(f"[调试] JSON解析成功")
            print(f"[调试] 完整响应数据: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
            
            conn.close()
            
            if 'error' in response_data:
                print(f"[调试] 发现错误字段: {response_data['error']}")
                print(f"总结请求错误: {response_data['error']['message']}")
                return None
            
            print(f"[调试] 尝试提取choices[0]['message']['content']...")
            print(f"[调试] choices数据: {response_data.get('choices')}")
            
            if 'choices' not in response_data or len(response_data['choices']) == 0:
                print(f"[调试] 错误: 响应中没有choices字段或为空")
                return None
            
            message = response_data['choices'][0].get('message', {})
            print(f"[调试] message字段: {message}")
            
            # 优先使用content字段
            summary = message.get('content', '').strip()
            print(f"[调试] content字段: '{summary}'")
            print(f"[调试] content长度: {len(summary)} 字符")
            
            # 如果content为空，尝试从reasoning_content提取
            if not summary:
                print(f"[调试] content为空，尝试从reasoning_content提取...")
                reasoning_content = message.get('reasoning_content', '')
                print(f"[调试] reasoning_content长度: {len(reasoning_content)} 字符")
                
                if reasoning_content:
                    # 方法1：查找 "4. **Drafting the Summary" 后面的内容
                    draft_match = re.search(r'4\.\s*\*\*Drafting the Summary.*?:\s*(.+)', reasoning_content, re.DOTALL)
                    if draft_match:
                        draft_text = draft_match.group(1).strip()
                        # 提取其中的中文部分
                        chinese_parts = re.findall(r'[\u4e00-\u9fff][\u4e00-\u9fff，。！？；：""''（）\\s]*', draft_text)
                        if chinese_parts:
                            summary = ''.join(chinese_parts).strip()
                            print(f"[调试] 从Draft中提取到: '{summary}'")
                    
                    # 方法2：如果方法1失败，提取所有中文句子
                    if not summary:
                        chinese_sentences = re.findall(r'[\u4e00-\u9fff]+[^.\n]*?[。！？]', reasoning_content)
                        if chinese_sentences:
                            # 取最后几句作为总结
                            summary = ''.join(chinese_sentences[-3:]).strip()
                            print(f"[调试] 从中文句子提取到: '{summary}'")
                    
                    # 方法3：如果还是没有，提取最后的中文段落
                    if not summary:
                        chinese_blocks = re.findall(r'[\u4e00-\u9fff][\u4e00-\u9fff\s，。！？；：""''（）]{20,}', reasoning_content)
                        if chinese_blocks:
                            summary = chinese_blocks[-1].strip()
                            print(f"[调试] 从中文段落提取到: '{summary}'")
            
            print(f"[调试] 最终summary: '{summary}'")
            print(f"[调试] 最终summary长度: {len(summary)} 字符")
            
            return summary if summary else None
            
        except json.JSONDecodeError as e:
            print(f"[调试] JSON解析失败！")
            print(f"[调试] JSON错误详情: {e}")
            print(f"[调试] 错误位置: 行{e.lineno} 列{e.colno}")
            return None
            
        except KeyError as e:
            print(f"[调试] 键值错误！")
            print(f"[调试] 缺少的键: {e}")
            print(f"[调试] 响应数据结构: {json.dumps(response_data, ensure_ascii=False) if 'response_data' in locals() else 'N/A'}")
            return None
            
        except Exception as e:
            import traceback
            print(f"[调试] 总结过程出现异常！")
            print(f"[调试] 异常类型: {type(e).__name__}")
            print(f"[调试] 异常信息: {e}")
            print(f"[调试] 完整堆栈跟踪:")
            print(traceback.format_exc())
            return None
    
    def send_request_stream(self, prompt, max_tokens=4096, debug=None):
        """发送流式请求，实时输出回复内容（带自动压缩功能）
        
        注意：为了支持组合模式下的外部调用，此方法现在接收 prompt 字符串
        并内部处理历史记录的组装。
        """
        # 优先使用类的 debug_mode，如果参数为 None 则使用默认值
        if debug is None:
            debug = self.debug_mode
        
        start_time = time.time()
        full_content = ''
        
        # 支持多轮工具调用的循环
        max_tool_rounds = 3  # 最多处理3轮工具调用
        
        for round_num in range(max_tool_rounds):
            if round_num > 0:
                if debug:
                    print(f"\n[调试] 第{round_num + 1}轮工具调用...")
            
            content, has_tool_call = self._send_single_stream(
                prompt, max_tokens, debug, round_num == 0
            )
            
            if content:
                full_content = content
            
            # 如果没有工具调用，或者已经达到最大轮数，退出循环
            if not has_tool_call or round_num >= max_tool_rounds - 1:
                break
        
        print()
        end_time = time.time()
        total_time = end_time - start_time
        
        return full_content, total_time
    
    def _send_single_stream(self, prompt, max_tokens, debug, is_first_round):
        """发送单次流式请求，返回(内容, 是否有工具调用)"""
        if debug:
            print(f"\n{'='*60}")
            print(f"[调试] 开始发送流式请求")
            print(f"[调试] 模型: {self.model}")
            print(f"[调试] BASE_URL: {self.base_url}")
            print(f"[调试] Host: {self.host}")
            print(f"[调试] Path: {self.path}")
            print(f"[调试] Token存在: {'是' if self.token else '否'}")
            print(f"{'='*60}\n")
        
        if self.base_url.startswith('https://'):
            conn = http.client.HTTPSConnection(self.host)
        else:
            conn = http.client.HTTPConnection(self.host)
        
        headers = {
            'Content-Type': 'application/json'
        }
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        if debug:
            print(f"[调试] 请求头: {headers}")
        
        # 清理消息序列，避免连续相同角色的消息导致 Jinja 模板错误
        cleaned_history = self._clean_message_sequence(self.chat_history)
        
        # 使用动态的 system prompt（支持上下文注入）
        messages_list = [
            {'role': 'system', 'content': self.system_prompt}
        ]
        
        # 只有当chat_history的最后一条不是当前prompt时，才添加prompt
        if cleaned_history and cleaned_history[-1].get('role') == 'user' and cleaned_history[-1].get('content') == prompt:
            # 最后一条已经是当前用户消息，不需要再添加
            messages_list.extend(cleaned_history)
        else:
            # 需要添加当前用户消息
            messages_list.extend(cleaned_history)
            messages_list.append({'role': 'user', 'content': prompt})
        
        data = {
            'model': self.model,
            'messages': messages_list,
            'tools': self.tools,
            'tool_choice': 'auto',
            'max_tokens': max_tokens,
            'temperature': 0.6,
            'stream': True
        }
        
        if debug:
            print(f"[调试] 请求数据大小: {len(json.dumps(data))} 字节")
            print(f"[调试] 消息数量: {len(data['messages'])}")
            print(f"[调试] 是否使用流式: {data['stream']}")
        
        try:
            if debug:
                print(f"[调试] 正在发送请求到: {self.path}/chat/completions ...")
            request_start = time.time()
            conn.request('POST', f'{self.path}/chat/completions', json.dumps(data), headers)
            response = conn.getresponse()
            request_end = time.time()
            
            if debug:
                print(f"[调试] 响应状态码: {response.status}")
                print(f"[调试] 响应头: {dict(response.getheaders())}")
                print(f"[调试] 请求耗时: {request_end - request_start:.2f}秒")
            
            if response.status != 200:
                error_body = response.read().decode('utf-8', errors='ignore')
                if debug:
                    print(f"[调试] 错误响应体: {error_body[:500]}")
                print(f"[错误] API返回非200状态码: {response.status}")
                return "", False
        
        except Exception as e:
            import traceback
            print(f"[错误] 发送请求时发生异常!")
            print(f"[错误] 异常类型: {type(e).__name__}")
            print(f"[错误] 异常信息: {e}")
            if debug:
                print(f"[调试] 堆栈跟踪:")
                print(traceback.format_exc())
            return "", False
        
        full_content = ''
        buffer = ''
        
        # 工具调用缓冲区
        tool_calls_buffer = {}  # 按index存储tool_call的累积数据
        pending_tool_calls = []  # 存储完整的tool_call，等待执行
        tool_call_response = ''  # 存储工具调用后AI的最终响应
        
        # 准备日志文件
        if debug:
            log_dir = os.path.join(os.path.dirname(__file__), 'logs')
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, f'chat_{time.strftime("%Y%m%d_%H%M%S")}.txt')
            print(f"调试模式已启用，输出将保存到: {log_file}")
        
        try:
            stream_start = time.time()
            chunk_count = 0
            
            while True:
                chunk = response.read(1024)
                if not chunk:
                    break
                
                chunk_count += 1
                if debug and chunk_count <= 3:
                    print(f"[调试] 收到第{chunk_count}个数据块，大小: {len(chunk)} 字节")
                
                buffer += chunk.decode('utf-8', errors='ignore')
                
                # 处理SSE格式数据
                lines = buffer.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('data: '):
                        json_str = line[6:].strip()
                        if json_str == '[DONE]':
                            stream_end = time.time()
                            if debug:
                                print(f"\n[调试] 流式响应结束")
                                print(f"[调试] 总共收到 {chunk_count} 个数据块")
                                print(f"[调试] 流式读取耗时: {stream_end - stream_start:.2f}秒")
                                print(f"[调试] 当前累计内容长度: {len(full_content)} 字符")
                            
                            # 流式响应结束，检查并执行待处理的工具调用
                            if pending_tool_calls:
                                if debug:
                                    print(f"[调试] 检测到 {len(pending_tool_calls)} 个待执行的工具调用")
                                for tool_call_data in pending_tool_calls:
                                    response_content = self._execute_pending_tool_call(
                                        tool_call_data, 
                                        data, 
                                        conn, 
                                        headers, 
                                        prompt
                                    )
                                    if response_content:
                                        tool_call_response = response_content
                                # 工具调用已执行完毕，返回最终响应，标记为无更多工具调用
                                return tool_call_response if tool_call_response else full_content, False
                            else:
                                # 没有工具调用，正常结束
                                if debug:
                                    print(f"[调试] 没有工具调用，返回正常响应")
                                return full_content, False
                        
                        try:
                            chunk_data = json.loads(json_str)
                            if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                choice = chunk_data['choices'][0]
                                delta = choice.get('delta', {})
                                
                                # 检测工具调用请求
                                if 'tool_calls' in delta:
                                    if debug:
                                        print(f"[调试] 检测到工具调用片段")
                                    for tc in delta['tool_calls']:
                                        index = tc.get('index', 0)
                                        
                                        # 初始化该index的tool_call缓冲区
                                        if index not in tool_calls_buffer:
                                            tool_calls_buffer[index] = {
                                                'id': None,
                                                'type': 'function',
                                                'function': {
                                                    'name': None,
                                                    'arguments': ''
                                                }
                                            }
                                        
                                        # 累积tool_call数据
                                        if 'id' in tc:
                                            tool_calls_buffer[index]['id'] = tc['id']
                                        
                                        if 'function' in tc:
                                            if 'name' in tc['function']:
                                                tool_calls_buffer[index]['function']['name'] = tc['function']['name']
                                                if debug:
                                                    print(f"[调试] 工具名称: {tc['function']['name']}")
                                            if 'arguments' in tc['function']:
                                                # 累积arguments片段
                                                tool_calls_buffer[index]['function']['arguments'] += tc['function']['arguments']
                                        
                                        # 尝试解析完整的arguments
                                        tool_args_str = tool_calls_buffer[index]['function']['arguments']
                                        if tool_args_str:
                                            try:
                                                tool_args = json.loads(tool_args_str)
                                                tool_name = tool_calls_buffer[index]['function']['name']
                                                
                                                # 如果成功解析，说明参数完整，加入待执行队列
                                                if tool_name:
                                                    if debug:
                                                        print(f"[调试] 工具参数解析成功，加入待执行队列")
                                                    pending_tool_calls.append({
                                                        'id': tool_calls_buffer[index]['id'],
                                                        'name': tool_name,
                                                        'arguments': tool_args
                                                    })
                                            except json.JSONDecodeError:
                                                # arguments还不完整，继续等待后续chunk
                                                pass
                                
                                # 正常文本内容
                                content = delta.get('content', '')
                                if content:
                                    print(content, end='', flush=True)
                                    full_content += content
                                    # 写入日志文件
                                    if debug:
                                        with open(log_file, 'a', encoding='utf-8') as f:
                                            f.write(content)
                        except json.JSONDecodeError as e:
                            if debug:
                                print(f"[调试] JSON解析失败: {e}")
                                print(f"[调试] 失败的JSON字符串: {json_str[:200]}")
                            pass
                
                # 保留未处理的部分
                if len(lines) > 0:
                    buffer = lines[-1]
                else:
                    buffer = ''
        except KeyboardInterrupt:
            print('\n\n用户中断')
            return full_content, False
        except Exception as e:
            import traceback
            print(f"\n[错误] 读取流式响应时发生异常!")
            print(f"[错误] 异常类型: {type(e).__name__}")
            print(f"[错误] 异常信息: {e}")
            if debug:
                print(f"[调试] 堆栈跟踪:")
                print(traceback.format_exc())
            return full_content, False
        finally:
            conn.close()
        
        # 流结束后的兜底检查（防止异常情况下pending_tool_calls未被处理）
        if pending_tool_calls and not tool_call_response:
            if debug:
                print(f"[调试] 流结束后检测到 {len(pending_tool_calls)} 个待执行的工具调用（兜底执行）")
            for tool_call_data in pending_tool_calls:
                response_content = self._execute_pending_tool_call(
                    tool_call_data, 
                    data, 
                    conn, 
                    headers, 
                    prompt
                )
                if response_content:
                    tool_call_response = response_content
            # 工具调用已执行完毕，返回最终响应，标记为无更多工具调用
            return tool_call_response if tool_call_response else full_content, False
        
        if debug:
            print(f"[调试] 流式请求完成，返回内容长度: {len(full_content)}")
        return full_content, False
    
    def _execute_pending_tool_call(self, tool_call_data, data, conn, headers, prompt):
        """执行累积完整的工具调用"""
        tool_id = tool_call_data['id']
        tool_name = tool_call_data['name']
        tool_args = tool_call_data['arguments']
        
        print(f"\n完整工具调用: {tool_name}")
        print(f"完整参数: {json.dumps(tool_args, ensure_ascii=False)}")
        
        # 执行工具
        normalized_tool_name = tool_name.lower()
        tool_result = self.execute_tool(normalized_tool_name, tool_args)
        
        print(f"工具执行结果: {json.dumps(tool_result, ensure_ascii=False)}")
        
        # 将工具执行结果添加到聊天历史
        self.add_to_history('assistant', {
            'tool_calls': [{
                'id': tool_id,
                'type': 'function',
                'function': {
                    'name': tool_name,
                    'arguments': json.dumps(tool_args, ensure_ascii=False)
                }
            }]
        })
        
        # 发送工具执行结果
        self.add_to_history('tool', {
            'tool_call_id': tool_id,
            'name': tool_name,
            'content': json.dumps(tool_result, ensure_ascii=False)
        })
        
        # 重新发送请求获取最终响应
        print("\nAI: ", end='', flush=True)
        conn.close()
        
        # 重新构建请求
        if self.base_url.startswith('https://'):
            conn = http.client.HTTPSConnection(self.host)
        else:
            conn = http.client.HTTPConnection(self.host)
        
        # 重新构建请求时禁用工具调用
        cleaned_history = self._clean_message_sequence(self.chat_history)
        
        # 使用动态的 system prompt（支持上下文注入）
        messages_list = [
            {'role': 'system', 'content': self.system_prompt}
        ]
        
        # 检查最后一条消息是否已经是当前用户的prompt，避免重复
        if cleaned_history and cleaned_history[-1].get('role') == 'user' and cleaned_history[-1].get('content') == prompt:
            # 最后一条已经是当前用户消息，不需要再添加
            messages_list.extend(cleaned_history)
        else:
            # 需要添加当前用户消息
            messages_list.extend(cleaned_history)
            messages_list.append({'role': 'user', 'content': prompt})
        
        data['messages'] = messages_list
        # 禁用工具调用，因为已经执行过了
        data['tool_choice'] = 'none'
        
        conn.request('POST', f'{self.path}/chat/completions', json.dumps(data), headers)
        response = conn.getresponse()
        
        # 重新读取响应流
        full_content = ''
        buffer = ''
        
        try:
            while True:
                chunk = response.read(1024)
                if not chunk:
                    break
                
                buffer += chunk.decode('utf-8', errors='ignore')
                
                lines = buffer.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('data: '):
                        json_str = line[6:].strip()
                        if json_str == '[DONE]':
                            continue
                        
                        try:
                            chunk_data = json.loads(json_str)
                            if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                delta = chunk_data['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    print(content, end='', flush=True)
                                    full_content += content
                        except json.JSONDecodeError:
                            pass
                
                if len(lines) > 0:
                    buffer = lines[-1]
                else:
                    buffer = ''
        finally:
            conn.close()
        
        return full_content
    
    def add_to_history(self, role, content):
        """添加消息到聊天历史"""
        if role == 'assistant' and isinstance(content, dict) and 'tool_calls' in content:
            self.chat_history.append({'role': role, **content})
        elif role == 'tool' and isinstance(content, dict):
            self.chat_history.append({'role': role, **content})
        else:
            self.chat_history.append({'role': role, 'content': content})
    
    def clear_history(self):
        """清空聊天历史"""
        self.chat_history = []
        print("聊天历史已清空")
    
    def set_system_prompt(self, additional_context: str):
        """
        动态更新 System Prompt，用于注入宠物档案。
        
        Args:
            additional_context: 额外的上下文信息（如宠物档案）
        """
        # 策略：保留原有的角色设定，追加宠物档案
        self.system_prompt = self.base_system_prompt + "\n\n" + additional_context
        print(f"[系统] 已更新 System Prompt，注入宠物上下文信息")
    
    def reset_system_prompt(self):
        """重置 System Prompt 为基础版本（用于切换宠物或退出咨询模式）"""
        self.system_prompt = self.base_system_prompt
        print(f"[系统] 已重置 System Prompt")
    
    def show_history_stats(self):
        """显示聊天历史统计信息"""
        rounds = self._count_rounds()
        context_tokens = self._get_context_tokens()
        message_count = len(self.chat_history)
        
        print(f"\n[聊天统计]")
        print(f"  消息数量: {message_count} 条")
        print(f"  对话轮数: {rounds} 轮")
        print(f"  上下文长度: {context_tokens} tokens")
        print(f"  压缩阈值: {self.max_rounds} 轮 或 {self.max_context_tokens} tokens")
        print()
    
    def _show_compress_settings(self):
        """显示压缩相关设置"""
        print("\n[压缩设置]")
        print(f"  自动压缩: {'✅ 启用' if self.auto_compress_enabled else '❌ 禁用'}")
        print(f"  下次跳过: {'是' if self.skip_next_compress else '否'}")
        print(f"  轮数阈值: {self.max_rounds} 轮")
        print(f"\n[可用命令]")
        print(f"  skip_compress / 跳过压缩  - 跳过下次自动压缩")
        print(f"  enable_compress / 启用压缩 - 启用自动压缩")
        print(f"  disable_compress / 禁用压缩 - 禁用自动压缩")
        print(f"  compress_settings / 压缩设置 - 显示此信息")
        print()
    
    def extract_summary_now(self):
        """强制立即提取当前对话摘要（跳过计数器限制）
        
        设计原则：
        - 手动触发优先级最高：无论对话长短都尝试提取
        - 兜底归档策略：即使 LLM 判定信息不足，也保存原始对话
        - 统一反馈：确保用户永远看到正向反馈
        """
        print("\n[强制提取] 正在调用 LLM 进行 5W 信息提取...")
        
        # 检查是否有对话历史
        if len(self.chat_history) < 2:
            # 无对话历史，直接保存提示
            self._save_short_consultation_record(
                reason="暂无对话记录",
                recent_messages=[]
            )
            return "已成功保存问诊记录至日志文件（当前无对话内容）。"
        
        # 获取最近的对话消息（最多取最近 10 条）
        recent_messages = self.chat_history[-10:]
        
        # 构建提取提示词（非累积模式）
        extract_prompt = self._build_extract_prompt(recent_messages, is_cumulative=False)
        
        # 调用 LLM 进行提取
        print("[强制提取] 正在调用 LLM...")
        response_data = self._send_extract_request(
            extract_prompt,
            max_tokens=4096,
            temperature=0.5
        )
        
        # 解析响应
        extracted_info, status, reason = self._parse_extraction_response(response_data)
        
        # 根据结果处理
        if status == "success":
            # 提取成功，保存到日志
            round_number = len(self.chat_history) // 2
            should_compress = self._should_compress()
            success = self._save_to_log_file(
                extracted_info=extracted_info,
                round_number=round_number,
                recent_messages=recent_messages,
                is_cumulative=False,
                counter_value=self.extract_message_counter,
                should_compress=should_compress
            )
            
            if success:
                print("[强制提取] ✅ 提取成功并已保存")
                return "已成功提取本次问诊精华，并保存至 D:\\chat-log 目录。您可以随时查阅宠物的健康档案。"
            else:
                print("[强制提取] ⚠️ 保存失败")
                return "提取成功但保存失败，请稍后重试。"
        
        elif status == "insufficient_info":
            # 信息不足，使用兜底策略：保存原始对话作为"简短问诊记录"
            print(f"[强制提取] ⚠️ LLM 判定信息不足：{reason}")
            print("[强制提取] 📝 启用兜底策略：保存原始对话记录")
            
            round_number = len(self.chat_history) // 2
            self._save_short_consultation_record(
                reason=reason,
                recent_messages=recent_messages,
                round_number=round_number
            )
            
            return "已成功保存本次问诊记录至 D:\\chat-log 目录（简短问诊记录）。您可以随时查阅宠物的健康档案。"
        
        elif status == "technical_error":
            # 技术故障，保存原始对话
            print(f"[强制提取] ❌ 技术故障：{reason}")
            print("[强制提取] 📝 启用兜底策略：保存原始对话记录")
            
            round_number = len(self.chat_history) // 2
            self._save_short_consultation_record(
                reason=f"技术故障：{reason}",
                recent_messages=recent_messages,
                round_number=round_number
            )
            
            return "已成功保存本次问诊记录至 D:\\chat-log 目录（原始对话备份）。您可以随时查阅宠物的健康档案。"
        
        else:
            # 其他错误，同样保存原始对话
            print(f"[强制提取] ❌ 提取失败：{reason}")
            print("[强制提取] 📝 启用兜底策略：保存原始对话记录")
            
            round_number = len(self.chat_history) // 2
            self._save_short_consultation_record(
                reason=reason,
                recent_messages=recent_messages,
                round_number=round_number
            )
            
            return "已成功保存本次问诊记录至 D:\\chat-log 目录（原始对话备份）。您可以随时查阅宠物的健康档案。"

    def _check_and_extract_key_info(self):
        """检查是否需要提取关键信息，并在满足条件时执行"""
        
        # 检查是否全局禁用
        if not self.auto_extract_enabled:
            print(f"[调试] 5W 提取已禁用，跳过检查")
            return
        
        # 检查是否单次跳过
        if self.skip_next_extract:
            self.skip_next_extract = False
            print("[关键信息提取] 用户跳过本次提取")
            return
        
        # 计算当前对话轮数
        rounds = len(self.chat_history) // 2
        
        # 调试日志
        print(f"[调试] 当前 chat_history 长度: {len(self.chat_history)}, 轮数: {rounds}, 提取间隔: {self.extract_interval}")
        
        # 每 extract_interval 轮对话触发一次
        if rounds > 0 and rounds % self.extract_interval == 0:
            print(f"\n[关键信息提取] 检测到第{rounds}轮对话，开始提取关键信息...")
            self._extract_5w_info()
        else:
            print(f"[调试] 不满足提取条件 (rounds={rounds}, rounds % {self.extract_interval} = {rounds % self.extract_interval})")
    
    def _extract_5w_info(self, messages=None):
        """执行 5W 关键信息提取（支持累积模式和自定义消息列表）
        
        Args:
            messages: 可选参数，传入自定义消息列表进行总结
                     如果为 None，则使用 self.chat_history 的最近消息
        """
        
        # 如果传入了自定义消息列表，直接使用；否则使用默认逻辑
        if messages is not None:
            recent_messages = messages
            is_cumulative = False  # 自定义消息列表不使用累积模式
            print(f"[关键信息提取] 🎯 精准提取模式：处理 {len(recent_messages)} 条指定消息")
        else:
            # 默认逻辑：提取最近的 extract_interval * 2 条消息
            recent_messages = self.chat_history[-(self.extract_interval * 2):]
            is_cumulative = (self.extract_message_counter > self.extract_interval)
            
            if is_cumulative:
                print(f"[关键信息提取] 🔄 累积模式：计数器={self.extract_message_counter}，提取最近 {len(recent_messages)} 条消息")
            else:
                print(f"[关键信息提取] 标准模式：计数器={self.extract_message_counter}，提取最近 {len(recent_messages)} 条消息")
        
        # 构建提取提示词（传入累积模式标志）
        extract_prompt = self._build_extract_prompt(recent_messages, is_cumulative)
        
        # 调用 LLM 进行提取
        print("[关键信息提取] 正在调用 LLM...")
        response_data = self._send_extract_request(
            extract_prompt, 
            max_tokens=4096,  # 增加 token 限制，支持更长的输出
            temperature=0.5
        )
        
        # 解析响应（返回三元组）
        extracted_info, status, reason = self._parse_extraction_response(response_data)
        
        # 根据结果更新状态
        if status == "success":
            # 提取成功，重置计数器
            if is_cumulative:
                print(f"[关键信息提取] ✅ 累积提取成功，计数器重置为 0")
            else:
                print(f"[关键信息提取] ✅ 提取成功，计数器重置为 0")
            
            self.extract_message_counter = 0  # ✅ 重置计数器
            
            # 保存到日志文件
            should_compress = self._should_compress()
            success = self._save_to_log_file(
                extracted_info=extracted_info,
                round_number=len(self.chat_history) // 2,
                recent_messages=recent_messages,
                is_cumulative=is_cumulative,
                counter_value=self.extract_message_counter,  # 注意：此时计数器已重置为0，但为了记录触发时的状态，可以传入重置前的值。不过需求文档中要求传入当前值。
                should_compress=should_compress
            )
            
            if success:
                print("[关键信息提取] ✅ 完成")
            else:
                print("[关键信息提取] ⚠️ 保存失败")
        
        elif status == "insufficient_info":
            # 提取失败（信息不足），计数器继续累加（不重置）
            print(f"[关键信息提取] ⚠️ 提取失败，计数器保持为 {self.extract_message_counter}（下次在第 {self.extract_message_counter + self.extract_interval} 条消息时再次尝试）")
            
            # 保存失败记录
            self._save_failed_extraction(
                round_number=len(self.chat_history) // 2,
                reason=reason,
                recent_messages=recent_messages
            )
        
        elif status == "technical_error":
            # 技术故障，不改变累积状态
            print(f"[关键信息提取] ❌ 技术故障，保持当前状态")
            print(f"[关键信息提取] 建议：请检查网络连接或稍后重试")
        
        else:
            # 其他错误（格式错误等）
            print(f"[关键信息提取] ❌ 提取失败：{reason}")
    
    def _build_extract_prompt(self, recent_messages, is_cumulative=False):
        """构建 5W 信息提取的提示词
        
        Args:
            recent_messages: 要提取的对话消息列表
            is_cumulative: 是否为累积模式（True=包含历史对话）
        """
        
        if is_cumulative:
            # 累积模式：分级处理
            # 计算分界点：前一半是历史，后一半是当前
            half_count = len(recent_messages) // 2
            historical_messages = recent_messages[:half_count]
            current_messages = recent_messages[half_count:]
            
            # 格式化历史对话
            historical_text = ""
            for i, msg in enumerate(historical_messages, 1):
                role = "用户" if msg['role'] == 'user' else "AI助手"
                content = msg.get('content', '')
                if isinstance(content, list):
                    content = str(content)
                historical_text += f"{i}. {role}: {content}\n"
            
            # 格式化当前对话
            current_text = ""
            for i, msg in enumerate(current_messages, 1):
                role = "用户" if msg['role'] == 'user' else "AI助手"
                content = msg.get('content', '')
                if isinstance(content, list):
                    content = str(content)
                current_text += f"{i}. {role}: {content}\n"
            
            prompt = f"""请分析以下对话内容，分为两个部分处理。

【第一部分：历史对话摘要】（共{len(historical_messages)}条消息）
{historical_text}

【第二部分：当前对话 5W 提取】（共{len(current_messages)}条消息）
{current_text}

【处理规则】

1. **对第一部分（历史对话）**：
   - 用 1-2 句话简要总结这部分对话的核心内容
   - 不需要提取 5W，只需要概括性描述
   - 示例：“用户与AI互相问候，用户自我介绍姓刘，双方进行了简单的寒暄。”

2. **对第二部分（当前对话）**：
   - 按照 5W 规则提取关键信息
   - 如果信息充足，严格按照格式输出 Who/What/When/Where/Why
   - 如果信息太少，输出：【无法提取】对话内容可提取的信息太少

3. **最终输出格式**（必须严格遵守）：

=== 历史对话摘要 ===
[这里写 1-2 句话的历史对话总结]

=== 当前对话 5W 信息 ===
- Who: [参与者姓名或角色]
- What: [主要事件或话题]
- When: [时间]
- Where: [地点]
- Why: [原因或目的]

【重要注意事项】
1. 必须分析所有对话内容，不能遗漏
2. 历史摘要要简洁，不超过 50 字
3. 5W 提取要保持原有格式要求
4. 使用中文输出
5. 直接输出结果，不要输出思考过程
6. 不要在输出中包含 "Thinking Process"、"分析" 等字样

【开始提取】"""

        else:
            # === 正常模式：标准 5W 提取 ===
            
            # 格式化对话历史
            conversation_text = ""
            for i, msg in enumerate(recent_messages, 1):
                role = "用户" if msg['role'] == 'user' else "AI助手"
                content = msg.get('content', '')
                if isinstance(content, list):
                    content = str(content)
                conversation_text += f"{i}. {role}: {content}\n"
            
            prompt = f"""请分析以下对话内容，按照 5W 规则提取关键信息。

【对话内容】（共{len(recent_messages)}条消息）
{conversation_text}

【提取规则】
请按照以下优先级处理：

1. **判断是否可提取**
   - 如果对话包含足够的实质性信息（讨论、计划、事件、决策等），请提取 5W
   - 如果对话只是问候、闲聊、或信息太少，无法提取有效信息，请输出：
     【无法提取】对话内容可提取的信息太少，没有值得提取的关键信息
   - 如果对话内容过长或超出你的处理能力，请输出：
     【无法提取】上下文太长，无法完整分析

2. **如果可以提取，请严格按照以下格式输出**
   - Who: [参与者姓名或角色，如果没有明确提及则写“未提及”]
   - What: [发生的主要事件或讨论的核心话题，用一句话概括]
   - When: [具体时间或时间段，如果没有则写“未提及”]
   - Where: [地点或场所，如果没有则写“未提及”]
   - Why: [原因、目的或动机，如果没有则写“未提及”]

【重要注意事项】
1. 必须分析所有对话内容，不能遗漏任何一条消息
2. 只提取对话中明确提到的信息，不要推测
3. 保持简洁，每个字段不超过 30 字
4. 如果某个信息在对话中出现多次，提取最重要的那个
5. 使用中文输出
6. 直接输出结果，不要输出任何思考过程、分析步骤或额外说明
7. 不要在输出中包含 "Thinking Process"、"分析"、"首先"、"Let" 等字样
8. 输出格式必须完全按照下面的示例，不要添加任何 Markdown 格式

【输出示例 - 可提取】
- Who: 张三
- What: 用户进行自我介绍
- When: 未提及
- Where: 北京
- Why: 寻求助手协助

【输出示例 - 无法提取】
【无法提取】对话内容可提取的信息太少，没有值得提取的关键信息

【开始提取】"""

        return prompt
    
    def _send_extract_request(self, prompt, max_tokens=256, temperature=0.3):
        """发送提取请求到 LLM"""
        try:
            if self.base_url.startswith('https://'):
                conn = http.client.HTTPSConnection(self.host)
            else:
                conn = http.client.HTTPConnection(self.host)
            
            headers = {
                'Content-Type': 'application/json'
            }
            if self.token:
                headers['Authorization'] = f'Bearer {self.token}'
            
            data = {
                'model': self.model,
                'messages': [
                    {'role': 'system', 'content': '你是一个专业的信息提取助手。请直接输出 5W 结果，不要输出任何思考过程、分析步骤或额外说明。'},
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': max_tokens,
                'temperature': temperature,
                'stream': False
            }
            
            conn.request('POST', f'{self.path}/chat/completions', json.dumps(data), headers)
            response = conn.getresponse()
            response_data = json.loads(response.read().decode())
            conn.close()
            
            return response_data
            
        except Exception as e:
            print(f"[提取请求错误] {str(e)}")
            return None
    
    def _parse_extraction_response(self, response_data):
        """解析 LLM 返回的提取结果
        
        Returns:
            tuple: (extracted_info, status, reason)
                - extracted_info: 提取的 5W 信息（成功时）或 None（失败时）
                - status: "success" | "insufficient_info" | "technical_error" | "format_error"
                - reason: 失败原因说明（成功时为 None）
        """
        
        # 1. 检查响应是否为空（技术故障）
        if response_data is None:
            return None, "technical_error", "API 调用失败，请检查网络连接"
        
        if 'choices' not in response_data or len(response_data['choices']) == 0:
            return None, "technical_error", "LLM 返回空响应，可能是 token 不足或模型错误"
        
        # 2. 提取内容
        choice = response_data['choices'][0]
        message = choice.get('message', {})
        
        # 优先使用 content 字段（最终结果），而不是 reasoning_content（思考过程）
        content = message.get('content', '').strip()
        
        # 如果 content 为空，才尝试从 reasoning_content 提取
        if not content:
            reasoning_content = message.get('reasoning_content', '')
            
            if reasoning_content:
                # 从 reasoning_content 中提取最后的 5W 结果
                who_match = re.search(r'-\s*Who:', reasoning_content)
                if who_match:
                    content = reasoning_content[who_match.start():].strip()
                else:
                    lines = reasoning_content.strip().split('\n')
                    content = '\n'.join(lines[-5:]).strip()
        
        # 如果仍然为空，技术故障
        if not content:
            delta = choice.get('delta', {})
            content = delta.get('content', '').strip()
        
        if not content:
            return None, "technical_error", "LLM 返回空内容，无法提取信息"
        
        # 3. 检查是否为累积模式的混合格式
        if '=== 历史对话摘要 ===' in content and '=== 当前对话 5W 信息 ===' in content:
            # 累积模式：提取 5W 部分
            five_w_section = content.split('=== 当前对话 5W 信息 ===')[1].strip()
            
            # 检查 5W 部分是否可提取
            if '【无法提取】' in five_w_section:
                # 即使历史有摘要，但当前对话仍无法提取
                return None, "insufficient_info", "当前对话内容可提取的信息太少"
            
            # 验证 5W 格式
            required_keywords = ['Who', 'What']
            has_required = any(keyword in five_w_section for keyword in required_keywords)
            
            if not has_required:
                return None, "format_error", f"5W 部分不符合格式要求。内容: {five_w_section[:200]}"
            
            # 提取成功，返回完整内容（包含历史摘要和 5W）
            print(f"[解析成功] 累积模式：提取到 {len(content)} 字符（含历史摘要）")
            return content, "success", None
        
        # 4. 检查 LLM 是否标记为“无法提取”（标准模式）
        if "【无法提取】" in content:
            reason_match = re.search(r'【无法提取】(.+)', content)
            reason = reason_match.group(1).strip() if reason_match else "对话内容无法提取"
            return None, "insufficient_info", reason
        
        # 5. 验证是否包含 5W 关键字段（标准模式）
        required_keywords = ['Who', 'What']
        has_required = any(keyword in content for keyword in required_keywords)
        
        if not has_required:
            if len(content) < 50:
                return None, "insufficient_info", "返回内容过短，无法提取有效信息"
            else:
                print(f"[调试] 返回内容前200字符: {content[:200]}")
                return None, "format_error", f"返回内容不符合 5W 格式要求（缺少 Who/What 字段）。返回内容长度: {len(content)} 字符"
        
        # 6. 检查“未提及”数量
        unmentioned_count = content.count("未提及")
        if unmentioned_count >= 4:
            return None, "insufficient_info", "对话内容可提取的信息太少，没有值得提取的关键信息"
        
        # 7. 提取成功
        print(f"[解析成功] 标准模式：提取到 {len(content)} 字符的 5W 结果")
        return content, "success", None
    
    def _save_to_log_file(self, extracted_info, round_number, recent_messages=None, is_cumulative=False, counter_value=0, should_compress=False):
        """将提取的关键信息保存到日志文件（增强版）
        
        Args:
            extracted_info: 提取的 5W 信息字符串
            round_number: 对话轮次
            recent_messages: 最近的消息列表（用于记录原始对话）
            is_cumulative: 是否为累积模式
            counter_value: 当前计数器值
            should_compress: 是否触发了压缩
        """
        
        log_dir = os.path.dirname(self.log_file_path)
        
        try:
            # 如果目录不存在，创建目录
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
                print(f"[日志保存] 创建目录: {log_dir}")
            
            # 获取当前时间
            from datetime import datetime
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 判断提取模式
            if is_cumulative:
                extract_mode = "累积模式（包含历史对话）"
            else:
                extract_mode = "标准模式"
            
            # 判断触发原因
            trigger_reason = f"计数器达到阈值 ({counter_value} % {self.extract_interval} == 0)"
            if is_cumulative and counter_value > self.extract_interval:
                trigger_reason += "，且之前有失败记录"
            
            # 开始构建日志内容
            log_content = "\n" + "=" * 60 + "\n"
            log_content += f"【记录时间】{current_time}\n"
            log_content += f"【对话轮次】第 {round_number} 轮\n"
            log_content += f"【提取模式】{extract_mode}\n"
            log_content += f"【计数器状态】extract_message_counter = {counter_value}\n"
            log_content += f"【触发原因】{trigger_reason}\n"
            log_content += "=" * 60 + "\n\n"
            
            # 判断是成功还是失败
            if extracted_info and "无法提取" not in extracted_info:
                # 成功提取
                log_content += "📊 5W 提取结果：\n"
                log_content += extracted_info.strip() + "\n\n"
                log_content += "✅ 提取状态：成功"
                if is_cumulative:
                    log_content += "（累积模式）"
                log_content += "\n"
            else:
                # 提取失败
                log_content += "❌ 提取状态：失败\n"
                # 提取失败原因
                if extracted_info:
                    reason_line = [line for line in extracted_info.split('\n') if '原因' in line or '无法提取' in line]
                    if reason_line:
                        log_content += f"【失败原因】{reason_line[0].strip()}\n"
                    else:
                        log_content += f"【失败原因】{extracted_info.strip()}\n"
                else:
                    log_content += "【失败原因】未知错误\n"
                log_content += "\n"
            
            # 添加原始对话记录
            if recent_messages:
                log_content += f"\n📝 原始对话（最近 {len(recent_messages)} 条消息）：\n"
                for i, msg in enumerate(recent_messages, 1):
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    
                    # 对 assistant 的内容进行截断和总结
                    if role == 'assistant':
                        # 只保留前 50 个字符，后面加省略号
                        if len(content) > 50:
                            summary = content[:50].replace('\n', ' ').strip() + "..."
                        else:
                            summary = content.replace('\n', ' ').strip()
                        log_content += f"[{i}] {role}: {summary}\n"
                    else:
                        # user 的消息完整显示
                        log_content += f"[{i}] {role}: {content}\n"
                log_content += "\n"
            
            # 添加保存位置和后续操作
            log_content += f"💾 保存位置：{self.log_file_path}\n"
            
            if should_compress:
                log_content += f"🗜️ 后续操作：触发压缩（保留后 {self.max_rounds * 2} 条）\n"
            else:
                log_content += f"🗜️ 后续操作：未触发压缩\n"
            
            log_content += "=" * 60 + "\n"
            
            # 写入文件
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                f.write(log_content)
            
            print(f"[日志保存] 成功保存到: {self.log_file_path}")
            return True
            
        except Exception as e:
            print(f"[日志保存] ❌ 保存失败: {e}")
            return False
    
    def _save_failed_extraction(self, round_number, reason, recent_messages):
        """保存无法提取的记录到日志（便于追踪和分析）
        
        Args:
            round_number: 对话轮次
            reason: 失败原因
            recent_messages: 最近的对话消息
        """
        
        try:
            # 生成对话摘要
            summary = self._generate_dialogue_summary(recent_messages)
            
            # 获取当前时间戳
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            
            # 格式化日志条目
            log_entry = f"\n{'='*60}\n"
            log_entry += f"【记录时间】{timestamp}\n"
            log_entry += f"【对话轮次】第 {round_number} 轮\n"
            log_entry += f"【提取状态】❌ 无法提取\n"
            log_entry += f"【失败原因】{reason}\n"
            log_entry += f"【对话摘要】{summary}\n"
            log_entry += f"{'='*60}\n"
            
            # 追加写入文件
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                f.write(log_entry)
            
            print(f"[关键信息提取] 📝 已记录失败信息到日志")
            print(f"[关键信息提取] 💡 原因: {reason}")
            
            # 同时也调用 _save_to_log_file 保存一份详细格式的失败记录（可选，为了格式统一）
            self._save_to_log_file(
                extracted_info=f"【无法提取】{reason}",
                round_number=round_number,
                recent_messages=recent_messages,
                is_cumulative=(self.extract_message_counter > self.extract_interval),
                counter_value=self.extract_message_counter,
                should_compress=False  # 失败时不触发压缩
            )
            
        except Exception as e:
            print(f"[关键信息提取] ⚠️ 保存失败记录时出错: {str(e)}")
    
    def _save_short_consultation_record(self, reason, recent_messages, round_number=None):
        """兜底归档策略：保存简短问诊记录（即使 LLM 判定信息不足）
        
        设计原则：
        - 手动触发优先级最高：确保用户永远看到正向反馈
        - 原始对话备份：即使无法提取 5W，也保存完整对话供后续查阅
        - 标记为“简短问诊记录”：区分于正式的 5W 提取结果
        
        Args:
            reason: 保存原因（如“信息不足”、“技术故障”等）
            recent_messages: 最近的对话消息列表
            round_number: 对话轮次（可选，自动计算）
        """
        try:
            # 如果未提供轮次，自动计算
            if round_number is None:
                round_number = len(self.chat_history) // 2
            
            # 获取当前时间戳
            from datetime import datetime
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 开始构建日志内容
            log_content = "\n" + "=" * 60 + "\n"
            log_content += f"【记录时间】{current_time}\n"
            log_content += f"【对话轮次】第 {round_number} 轮\n"
            log_content += f"【记录类型】📝 简短问诊记录（兜底归档）\n"
            log_content += f"【保存原因】{reason}\n"
            log_content += "=" * 60 + "\n\n"
            
            # 添加原始对话记录
            if recent_messages:
                log_content += f"💬 原始对话（共 {len(recent_messages)} 条消息）：\n\n"
                for i, msg in enumerate(recent_messages, 1):
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    
                    # 对 assistant 的内容进行截断和总结
                    if role == 'assistant':
                        # 只保留前 100 个字符，后面加省略号
                        if len(content) > 100:
                            summary = content[:100].replace('\n', ' ').strip() + "..."
                        else:
                            summary = content.replace('\n', ' ').strip()
                        log_content += f"[{i}] AI助手: {summary}\n\n"
                    else:
                        # user 的消息完整显示
                        log_content += f"[{i}] 用户: {content}\n\n"
            else:
                log_content += "💬 无对话记录\n\n"
            
            # 添加说明
            log_content += "📌 说明：\n"
            log_content += "   本次问诊因信息量不足或技术原因未能提取标准 5W 信息，\n"
            log_content += "   但系统已为您保存了完整的原始对话记录，方便您后续查阅。\n\n"
            
            # 添加保存位置
            log_content += f"💾 保存位置：{self.log_file_path}\n"
            log_content += "=" * 60 + "\n"
            
            # 写入文件
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                f.write(log_content)
            
            print(f"[兜底归档] ✅ 已成功保存简短问诊记录到: {self.log_file_path}")
            return True
            
        except Exception as e:
            print(f"[兜底归档] ❌ 保存失败: {e}")
            return False

    def _generate_dialogue_summary(self, recent_messages):
        """生成对话摘要（用于失败记录）
        
        Args:
            recent_messages: 最近的对话消息列表
            
        Returns:
            str: 对话摘要（50 字以内）
        """
        try:
            # 提取用户和 AI 的消息
            user_msgs = [msg.get('content', '') for msg in recent_messages if msg.get('role') == 'user']
            ai_msgs = [msg.get('content', '') for msg in recent_messages if msg.get('role') == 'assistant']
            
            # 拼接摘要
            summary_parts = []
            if user_msgs:
                summary_parts.append(f"用户：{'、'.join(user_msgs[:3])}")
            if ai_msgs:
                summary_parts.append(f"AI：{'、'.join(ai_msgs[:3])}")
            
            summary = ' | '.join(summary_parts)
            
            # 截断到 50 字
            if len(summary) > 50:
                summary = summary[:47] + "..."
            
            return summary
            
        except Exception as e:
            return f"生成摘要失败: {str(e)}"
    
    def _clean_extraction_content(self, content):
        """清理提取内容，移除冗余思考过程，保留对话上下文和5W结果"""
        if not content:
            return content
        
        # 查找 "Analyze the Dialogue Content" 或 "Analyze the Dialogue" 的位置
        # 支持格式：2. **Analyze the Dialogue:** 或 2. **Analyze the Dialogue Content:**
        dialogue_match = re.search(r'\d+\.\s*\*{0,2}Analyze the Dialogue(?: Content)?\*{0,2}:', content)
        
        # 查找标准格式的 5W 结果（在行首，带 - 前缀或不带）
        # 排除 **Who:** 这种 Markdown 格式
        five_w_match = re.search(r'(?:^|\n)\s*-\s*(Who|What|When|Where|Why):', content, re.MULTILINE)
        
        # 如果没有找到带 - 的格式，尝试找不带 - 的格式（但要确保是在行首）
        if not five_w_match:
            five_w_match = re.search(r'(?:^|\n)(Who|What|When|Where|Why):', content, re.MULTILINE)
        
        if dialogue_match and five_w_match:
            # 两者都存在，保留从对话分析开始到结尾的所有内容
            start_pos = dialogue_match.start()
            clean_content = content[start_pos:].strip()
            return clean_content
        elif five_w_match:
            # 只有5W结果，保留5W部分
            start_pos = five_w_match.start()
            clean_content = content[start_pos:].strip()
            return clean_content
        elif dialogue_match:
            # 只有对话分析，保留对话分析部分
            start_pos = dialogue_match.start()
            clean_content = content[start_pos:].strip()
            return clean_content
        
        # 如果都没有匹配，尝试移除常见的思考过程标记
        thinking_markers = [
            'Thinking Process:',
            '思考过程',
            '分析过程',
            'Let me think',
            'First,',
            'Second,',
            'Finally,'
        ]
        
        for marker in thinking_markers:
            if marker in content:
                parts = content.split(marker, 1)
                if len(parts) > 1:
                    remaining = parts[1].strip()
                    # 检查剩余内容是否包含有用信息
                    if remaining and len(remaining) > 50:
                        return remaining.strip()
        
        # 如果都没有匹配，返回原始内容
        return content
    
    def _show_extract_settings(self):
        """显示关键信息提取相关设置"""
        print("\n[关键信息提取设置]")
        print(f"  自动提取: {'✅ 启用' if self.auto_extract_enabled else '❌ 禁用'}")
        print(f"  下次跳过: {'是' if self.skip_next_extract else '否'}")
        print(f"  提取频率: 每 {self.extract_interval} 轮对话")
        print(f"  日志路径: {self.log_file_path}")
        print(f"\n[可用命令]")
        print(f"  skip_extract / 跳过提取   - 跳过下次提取")
        print(f"  enable_extract / 启用提取  - 启用自动提取")
        print(f"  disable_extract / 禁用提取 - 禁用自动提取")
        print(f"  extract_settings / 提取设置 - 显示此信息")
        print()
    
    def run(self):
        """运行交互式聊天界面"""
        print("=" * 60)
        print("LLM 聊天压缩客户端（Practice03）")
        print("=" * 60)
        print(f"模型: {self.model}")
        print(f"API地址: {self.base_url}")
        print("=" * 60)
        print("核心功能:")
        print("  ✓ 自动检测对话轮数和上下文长度")
        print("  ✓ 超过5轮或3000 tokens时自动触发压缩")
        print("  ✓ 前70%内容LLM总结，后30%保留原文")
        print("  ✓ 支持工具调用（文件操作、网页访问）")
        print("=" * 60)
        print("可用命令:")
        print("  exit/quit - 退出程序")
        print("  clear     - 清空聊天历史")
        print("  debug     - 切换调试模式")
        print("  log       - 切换详细日志模式")
        print("  stats     - 显示聊天统计信息")
        print("  skip_compress / 跳过压缩 - 跳过下次自动压缩")
        print("  enable_compress / 启用压缩 - 启用自动压缩")
        print("  disable_compress / 禁用压缩 - 禁用自动压缩")
        print("  compress_settings / 压缩设置 - 显示压缩设置")
        print("  skip_extract / 跳过提取   - 跳过下次关键信息提取")
        print("  disable_extract / 禁用提取 - 禁用自动提取")
        print("  extract_settings / 提取设置 - 查看提取设置")
        print("  按 Ctrl+C 随时退出")
        print("=" * 60)
        print()
        
        debug_mode = False
        
        while True:
            try:
                user_input = input("你: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['exit', 'quit']:
                    print("再见！")
                    break
                
                if user_input.lower() == 'clear':
                    self.clear_history()
                    continue
                
                if user_input.lower() == 'debug':
                    debug_mode = not debug_mode
                    status = "已启用" if debug_mode else "已禁用"
                    print(f"调试模式{status}")
                    continue
                
                if user_input.lower() == 'log':
                    self.debug_mode = not self.debug_mode
                    status = "已启用" if self.debug_mode else "已禁用"
                    print(f"📝 详细日志模式{status}")
                    if self.debug_mode:
                        print("   ✓ 将显示所有调试信息")
                        print("   ✓ 包括 API 请求/响应、工具调用详情")
                    else:
                        print("   ✓ 仅显示关键信息")
                        print("   ✓ 界面更简洁")
                    continue
                
                if user_input.lower() == 'stats':
                    self.show_history_stats()
                    continue
                
                # 处理压缩控制命令
                if user_input.lower() in ['skip_compress', '跳过压缩']:
                    self.skip_next_compress = True
                    print("[设置] 下次将跳过自动压缩")
                    continue
                
                if user_input.lower() in ['enable_compress', '启用压缩']:
                    self.auto_compress_enabled = True
                    self.skip_next_compress = False
                    print("[设置] 已启用自动压缩")
                    continue
                
                if user_input.lower() in ['disable_compress', '禁用压缩']:
                    self.auto_compress_enabled = False
                    print("[设置] 已禁用自动压缩")
                    continue
                
                if user_input.lower() in ['compress_settings', '压缩设置']:
                    self._show_compress_settings()
                    continue
                
                # 处理关键信息提取控制命令
                if user_input.lower() in ['skip_extract', '跳过提取']:
                    self.skip_next_extract = True
                    print("[设置] 下次将跳过关键信息提取")
                    continue
                
                if user_input.lower() in ['enable_extract', '启用提取']:
                    self.auto_extract_enabled = True
                    self.skip_next_extract = False
                    print("[设置] 已启用自动提取")
                    continue
                
                if user_input.lower() in ['disable_extract', '禁用提取']:
                    self.auto_extract_enabled = False
                    print("[设置] 已禁用自动提取")
                    continue
                
                if user_input.lower() in ['extract_settings', '提取设置']:
                    self._show_extract_settings()
                    continue
                
                # ========== 处理 /search 命令 ==========
                if user_input.startswith('/search'):
                    # 提取搜索关键词
                    query = user_input[7:].strip()  # 去掉 '/search' 前缀
                    if not query:
                        query = "查找聊天历史"  # 默认查询
                    
                    print(f"\n{'='*60}")
                    print(f"[搜索命令] 搜索关键词: {query}")
                    print(f"{'='*60}")
                    
                    # 直接调用工具
                    result = tools.search_chat_history(query, debug=self.debug_mode)
                    
                    # 显示结果
                    if result.get('success'):
                        print(f"\n[搜索结果] {result.get('message')}")
                        if result.get('content'):
                            content = result.get('content')
                            # 清理内容（移除 Thinking Process）
                            clean_content = self._clean_extraction_content(content)
                            print(clean_content)
                        print(f"\n{'='*60}")
                    else:
                        print(f"\n[搜索失败] {result.get('message', result.get('error'))}")
                        if result.get('suggestion'):
                            print(f"[建议] {result.get('suggestion')}")
                        print(f"\n{'='*60}")
                    
                    continue  # 不继续处理为普通对话
                
                # 累加 5W 提取计数器
                self.extract_message_counter += 1
                if self.debug_mode:
                    print(f"[调试] 5W 提取计数器: {self.extract_message_counter}")
                
                self.add_to_history('user', user_input)
                
                print("\nAI: ", end='', flush=True)
                if debug_mode:
                    print(f"\n[调试] 准备调用 send_request_stream...")
                    print(f"[调试] 用户输入长度: {len(user_input)} 字符")
                    print(f"[调试] 当前聊天历史条数: {len(self.chat_history)}")
                
                response, time_taken = self.send_request_stream(user_input, debug=debug_mode)
                
                if debug_mode:
                    print(f"\n[调试] send_request_stream 返回")
                    print(f"[调试] response 类型: {type(response)}")
                    print(f"[调试] response 值: '{response}'")
                    print(f"[调试] response 长度: {len(response) if response else 0}")
                    print(f"[调试] time_taken: {time_taken}")
                
                # 注意：response 已经在 _send_single_stream 中流式输出了，这里不需要再打印
                # 只需要添加一个换行符即可
                if response:
                    print()  # 添加换行，与流式输出的内容分隔
                if response:
                    self.add_to_history('assistant', response)
                    print(f"[耗时: {time_taken:.2f}秒]")
                    
                    # ========== AI 回复完成后，检查是否需要提取和压缩 ==========
                    # 检查是否达到提取间隔
                    if self.extract_message_counter > 0 and self.extract_message_counter % self.extract_interval == 0:
                        print("\n[系统触发] 检测到对话达到提取阈值，开始执行归档与清理...")
                        
                        # 1. 先执行关键信息提取 (5W)
                        if self.auto_extract_enabled and not self.skip_next_extract:
                            print("[系统触发] 步骤 1/2: 正在执行 5W 关键信息提取...")
                            self._extract_5w_info()
                        elif self.skip_next_extract:
                            self.skip_next_extract = False
                            print("[系统触发] 用户已跳过本次 5W 提取")
                        
                        # 2. 后执行上下文压缩（仅在满足压缩条件时）
                        if self._should_compress():
                            if self.auto_compress_enabled and not self.skip_next_compress:
                                print("\n[系统触发] 步骤 2/2: 正在执行上下文压缩...")
                                self._compress_chat_history()
                            elif self.skip_next_compress:
                                self.skip_next_compress = False
                                print("[系统触发] 用户已跳过本次上下文压缩")
                    else:
                        # 未达到提取间隔，不执行任何操作
                        pass
                    
                else:
                    print("\n抱歉，模型没有返回有效内容。")
                    self.chat_history.pop()
                
                print()
                
            except KeyboardInterrupt:
                print("\n\n收到中断信号，退出聊天...")
                break
            except Exception as e:
                print(f"\n发生错误: {e}")
                print("请重试或输入 'exit' 退出")
                print()

if __name__ == "__main__":
    client = ChatCompressClient()
    client.run()
