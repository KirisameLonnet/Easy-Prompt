"""
Handles all interactions with the web search tool.
"""
import re
import requests
from typing import Optional, Dict, Any, List
from web_scraper import web_scraper


class SearchHelper:
    """
    搜索助手，用于检测用户查询意图并执行网络搜索
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        })
    
    def detect_character_query(self, message: str) -> Optional[Dict[str, Any]]:
        """
        检测用户是否在询问角色/人物信息
        
        Returns:
            如果是询问角色，返回 {
                'is_query': True,
                'query_type': 'character_info',
                'character_name': str,
                'original_message': str
            }
            否则返回 None
        """
        # 询问角色的常见模式（优化后的正则表达式）
        patterns = [
            # "你知道雷电将军这个角色吗"
            (r'(?:你知道|你了解|你认识|听说过)(?:吗)?(.+?)(?:这个)?(?:角色|人物)', 1),
            # "关于孙悟空角色的信息" - 提取"孙悟空"
            (r'关于(.+?)(?:这个)?(?:角色|人物)', 1),
            # "角色鸣人是什么样的"
            (r'角色(.+?)(?:是什么|是谁|怎么样|如何)', 1),
            # "介绍一下艾斯这个角色"
            (r'介绍(?:一下)?(.+?)(?:这个)?(?:角色|人物)', 1),
            # "雷电将军这个角色的背景"
            (r'(.+?)(?:这个)?(?:角色|人物)(?:的)?(?:背景|设定|信息|资料)', 1),
        ]
        
        # 需要排除的无效词
        invalid_words = ['这个', '那个', '某个', '一个', '我想创建', '创建', '新建', '关于']
        
        for pattern, group_idx in patterns:
            match = re.search(pattern, message)
            if match:
                character_name = match.group(group_idx).strip()
                
                # 清理角色名称
                # 移除开头的"关于"等词
                for word in ['关于', '对于', '针对']:
                    if character_name.startswith(word):
                        character_name = character_name[len(word):].strip()
                
                # 验证角色名称有效性
                is_valid = (
                    character_name and 
                    len(character_name) > 1 and 
                    character_name not in invalid_words and
                    not any(invalid in character_name for invalid in ['创建', '新建'])
                )
                
                if is_valid:
                    return {
                        'is_query': True,
                        'query_type': 'character_info',
                        'character_name': character_name,
                        'original_message': message
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
