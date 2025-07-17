# foldertree
A Python tool to generate folder structures from tree-like format.

# Features

- Multiple Input Formats: Supports tree-like structures, YAML, and simple indentation
- Auto-detection: Automatically detects input format
- Comment Support: Adds comments to generated files based on file extensions
- Python Package Detection: Automatically creates `__init__.py` files in Python packages
- Smart Skipping: Skips common files like `__pycache__`, .git, etc.
- Dry Run Mode: Preview what will be created without actual file creation
- Flexible Output: Specify custom output directories

# Installation
```bash
pip install foldertree
```

# Usage

## Command Line

```bash
# From file
foldertree -f structure.tree

# From stdin
echo "api/
  routes.py
core/
  classifier.py" | foldertree

# Dry run (preview only)
foldertree -f structure.tree --dry-run

# Specify output directory
foldertree -f structure.tree -o /path/to/output

# Force specific format
foldertree -f structure.yaml --format yaml
```

## Python

```bash
from foldertree import TreeParser, TreeGenerator

# Parse structure
parser = TreeParser()
tree = parser.parse("""
api/
  routes.py    # FastAPI endpoints
core/
  classifier.py  # ML model
""")

# Generate structure
generator = TreeGenerator("./output")
result = generator.generate(tree)
print(f"Created {len(result['created_files'])} files")
```

# Input Formats

- Tree Format (with symbols)
```bash
├── api/
│   ├── __init__.py
│   └── routes.py
├── core/
│   ├── __init__.py
│   └── classifier.py
├── data/
│   ├── chunks_head/
│   └── highlight.json
└── main.py
```

- Simple Indentation
```txt
api/
  routes.py                  # FastAPI endpoints
core/
  classifier.py              # ML model
main.py
```

- YAML Format
```YAML
structure:
  api:
    - routes.py
    - __init__.py
  core:
    - classifier.py
    - __init__.py
  main.py: null
```
___

# Comment Support
The tool automatically adds appropriate comments to files based on their extensions:

- .py files: # Comment
- .js/.ts files: // Comment
- .css files: /* Comment */
- .html/.xml files: <!-- Comment -->
- And many more...

# Smart Features
## Automatic `__init__.py` Creation
When directories contain .py files, `__init__.py` is automatically created to make them proper Python packages.
## Intelligent Skipping
Automatically skips common files and directories:

- `__pycache__`
- .git
- node_modules
- .env
- Build/dist directories
- And more...

# Options

- -f, --file: Input file containing folder structure
- -o, --output: Output directory (default: current directory)
- --format: Force input format (tree, yaml, simple, auto)
- --dry-run: Show what would be created without creating files
- -v, --verbose: Verbose output
- --version: Show version