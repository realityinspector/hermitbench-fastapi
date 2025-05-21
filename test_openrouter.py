"""
Simple test script to verify OpenRouter API connection and list available models.
"""
import os
import asyncio
import json
from dotenv import load_dotenv
from app.core.openrouter import OpenRouterClient

async def list_models():
    # Load environment variables
    load_dotenv()
    
    # Get API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not found in environment variables")
        return
    
    print(f"Using API key: {api_key[:5]}...{api_key[-4:]}")
    
    # Create client
    client = OpenRouterClient(api_key=api_key)
    
    try:
        # Get models
        print("Fetching models from OpenRouter...")
        models = await client.get_models()
        
        # Print models in a readable format
        print(f"\nFound {len(models)} models:")
        for model in models:
            print(f"- ID: {model.get('id', 'Unknown')}")
            print(f"  Name: {model.get('name', 'Unknown')}")
            print(f"  Context Length: {model.get('context_length', 'Unknown')}")
            print()
        
        # Save models to a file for reference
        with open("openrouter_models.json", "w") as f:
            json.dump(models, f, indent=2)
        print("Models saved to openrouter_models.json")
        
        # Test a simple chat completion with GPT-3.5-turbo
        test_model = "openai/gpt-3.5-turbo"
        print(f"\nTesting chat completion with {test_model}...")
        
        response = await client.chat_completion(
            model=test_model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say hello!"}
            ],
            temperature=0.7
        )
        
        # Print the response
        print("\nChat Completion Response:")
        print(f"Model: {response.get('model', 'Unknown')}")
        if "choices" in response and len(response["choices"]) > 0:
            print(f"Content: {response['choices'][0]['message']['content']}")
        else:
            print("No content in response.")
        
        # Save response to a file
        with open("openrouter_test_response.json", "w") as f:
            json.dump(response, f, indent=2)
        print("Response saved to openrouter_test_response.json")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(list_models())