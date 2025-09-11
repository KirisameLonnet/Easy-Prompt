import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote
import time
from typing import Optional, Dict, Any
import json

class WebScraper:
    """
    网页内容抓取器，支持中文链接和多种网页格式
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.timeout = 15
    
    def extract_url_from_text(self, text: str) -> Optional[str]:
        """
        从文本中提取URL，支持中文链接格式
        支持格式：
        - https://example.com
        - 【@https://example.com】
        - 【@https://example.com 描述文字】
        """
        # 匹配【@URL】格式
        bracket_pattern = r'【@\s*([^\s】]+)\s*[^】]*】'
        bracket_match = re.search(bracket_pattern, text)
        if bracket_match:
            return bracket_match.group(1)
        
        # 匹配普通URL格式
        url_pattern = r'https?://[^\s]+'
        url_match = re.search(url_pattern, text)
        if url_match:
            return url_match.group(0)
        
        return None
    
    def is_valid_url(self, url: str) -> bool:
        """检查URL是否有效"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def scrape_webpage(self, url: str) -> Dict[str, Any]:
        """
        抓取网页内容并提取关键信息
        """
        try:
            # 确保URL格式正确
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            print(f"正在抓取网页内容: {url}")
            
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # 检测编码
            if response.encoding == 'ISO-8859-1':
                response.encoding = response.apparent_encoding
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 提取基本信息
            title = self._extract_title(soup)
            description = self._extract_description(soup)
            content = self._extract_main_content(soup)
            keywords = self._extract_keywords(soup)
            
            result = {
                'url': url,
                'title': title,
                'description': description,
                'content': content,
                'keywords': keywords,
                'success': True,
                'error': None
            }
            
            print(f"成功抓取网页: {title}")
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"网页抓取失败: {e}")
            return {
                'url': url,
                'title': None,
                'description': None,
                'content': None,
                'keywords': [],
                'success': False,
                'error': f"网络请求失败: {str(e)}"
            }
        except Exception as e:
            print(f"网页解析失败: {e}")
            return {
                'url': url,
                'title': None,
                'description': None,
                'content': None,
                'keywords': [],
                'success': False,
                'error': f"解析失败: {str(e)}"
            }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取网页标题"""
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        
        # 尝试从h1标签获取
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()
        
        return "无标题"
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """提取网页描述"""
        # 尝试meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc.get('content').strip()
        
        # 尝试og:description
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc and og_desc.get('content'):
            return og_desc.get('content').strip()
        
        return ""
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """提取主要内容"""
        # 移除脚本和样式标签
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.decompose()
        
        # 尝试找到主要内容区域
        main_content = None
        
        # 常见的正文容器，按优先级排序
        content_selectors = [
            '.mw-parser-output',      # 萌娘百科主要内容
            '.mw-content-container',  # 萌娘百科容器
            'main',
            '.content',
            '.main-content',
            '.post-content',
            '.entry-content',
            '.article-content',
            '#content',
            '.mw-body-content'        # 萌娘百科正文
        ]
        
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                print(f"找到内容容器: {selector}")
                break
        
        # 如果没找到特定容器，尝试从body中提取
        if not main_content:
            # 尝试找到包含最多文本的div
            divs = soup.find_all('div')
            max_text_length = 0
            for div in divs:
                text_length = len(div.get_text().strip())
                if text_length > max_text_length:
                    max_text_length = text_length
                    main_content = div
            
            if not main_content:
                main_content = soup.find('body')
        
        if main_content:
            # 提取文本内容
            text = main_content.get_text()
            # 清理文本
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # 移除常见的无用文本
            unwanted_patterns = [
                r'编辑.*?条目',
                r'添加.*?内容',
                r'萌娘百科.*?欢迎您',
                r'本条目.*?介绍',
                r'关于.*?请见',
                r'外部链接',
                r'注释',
                r'参考资料',
                r'分类.*?导航',
                r'页面.*?工具',
                r'个人.*?工具',
                r'登录.*?创建.*?账户',
                r'讨论.*?贡献',
                r'移动版.*?桌面版',
            ]
            
            import re
            for pattern in unwanted_patterns:
                text = re.sub(pattern, '', text, flags=re.IGNORECASE)
            
            # 再次清理
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk and len(chunk) > 3)
            
            # 限制长度
            if len(text) > 2000:
                text = text[:2000] + "..."
            
            return text
        
        return ""
    
    def _extract_keywords(self, soup: BeautifulSoup) -> list:
        """提取关键词"""
        keywords = []
        
        # 从meta keywords提取
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            keywords.extend(meta_keywords.get('content').split(','))
        
        # 从标题和h标签提取
        title = self._extract_title(soup)
        if title and title != "无标题":
            keywords.append(title)
        
        # 从h1-h3标签提取
        for i in range(1, 4):
            for h_tag in soup.find_all(f'h{i}'):
                text = h_tag.get_text().strip()
                if text and len(text) < 50:  # 避免过长的标题
                    keywords.append(text)
        
        # 清理和去重
        keywords = [kw.strip() for kw in keywords if kw.strip()]
        keywords = list(dict.fromkeys(keywords))  # 去重但保持顺序
        
        return keywords[:10]  # 限制数量
    
    def process_user_input(self, user_input: str) -> Dict[str, Any]:
        """
        处理用户输入，检测并抓取链接内容
        """
        url = self.extract_url_from_text(user_input)
        
        if not url:
            return {
                'has_url': False,
                'url': None,
                'web_content': None,
                'original_input': user_input
            }
        
        if not self.is_valid_url(url):
            return {
                'has_url': True,
                'url': url,
                'web_content': None,
                'error': '无效的URL格式',
                'original_input': user_input
            }
        
        web_content = self.scrape_webpage(url)
        
        return {
            'has_url': True,
            'url': url,
            'web_content': web_content,
            'original_input': user_input
        }

# 全局实例
web_scraper = WebScraper()

