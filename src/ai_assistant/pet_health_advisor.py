"""
AI 宠物健康顾问模块

作者：刘同学
日期：2026-04-16
课程：《数据结构》项目 - Phase 1

模块职责：
- 基于 LLM 提供智能宠物健康咨询
- 分析喂养计划、诊断症状、生成健康建议
- 支持猫/狗差异化知识库

架构设计原则（面向未来商业化）：
1. **接口隔离**：所有方法接收简化的数据字典（DTO），不直接依赖 PetProfile 对象
   → 优势：底层存储从内存切换到 MySQL/PostgreSQL 时，AI 逻辑无需修改
   
2. **Prompt 工程服务化**：所有 LLM Prompt 封装为独立方法
   → 优势：便于 A/B 测试不同 Prompt 效果，统一管理提示词版本
   
3. **错误韧性**：完善的异常处理（超时、网络错误、无效 JSON）
   → 优势：生产环境中保证系统稳定性，避免单点故障
   
4. **可扩展性**：预留物种判断、多语言支持、个性化配置接口
   → 优势：未来支持更多宠物类型（鸟、鱼、爬行动物等）

技术栈：
- ChatCompressClient：本地 LLM 客户端（Qwen via LM Studio）
- 标准库：json, time, logging（错误追踪）
"""

import sys
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

# 配置导入路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ai_assistant.chat_compress_client import ChatCompressClient

# 配置日志
log_dir = project_root / 'logs'
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'pet_health_advisor.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('PetHealthAdvisor')


class PetHealthAdvisor:
    """
    智能宠物健康顾问
    
    整合 LLM 能力与宠物档案数据，提供个性化的健康咨询服务。
    
    设计理念：
    - 输入：简化的数据字典（DTO），解耦数据存储层
    - 输出：结构化的建议文本，易于前端展示
    - 容错：LLM 失败时降级为规则引擎建议
    
    时间复杂度分析：
    - LLM 调用：O(1) 次网络请求（但实际耗时取决于 LLM 响应速度，通常 2-10 秒）
    - 数据格式化：O(n) n 为健康记录数量
    - 总体：受限于 LLM 响应时间，而非算法复杂度
    
    示例用法：
        >>> advisor = PetHealthAdvisor()
        >>> pet_data = {
        ...     "name": "小白",
        ...     "species": "dog",
        ...     "breed": "金毛犬",
        ...     "age": 2,
        ...     "weight": 25.5,
        ...     "gender": "male",
        ...     "recent_records": [
        ...         {"date": "2026-04-15", "type": "checkup", "desc": "常规体检"}
        ...     ]
        ... }
        >>> advice = advisor.analyze_feeding_plan(pet_data)
        >>> print(advice)
    """
    
    def __init__(self):
        """初始化 AI 健康顾问（采用组合模式）"""
        try:
            self.client = ChatCompressClient()
            # 医疗模式下关闭自动压缩，防止丢失关键病情描述
            self.client.auto_compress_enabled = False
            logger.info("AI 健康顾问初始化成功 (医疗模式)")
        except Exception as e:
            logger.error(f"AI 健康顾问初始化失败: {e}")
            raise
    
    # ==================== 核心业务方法 ====================
    
    def analyze_feeding_plan(self, pet_profile_dict: Dict[str, Any]) -> str:
        """
        分析并生成个性化喂养计划
        
        架构设计说明：
        - 接收字典而非 PetProfile 对象 → 解耦数据存储层
        - 未来迁移到 MySQL 时，只需修改数据获取逻辑，AI 分析逻辑不变
        
        时间复杂度：O(1) 次 LLM 调用（实际耗时 2-10 秒）
        
        Args:
            pet_profile_dict: 宠物档案字典，包含以下字段：
                - name (str): 宠物名字
                - species (str): 物种 "cat" / "dog" / "other"
                - breed (str): 品种
                - age (float): 年龄（岁）
                - weight (float): 体重（公斤）
                - gender (str): 性别
                - recent_records (list): 最近健康记录列表（可选）
        
        Returns:
            str: LLM 生成的喂养建议文本
        
        Raises:
            ValueError: 如果缺少必要字段
            RuntimeError: 如果 LLM 调用失败
        
        示例：
            >>> pet_data = {
            ...     "name": "小白",
            ...     "species": "dog",
            ...     "breed": "金毛犬",
            ...     "age": 2,
            ...     "weight": 25.5
            ... }
            >>> advisor.analyze_feeding_plan(pet_data)
            '根据小白的年龄和体重，建议每日喂食...'
        """
        # 数据校验
        self._validate_pet_profile(pet_profile_dict, required_fields=["name", "species", "age", "weight"])
        
        # 构建 LLM Prompt
        prompt = self._build_feeding_plan_prompt(pet_profile_dict)
        
        # 调用 LLM
        try:
            logger.info(f"开始分析 {pet_profile_dict['name']} 的喂养计划...")
            response, time_taken = self.client.send_request_stream(prompt, max_tokens=1024)
            
            if not response:
                raise RuntimeError("LLM 未返回有效内容")
            
            logger.info(f"喂养计划分析完成，耗时 {time_taken:.2f} 秒")
            return response
            
        except Exception as e:
            logger.error(f"喂养计划分析失败: {e}")
            # 降级策略：返回规则引擎建议
            return self._fallback_feeding_advice(pet_profile_dict)
    
    def diagnose_symptoms(self, pet_profile_dict: Dict[str, Any], symptoms: str) -> str:
        """
        根据症状描述进行初步诊断
        
        架构设计说明：
        - 症状作为独立参数传入 → 支持用户实时输入
        - 结合宠物档案（年龄、品种）提高诊断准确性
        
        时间复杂度：O(1) 次 LLM 调用
        
        Args:
            pet_profile_dict: 宠物档案字典（同 analyze_feeding_plan）
            symptoms: 用户描述的症状（如 "呕吐、腹泻、食欲不振"）
        
        Returns:
            str: LLM 生成的诊断建议（包含可能原因、紧急程度、就医建议）
        
        Raises:
            ValueError: 如果症状描述为空
            RuntimeError: 如果 LLM 调用失败
        
        示例：
            >>> pet_data = {"name": "小花", "species": "cat", "age": 1, "weight": 4.2}
            >>> advisor.diagnose_symptoms(pet_data, "呕吐、腹泻")
            '根据症状描述，可能的原因包括...'
        """
        # 数据校验
        if not symptoms or not symptoms.strip():
            raise ValueError("症状描述不能为空")
        
        self._validate_pet_profile(pet_profile_dict, required_fields=["name", "species", "age"])
        
        # 构建 LLM Prompt
        prompt = self._build_diagnosis_prompt(pet_profile_dict, symptoms)
        
        # 调用 LLM
        try:
            logger.info(f"开始诊断 {pet_profile_dict['name']} 的症状...")
            response, time_taken = self.client.send_request_stream(prompt, max_tokens=1024)
            
            if not response:
                raise RuntimeError("LLM 未返回有效内容")
            
            logger.info(f"症状诊断完成，耗时 {time_taken:.2f} 秒")
            return response
            
        except Exception as e:
            logger.error(f"症状诊断失败: {e}")
            # 降级策略：返回通用建议
            return self._fallback_diagnosis_advice(symptoms)
    
    def generate_health_report(self, pet_profile_dict: Dict[str, Any]) -> str:
        """
        生成综合健康报告
        
        架构设计说明：
        - 整合历史健康记录 → 展示趋势分析能力
        - 输出结构化报告 → 便于前端渲染或导出 PDF
        
        时间复杂度：O(n) n 为健康记录数量（格式化数据）+ O(1) LLM 调用
        
        Args:
            pet_profile_dict: 宠物档案字典，必须包含 recent_records 字段
        
        Returns:
            str: 格式化的健康报告（包含整体评估、风险提示、改进建议）
        
        示例：
            >>> pet_data = {
            ...     "name": "小白",
            ...     "species": "dog",
            ...     "recent_records": [
            ...         {"date": "2026-04-15", "type": "checkup", "desc": "常规体检"},
            ...         {"date": "2026-03-10", "type": "illness", "desc": "感冒发烧"}
            ...     ]
            ... }
            >>> advisor.generate_health_report(pet_data)
        """
        # 数据校验
        self._validate_pet_profile(pet_profile_dict, required_fields=["name", "species"])
        
        if "recent_records" not in pet_profile_dict:
            pet_profile_dict["recent_records"] = []
        
        # 构建 LLM Prompt
        prompt = self._build_health_report_prompt(pet_profile_dict)
        
        # 调用 LLM
        try:
            logger.info(f"开始生成 {pet_profile_dict['name']} 的健康报告...")
            response, time_taken = self.client.send_request_stream(prompt, max_tokens=2048)
            
            if not response:
                raise RuntimeError("LLM 未返回有效内容")
            
            logger.info(f"健康报告生成完成，耗时 {time_taken:.2f} 秒")
            return response
            
        except Exception as e:
            logger.error(f"健康报告生成失败: {e}")
            return f"抱歉，暂时无法生成健康报告。错误信息：{str(e)}"
    
    # ==================== Prompt 工程方法（服务化封装）====================
    
    def _build_feeding_plan_prompt(self, pet_profile_dict: Dict[str, Any]) -> str:
        """
        构建喂养计划分析的 LLM Prompt
        
        设计原则：
        - 结构化 Prompt → 提高 LLM 输出一致性
        - 物种差异化 → 猫/狗营养需求不同
        - 年龄阶段适配 → 幼宠/成宠/老宠喂养策略不同
        
        Args:
            pet_profile_dict: 宠物档案字典
        
        Returns:
            str: 格式化的 Prompt 文本
        """
        name = pet_profile_dict.get("name", "未知宠物")
        species = pet_profile_dict.get("species", "unknown")
        breed = pet_profile_dict.get("breed", "未知品种")
        age = pet_profile_dict.get("age", 0)
        weight = pet_profile_dict.get("weight", 0)
        gender = pet_profile_dict.get("gender", "unknown")
        
        # 物种映射（中文显示）
        species_map = {"cat": "猫咪", "dog": "狗狗", "other": "其他宠物", "unknown": "宠物"}
        species_cn = species_map.get(species, "宠物")
        
        # 年龄阶段判断
        if age < 1:
            life_stage = "幼年"
        elif age < 7:
            life_stage = "成年"
        else:
            life_stage = "老年"
        
        # 构建健康记录摘要（如果有）
        records_summary = ""
        if "recent_records" in pet_profile_dict and pet_profile_dict["recent_records"]:
            records_summary = "\n【最近健康记录】\n"
            for record in pet_profile_dict["recent_records"][-5:]:  # 最近 5 条
                records_summary += f"- {record.get('date', '未知日期')}: {record.get('desc', '无描述')}\n"
        
        prompt = f"""你是一位专业的宠物营养师，请为以下宠物制定个性化的喂养计划。

【宠物档案】
- 名字：{name}
- 物种：{species_cn}
- 品种：{breed}
- 年龄：{age} 岁（{life_stage}期）
- 体重：{weight} kg
- 性别：{"公" if gender == "male" else "母" if gender == "female" else "未知"}
{records_summary}

【任务要求】
请提供以下内容：
1. **每日喂食量建议**：根据年龄、体重计算具体克数
2. **喂食频率**：每日几次，每次间隔多久
3. **营养配比**：蛋白质、脂肪、碳水化合物的比例建议
4. **推荐食物类型**：干粮/湿粮/生骨肉等
5. **注意事项**：该品种/年龄段的特殊饮食禁忌

【输出格式】
请使用清晰的 Markdown 格式，分点列出建议。语气要亲切专业，像在和宠物主人对话。

【开始分析】"""
        
        return prompt
    
    def _build_diagnosis_prompt(self, pet_profile_dict: Dict[str, Any], symptoms: str) -> str:
        """
        构建症状诊断的 LLM Prompt
        
        设计原则：
        - 强调"非医疗诊断"免责声明 → 法律合规
        - 提供紧急程度判断 → 帮助用户决策是否立即就医
        - 结合年龄/品种特点 → 提高诊断准确性
        
        Args:
            pet_profile_dict: 宠物档案字典
            symptoms: 用户描述的症状
        
        Returns:
            str: 格式化的 Prompt 文本
        """
        name = pet_profile_dict.get("name", "未知宠物")
        species = pet_profile_dict.get("species", "unknown")
        breed = pet_profile_dict.get("breed", "未知品种")
        age = pet_profile_dict.get("age", 0)
        
        species_map = {"cat": "猫咪", "dog": "狗狗", "other": "其他宠物", "unknown": "宠物"}
        species_cn = species_map.get(species, "宠物")
        
        prompt = f"""你是一位经验丰富的宠物兽医助手（注意：你不是真正的医生，仅提供参考建议）。

【宠物信息】
- 名字：{name}
- 物种：{species_cn}
- 品种：{breed}
- 年龄：{age} 岁

【症状描述】
{symptoms}

【任务要求】
请提供以下内容：
1. **可能原因**：列出 2-3 个最可能的病因（按可能性排序）
2. **紧急程度**：🟢 低 / 🟡 中 / 🔴 高（并说明判断依据）
3. **家庭护理建议**：在就医前可以采取的措施
4. **何时就医**：什么情况下必须立即去医院
5. **预防措施**：未来如何避免类似问题

【重要声明】
请在回答开头明确标注："⚠️ 本建议仅供参考，不能替代专业兽医诊断。如症状严重或持续，请立即就医。"

【输出格式】
使用清晰的 Markdown 格式，语气要温和专业，避免引起宠物主人恐慌。

【开始诊断】"""
        
        return prompt
    
    def _build_health_report_prompt(self, pet_profile_dict: Dict[str, Any]) -> str:
        """
        构建健康报告的 LLM Prompt
        
        设计原则：
        - 整合历史记录 → 展示趋势分析能力
        - 输出结构化报告 → 便于前端展示或导出
        
        Args:
            pet_profile_dict: 宠物档案字典（包含 recent_records）
        
        Returns:
            str: 格式化的 Prompt 文本
        """
        name = pet_profile_dict.get("name", "未知宠物")
        species = pet_profile_dict.get("species", "unknown")
        breed = pet_profile_dict.get("breed", "未知品种")
        age = pet_profile_dict.get("age", 0)
        weight = pet_profile_dict.get("weight", 0)
        
        species_map = {"cat": "猫咪", "dog": "狗狗", "other": "其他宠物", "unknown": "宠物"}
        species_cn = species_map.get(species, "宠物")
        
        # 格式化健康记录
        records_text = "暂无健康记录"
        if "recent_records" in pet_profile_dict and pet_profile_dict["recent_records"]:
            records_text = ""
            for record in pet_profile_dict["recent_records"]:
                records_text += f"- {record.get('date', '未知日期')} [{record.get('type', '未知类型')}]: {record.get('desc', '无描述')}\n"
        
        prompt = f"""你是一位专业的宠物健康管理师，请根据以下信息生成综合健康报告。

【宠物档案】
- 名字：{name}
- 物种：{species_cn}
- 品种：{breed}
- 年龄：{age} 岁
- 体重：{weight} kg

【健康记录时间线】
{records_text}

【任务要求】
请生成一份结构化的健康报告，包含：
1. **整体评估**：健康状况评分（1-10 分）及简要评价
2. **历史趋势分析**：从健康记录中发现的模式或问题
3. **风险提示**：当前存在的潜在健康风险
4. **改进建议**：具体的行动项（如增加运动、调整饮食、定期体检等）
5. **下次体检建议时间**：根据年龄和健康状况推荐

【输出格式】
使用清晰的 Markdown 格式，包含标题、列表、重点标注。语气要专业且鼓励性强。

【开始生成报告】"""
        
        return prompt
    
    # ==================== 降级策略（LLM 失败时的备选方案）====================
    
    def _fallback_feeding_advice(self, pet_profile_dict: Dict[str, Any]) -> str:
        """
        降级策略：基于规则的喂养建议（当 LLM 不可用时）
        
        设计原则：
        - 保证基本可用性 → 用户体验不中断
        - 简单规则引擎 → 覆盖常见场景
        
        Args:
            pet_profile_dict: 宠物档案字典
        
        Returns:
            str: 基于规则的喂养建议
        """
        name = pet_profile_dict.get("name", "宠物")
        species = pet_profile_dict.get("species", "unknown")
        age = pet_profile_dict.get("age", 0)
        weight = pet_profile_dict.get("weight", 0)
        
        advice = f"【{name} 的喂养建议（基础版）】\n\n"
        
        if species == "dog":
            if age < 1:
                advice += f"- 幼犬期：每日喂食 3-4 次，每次约 {weight * 20:.0f}g 幼犬粮\n"
                advice += "- 选择高蛋白、易消化的幼犬专用粮\n"
            elif age < 7:
                advice += f"- 成犬期：每日喂食 2 次，每次约 {weight * 15:.0f}g 成犬粮\n"
                advice += "- 保持均衡营养，适量添加肉类和蔬菜\n"
            else:
                advice += f"- 老年犬：每日喂食 2 次，每次约 {weight * 12:.0f}g 老年犬粮\n"
                advice += "- 选择低脂、易消化的配方，关注关节健康\n"
        elif species == "cat":
            if age < 1:
                advice += f"- 幼猫期：每日喂食 4-5 次，每次约 {weight * 25:.0f}g 幼猫粮\n"
                advice += "- 保证充足饮水，选择高蛋白猫粮\n"
            elif age < 7:
                advice += f"- 成猫期：每日喂食 2-3 次，每次约 {weight * 20:.0f}g 成猫粮\n"
                advice += "- 干湿搭配，预防泌尿系统疾病\n"
            else:
                advice += f"- 老年猫：每日喂食 2-3 次，每次约 {weight * 18:.0f}g 老年猫粮\n"
                advice += "- 关注肾脏健康，选择低磷配方\n"
        else:
            advice += "- 请咨询专业兽医获取个性化喂养建议\n"
        
        advice += "\n⚠️ 注意：以上为基础建议，具体情况请咨询兽医或宠物营养师。"
        
        return advice
    
    def _fallback_diagnosis_advice(self, symptoms: str) -> str:
        """
        降级策略：基于规则的诊断建议
        
        Args:
            symptoms: 症状描述
        
        Returns:
            str: 通用诊断建议
        """
        advice = "【症状初步分析（基础版）】\n\n"
        advice += "⚠️ 本建议仅供参考，不能替代专业兽医诊断。\n\n"
        
        # 关键词匹配（简单规则引擎）
        urgent_keywords = ["昏迷", "抽搐", "呼吸困难", "大量出血", "中毒"]
        warning_keywords = ["呕吐", "腹泻", "发烧", "不吃东西", "精神萎靡"]
        
        if any(keyword in symptoms for keyword in urgent_keywords):
            advice += "🔴 **紧急程度：高**\n"
            advice += "您的宠物出现严重症状，建议**立即前往宠物医院**！\n\n"
        elif any(keyword in symptoms for keyword in warning_keywords):
            advice += "🟡 **紧急程度：中**\n"
            advice += "建议尽快（24 小时内）带宠物就医检查。\n\n"
        else:
            advice += "🟢 **紧急程度：低**\n"
            advice += "可以先观察 1-2 天，如症状持续或加重再就医。\n\n"
        
        advice += "【家庭护理建议】\n"
        advice += "1. 保持环境安静舒适\n"
        advice += "2. 提供充足的清洁饮水\n"
        advice += "3. 暂时减少活动量，让宠物休息\n"
        advice += "4. 记录症状变化（频率、严重程度）\n\n"
        
        advice += "【何时就医】\n"
        advice += "- 症状持续超过 24 小时\n"
        advice += "- 症状明显加重\n"
        advice += "- 出现新的症状\n"
        advice += "- 宠物精神状态明显变差"
        
        return advice
    
    def compress_memory(self):
        """手动触发记忆压缩（医疗模式下使用）"""
        self.client._compress_chat_history()
        logger.info("已执行手动记忆压缩")

    def get_medical_summary(self):
        """获取当前的病历摘要（5W 信息提取）"""
        summary = self.client._extract_5w_info()
        return summary

    # ==================== 工具方法 ====================
    
    def _validate_pet_profile(self, pet_profile_dict: Dict[str, Any], required_fields: List[str]):
        """
        校验宠物档案字典的必要字段
        
        设计原则：
        - 早期失败 → 快速发现数据问题
        - 清晰错误信息 → 便于调试
        
        Args:
            pet_profile_dict: 宠物档案字典
            required_fields: 必需字段列表
        
        Raises:
            ValueError: 如果缺少必要字段
        """
        missing_fields = [field for field in required_fields if field not in pet_profile_dict]
        if missing_fields:
            raise ValueError(f"宠物档案缺少必要字段: {', '.join(missing_fields)}")
    
    def format_pet_profile_for_llm(self, pet_profile_dict: Dict[str, Any]) -> str:
        """
        将宠物档案字典格式化为 LLM 友好的字符串
        
        设计原则：
        - 简洁明了 → 节省 Token
        - 结构化 → 便于 LLM 理解
        
        Args:
            pet_profile_dict: 宠物档案字典
        
        Returns:
            str: 格式化的字符串
        """
        lines = [
            f"名字: {pet_profile_dict.get('name', '未知')}",
            f"物种: {pet_profile_dict.get('species', 'unknown')}",
            f"品种: {pet_profile_dict.get('breed', '未知')}",
            f"年龄: {pet_profile_dict.get('age', 0)} 岁",
            f"体重: {pet_profile_dict.get('weight', 0)} kg",
            f"性别: {pet_profile_dict.get('gender', 'unknown')}"
        ]
        
        return "\n".join(lines)


# ==================== 测试代码 ====================
if __name__ == "__main__":
    print("=" * 60)
    print("  AI 宠物健康顾问模块测试")
    print("=" * 60)
    
    try:
        advisor = PetHealthAdvisor()
        
        # 测试数据
        dog_profile = {
            "name": "小白",
            "species": "dog",
            "breed": "金毛犬",
            "age": 2,
            "weight": 25.5,
            "gender": "male",
            "recent_records": [
                {"date": "2026-04-15", "type": "checkup", "desc": "常规体检，体重正常"},
                {"date": "2026-03-10", "type": "illness", "desc": "感冒发烧，服药治疗"}
            ]
        }
        
        cat_profile = {
            "name": "小花",
            "species": "cat",
            "breed": "布偶猫",
            "age": 1,
            "weight": 4.2,
            "gender": "female",
            "recent_records": [
                {"date": "2026-04-10", "type": "vaccine", "desc": "接种猫三联疫苗"}
            ]
        }
        
        print("\n【测试1】喂养计划分析")
        print("-" * 60)
        feeding_advice = advisor.analyze_feeding_plan(dog_profile)
        print(feeding_advice)
        
        print("\n\n【测试2】症状诊断")
        print("-" * 60)
        diagnosis = advisor.diagnose_symptoms(cat_profile, "呕吐、腹泻、食欲不振")
        print(diagnosis)
        
        print("\n\n【测试3】健康报告生成")
        print("-" * 60)
        health_report = advisor.generate_health_report(dog_profile)
        print(health_report)
        
        print("\n" + "=" * 60)
        print("  所有测试完成！✅")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
