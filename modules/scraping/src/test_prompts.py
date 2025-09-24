#!/usr/bin/env python3
"""Test prompt parsing"""

from pathlib import Path

def test_prompt_parsing():
    prompts_path = Path(__file__).parent.parent / "prompts.md"
    print(f"Looking for prompts at: {prompts_path}")
    print(f"File exists: {prompts_path.exists()}")

    if not prompts_path.exists():
        return

    with open(prompts_path, 'r', encoding='utf-8') as f:
        content = f.read()

    print(f"File content length: {len(content)}")

    # Parse prompts from markdown
    prompts = {}
    current_section = None
    current_prompt = []
    in_code_block = False

    lines = content.split('\n')
    for i, line in enumerate(lines):
        # Only process section headers when not in code block
        if not in_code_block and line.startswith('## ') and not line.startswith('## Version') and not line.startswith('## ARCHIVE'):
            current_section = line[3:].strip()
            current_prompt = []
            print(f"Line {i+1}: Found section: {current_section}")
        elif line.strip() == '```' and current_section:
            if not in_code_block:
                in_code_block = True
                current_prompt = []
                print(f"Line {i+1}: Starting code block for {current_section}")
            else:
                in_code_block = False
                if current_section and current_prompt:
                    prompts[current_section] = '\n'.join(current_prompt)
                    print(f"Line {i+1}: Saved prompt for {current_section}: {len(current_prompt)} lines")
        elif in_code_block and current_section:
            current_prompt.append(line)

    print(f"\nLoaded {len(prompts)} prompts: {list(prompts.keys())}")

    for name, prompt in prompts.items():
        print(f"\n{name}: {len(prompt)} characters")
        print(f"First 100 chars: {prompt[:100]}...")

if __name__ == "__main__":
    test_prompt_parsing()