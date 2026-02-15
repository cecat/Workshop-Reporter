#!/usr/bin/env python3
"""
Test report generation with the actual master prompt and session notes
"""

from openai import OpenAI
import yaml
import time
from pathlib import Path
from datetime import timedelta

def load_config(file_path="config.yml"):
    """Load configuration from config.yml"""
    with open(file_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

def load_master_prompt(file_path="tpc25_master_prompt.yaml"):
    """Load the master prompt from YAML file"""
    with open(file_path, 'r') as f:
        prompt_data = yaml.safe_load(f)
    return prompt_data.get('master_prompt')

def load_session_notes():
    """Load session notes from _INPUT directory"""
    input_dir = Path("_INPUT")
    notes_file = input_dir / "Session Notes Test.docx"
    
    if notes_file.exists():
        # For DOCX files, we'd need python-docx library
        # For now, let's check if there's a text version
        print(f"⚠️  Found DOCX file: {notes_file}")
        print(f"⚠️  Note: This test uses the master prompt without actual notes content")
        print(f"⚠️  To process DOCX files, the full generator uses additional libraries\n")
        return None
    
    # Check for any text files
    txt_files = list(input_dir.glob("*.txt"))
    if txt_files:
        with open(txt_files[0], 'r', encoding='utf-8') as f:
            return f.read()
    
    return None

def main():
    print("=" * 70)
    print("TPC Session Report Generation Test")
    print("=" * 70)
    print()
    
    # Load configuration and prompt
    print("📖 Loading configuration and prompt...")
    config = load_config()
    model_config = config['model']
    master_prompt = load_master_prompt()
    
    print(f"✅ Endpoint: {model_config['endpoint']}")
    print(f"✅ Model: {model_config['name']}")
    print(f"✅ Max tokens: {model_config.get('max_tokens', 4000)}")
    print(f"✅ Temperature: {model_config.get('temperature', 0.7)}")
    print()
    
    # Load session notes (if available)
    session_notes = load_session_notes()
    
    # Build the test prompt
    test_prompt = master_prompt + "\n\n"
    test_prompt += "Target Session: Model Architecture and Performance Evaluation (MAPE)\n\n"
    
    if session_notes:
        test_prompt += f"Discussion Notes:\n{session_notes}\n\n"
    
    test_prompt += "Lightning talks data and attendees data will be provided from local CSV files."
    
    print(f"📝 Prompt length: {len(test_prompt)} characters")
    print()
    
    # Initialize client
    client = OpenAI(
        base_url=model_config['endpoint'],
        api_key="not-needed"
    )
    
    # Generate report
    print("🚀 Generating report...")
    print("-" * 70)
    print()
    
    start_time = time.time()
    
    try:
        response = client.chat.completions.create(
            model=model_config['name'],
            messages=[
                {
                    "role": "system",
                    "content": config['system']['system_message']
                },
                {
                    "role": "user",
                    "content": test_prompt
                }
            ],
            max_tokens=model_config.get('max_tokens', 4000),
            temperature=model_config.get('temperature', 0.7),
            stream=True
        )
        
        # Collect and display streaming response
        full_response = ""
        token_count = 0
        
        for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
                full_response += content
                token_count += 1
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        print("\n")
        print("-" * 70)
        print()
        print("✅ Report generation complete!")
        print()
        print("📊 Statistics:")
        print(f"   ⏱️  Time elapsed: {timedelta(seconds=int(elapsed))} ({elapsed:.2f}s)")
        print(f"   📝 Response length: {len(full_response)} characters")
        print(f"   🔢 Approximate tokens: {token_count}")
        print(f"   ⚡ Tokens/second: {token_count/elapsed:.2f}")
        print()
        
        # Save output
        output_file = "test_report_output.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# Test Report Generation Output\n")
            f.write(f"# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Time elapsed: {elapsed:.2f}s\n")
            f.write(f"# Model: {model_config['name']}\n\n")
            f.write(full_response)
        
        print(f"💾 Output saved to: {output_file}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
