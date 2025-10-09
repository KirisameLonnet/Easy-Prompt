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
            'DNT': '1',
        })
        self.timeout = 20  # 增加超时时间
    
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
            
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
            response.raise_for_status()
            
            # 优化编码检测
            # 1. 首先尝试从响应头获取编码
            content_type = response.headers.get('content-type', '').lower()
            charset = None
            if 'charset=' in content_type:
                charset = content_type.split('charset=')[-1].split(';')[0].strip()
            
            # 2. 如果没有从头部获取到，使用chardet检测
            if not charset or charset in ['iso-8859-1', 'latin-1']:
                charset = response.apparent_encoding
            
            # 3. 默认使用UTF-8
            if not charset:
                charset = 'utf-8'
            
            # 设置正确的编码
            response.encoding = charset
            print(f"检测到编码: {charset}")
            
            # 使用lxml解析器，对中文内容更友好
            try:
                soup = BeautifulSoup(response.content, 'lxml')
            except:
                # 如果lxml不可用，降级到html.parser
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
        """提取网页标题，优先支持MediaWiki（萌娘百科）结构"""
        # 1. MediaWiki特定选择器
        mediawiki_selectors = [
            'h1.firstHeading',           # MediaWiki标准标题
            'h1#firstHeading',            # 另一种MediaWiki标题
            '.mw-page-title-main',        # 新版MediaWiki
            'h1.page-header__title',      # 某些MediaWiki主题
        ]
        
        for selector in mediawiki_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title_text = title_elem.get_text().strip()
                if title_text:
                    print(f"从MediaWiki选择器 {selector} 提取标题: {title_text}")
                    return title_text
        
        # 2. 标准h1标签
        h1_tag = soup.find('h1')
        if h1_tag:
            h1_text = h1_tag.get_text().strip()
            if h1_text and len(h1_text) < 200:  # 避免提取到过长的文本
                print(f"从h1标签提取标题: {h1_text}")
                return h1_text
        
        # 3. 从title标签提取并清理
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.get_text().strip()
            # 清理title中的网站名称后缀
            for separator in [' - ', ' | ', ' – ', '—']:
                if separator in title_text:
                    title_text = title_text.split(separator)[0].strip()
            if title_text and title_text != "无标题":
                print(f"从title标签提取标题: {title_text}")
                return title_text
        
        # 4. OpenGraph标题
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            title_text = og_title.get('content').strip()
            if title_text:
                print(f"从OpenGraph提取标题: {title_text}")
                return title_text
        
        print("警告: 无法提取网页标题")
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
        """提取主要内容，优化MediaWiki支持"""
        # 移除不需要的标签
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
            tag.decompose()
        
        # 移除MediaWiki特定的导航和工具元素
        mediawiki_remove_selectors = [
            '.mw-editsection',           # 编辑链接
            '.mw-jump-link',             # 跳转链接
            '#toc',                      # 目录
            '.toc',                      # 目录
            '.navbox',                   # 导航框
            '.infobox',                  # 信息框（可选）
            '.catlinks',                 # 分类链接
            '#catlinks',
            '.printfooter',
            '.mw-indicators',
            'div.thumb',                 # 缩略图容器
            'table.ambox',               # 消息框
        ]
        
        for selector in mediawiki_remove_selectors:
            for elem in soup.select(selector):
                elem.decompose()
        
        # 尝试找到主要内容区域
        main_content = None
        
        # MediaWiki和常见网站的正文容器，按优先级排序
        content_selectors = [
            '#mw-content-text .mw-parser-output',  # MediaWiki主要内容（组合选择器）
            '.mw-parser-output',                   # 萌娘百科主要内容
            '#bodyContent',                        # MediaWiki body内容
            '.mw-body-content',                    # MediaWiki正文
            '#mw-content-text',                    # MediaWiki内容文本
            'main',                                # HTML5语义化
            '.content',
            '.main-content',
            '.post-content',
            '.entry-content',
            '.article-content',
            'article',
            '#content',
        ]
        
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                # 再次清理内部的导航元素
                for nav in main_content.select('nav, .navigation'):
                    nav.decompose()
                
                content_text = main_content.get_text(separator=' ', strip=True)
                if content_text and len(content_text) > 100:  # 确保有足够的内容
                    print(f"找到内容容器: {selector}, 内容长度: {len(content_text)}")
                    break
                else:
                    print(f"找到容器但内容不足: {selector}, 内容长度: {len(content_text) if content_text else 0}")
                    main_content = None
        
        # 如果没找到特定容器，尝试从body中提取
        if not main_content:
            print("使用备用方案：从body提取内容")
            main_content = soup.find('body')
        
        if not main_content:
            print("警告：未找到任何内容容器")
            return ""
        
        # 提取段落文本，保留结构
        paragraphs = []
        
        # 优先提取p标签内容
        for p in main_content.find_all('p', limit=20):  # 限制段落数量
            text = p.get_text(separator=' ', strip=True)
            if text and len(text) > 20:  # 过滤太短的段落
                paragraphs.append(text)
        
        # 如果段落太少，补充其他文本
        if len(paragraphs) < 3:
            for elem in main_content.find_all(['div', 'section'], limit=10):
                text = elem.get_text(separator=' ', strip=True)
                if text and len(text) > 50 and text not in paragraphs:
                    paragraphs.append(text)
        
        # 合并段落
        content = ' '.join(paragraphs)
        
        # 清理文本
        import re
        
        # 移除常见的无用文本模式
        unwanted_patterns = [
            r'编辑.*?段落',
            r'编辑.*?章节',
            r'跳转至.*?导航',
            r'萌娘百科.*?欢迎',
            r'维基百科.*?自由',
            r'登录.*?创建账户',
            r'讨论.*?贡献.*?工具',
            r'个人工具',
            r'页面工具',
            r'分类：.*',
            r'隐藏分类：',
            r'导航菜单',
            r'参考资料\[编辑\]',
            r'外部链接\[编辑\]',
            r'\[编辑\]',
            r'\[查看\]',
            r'\[讨论\]',
            r'\[×\]',
        ]
        
        for pattern in unwanted_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)
        
        # 移除多余的空白字符
        content = re.sub(r'\s+', ' ', content).strip()
        
        # 限制长度
        if len(content) > 2500:
            content = content[:2500] + "..."
        
        if not content or len(content) < 50:
            print(f"警告：提取的内容过短或为空，长度: {len(content)}")
        else:
            print(f"成功提取内容，长度: {len(content)}")
        
        return content
    
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

