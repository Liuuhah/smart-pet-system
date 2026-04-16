import os
import json
from datetime import datetime
import stat
import urllib.request
import urllib.error

class Tools:
    def list_directory(self, directory_path):
        """列出指定目录下的所有文件和子目录，包括文件的基本属性（大小、修改时间等）"""
        try:
            # 如果directory_path为None，返回错误
            if directory_path is None:
                return {"error": "未提供目录路径参数"}
            
            # 处理相对路径
            if not os.path.isabs(directory_path):
                directory_path = os.path.abspath(directory_path)
            
            if not os.path.exists(directory_path):
                return {"error": f"目录不存在: {directory_path}"}
            
            if not os.path.isdir(directory_path):
                return {"error": f"路径不是目录: {directory_path}"}
            
            items = []
            for item in os.listdir(directory_path):
                item_path = os.path.join(directory_path, item)
                item_stat = os.stat(item_path)
                
                item_info = {
                    "name": item,
                    "path": item_path,
                    "type": "directory" if os.path.isdir(item_path) else "file",
                    "size": item_stat.st_size,
                    "last_modified": datetime.fromtimestamp(item_stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    "mode": stat.filemode(item_stat.st_mode)
                }
                items.append(item_info)
            
            return {"items": items, "total": len(items)}
        except Exception as e:
            return {"error": f"执行错误: {str(e)}"}
    
    def rename_file(self, directory_path, old_filename, new_filename):
        """修改某个目录下某个文件的名字"""
        try:
            # 检查参数
            if not directory_path or not old_filename or not new_filename:
                return {"error": "缺少必要参数"}
            
            # 处理相对路径
            if not os.path.isabs(directory_path):
                directory_path = os.path.abspath(directory_path)
            
            # 构建完整路径
            old_path = os.path.join(directory_path, old_filename)
            new_path = os.path.join(directory_path, new_filename)
            
            # 检查文件是否存在
            if not os.path.exists(old_path):
                return {"error": f"文件不存在: {old_path}"}
            
            # 检查新文件名是否已存在
            if os.path.exists(new_path):
                return {"error": f"新文件名已存在: {new_path}"}
            
            # 执行重命名
            os.rename(old_path, new_path)
            
            return {"success": True, "message": f"文件已重命名为: {new_filename}", "old_path": old_path, "new_path": new_path}
        except Exception as e:
            return {"error": f"执行错误: {str(e)}"}
    
    def delete_file(self, directory_path, filename):
        """删除某个目录下某个文件"""
        try:
            # 检查参数
            if not directory_path or not filename:
                return {"error": "缺少必要参数"}
            
            # 处理相对路径
            if not os.path.isabs(directory_path):
                directory_path = os.path.abspath(directory_path)
            
            # 构建完整路径
            file_path = os.path.join(directory_path, filename)
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return {"error": f"文件不存在: {file_path}"}
            
            # 检查是否为文件
            if not os.path.isfile(file_path):
                return {"error": f"路径不是文件: {file_path}"}
            
            # 执行删除
            os.remove(file_path)
            
            return {"success": True, "message": f"文件已删除: {filename}", "deleted_path": file_path}
        except Exception as e:
            return {"error": f"执行错误: {str(e)}"}
    
    def create_file(self, directory_path, filename, content):
        """在某个目录下新建一个文件，并且写入内容"""
        try:
            # 检查参数
            if not directory_path or not filename:
                return {"error": "缺少必要参数"}
            
            # 处理相对路径
            if not os.path.isabs(directory_path):
                directory_path = os.path.abspath(directory_path)
            
            # 检查目录是否存在
            if not os.path.exists(directory_path):
                return {"error": f"目录不存在: {directory_path}"}
            
            if not os.path.isdir(directory_path):
                return {"error": f"路径不是目录: {directory_path}"}
            
            # 构建完整路径
            file_path = os.path.join(directory_path, filename)
            
            # 检查文件是否已存在
            if os.path.exists(file_path):
                return {"error": f"文件已存在: {file_path}"}
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content if content else '')
            
            return {"success": True, "message": f"文件已创建: {filename}", "file_path": file_path}
        except Exception as e:
            return {"error": f"执行错误: {str(e)}"}
    
    def read_file(self, directory_path, filename):
        """读取某个目录下面的某个文件的内容"""
        try:
            # 检查参数
            if not directory_path or not filename:
                return {"error": "缺少必要参数"}
            
            # 处理相对路径
            if not os.path.isabs(directory_path):
                directory_path = os.path.abspath(directory_path)
            
            # 构建完整路径
            file_path = os.path.join(directory_path, filename)
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return {"error": f"文件不存在: {file_path}"}
            
            # 检查是否为文件
            if not os.path.isfile(file_path):
                return {"error": f"路径不是文件: {file_path}"}
            
            # 读取文件内容
            encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16']
            content = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                return {"error": f"无法读取文件: {file_path}"}
            
            # 获取文件信息
            file_stat = os.stat(file_path)
            file_info = {
                "name": filename,
                "path": file_path,
                "size": file_stat.st_size,
                "last_modified": datetime.fromtimestamp(file_stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "mode": stat.filemode(file_stat.st_mode)
            }
            
            return {"success": True, "content": content, "file_info": file_info}
        except Exception as e:
            return {"error": f"执行错误: {str(e)}"}
    
    def curl(self, url):
        """通过curl访问网页，并返回网页内容"""
        try:
            # 检查参数
            if not url:
                return {"error": "缺少URL参数"}
            
            original_url = url
            
            # 如果是 wttr.in 天气预报网站，自动添加 format=j1 参数（返回3天预报JSON）
            if 'wttr.in' in url and 'format=' not in url:
                # 判断 URL 是否已经有查询参数
                if '?' in url:
                    url = url + '&format=j1'
                else:
                    url = url + '?format=j1'
            
            # 执行HTTP请求
            with urllib.request.urlopen(url) as response:
                # 获取响应状态码
                status_code = response.getcode()
                # 获取响应头
                headers = dict(response.getheaders())
                # 获取内容类型
                content_type = headers.get('Content-Type', '')
                # 读取响应内容
                content = response.read().decode('utf-8', errors='ignore')
                
                # 对wttr.in特殊处理：保留完整内容（天气预报数据很短）
                if 'wttr.in' in original_url:
                    # wttr.in的format=2返回简洁文本，通常只有几十字节
                    # format=1返回更详细的文本
                    # 不截断，直接返回完整内容
                    pass
                elif 'json' in content_type:
                    # JSON格式保留更多
                    content = content[:5000]
                elif 'html' in content_type:
                    # HTML格式只保留前2000字符
                    content = content[:2000] + '\n...[HTML内容已截断]...'
                else:
                    # 其他格式保留3000字符
                    content = content[:3000]
                
                return {
                    "success": True,
                    "url": url,
                    "status_code": status_code,
                    "content_type": content_type,
                    "content": content
                }
        except urllib.error.URLError as e:
            return {"error": f"URL错误: {str(e)}"}
        except urllib.error.HTTPError as e:
            return {"error": f"HTTP错误: {e.code} - {e.reason}"}
        except Exception as e:
            return {"error": f"执行错误: {str(e)}"}

# 工具实例
tools = Tools()
