import os
import sys
import argparse
from prompt_toolkit import prompt
from prompt_toolkit.shortcuts import confirm

def load_env_from_dir(env_dir):
    """Manually loads files from a directory into environment variables."""
    if not os.path.exists(env_dir): return
    for filename in os.listdir(env_dir):
        with open(os.path.join(env_dir, filename), 'r', encoding='utf-8') as f:
            os.environ[filename] = f.read().strip()

def main():
    """The main entry point for the CLI-based application."""
    env_dir = os.path.join(os.path.dirname(__file__), 'env')
    load_env_from_dir(env_dir)

    from language_manager import lang_manager
    from conversation_handler import ConversationHandler
    from evaluator_service import EvaluatorService
    import llm_helper

    parser = argparse.ArgumentParser(description="Easy-Prompt: An intelligent RolePlay Prompt Generator.")
    parser.add_argument('--nsfw', action='store_true', help='Disable all content safety filters.')
    args = parser.parse_args()

    print(lang_manager.t("APP_STARTING"))
    
    if args.nsfw:
        print("\n" + "="*50)
        print(f"== {lang_manager.t('NSFW_MODE_ACTIVE_WARNING_HEADER')} ==".center(48))
        print(f"== {lang_manager.t('NSFW_MODE_ACTIVE_WARNING_FILTERS')} ==".center(48))
        print(f"= {lang_manager.t('NSFW_MODE_ACTIVE_WARNING_CONTENT')} =".center(48))
        print("="*50 + "\n")

    llm_helper.init_llm(nsfw_mode=args.nsfw)
    
    evaluator = EvaluatorService()
    evaluator.start()
    handler = ConversationHandler()
    
    print(f"\n--- {lang_manager.t('EASYPROMPT_INITIALIZED')} ---")
    print(lang_manager.t("AI_PROMPT"), end='', flush=True)
    initial_stream = handler.get_initial_greeting()
    for chunk in initial_stream:
        print(chunk, end='', flush=True)
    print("\n" + "-" * 20)

    try:
        while True:
            user_input = prompt(lang_manager.t("YOU_PROMPT"))
            if user_input.lower() in ['quit', 'exit']:
                break
            if not user_input:
                continue

            print(lang_manager.t("AI_PROMPT"), end='', flush=True)
            
            full_response = ""
            for chunk in handler.handle_message(user_input):
                full_response += chunk
                print(chunk, end='', flush=True)
            
            if full_response.startswith("CONFIRM_GENERATION::"):
                reason = full_response.split("::", 1)[1]
                print(f"\n\n[AI] {reason}")
                try:
                    if confirm(lang_manager.t("CONFIRM_GENERATION_PROMPT")):
                        print(lang_manager.t("AI_PROMPT"), end='', flush=True)
                        for final_chunk in handler.finalize_prompt():
                            if final_chunk == "::FINAL_PROMPT_END::":
                                break
                            print(final_chunk, end='', flush=True)
                        print()
                        break # End of session
                    else:
                        print(f"AI: {lang_manager.t('CONTINUE_PROMPT')}")
                        continue
                except (KeyboardInterrupt, EOFError):
                    break # Treat Ctrl+C as "no"
            
            print()

    except (KeyboardInterrupt, EOFError):
        print(f"\n{lang_manager.t('EXITING')}")
    finally:
        evaluator.stop()
        print(lang_manager.t("APP_SHUTDOWN"))

if __name__ == "__main__":
    main()