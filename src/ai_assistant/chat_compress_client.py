import os
import json
import time
import http.client
from urllib.parse import urlparse
import re
from tools import tools

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
        self.max_rounds = 4  # 最大对话轮数
        self.max_context_tokens = 3000  # 最大上下文token数
        self.compress_ratio = 0.7  # 压缩前70%的内容
    
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
                    "description": "通过curl访问网页，并返回网页内容",
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
            # 创建压缩后的摘要消息
            compressed_message = {
                'role': 'system',
                'content': f"【历史对话摘要】\n{summary}\n\n【说明】以上是之前对话的摘要，以下是最近的对话内容："
            }
            
            # 更新聊天历史：摘要 + 保留的最近消息
            self.chat_history = [compressed_message] + messages_to_keep
            
            print(f"[压缩完成] 从{total_messages}条消息压缩为{len(self.chat_history)}条消息")
            print(f"[压缩效果] 保留了最近{keep_count}条原始消息")
        else:
            print("[压缩失败] LLM总结失败，保持原聊天记录")
    
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
                'max_tokens': 262144,
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
                        chinese_parts = re.findall(r'[\u4e00-\u9fff][\u4e00-\u9fff，。！？；：""''（）\s]*', draft_text)
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
    
    def send_request_stream(self, prompt, max_tokens=262144, debug=False):
        """发送流式请求，实时输出回复内容（带自动压缩功能）"""
        # 在发送新请求前，检查是否需要压缩
        if self._should_compress():
            self._compress_chat_history()
        
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
                {'role': 'system', 'content': '你是一个友好的AI助手，具有文件操作能力。当用户需要进行文件操作时，请使用工具调用格式。'},
                *self.chat_history,
                {'role': 'user', 'content': prompt}
            ],
            'tools': self.tools,
            'tool_choice': 'auto',
            'max_tokens': max_tokens,
            'temperature': 0.6,
            'stream': True
        }
        
        conn.request('POST', f'{self.path}/chat/completions', json.dumps(data), headers)
        response = conn.getresponse()
        
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
            while True:
                chunk = response.read(1024)
                if not chunk:
                    break
                
                buffer += chunk.decode('utf-8', errors='ignore')
                
                # 处理SSE格式数据
                lines = buffer.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('data: '):
                        json_str = line[6:].strip()
                        if json_str == '[DONE]':
                            # 流式响应结束，检查并执行待处理的工具调用
                            if pending_tool_calls:
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
                                # 有工具调用，返回工具执行后的响应
                                return tool_call_response if tool_call_response else full_content, True
                            else:
                                # 没有工具调用，正常结束
                                return full_content, False
                            continue
                        
                        try:
                            chunk_data = json.loads(json_str)
                            if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                choice = chunk_data['choices'][0]
                                delta = choice.get('delta', {})
                                
                                # 检测工具调用请求
                                if 'tool_calls' in delta:
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
                            pass
                
                # 保留未处理的部分
                if len(lines) > 0:
                    buffer = lines[-1]
                else:
                    buffer = ''
        except KeyboardInterrupt:
            print('\n\n用户中断')
            return full_content, False
        finally:
            conn.close()
        
        # 流结束后的兜底检查
        if pending_tool_calls:
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
            return tool_call_response if tool_call_response else full_content, True
        
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
        data['messages'] = [
            {'role': 'system', 'content': '你是一个友好的AI助手，具有文件操作能力。当用户需要进行文件操作时，请使用工具调用格式。'},
            *self.chat_history,
            {'role': 'user', 'content': prompt}
        ]
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
        print("  stats     - 显示聊天统计信息")
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
                
                if user_input.lower() == 'stats':
                    self.show_history_stats()
                    continue
                
                self.add_to_history('user', user_input)
                
                print("AI: ", end='', flush=True)
                response, time_taken = self.send_request_stream(user_input, debug=debug_mode)
                
                if response:
                    self.add_to_history('assistant', response)
                    print(f"[耗时: {time_taken:.2f}秒]")
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
