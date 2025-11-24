"""
Handles all interactions with the web search tool.
"""
import json
import re
import requests
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from web_scraper import web_scraper
from llm_helper import run_structured_prompt, get_current_api_type


@dataclass
class SearchIntent:
    """Represents the decision on whether a message should trigger web search."""

    should_search: bool
    intent_type: str = "concept"  # concept | character | fresh_news
    query: str = ""
    confidence: float = 0.0
    reason: str = ""
    focus_term: Optional[str] = None
    signals: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "should_search": self.should_search,
            "intent_type": self.intent_type,
            "query": self.query,
            "confidence": self.confidence,
            "reason": self.reason,
            "focus_term": self.focus_term,
            "signals": self.signals,
        }


class SearchHelper:
    """
    搜索助手，用于检测用户查询意图并执行网络搜索
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        })

        # Precompiled keyword lists for intent detection
        self.explicit_search_words = [
            "搜索", "搜一下", "查一下", "查查", "联网", "上网查", "帮我查", "帮我搜",
            "google", "百度", "检索", "look up", "search"
        ]
        self.uncertainty_words = [
            "不知道", "不清楚", "不熟悉", "不了解", "没听过", "忘了", "搞不懂",
            "不明白", "not familiar", "no idea"
        ]
        self.assistant_probe_patterns = [
            r'(?:你知道|你了解|你认识|听说过).+吗',
            r'do you know [^?]+\?'
        ]
        self.time_sensitive_words = [
            "最新", "最近", "现在", "当前", "实时", "今年", "刚刚", "news",
            "today", "update", "发生了什么", "情况如何"
        ]
        self.verification_words = [
            "证据", "根据", "来源", "出处", "参考", "citation", "official", "可信"
        ]
        self.fact_keywords = [
            "历史", "原理", "背景", "信息", "资料", "事实", "统计", "情况", "数据",
            "status", "evidence"
        ]
        self.info_words = [
            "介绍", "说明", "解释", "告诉", "资料", "背景", "梗概", "详情", "概述",
            "what is", "who is", "explain", "describe"
        ]
        self.definition_phrases = [
            "什么是", "啥是", "何谓", "who is", "what is", "定义", "meaning of",
            "什么意思", "是什么", "是哪位", "which is", "告诉我关于"
        ]
        self.character_keywords = [
            "角色", "人物", "女主", "男主", "英雄", "反派", "character", "hero",
            "villain", "npc"
        ]
        self.news_keywords = [
            "新闻", "动态", "发生", "事件", "爆发", "update", "latest", "today",
            "现在怎么样", "现状"
        ]
        self.creative_keywords = [
            "创建", "写一个", "生成", "设计", "编写", "做一个", "write a", "create",
            "build", "生成一个", "请帮我写"
        ]
        self.stopwords_for_queries = {
            "这个", "那个", "角色", "人物", "资料", "信息", "东西", "什么", "请问",
            "一下", "关于", "介绍", "最新", "最近", "帮我", "一个", "有哪些", "情况",
            "发生", "告诉", "故事", "如何", "怎么", "怎么样", "怎样", "请", "想要",
            "需要", "生成", "创造", "创建", "设计", "写", "写个", "写一段", "someone",
            "news", "today"
        }
        self.llm_planner_system_prompt = (
            "You are an assistant that decides whether to perform a real-time web search before "
            "answering a user. You must carefully analyze the user's message, determine if fresh, factual, or "
            "character-specific information from the internet is required, and output a strict JSON object with "
            "the following fields: should_search (bool), intent_type (concept|character|fresh_news), query "
            "(string), confidence (0-1 float), reason (short string), focus_term (string). Only respond with JSON."
        )

    def _add_signal(self, signals: Dict[str, Dict[str, Any]], key: str, weight: float, explanation: str):
        signals[key] = {"weight": weight, "explanation": explanation}

    def _collect_search_signals(self, message: str, focus_term: Optional[str]) -> Dict[str, Dict[str, Any]]:
        signals: Dict[str, Dict[str, Any]] = {}
        lowered = message.lower()

        if any(word in message for word in self.explicit_search_words):
            self._add_signal(signals, 'explicit_request', 3.2, "用户明确要求联网/搜索")

        if any(word in message for word in self.uncertainty_words):
            self._add_signal(signals, 'knowledge_gap', 1.6, "用户表示不熟悉或缺乏信息")

        for pattern in self.assistant_probe_patterns:
            if re.search(pattern, message, flags=re.IGNORECASE):
                self._add_signal(signals, 'knowledge_gap', 1.5, "用户确认助手是否了解某对象")
                break

        if any(word in message for word in self.time_sensitive_words) or re.search(r'20\d{2}', message):
            self._add_signal(signals, 'time_sensitive', 2.4, "问题涉及最新/时间敏感信息")

        if '?' in message or '？' in message:
            self._add_signal(signals, 'question_form', 1.0, "输入呈疑问句形式")

        if any(word in lowered for word in ['what is', 'who is', 'explain', 'tell me about', 'can you explain']):
            self._add_signal(signals, 'english_query', 1.4, "英文信息查询需求")

        if any(word in message for word in self.verification_words):
            self._add_signal(signals, 'verification_need', 1.5, "用户要求权威来源/证据")

        if any(word in message for word in self.fact_keywords):
            self._add_signal(signals, 'factual_need', 1.2, "问题涉及客观资料")

        if any(word in message for word in self.info_words):
            self._add_signal(signals, 'info_request', 1.3, "用户请求现有信息简介")

        if any(phrase in message for phrase in self.definition_phrases):
            self._add_signal(signals, 'definition_request', 1.4, "用户在询问概念/定义")

        if focus_term:
            self._add_signal(signals, 'specific_target', 1.1, f"检测到可能的查询对象: {focus_term}")

        if any(word in message for word in self.creative_keywords):
            self._add_signal(signals, 'creative_only', -2.3, "输入以创作/生成需求为主")

        return signals

    def _normalize_focus_term(self, text: str) -> str:
        if not text:
            return ""
        cleaned = text.strip()
        cleaned = cleaned.strip("，,。.?？!！：:;·-~ ")
        for prefix in ['关于', '对于', '针对', '介绍', '说明']:
            if cleaned.startswith(prefix) and len(cleaned) > len(prefix) + 1:
                cleaned = cleaned[len(prefix):]
        for suffix in ['角色', '人物', '设定', '资料', '信息']:
            if cleaned.endswith(suffix) and len(cleaned) > len(suffix) + 1:
                cleaned = cleaned[:-len(suffix)]
        return cleaned.strip()

    def _extract_focus_term(self, message: str) -> Optional[str]:
        if not message:
            return None

        search_patterns = [
            r'(?:联网)?(?:搜索|搜|查)(?:一下|一下下|下|一波)?(?P<term>[\u4e00-\u9fa5A-Za-z0-9·]{2,64})',
            r'look up (?P<term>[A-Za-z0-9\s\-]{2,64})',
            r'google (?P<term>[A-Za-z0-9\s\-]{2,64})'
        ]
        for pattern in search_patterns:
            match = re.search(pattern, message, flags=re.IGNORECASE)
            if match:
                term = self._normalize_focus_term(match.group('term'))
                if term:
                    return term

        ask_assistant_patterns = [
            r'(?:你知道|你了解|你认识|听说过)(?P<term>[\u4e00-\u9fa5A-Za-z0-9·]{2,32})(?:吗)?',
            r'do you know (?P<term>[A-Za-z0-9\s\-]{2,64})'
        ]
        for pattern in ask_assistant_patterns:
            match = re.search(pattern, message, flags=re.IGNORECASE)
            if match:
                term = self._normalize_focus_term(match.group('term'))
                if term:
                    return term

        quoted = re.search(r'[“"《「『【(（](?P<term>[\u4e00-\u9fa5A-Za-z0-9\s\-·]{2,64})[”"》」』】)）]', message)
        if quoted:
            term = self._normalize_focus_term(quoted.group('term'))
            if term:
                return term

        cn_patterns = [
            r'什么是(?P<term>[^?？。！!]+)',
            r'(?P<term>[^?？。！!]+?)是什么',
            r'(?P<term>[^?？。！!]+?)是谁',
            r'介绍(?:一下)?(?P<term>[^?？。！!]+)',
            r'关于(?P<term>[^?？。！!]+?)(?:的|是|有)',
        ]
        for pattern in cn_patterns:
            match = re.search(pattern, message)
            if match:
                term = self._normalize_focus_term(match.group('term'))
                if term:
                    return term

        en_patterns = [
            r'what is (?P<term>[a-z0-9\s\-&]+)',
            r'who is (?P<term>[a-z0-9\s\-&]+)',
            r'can you explain (?P<term>[a-z0-9\s\-&]+)',
            r'tell me about (?P<term>[a-z0-9\s\-&]+)',
            r'explain (?P<term>[a-z0-9\s\-&]+)',
        ]
        lowered = message.lower()
        for pattern in en_patterns:
            match = re.search(pattern, lowered)
            if match:
                term = self._normalize_focus_term(match.group('term'))
                if term:
                    return term

        return None

    def _extract_chinese_candidates(self, message: str) -> List[str]:
        return re.findall(r'[\u4e00-\u9fa5]{2,8}', message)

    def _extract_english_candidates(self, message: str) -> List[str]:
        candidates = re.findall(r'[A-Za-z][A-Za-z0-9\s\-]{2,60}', message)
        return [cand.strip() for cand in candidates]

    def _derive_query_from_message(self, message: str, intent_type: str, focus_term: Optional[str]) -> str:
        if focus_term:
            return focus_term[:80]

        if intent_type == 'character':
            char_patterns = [
                r'(?P<name>[\u4e00-\u9fa5A-Za-z0-9·]{2,16})(?:这个|这位|这名)?(?:角色|人物)',
                r'角色(?P<name>[\u4e00-\u9fa5A-Za-z0-9·]{2,16})',
                r'character (?P<name>[A-Za-z0-9\s\-]{2,32})'
            ]
            for pattern in char_patterns:
                match = re.search(pattern, message, flags=re.IGNORECASE)
                if match:
                    candidate = self._normalize_focus_term(match.group('name'))
                    if candidate:
                        return candidate[:80]

        candidates: List[str] = []
        candidates.extend(self._extract_chinese_candidates(message))
        candidates.extend(self._extract_english_candidates(message))

        for candidate in candidates:
            normalized = self._normalize_focus_term(candidate)
            if normalized and normalized.lower() not in self.stopwords_for_queries:
                return normalized[:80]

        trimmed = re.sub(r'[?？。！!、,:;]', ' ', message).strip()
        return trimmed[:80] if trimmed else message[:80]

    def _looks_like_name(self, term: Optional[str]) -> bool:
        if not term:
            return False
        has_chinese = bool(re.search(r'[\u4e00-\u9fa5]', term))
        if has_chinese and len(term) <= 6:
            return True
        if term and term[0].isupper():
            return True
        return False

    def _guess_intent_type(self, message: str, focus_term: Optional[str], signals: Dict[str, Dict[str, Any]]) -> str:
        lowered = message.lower()
        if any(word in message for word in self.news_keywords) or '发生了' in message:
            return 'fresh_news'
        if any(word in message for word in self.character_keywords):
            return 'character'
        if focus_term and self._looks_like_name(focus_term):
            if any(word in message for word in ['角色', '人物', 'character']):
                return 'character'
            if 'explicit_request' in signals or 'knowledge_gap' in signals:
                return 'character'
        if any(word in lowered for word in ['latest', 'update', 'news']):
            return 'fresh_news'
        return 'concept'

    def plan_search_strategy(self, message: str) -> Dict[str, Any]:
        """Assess whether the assistant should perform a web search before answering."""
        content = (message or "").strip()
        if not content:
            return SearchIntent(False).to_dict()

        heuristic_intent = self._build_heuristic_intent(content)

        llm_plan = self._call_llm_planner(content, heuristic_intent)
        if llm_plan:
            return llm_plan.to_dict()
        return heuristic_intent.to_dict()

    def _build_heuristic_intent(self, content: str) -> SearchIntent:
        focus_term = self._extract_focus_term(content)
        signals = self._collect_search_signals(content, focus_term)
        intent_type = self._guess_intent_type(content, focus_term, signals)

        positive_score = sum(max(0.0, data['weight']) for data in signals.values())
        negative_score = sum(-min(0.0, data['weight']) for data in signals.values())
        net_score = positive_score - negative_score

        base_threshold = 2.4
        should_search = net_score >= base_threshold or 'explicit_request' in signals
        if 'time_sensitive' in signals:
            should_search = net_score >= 1.3 or 'explicit_request' in signals
        if 'creative_only' in signals and net_score < 3.5 and 'explicit_request' not in signals:
            should_search = False

        confidence = max(0.0, min(1.0, positive_score / 6.0))
        query = self._derive_query_from_message(content, intent_type, focus_term) if should_search else ""

        positive_reasons = [data['explanation'] for data in signals.values() if data['weight'] > 0]
        negative_reasons = [data['explanation'] for data in signals.values() if data['weight'] < 0]
        reason_parts = []
        if positive_reasons:
            reason_parts.append('；'.join(positive_reasons))
        if negative_reasons:
            reason_parts.append(f"抑制条件: {'；'.join(negative_reasons)}")
        reason = '；'.join(reason_parts) if reason_parts else "未触发联网条件"

        return SearchIntent(
            should_search=should_search,
            intent_type=intent_type,
            query=query,
            confidence=confidence,
            reason=reason,
            focus_term=focus_term,
            signals=signals
        )

    def _call_llm_planner(self, message: str, heuristic_intent: SearchIntent) -> Optional[SearchIntent]:
        if get_current_api_type() == "none":
            return None

        heuristic_payload = heuristic_intent.to_dict().copy()
        try:
            user_prompt = (
                "<UserMessage>\n"
                f"{message}\n"
                "</UserMessage>\n"
                "<HeuristicSuggestion>\n"
                f"{json.dumps(heuristic_payload, ensure_ascii=False)}\n"
                "</HeuristicSuggestion>\n"
                "请基于用户输入与启发式建议，判断是否需要联网搜索，并输出严格的JSON。"
            )
            response = run_structured_prompt(self.llm_planner_system_prompt, user_prompt)
            parsed = self._parse_planner_response(response)
            if not parsed:
                return None

            should_search = bool(parsed.get('should_search'))
            intent_type = parsed.get('intent_type', heuristic_intent.intent_type)
            query = parsed.get('query') or heuristic_intent.query
            focus_term = parsed.get('focus_term') or heuristic_intent.focus_term
            confidence = parsed.get('confidence', heuristic_intent.confidence)
            reason = parsed.get('reason') or heuristic_intent.reason

            if should_search and not query and focus_term:
                query = focus_term

            intent = SearchIntent(
                should_search=should_search,
                intent_type=intent_type or 'concept',
                query=(query or "")[:120],
                confidence=max(0.0, min(1.0, float(confidence) if confidence is not None else heuristic_intent.confidence)),
                reason=reason,
                focus_term=focus_term,
                signals=heuristic_intent.signals
            )
            return intent
        except Exception as exc:
            print(f"LLM搜索规划失败: {exc}")
            return None

    def _parse_planner_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        if not response_text:
            return None
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip('`')
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:]
        cleaned = cleaned.strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return None
    
    def detect_character_query(self, message: str) -> Optional[Dict[str, Any]]:
        """新版角色查询检测，基于多信号意图分析。"""
        intent = self.plan_search_strategy(message)
        if intent['should_search'] and intent['intent_type'] == 'character' and intent['query']:
            character_name = self._normalize_focus_term(intent['query'])
            if not character_name:
                return None
            return {
                'is_query': True,
                'query_type': 'character_info',
                'character_name': character_name,
                'original_message': message,
                'confidence': intent.get('confidence', 0.0),
                'reason': intent.get('reason', '')
            }
        return None

    def detect_concept_query(self, message: str) -> Optional[Dict[str, Any]]:
        """新版概念/事实查询检测，避免依赖固定正则。"""
        intent = self.plan_search_strategy(message)
        if intent['should_search'] and intent['intent_type'] in ('concept', 'fresh_news') and intent['query']:
            concept_name = self._normalize_focus_term(intent['query'])
            if not concept_name:
                return None
            return {
                'is_query': True,
                'query_type': 'concept_info',
                'concept_name': concept_name,
                'original_message': message,
                'confidence': intent.get('confidence', 0.0),
                'reason': intent.get('reason', '')
            }
        return None
    
    def search_duckduckgo(self, query: str, max_results: int = 3) -> Dict[str, Any]:
        """
        使用DuckDuckGo进行搜索
        
        Args:
            query: 搜索关键词
            max_results: 最大返回结果数
            
        Returns:
            {
                'success': bool,
                'query': str,
                'results': List[Dict],  # 每个结果包含 title, url, snippet
                'error': Optional[str]
            }
        """
        try:
            # 使用DuckDuckGo Instant Answer API
            api_url = 'https://api.duckduckgo.com/'
            params = {
                'q': query,
                'format': 'json',
                'pretty': 1,
                'no_html': 1,
                'skip_disambig': 1
            }
            
            print(f"正在搜索: {query}")
            response = self.session.get(api_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            results = []
            
            # 提取摘要信息
            if data.get('AbstractText'):
                results.append({
                    'title': data.get('Heading', query),
                    'url': data.get('AbstractURL', ''),
                    'snippet': data.get('AbstractText', ''),
                    'source': data.get('AbstractSource', 'DuckDuckGo')
                })
            
            # 提取相关主题
            related_topics = data.get('RelatedTopics', [])
            for topic in related_topics[:max_results-1]:
                if isinstance(topic, dict) and 'Text' in topic:
                    results.append({
                        'title': topic.get('Text', '')[:100],
                        'url': topic.get('FirstURL', ''),
                        'snippet': topic.get('Text', ''),
                        'source': 'DuckDuckGo'
                    })
            
            # 如果DuckDuckGo没有直接结果，尝试使用HTML搜索
            if not results:
                html_results = self._search_duckduckgo_html(query, max_results)
                if html_results['success']:
                    results = html_results['results']
            
            return {
                'success': True,
                'query': query,
                'results': results[:max_results],
                'error': None
            }
            
        except Exception as e:
            print(f"搜索失败: {e}")
            return {
                'success': False,
                'query': query,
                'results': [],
                'error': str(e)
            }
    
    def _search_duckduckgo_html(self, query: str, max_results: int = 3) -> Dict[str, Any]:
        """
        使用DuckDuckGo HTML搜索作为备用方案
        """
        try:
            from bs4 import BeautifulSoup
            
            search_url = 'https://html.duckduckgo.com/html/'
            data = {'q': query}
            
            response = self.session.post(search_url, data=data, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            # 解析搜索结果
            result_divs = soup.find_all('div', class_='result')
            for div in result_divs[:max_results]:
                title_tag = div.find('a', class_='result__a')
                snippet_tag = div.find('a', class_='result__snippet')
                
                if title_tag:
                    results.append({
                        'title': title_tag.get_text().strip(),
                        'url': title_tag.get('href', ''),
                        'snippet': snippet_tag.get_text().strip() if snippet_tag else '',
                        'source': 'DuckDuckGo'
                    })
            
            return {
                'success': True,
                'query': query,
                'results': results,
                'error': None
            }
            
        except Exception as e:
            print(f"HTML搜索失败: {e}")
            return {
                'success': False,
                'query': query,
                'results': [],
                'error': str(e)
            }
    
    def _prioritize_wiki_sites(self, search_results: List[Dict]) -> List[Dict]:
        """
        对搜索结果进行优先级排序，wiki/百科类网站优先
        
        优先级顺序：
        1. 萌娘百科 (moegirl.org.cn)
        2. 维基百科 (wikipedia.org)
        3. Fandom Wiki (fandom.com)
        4. 百度百科 (baike.baidu.com)
        5. 其他百科类网站
        6. 其他网站
        """
        # 定义优先级权重
        priority_domains = [
            ('moegirl.org', 100),      # 萌娘百科
            ('wikipedia.org', 90),      # 维基百科
            ('fandom.com', 85),         # Fandom Wiki
            ('wiki.biligame.com', 80),  # 哔哩哔哩游戏Wiki
            ('baike.baidu.com', 70),    # 百度百科
            ('hudong.com', 60),         # 互动百科
        ]
        
        def get_priority(url: str) -> int:
            """计算URL的优先级分数"""
            if not url:
                return 0
            
            # 检查是否包含优先域名
            for domain, score in priority_domains:
                if domain in url.lower():
                    return score
            
            # 检查是否是wiki类网站
            if 'wiki' in url.lower():
                return 50
            
            # 默认优先级
            return 10
        
        # 按优先级排序
        sorted_results = sorted(
            search_results, 
            key=lambda x: get_priority(x.get('url', '')), 
            reverse=True
        )
        
        return sorted_results
    
    def _extract_character_details(self, web_content: Dict[str, Any], character_name: str) -> Dict[str, Any]:
        """
        从网页内容中提取角色详细信息（性格、台词、背景等）
        
        Returns:
            {
                'personality': str,      # 性格特征
                'quotes': List[str],     # 经典台词
                'background': str,       # 背景故事
                'appearance': str,       # 外貌特征
                'relationships': str,    # 人际关系
                'abilities': str,        # 能力/技能
                'other_info': str       # 其他信息
            }
        """
        if not web_content or not web_content.get('success'):
            return {}
        
        content = web_content.get('content', '')
        title = web_content.get('title', '')
        
        details = {
            'personality': '',
            'quotes': [],
            'background': '',
            'appearance': '',
            'relationships': '',
            'abilities': '',
            'other_info': ''
        }
        
        # 使用关键词提取相关段落
        keywords_map = {
            'personality': ['性格', '个性', '特点', '脾气', '性情'],
            'quotes': ['台词', '语录', '名言', '口头禅', '说话'],
            'background': ['背景', '经历', '故事', '生平', '来历', '身世'],
            'appearance': ['外貌', '形象', '外观', '长相', '样貌', '特征'],
            'relationships': ['关系', '人际', '朋友', '家人', '同伴'],
            'abilities': ['能力', '技能', '特技', '招式', '技巧', '元素'],
        }
        
        # 分段处理内容
        sentences = content.split('。')
        
        for category, keywords in keywords_map.items():
            relevant_sentences = []
            for sentence in sentences:
                if any(kw in sentence for kw in keywords):
                    # 清理句子
                    clean_sentence = sentence.strip()
                    if clean_sentence and len(clean_sentence) > 5:
                        relevant_sentences.append(clean_sentence)
            
            if relevant_sentences:
                if category == 'quotes':
                    # 台词单独处理为列表
                    details[category] = relevant_sentences[:5]  # 最多5条台词
                else:
                    # 其他信息合并
                    details[category] = '。'.join(relevant_sentences[:3])  # 最多3句话
        
        # 如果没有提取到任何信息，使用全文前500字作为基础信息
        if not any(details.values()):
            details['other_info'] = content[:500]
        
        return details

    def _extract_concept_highlights(self, content: str) -> Dict[str, Any]:
        """从网页正文中提取概念概要和关键要点"""
        if not content:
            return {'definition': '', 'key_points': []}

        sentences = re.split(r'[。！？!?\.]\s*', content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

        if not sentences:
            return {'definition': content[:200], 'key_points': []}

        definition = sentences[0]

        keyword_groups = [
            ['应用', '用途', '使用', '场景'],
            ['特点', '特征', '优势', '劣势'],
            ['起源', '历史', '背景'],
            ['注意', '风险', '限制'],
        ]

        key_points: List[str] = []
        for keywords in keyword_groups:
            for sentence in sentences[1:]:
                if any(keyword in sentence for keyword in keywords) and sentence not in key_points:
                    key_points.append(sentence)
                    break
            if len(key_points) >= 4:
                break

        # 如果关键词匹配不足，补充前几句
        if len(key_points) < 3:
            for sentence in sentences[1:6]:
                if sentence not in key_points:
                    key_points.append(sentence)
                if len(key_points) >= 4:
                    break

        return {
            'definition': definition,
            'key_points': key_points[:4]
        }
    
    def search_character_info(self, character_name: str) -> Dict[str, Any]:
        """
        搜索角色信息，优先使用wiki/百科类网站
        
        Args:
            character_name: 角色名称
            
        Returns:
            {
                'success': bool,
                'character_name': str,
                'search_results': List[Dict],
                'web_content': Optional[Dict],  # 最佳搜索结果的网页内容
                'character_details': Optional[Dict],  # 提取的角色详细信息
                'error': Optional[str]
            }
        """
        # 构建多个搜索查询，提高搜索质量
        search_queries = [
            f"{character_name} 萌娘百科",
            f"{character_name} 维基百科",
            f"{character_name} 角色设定",
        ]
        
        all_results = []
        
        # 执行多次搜索，收集结果
        for query in search_queries:
            search_result = self.search_duckduckgo(query, max_results=2)
            if search_result['success'] and search_result['results']:
                all_results.extend(search_result['results'])
        
        # 去重（基于URL）
        seen_urls = set()
        unique_results = []
        for result in all_results:
            url = result.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        if not unique_results:
            return {
                'success': False,
                'character_name': character_name,
                'search_results': [],
                'web_content': None,
                'character_details': None,
                'error': '未找到相关搜索结果'
            }
        
        # 优先选择wiki/百科类网站
        prioritized_results = self._prioritize_wiki_sites(unique_results)
        
        print(f"搜索到 {len(prioritized_results)} 个结果，优先尝试wiki/百科网站...")
        
        # 尝试抓取最佳结果的网页内容
        web_content = None
        character_details = None
        
        for i, result in enumerate(prioritized_results[:3]):  # 尝试前3个结果
            url = result.get('url', '')
            if url and url.startswith('http'):
                try:
                    print(f"尝试抓取第 {i+1} 个结果: {url}")
                    content = web_scraper.scrape_webpage(url)
                    
                    if content and content.get('success') and content.get('content'):
                        web_content = content
                        # 提取角色详细信息
                        character_details = self._extract_character_details(content, character_name)
                        print(f"✅ 成功抓取并提取信息: {content.get('title', '未知')}")
                        break  # 找到有效内容就停止
                    else:
                        print(f"⚠️ 内容为空或抓取失败")
                except Exception as e:
                    print(f"抓取失败: {e}")
                    continue
        
        return {
            'success': True,
            'character_name': character_name,
            'search_results': prioritized_results[:5],  # 返回前5个结果
            'web_content': web_content,
            'character_details': character_details,
            'error': None
        }

    def search_concept_info(self, concept_name: str) -> Dict[str, Any]:
        """搜索通用概念/术语的信息"""
        search_queries = [
            concept_name,
            f"{concept_name} 是什么",
            f"{concept_name} 意义",
            f"{concept_name} 用途"
        ]

        aggregated_results: List[Dict[str, Any]] = []
        for query in search_queries:
            search_result = self.search_duckduckgo(query, max_results=2)
            if search_result['success'] and search_result['results']:
                aggregated_results.extend(search_result['results'])

        seen_urls = set()
        unique_results = []
        for result in aggregated_results:
            url = result.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)

        if not unique_results:
            return {
                'success': False,
                'concept_name': concept_name,
                'search_results': [],
                'web_content': None,
                'concept_summary': '',
                'key_points': [],
                'error': '未找到相关搜索结果'
            }

        prioritized_results = self._prioritize_wiki_sites(unique_results)

        web_content = None
        highlights = {'definition': '', 'key_points': []}

        for i, result in enumerate(prioritized_results[:3]):
            url = result.get('url', '')
            if url and url.startswith('http'):
                try:
                    content = web_scraper.scrape_webpage(url)
                    if content and content.get('success') and content.get('content'):
                        web_content = content
                        highlights = self._extract_concept_highlights(content.get('content', ''))
                        break
                except Exception as exc:
                    print(f"概念搜索抓取失败({i+1}): {exc}")
                    continue

        if not highlights['definition'] and prioritized_results:
            highlights['definition'] = prioritized_results[0].get('snippet', '')[:200]

        return {
            'success': True,
            'concept_name': concept_name,
            'search_results': prioritized_results[:5],
            'web_content': web_content,
            'concept_summary': highlights.get('definition', ''),
            'key_points': highlights.get('key_points', []),
            'source_title': (web_content or {}).get('title'),
            'source_url': (web_content or {}).get('url'),
            'error': None
        }
    
    def format_search_results(self, search_data: Dict[str, Any]) -> str:
        """
        格式化搜索结果为可读文本，包括提取的角色详细信息
        """
        if not search_data['success']:
            return f"❌ 搜索失败: {search_data.get('error', '未知错误')}"
        
        character_name = search_data['character_name']
        search_results = search_data['search_results']
        web_content = search_data.get('web_content')
        character_details = search_data.get('character_details')
        
        # 构建格式化文本
        formatted_text = f"\n🔍 搜索角色: {character_name}\n\n"
        
        # 添加角色详细信息（如果有提取到）
        if character_details:
            formatted_text += "📋 角色详细信息:\n\n"
            
            if character_details.get('background'):
                formatted_text += f"📖 背景故事:\n{character_details['background']}\n\n"
            
            if character_details.get('personality'):
                formatted_text += f"💭 性格特征:\n{character_details['personality']}\n\n"
            
            if character_details.get('appearance'):
                formatted_text += f"👤 外貌特征:\n{character_details['appearance']}\n\n"
            
            if character_details.get('abilities'):
                formatted_text += f"⚡ 能力技能:\n{character_details['abilities']}\n\n"
            
            if character_details.get('quotes') and len(character_details['quotes']) > 0:
                formatted_text += f"💬 经典台词:\n"
                for i, quote in enumerate(character_details['quotes'][:3], 1):
                    formatted_text += f"  {i}. {quote}\n"
                formatted_text += "\n"
            
            if character_details.get('relationships'):
                formatted_text += f"👥 人际关系:\n{character_details['relationships']}\n\n"
            
            if character_details.get('other_info') and not any([
                character_details.get('background'),
                character_details.get('personality'),
                character_details.get('appearance')
            ]):
                formatted_text += f"ℹ️ 其他信息:\n{character_details['other_info'][:300]}...\n\n"
        
        # 添加搜索来源
        if search_results:
            formatted_text += "📚 信息来源:\n"
            for i, result in enumerate(search_results[:3], 1):
                formatted_text += f"{i}. {result.get('title', '无标题')}\n"
                if result.get('url'):
                    formatted_text += f"   🔗 {result['url']}\n"
        
        # 添加网页内容信息
        if web_content and web_content.get('success'):
            formatted_text += f"\n📄 主要来源: {web_content.get('title', '未知')}\n"
        
        formatted_text += "\n✅ 搜索完成，请基于以上信息继续完善角色设定。\n"
        
        return formatted_text


# 全局实例
search_helper = SearchHelper()
