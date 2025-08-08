import asyncio
import os

def load_env_from_dir(env_dir):
    """
    Manually loads files from a directory into environment variables.
    """
    if not os.path.exists(env_dir):
        return
    
    print(f"Loading environment variables from: {env_dir}")
    for filename in os.listdir(env_dir):
        with open(os.path.join(env_dir, filename), 'r') as f:
            value = f.read().strip()
            os.environ[filename] = value
            print(f"  - Set {filename}")

async def main():
    """
    Tests the connection to the Google Gemini API using the configured credentials.
    """
    print("--- Running API Connection Test ---")

    # Manually load environment variables
    env_dir = os.path.join(os.path.dirname(__file__), 'env')
    load_env_from_dir(env_dir)

    # IMPORTANT: Import the helper *after* setting the environment variables
    import llm_helper
    
    # Initialize the LLM with the loaded variables
    llm_helper.init_llm()

    if not llm_helper.get_model():
        print("\n[FAILURE] ❌ LLM initialization failed. Check API Key in `env/GOOGLE_API_KEY`.")
        return

    print(f"\nAttempting to connect with model: {llm_helper.MODEL_NAME}")
    print("Sending a test prompt: 'Hello, world!'...")

    try:
        response = await llm_helper.generate_response("Hello, world!")

        if "Error" in response:
            print(f"\n[FAILURE] ❌ API call failed. Response: {response}")
        else:
            print("\n[SUCCESS] ✅ API connection is working.")
            print(f"Received response: {response[:200]}...")

    except Exception as e:
        print(f"\n[FAILURE] ❌ An unexpected error occurred: {e}")

    print("\n--- Test Complete ---")


if __name__ == "__main__":
    asyncio.run(main())