#!/usr/bin/env python3
"""
Simple test script to verify all prompts are loading correctly.
"""
import json
import os
import sys
from app.utils.prompt_loader import load_prompt, load_all_prompts

def test_all_prompts():
    """Test that all prompt files can be loaded correctly."""
    prompt_files = [
        "prompts/initial_prompt.json",
        "prompts/judge_evaluation_prompt.json",
        "prompts/judge_system_prompt.json",
        "prompts/persona_card_prompt.json",
        "prompts/thematic_synthesis_prompt.json"
    ]
    
    success = True
    for file_path in prompt_files:
        print(f"Testing file: {file_path}")
        try:
            # Try to open and parse the raw file first
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                parsed = json.loads(content)
                print(f"  ✓ Raw JSON parsing successful: {list(parsed.keys())}")
            
            # Now test with our prompt loader
            if "_prompt" in file_path:
                # This is likely a file with a primary prompt key
                key = os.path.basename(file_path).replace(".json", "")
                prompt = load_prompt(file_path, key)
                print(f"  ✓ Successfully loaded prompt with key: {key}")
            
            # Try loading all prompts
            all_prompts = load_all_prompts(file_path)
            print(f"  ✓ Successfully loaded all prompts: {list(all_prompts.keys())}")
            
        except Exception as e:
            print(f"  ✗ Error loading {file_path}: {str(e)}")
            success = False
    
    return success

if __name__ == "__main__":
    print("Testing all prompt files...")
    success = test_all_prompts()
    if success:
        print("\nAll prompt files loaded successfully! ✓")
        sys.exit(0)
    else:
        print("\nSome prompt files failed to load. ✗")
        sys.exit(1)