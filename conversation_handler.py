import os
from profile_manager import ProfileManager
from llm_helper import (
    start_chat_session,
    get_conversation_response_stream,
    write_final_prompt_stream,
    evaluate_profile
)
from language_manager import lang_manager
from typing import Optional
from web_scraper import web_scraper
from search_helper import search_helper

class ConversationHandler:
    """
    Orchestrates the conversation using a diagnostic-driven approach.
    支持用户隔离和多用户系统。
    """
    def __init__(
        self, 
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """
        初始化 ConversationHandler
        
        Args:
            session_id: 会话ID
            user_id: 用户ID（用于用户隔离）
        """
        self.session_id = session_id
        self.user_id = user_id
        self.profile_manager = ProfileManager(
            session_id=session_id,
            user_id=user_id
        )
        self.chat_session = start_chat_session()
        self.last_critique = "角色档案为空，请引导用户描述角色的核心身份。"
        
        # 如果是恢复的session，加载之前的critique
        if session_id:
            self.load_session_state()
    
    def load_session_state(self):
        """Loads session state from metadata."""
        metadata = self.profile_manager.load_session_metadata()
        if metadata:
            # 恢复最后的critique
            evaluation_data = metadata.get("evaluation_data", {})
            self.last_critique = evaluation_data.get("last_critique", self.last_critique)
    
    def save_session_state(self):
        """Saves current session state to metadata."""
        self.profile_manager.update_session_metadata({
            "evaluation_data": {
                "last_critique": self.last_critique
            }
        })
        
    def get_initial_greeting(self):
        """
        Gets the initial greeting for the conversation.
        """
        initial_prompt = lang_manager.system_prompts.INITIAL_USER_PROMPT
        return self.handle_message(initial_prompt, is_initial=True)

    def handle_message(self, message: str, is_initial: bool = False):
        """
        Handles a user message, yields a stream of the LLM response, and then
        updates the profile based on the full response.
        """
        if not self.chat_session:
            yield lang_manager.t("ERROR_LLM_NOT_CONFIGURED")
            return
        
        # 1. 检查是否是角色/人物查询
        character_query = search_helper.detect_character_query(message)
        if character_query:
            character_name = character_query['character_name']
            yield f"🔍 检测到角色查询: {character_name}"
            yield f"⏳ 正在搜索wiki/百科网站..."
            
            # 执行搜索
            search_data = search_helper.search_character_info(character_name)
            
            if search_data['success'] and search_data['search_results']:
                # 显示找到的来源
                yield f"\n📚 找到 {len(search_data['search_results'])} 个信息来源"
                
                # 显示角色详细信息
                character_details = search_data.get('character_details')
                if character_details:
                    # 显示提取到的关键信息摘要
                    if character_details.get('personality'):
                        yield f"💭 性格: {character_details['personality'][:80]}..."
                    if character_details.get('background'):
                        yield f"📖 背景: {character_details['background'][:80]}..."
                    if character_details.get('quotes'):
                        yield f"💬 台词: 找到 {len(character_details['quotes'])} 条经典台词"
                
                # 构建增强的消息内容
                enhanced_message = f"""
用户询问: {message}

角色名称: {character_name}

"""
                # 添加提取的角色详细信息
                if character_details:
                    enhanced_message += "=== 角色详细信息 ===\n\n"
                    
                    if character_details.get('background'):
                        enhanced_message += f"【背景故事】\n{character_details['background']}\n\n"
                    
                    if character_details.get('personality'):
                        enhanced_message += f"【性格特征】\n{character_details['personality']}\n\n"
                    
                    if character_details.get('appearance'):
                        enhanced_message += f"【外貌特征】\n{character_details['appearance']}\n\n"
                    
                    if character_details.get('abilities'):
                        enhanced_message += f"【能力技能】\n{character_details['abilities']}\n\n"
                    
                    if character_details.get('quotes'):
                        enhanced_message += f"【经典台词】\n"
                        for i, quote in enumerate(character_details['quotes'][:5], 1):
                            enhanced_message += f"{i}. {quote}\n"
                        enhanced_message += "\n"
                    
                    if character_details.get('relationships'):
                        enhanced_message += f"【人际关系】\n{character_details['relationships']}\n\n"
                    
                    if character_details.get('other_info'):
                        enhanced_message += f"【补充信息】\n{character_details['other_info']}\n\n"
                
                # 添加搜索来源
                enhanced_message += "=== 信息来源 ===\n"
                for i, result in enumerate(search_data['search_results'][:3], 1):
                    enhanced_message += f"{i}. {result.get('title', '无标题')}\n"
                    if result.get('snippet'):
                        enhanced_message += f"   {result['snippet'][:150]}...\n"
                
                # 添加网页原始内容（如果有）
                web_content = search_data.get('web_content')
                if web_content and web_content.get('success') and web_content.get('content'):
                    enhanced_message += f"\n=== 网页详细内容 ===\n"
                    enhanced_message += f"标题: {web_content.get('title', '')}\n"
                    enhanced_message += f"内容: {web_content.get('content', '')[:1000]}\n"
                
                enhanced_message += """

请基于以上搜索到的详细信息，帮助用户了解这个角色。
如果用户想基于这个角色创建prompt，请引导用户确认是否需要修改某些设定，或者直接使用这些信息。
"""
                message = enhanced_message
                yield f"✅ 搜索完成，已提取角色详细信息"
            else:
                error_msg = search_data.get('error', '未找到相关信息')
                yield f"⚠️ 搜索结果有限: {error_msg}"
                yield f"💡 将尝试基于现有知识回答您的问题"
        
        # 2. 检查用户输入是否包含链接
        link_result = web_scraper.process_user_input(message)
        if link_result['has_url']:
            yield f"🔗 检测到链接: {link_result['url']}"
            
            if link_result['web_content'] and link_result['web_content']['success']:
                web_content = link_result['web_content']
                yield f"📄 网页标题: {web_content['title']}"
                
                if web_content['description']:
                    yield f"📝 网页描述: {web_content['description']}"
                
                # 调试信息：显示网页内容长度
                content_length = len(web_content['content']) if web_content['content'] else 0
                yield f"📊 网页内容长度: {content_length} 字符"
                
                # 将网页内容整合到消息中
                enhanced_message = f"""
用户输入: {message}

网页内容:
标题: {web_content['title']}
描述: {web_content['description']}
内容: {web_content['content']}
关键词: {', '.join(web_content['keywords'])}

请基于以上网页内容帮助用户完善角色设定。
"""
                message = enhanced_message
                yield f"✅ 网页内容已整合到上下文中，内容长度: {content_length} 字符"
            else:
                error_msg = link_result.get('error', '网页抓取失败')
                yield f"❌ 网页抓取失败: {error_msg}"
                # 继续使用原始消息

        # On subsequent turns, first evaluate the profile to get a new critique
        if not is_initial:
            full_profile = self.profile_manager.get_full_profile()
            if full_profile:
                evaluation = evaluate_profile(full_profile)
                self.last_critique = evaluation.get("critique", self.last_critique)
                
                # 保存session状态
                self.save_session_state()
                
                if evaluation.get("is_ready_for_writing", False):
                    confirmation_reason = evaluation.get("critique", "角色档案似乎已足够完整。")
                    yield f"CONFIRM_GENERATION::{confirmation_reason}"
                    return

        # Get the generator for the streaming response
        response_generator = get_conversation_response_stream(self.chat_session, message, self.last_critique)
        
        # Handle the generator that yields chunks and final result
        full_response_chunks = []
        new_trait = "None"
        
        for chunk in response_generator:
            if isinstance(chunk, tuple) and len(chunk) == 3 and chunk[0] == "__FINAL_RESULT__":
                # This is the final result tuple
                _, ai_response, new_trait = chunk
                break
            yield chunk
            full_response_chunks.append(chunk)
        
        # Now that the stream is complete, append the new trait
        if new_trait and new_trait.lower() != "none":
            self.profile_manager.append_trait(new_trait)
        else:
            # 即使没有提取到特征，也要记录用户输入，确保评估能够触发
            # 这样可以处理网页内容、URL等特殊输入
            self.profile_manager.append_trait(f"用户输入: {message}")
        
        # Signal that evaluation should start (will be handled separately in main.py)
        yield f"EVALUATION_TRIGGER::{lang_manager.t('EVALUATOR_EVALUATING')}"

    def finalize_prompt(self):
        """
        Finalizes the process by generating and saving the prompt.
        Yields the streaming content of the final prompt.
        """
        full_profile = self.profile_manager.get_full_profile()
        yield "\n" + lang_manager.t("FINAL_PROMPT_HEADER") + "\n"
        
        final_prompt_stream = write_final_prompt_stream(full_profile)
        final_prompt_content = ""
        for final_chunk in final_prompt_stream:
            yield final_chunk
            final_prompt_content += final_chunk
        
        self.profile_manager.save_final_prompt(final_prompt_content)
        yield "::FINAL_PROMPT_END::"