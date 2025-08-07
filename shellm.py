#!/usr/bin/env python3
"""
shellm - Natural language to shell command CLI tool
"""

import argparse
import sys
from pathlib import Path
import yaml
from platformdirs import user_config_dir
from openai import OpenAI

DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-3.5-turbo"


def get_config_path():
    """Get path to config file."""
    config_dir = user_config_dir("shellm")
    return Path(config_dir) / "config.yaml"


def create_default_config():
    """Create config file by prompting user for each field."""
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    print("Setting up shellm configuration...")
    print(f"Config will be saved to: {config_path}")
    print()

    # Prompt for API key
    api_key = input("Enter your API key: ").strip()

    # Prompt for base URL with default
    base_url = input(f"Enter API base URL [{DEFAULT_BASE_URL}]: ").strip()
    if not base_url:
        base_url = DEFAULT_BASE_URL

    # Prompt for model with default
    model = input(f"Enter model name [{DEFAULT_MODEL}]: ").strip()
    if not model:
        model = DEFAULT_MODEL

    config = {
        'api': {
            'base_url': base_url,
            'key': api_key,
            'model': model
        }
    }

    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

    print(f"\nConfiguration saved to: {config_path}")
    return config


def load_config():
    """Load configuration from file."""
    config_path = get_config_path()

    if not config_path.exists():
        return create_default_config()

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"Error loading config: {e}", file=sys.stderr)
        return create_default_config()


def get_client():
    """Initialize client from config."""
    config = load_config()
    api_config = config.get('api', {})

    api_key = api_config.get('key', '')
    base_url = api_config.get('base_url', DEFAULT_BASE_URL)

    if not api_key:
        print("Error: No API key found in config", file=sys.stderr)
        print(f"Set key in config file: {get_config_path()}", file=sys.stderr)
        sys.exit(1)

    return OpenAI(api_key=api_key, base_url=base_url), api_config.get('model', DEFAULT_MODEL)


def generate_shell_command(client, model, description):
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
            model=model,
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

    # Initialize client
    client, model = get_client()

    # Generate command
    command = generate_shell_command(client, model, args.description)

    # Output the command
    print(command)


if __name__ == '__main__':
    main()
