# shellm

Natural language to shell command CLI tool for Linux developers.

## Installation

```bash
pip install shellm
```

## Setup

Set your OpenAI API key:

```bash
export OPENAI_API_KEY='your-api-key-here'
```

## Usage

```bash
shellm "describe what you want to do"
```

### Examples

```bash
shellm "list all python files"
# Output: find . -name "*.py"

shellm "find files larger than 100MB"
# Output: find . -size +100M

shellm "show disk usage for current directory"
# Output: du -sh .

shellm "count lines of code in python files"
# Output: find . -name "*.py" -exec wc -l {} + | tail -1
```

## Requirements

- Python 3.8+
- OpenAI API key
- Linux environment

## License

MIT