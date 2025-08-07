#!/usr/bin/env python3
"""
shellm - Natural language to shell command CLI tool
"""

import argparse
import os
import sys
from openai import OpenAI


def get_openai_client():
    """Initialize OpenAI client with API key from environment."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set", file=sys.stderr)
        print("Set it with: export OPENAI_API_KEY='your-api-key'", file=sys.stderr)
        sys.exit(1)
    
    return OpenAI(api_key=api_key)


def generate_shell_command(client, description):
    """Generate shell command from natural language description."""
    system_prompt = """You are a Linux shell command assistant. Convert natural language descriptions into shell commands.

Rules:
- Return ONLY the shell command, no explanations
- Use common Linux utilities and commands
- Prefer safe, standard commands
- If multiple commands are needed, separate with && or ;
- Don't include dangerous commands like rm -rf / without clear intent"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": description}
            ],
            max_tokens=200,
            temperature=0.1
        )
        
        command = response.choices[0].message.content.strip()
        return command
        
    except Exception as e:
        print(f"Error calling OpenAI API: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Convert natural language to shell commands",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  shellm "list all python files"
  shellm "find files larger than 100MB"
  shellm "show disk usage for current directory"
        """
    )
    
    parser.add_argument(
        'description',
        help='Natural language description of what you want to do'
    )
    
    parser.add_argument(
        '-v', '--version',
        action='version',
        version='shellm 0.1.0'
    )
    
    args = parser.parse_args()
    
    # Initialize OpenAI client
    client = get_openai_client()
    
    # Generate command
    command = generate_shell_command(client, args.description)
    
    # Output the command
    print(command)


if __name__ == '__main__':
    main()