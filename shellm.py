#!/usr/bin/env python3
"""
shellm - Natural language to shell command CLI tool
"""

import argparse
import sys
import shutil
from pathlib import Path
import yaml
from platformdirs import user_config_dir
import requests
import json

DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-3.5-turbo"


def get_config_path():
    """Get path to config file."""
    config_dir = user_config_dir("shellm")
    return Path(config_dir) / "config.yaml"


def get_prompts_path():
    """Get path to prompts file."""
    config_dir = user_config_dir("shellm")
    return Path(config_dir) / "prompts.yaml"


def copy_default_prompts():
    """Copy default prompts.yaml from project directory to config directory."""
    prompts_path = get_prompts_path()
    prompts_path.parent.mkdir(parents=True, exist_ok=True)

    # Copy default prompts.yaml from project directory
    default_prompts_path = Path(__file__).parent / "prompts.yaml"
    if default_prompts_path.exists():
        shutil.copy2(default_prompts_path, prompts_path)

        # Load and return the copied prompts
        with open(prompts_path, 'r') as f:
            return yaml.safe_load(f)

    # Fallback if source file doesn't exist
    return {'system_prompt': 'You are a helpful assistant that converts natural language to shell commands.'}


def load_prompts():
    """Load prompts from config directory."""
    prompts_path = get_prompts_path()

    if not prompts_path.exists():
        return copy_default_prompts()

    try:
        with open(prompts_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading prompts: {e}", file=sys.stderr)
        return copy_default_prompts()


def create_default_config():
    """Create config file by prompting user for each field."""
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    print("Setting up shellm configuration...")
    print(f"Config will be saved to: {config_path}")
    print()

    # Prompt for base URL with default
    base_url = input(f"Enter API base URL [{DEFAULT_BASE_URL}]: ").strip()
    if not base_url:
        base_url = DEFAULT_BASE_URL

    # Prompt for API key
    api_key = input("Enter your API key: ").strip()

    # Prompt for model with default
    model = input(f"Enter model name [{DEFAULT_MODEL}]: ").strip()
    if not model:
        model = DEFAULT_MODEL

    config = {
        'api': {
            'base_url': base_url,
            'key': api_key,
            'model': model
        },
        'network': {
            'proxy': None,
            'ca_cert_path': None,
            'ssl_verify': True
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

    if 'api' not in config:
        print("Error: Invalid config file - missing 'api' section", file=sys.stderr)
        print(f"Config file: {get_config_path()}", file=sys.stderr)
        print("Delete the config file to recreate it", file=sys.stderr)
        sys.exit(1)

    api_config = config['api']
    api_required_fields = ['base_url', 'key', 'model']

    for field in api_required_fields:
        if field not in api_config:
            print(f"Error: Missing required field '{field}' in config", file=sys.stderr)
            print(f"Config file: {get_config_path()}", file=sys.stderr)
            print("Delete the config file to recreate it", file=sys.stderr)
            sys.exit(1)

        if not api_config[field]:
            print(f"Error: Empty value for required field '{field}' in config", file=sys.stderr)
            print(f"Config file: {get_config_path()}", file=sys.stderr)
            sys.exit(1)

    base_url = api_config['base_url']
    api_key = api_config['key']
    model = api_config['model']

    # Load system prompt from prompts file
    prompts_config = load_prompts()
    system_prompt = prompts_config.get('system_prompt', 'You are a helpful assistant that converts natural language to shell commands.')
    description_prompt = prompts_config.get('description_prompt', 'Analyze the safety of this shell command.')

    # Load optional network configuration
    network_config = config.get('network', {})
    proxy = network_config.get('proxy')
    ca_cert_path = network_config.get('ca_cert_path')
    ssl_verify = network_config.get('ssl_verify', True)

    return api_key, base_url, model, system_prompt, description_prompt, proxy, ca_cert_path, ssl_verify


def generate_shell_command(api_key, base_url, model, system_prompt, description, proxy=None, ca_cert_path=None, ssl_verify=True):
    """Generate shell command from natural language description."""

    try:
        url = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": description}
            ],
            "max_tokens": 200,
            "temperature": 0.1
        }

        # Build request kwargs with optional network configurations
        request_kwargs = {}
        if proxy:
            request_kwargs['proxies'] = {'http': proxy, 'https': proxy}
        if ca_cert_path:
            request_kwargs['verify'] = ca_cert_path
        elif not ssl_verify:
            request_kwargs['verify'] = False

        response = requests.post(url, headers=headers, json=data, **request_kwargs)
        response.raise_for_status()

        result = response.json()
        command = result["choices"][0]["message"]["content"].strip()
        return command

    except Exception as e:
        print(f"Error calling API: {e}", file=sys.stderr)
        sys.exit(1)


def describe_shell_command(api_key, base_url, model, description_prompt, command, proxy=None, ca_cert_path=None, ssl_verify=True):
    """Describe the generated shell command."""

    try:
        url = f"{base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": description_prompt},
                {"role": "user", "content": f"Analyze this shell command: {command}"}
            ],
            "max_tokens": 150,
            "temperature": 0.1
        }

        # Build request kwargs with optional network configurations
        request_kwargs = {}
        if proxy:
            request_kwargs['proxies'] = {'http': proxy, 'https': proxy}
        if ca_cert_path:
            request_kwargs['verify'] = ca_cert_path
        elif not ssl_verify:
            request_kwargs['verify'] = False

        response = requests.post(url, headers=headers, json=data, **request_kwargs)
        response.raise_for_status()

        result = response.json()
        assessment = result["choices"][0]["message"]["content"].strip()
        return assessment

    except Exception as e:
        print(f"Error assessing command: {e}", file=sys.stderr)
        return "UNKNOWN: Unable to assess command"


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
    api_key, base_url, model, system_prompt, description_prompt, proxy, ca_cert_path, ssl_verify = get_client()

    # Generate command
    command = generate_shell_command(api_key, base_url, model, system_prompt, args.description, proxy, ca_cert_path, ssl_verify)

    # Output the command
    print(command)

    # Describe the shell command
    description = describe_shell_command(api_key, base_url, model, description_prompt, command, proxy, ca_cert_path, ssl_verify)
    print(description)


if __name__ == '__main__':
    main()
