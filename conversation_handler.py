import os
from profile_manager import ProfileManager
from llm_helper import (
    start_chat_session,
    get_conversation_response_stream,
    write_final_prompt_stream,
    evaluate_profile
)
from language_manager import lang_manager

class ConversationHandler:
    """
    Orchestrates the conversation using a diagnostic-driven approach.
    """
    def __init__(self):
        self.profile_manager = ProfileManager()
        self.chat_session = start_chat_session()
        self.last_critique = "角色档案为空，请引导用户描述角色的核心身份。"
        
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

        # On subsequent turns, first evaluate the profile to get a new critique
        if not is_initial:
            full_profile = self.profile_manager.get_full_profile()
            if full_profile:
                evaluation = evaluate_profile(full_profile)
                self.last_critique = evaluation.get("critique", self.last_critique)
                
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