import json
import threading
import jieba

import numpy as np
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
import logging

from app.rag.llm import invoke_chat
from app.tools.executor import MERCHANT_TOOLS, USER_TOOLS

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
INTENT_DATASET_PATH = BASE_DIR / "intent_dataset.json"


class SklearnIntentRecognizer:
    def __init__(self, dataset_path: Path):
        self.dataset_path = dataset_path
        self.lock = threading.Lock()

        self.responses = {
            "system_help": "💡 **系统指引 - 帮助中心**\n\n欢迎使用 ReviewPulse Agent！您可以直接向我提问，我会为您查询相关数据或解答疑问。您还可以对我的回答进行“赞/踩”评价哦。",
            "system_version": "💡 **系统指引 - 版本查询**\n\n当前系统版本：**ReviewPulse Agent v2.0 (LLM Router版)**",

            "nav_doc_manage": "💡 **系统指引 - 文档管理**\n\n检测到您想要管理知识库。请点击系统上方菜单栏的 **[文档管理]**，在该页面您可以上传、预览和删除相关文档。",
            "nav_dynamic_manage": "💡 **系统指引 - 动态管理**\n\n想要发布最新活动或店铺公告吗？请点击系统上方菜单栏的 **[动态管理]**，然后点击左上角的蓝色按钮 **[发布新内容]** 即可完成发布！",
            "nav_merchant_comment": "💡 **系统指引 - 评论处理**\n\n想要处理顾客评价？请点击系统上方菜单栏的 **[评论处理]**。在这里您可以清晰地查看所有顾客的留言、评分明细（环境/口味/服务），以及评价的审核状态。",

            "nav_user_collection": "💡 **系统指引 - 收藏管理**\n\n想要查看或管理您的收藏夹？请点击系统上方菜单栏的 **[收藏管理]**。在这里您可以查看所有收藏的优质店铺，还能进行批量取消收藏和修改自定义标签哦。",
            "nav_user_comment": "💡 **系统指引 - 评价管理**\n\n想要管理您发布的评价？请点击系统上方菜单栏的 **[评价管理]**。您可以在那里查看所有历史评价的审核状态（待审核/审核通过/未通过），并支持批量删除操作。"
        }

        self.role_permissions = {
            "nav_doc_manage": ["merchant"],
            "nav_dynamic_manage": ["merchant"],
            "nav_merchant_comment": ["merchant"],
            "nav_user_collection": ["user"],
            "nav_user_comment": ["user"],
            "system_help": ["user", "merchant"],
            "system_version":["user", "merchant"]
        }

        self.confidence_threshold = 0.85
        self.auto_learn_threshold = 0.80
        self.dataset = self._load_or_create_dataset()
        self.known_texts = set(item["text"] for item in self.dataset)
        self._train_model()

    def _load_or_create_dataset(self) -> list[dict]:
        """加载数据集，如果发现是老版本（包含 modify_knowledge_base），则覆写为最新版本"""
        need_rebuild = False
        if self.dataset_path.exists():
            with open(self.dataset_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if any(item["label"] == "modify_knowledge_base" for item in data):
                    need_rebuild = True
                else:
                    return data
        default_data = [
            {"text": "怎么上传文档", "label": "nav_doc_manage"},
            {"text": "帮我添加一份新文件到知识库", "label": "nav_doc_manage"},
            {"text": "如何删除知识库里的内容", "label": "nav_doc_manage"},
            {"text": "我要上传PDF文件", "label": "nav_doc_manage"},

            {"text": "怎么发动态", "label": "nav_dynamic_manage"},
            {"text": "我要发布新内容", "label": "nav_dynamic_manage"},
            {"text": "在哪发店庆公告", "label": "nav_dynamic_manage"},
            {"text": "怎么删除发错的动态", "label": "nav_dynamic_manage"},
            {"text": "怎么通知顾客我的店升级了", "label": "nav_dynamic_manage"},

            {"text": "在哪看用户评价", "label": "nav_merchant_comment"},
            {"text": "顾客评论去哪看", "label": "nav_merchant_comment"},
            {"text": "查看用户打分", "label": "nav_merchant_comment"},

            {"text": "我的收藏夹在哪", "label": "nav_user_collection"},
            {"text": "怎么取消收藏", "label": "nav_user_collection"},
            {"text": "在哪看我收藏的店", "label": "nav_user_collection"},
            {"text": "去哪修改收藏标签", "label": "nav_user_collection"},

            {"text": "我发过的评价在哪看", "label": "nav_user_comment"},
            {"text": "怎么删除我的评价", "label": "nav_user_comment"},
            {"text": "我的评论审核通过了吗", "label": "nav_user_comment"},

            {"text": "系统怎么用", "label": "system_help"},
            {"text": "你能干什么", "label": "system_help"},
            {"text": "当前是什么版本", "label": "system_version"},
            {"text": "查一下更新日志", "label": "system_version"},

            {"text": "商家违规怎么处罚", "label": "query"},
            {"text": "好评返现抓到会怎样", "label": "query"},
            {"text": "帮我找家川菜馆", "label": "query"},
            {"text": "最近有没有差评", "label": "query"},
            {"text": "我最近收到差评了吗", "label": "query"}
        ]
        with open(self.dataset_path, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, ensure_ascii=False, indent=4)
        return default_data


    def _train_model(self):
        texts = [item["text"] for item in self.dataset]
        labels = [item["label"] for item in self.dataset]
        segmented_texts = [" ".join(jieba.cut(text)) for text in texts]
        self.model = make_pipeline(TfidfVectorizer(ngram_range=(1, 2)), MultinomialNB(alpha=0.1))
        self.model.fit(segmented_texts, labels)

    def detect(self, query: str, user_type: str) -> tuple[str, str | None]:
        if not query:
            return "query", None
        query_seg = " ".join(jieba.cut(query))
        probs = self.model.predict_proba([query_seg])[0]
        max_idx = np.argmax(probs)
        max_prob = probs[max_idx]
        predicted_intent = self.model.classes_[max_idx]

        if max_prob >= self.confidence_threshold and predicted_intent != "query":
            allowed_roles = self.role_permissions.get(predicted_intent, ["user", "merchant", "admin"])
            if user_type not in allowed_roles:
                role_names = {"user": "普通用户", "merchant": "入驻商家", "admin": "管理员"}
                current_role = role_names.get(user_type, "未知角色")

                return "system_action", f"🚫 **越权操作拦截**\n\n抱歉，您当前的身份是【{current_role}】，系统暂未向您开放此功能或页面的访问权限。"

            return predicted_intent, self.responses.get(predicted_intent)
        return "query", None


class LLMRouter:
    def __init__(self):
        self.prompt_template = """
        你是一个智能对话路由引擎。你的任务是分析用户的输入，并将其准确分类到以下三个意图之一：

        1. [knowledge_query]：
           - 若角色是商家/管理员：用户在询问平台运营规范、开店流程、处罚规定等必须查阅【平台文档】的问题。
           - 若角色是普通用户：用户在询问店铺环境、商品价格、退换货政策、售后说明等必须查阅【商家店铺文档】的问题。
        2. [tool_use]：
           - 用户意图明确匹配了当前角色可用的某个【特定数据查询工具】。
           - 当前角色({role_name})可用的工具列表及说明如下：
{tools_description}
           - 如果用户的需求可以通过上述某个工具解决（哪怕你作为AI无法直接查到，但工具描述里写了能查），请必须归类为 tool_use！
        3. [complex_planning]：
           - 当用户的问题极其复杂，需要明确的多步拆解，或者涉及两项以上独立任务时。
           - 例如：“对比一下最近两个月的差评占比”、“深度分析一下最近店铺销量下滑的所有可能原因”。
        4. [general_chat]：
           - 日常打招呼、闲聊、情绪宣泄，或者不需要查阅专业知识、也不需要查询具体业务数据,能回答的简单通用问题。
           - 例如：“你好”、“你叫什么名字”、“今天天气真好”、“给我讲个笑话”。
        请严格只输出中括号内的英文单词（knowledge_query, tool_use, complex_planning 或 general_chat），不要输出任何标点符号和额外解释。
        """

    async def route(self, query: str, model_name: str, user_type: str) -> str:
        """调用 LLM 进行意图分类"""
        role_map = {
            "user": "普通买家/消费者",
            "merchant": "平台入驻商家",
            "admin": "平台系统管理员"
        }
        role_name = role_map.get(user_type, "未知角色")

        available_tools = MERCHANT_TOOLS if user_type == "merchant" else USER_TOOLS
        if not available_tools:
            tools_description = "(当前角色暂无可用工具)"
        else:
            tools_description = ""
            for idx, tool in enumerate(available_tools, 1):
                func = tool.get("function", {})
                t_name = func.get("name", "未知工具")
                t_desc = func.get("description", "无描述")
                tools_description += f"{idx}. 工具名称：【{t_name}】，用途：{t_desc}\n"

        system_prompt = self.prompt_template.format(
            role_name=role_name,
            tools_description=tools_description
        )
        try:
            result = await invoke_chat(
                messages=[
                    ("system", system_prompt),
                    ("user", query)
                ],
                model_name=model_name,
                temperature=0.1
            )
            intent = result.strip().lower()

            if "knowledge_query" in intent: return "knowledge_query"
            if "complex_planning" in intent: return "complex_planning"
            if "tool_use" in intent: return "tool_use"
            return "general_chat"

        except Exception as e:
            logger.error(f"LLM 路由失败: {e}")
            return "knowledge_query"


class MasterRouter:
    def __init__(self):
        self.fast_router = SklearnIntentRecognizer(INTENT_DATASET_PATH)
        self.deep_router = LLMRouter()

    async def determine_intent(self, query: str, model_name: str, user_type: str = "user") -> tuple[str, str | None]:
        fast_intent, direct_response = self.fast_router.detect(query, user_type)
        if fast_intent != "query":
            return "system_action", direct_response

        llm_intent = await self.deep_router.route(query, model_name, user_type)
        print(f"大模型分类为 '{query[:15]}...': {llm_intent}")

        return llm_intent, None

master_router = MasterRouter()
