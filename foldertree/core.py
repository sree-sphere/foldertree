#!/usr/bin/env python3
"""
FolderTree Generator - Create folder structures from various input formats
"""

import os
import sys
import re
import yaml
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
import json


@dataclass
class TreeNode:
    """Represents a node in the folder tree structure"""
    name: str
    is_directory: bool
    comment: Optional[str] = None
    children: Optional[List['TreeNode']] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []
    
    def to_dict(self):
        return {
            "name": self.name,
            "is_directory": self.is_directory,
            "comment": self.comment,
            "children": [child.to_dict() for child in self.children]
        }


class TreeParser:
    """Parse various input formats into a tree structure"""
    
    def __init__(self):
        self.comment_styles = {
            '.py': '#',
            '.js': '//',
            '.ts': '//',
            '.java': '//',
            '.cpp': '//',
            '.c': '//',
            '.h': '//',
            '.hpp': '//',
            '.css': '/*',
            '.html': '<!--',
            '.xml': '<!--',
            '.yml': '#',
            '.yaml': '#',
            '.sh': '#',
            '.bash': '#',
            '.zsh': '#',
            '.fish': '#',
            '.ps1': '#',
            '.rb': '#',
            '.go': '//',
            '.rs': '//',
            '.php': '//',
            '.sql': '--',
            '.r': '#',
            '.m': '%',
            '.tex': '%',
            '.lua': '--',
            '.pl': '#',
            '.swift': '//',
            '.kt': '//',
            '.scala': '//',
            '.clj': ';',
            '.hs': '--',
            '.elm': '--',
            '.dart': '//',
            '.vue': '//',
            '.jsx': '//',
            '.tsx': '//',
        }
    
    def _calculate_tree_indent_level(self, line: str) -> int:
        """Calculate indentation level for tree format lines"""
        # Count the tree symbols and spaces to determine depth
        tree_symbols = re.match(r'^([│├└─\s]*)', line).group(1)

        level = 0
        i = 0
        while i < len(tree_symbols):
            if tree_symbols[i] in '├└':
                level += 1
                i += 4  # skip "├── " or "└── "
            elif tree_symbols[i] == '│':
                level += 1
                i += 4  # skip "│   "
            else:
                i += 1

        return level

    def _clean_tree_line(self, line: str) -> Tuple[str, str]:
        """Clean tree line and extract comment"""
        clean_line = re.sub(r'^[│├└─\s]*', '', line).strip()
        comment = None
        if '#' in clean_line:
            parts = clean_line.split('#', 1)
            clean_line = parts[0].strip()
            comment = parts[1].strip()
        return clean_line, comment

    @staticmethod
    def _inject_slashes_for_tree_format(content: str) -> str:
        """
        Add trailing slashes to directory names in tree-drawing format (├──, └──).
        This looks at indent structure to guess if an entry is a folder.
        """
        lines = content.strip().splitlines()
        result = []
        for i, line in enumerate(lines):
            if not re.match(r'^[│├└─\s]*\S', line):
                result.append(line)
                continue

            # Check if this line likely represents a directory
            indent_level = 0
            tree_symbols = re.match(r'^([│├└─\s]*)', line).group(1)
            for symbol in tree_symbols:
                if symbol in '├└│':
                    indent_level += 1

            clean_line = re.sub(r'^[│├└─\s]*', '', line).strip()
            name = clean_line.split('#', 1)[0].strip()

            is_directory = '.' not in name and not name.endswith('/')
            # Peek ahead to see if deeper indent follows
            for j in range(i + 1, len(lines)):
                next_line = lines[j]
                if not re.match(r'^[│├└─\s]*\S', next_line):
                    continue
                next_indent = 0
                tree_symbols_next = re.match(r'^([│├└─\s]*)', next_line).group(1)
                for symbol in tree_symbols_next:
                    if symbol in '├└│':
                        next_indent += 1
                if next_indent > indent_level:
                    is_directory = True
                    break  # stop as soon as one deeper indent found
                elif next_indent <= indent_level:
                    break  # stop if not deeper — not a dir


            if is_directory and not name.endswith('/'):
                line = line.replace(name, f'{name}/', 1)

            result.append(line)

        return '\n'.join(result)


    def parse_tree_format(self, content: str) -> TreeNode:
        """Parse tree-like structure (with ├── └── symbols) using indent-based parent detection"""
        print("parsing tree format")
        content = self._inject_slashes_for_tree_format(content)
        lines = content.strip().split('\n')

        # Handle optional root line
        root_name = "."
        if lines and lines[0].strip() == ".":
            lines = lines[1:]

        root = TreeNode(root_name, True)
        stack: List[Tuple[TreeNode, int]] = [(root, -1)]

        for i, line in enumerate(lines):
            if not line.strip():
                continue
            if not re.match(r'^[│├└─\s]*\S', line):
                continue

            indent_level = self._calculate_tree_indent_level(line)
            clean_line, comment = self._clean_tree_line(line)

            if clean_line in ("…", "...") or not clean_line:
                continue

            # Peek ahead to next valid line to determine if it's a dir
            is_directory = False
            for j in range(i + 1, len(lines)):
                next_line = lines[j]
                if not re.match(r'^[│├└─\s]*\S', next_line):
                    continue
                next_indent = self._calculate_tree_indent_level(next_line)
                if next_indent > indent_level:
                    is_directory = True
                break

            name = clean_line.rstrip("/\\")

            while len(stack) > 1 and stack[-1][1] >= indent_level:
                stack.pop()
            parent = stack[-1][0]

            node = TreeNode(name, is_directory, comment)
            parent.children.append(node)
            stack.append((node, indent_level))

        return root

    
    def parse_yaml_format(self, yaml_content):
        yaml_data = yaml.safe_load(yaml_content)
        return self._yaml_to_tree(yaml_data, '.')
    
    def _yaml_to_tree(self, data: Union[Dict, List, str], name: str) -> TreeNode:
        """Convert YAML data to tree structure"""
        if isinstance(data, dict):
            node = TreeNode(name, True)
            for key, value in data.items():
                child = self._yaml_to_tree(value, key)
                node.children.append(child)
            return node
        elif isinstance(data, list):
            node = TreeNode(name, True)
            for i, item in enumerate(data):
                if isinstance(item, dict):
                    for key, value in item.items():
                        child = self._yaml_to_tree(value, key)
                        node.children.append(child)
                else:
                    child = TreeNode(str(item), False)
                    node.children.append(child)
            return node
        else:
            return TreeNode(str(data), False)
    
    def _calculate_simple_indent_level(self, line: str) -> int:
        """Calculate indentation level for simple format"""
        # Count leading spaces, treating 4 spaces as one level
        leading_spaces = len(line) - len(line.lstrip(' '))
        return leading_spaces // 4
    
    @staticmethod
    def _inject_slashes_for_simple_tree(content: str) -> str:
        """
        Take an indented “simple” tree (no ├─ lines) and append a trailing slash to any line that:
        - isnt already ended with /
        - doesnt look like it has an extension (no dot in the last path component)
        so that the existing parser will treat it as a folder.
        """
        # matches any non-blank line whose name starts with a non-dot, non-slash, and has no trailing slash.
        pattern = re.compile(r'^([ \t]*)([^\s./][^\n]*)$', flags=re.M)

        def _slashify(match: re.Match) -> str:
            indent, name = match.groups()
            # if it already has an extension, or is a file-like, leave it
            if '.' in name or name.endswith('/'):
                return match.group(0)
            # otherwise append slash
            return f"{indent}{name}/"

        return pattern.sub(_slashify, content)
    
    def parse_simple_format(self, content: str) -> TreeNode:
        """Parse simple indented format"""
        raw_lines = content.splitlines()
        if raw_lines and raw_lines[0].strip() == ".":
            raw_lines = raw_lines[1:]
        content = self._inject_slashes_for_simple_tree('\n'.join(raw_lines))
        lines = content.splitlines()
        root = TreeNode(".", True)
        stack = [(root, -1)]
        
        for i, line in enumerate(lines):
            if not line.strip():
                continue
            
            # Calculate indentation level (4 spaces = 1 level)
            indent_level = self._calculate_simple_indent_level(line)
            clean_line = line.strip()
            
            # Extract comment
            comment = None
            if '#' in clean_line:
                parts = clean_line.split('#', 1)
                clean_line = parts[0].strip()
                comment = parts[1].strip()
            
            if not clean_line:
                continue
            
            # Determine if directory
            is_directory = clean_line.endswith('/') or not self._has_extension(clean_line)
            name = clean_line.rstrip('/')
            
            # Find parent based on indentation
            while len(stack) > 1 and stack[-1][1] >= indent_level:
                stack.pop()
            
            parent = stack[-1][0]
            
            # Create node
            node = TreeNode(name, is_directory, comment)
            parent.children.append(node)
            stack.append((node, indent_level))
        
        return root
    
    def _has_extension(self, filename: str) -> bool:
        """Check if filename has an extension.

        Treat standalone dot‑files (.gitignore, .env) as having an extension, so they become files, not directories.
        """
        # if its a leading single dot‑file with no other dots, treat it as a file
        if filename.startswith('.') and filename.count('.') == 1:
            return True
        # otherwise fall back to "contains a dot somewhere" but not a leading dot
        return '.' in filename and not filename.startswith('.')
    
    def parse(self, content: str, format_type: str = 'auto') -> TreeNode:
        """Parse content based on format type"""
        stripped = content.strip()
        
        if format_type == 'auto':
            # Auto-detect format
            if any(line.strip().startswith(('├', '└', '│')) for line in stripped.split('\n')):
                format_type = 'tree'
            elif stripped.startswith(('-', '{', '[', 'name:', 'structure:')):
                format_type = 'yaml'
            else:
                format_type = 'simple'

        if format_type == 'tree':
            return self.parse_tree_format(content)
        elif format_type == 'yaml':
            import yaml
            parsed = yaml.safe_load(content)
            return self._parse_yaml(parsed)
        elif format_type == 'simple':
            return self.parse_simple_format(content)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def _parse_yaml(self, node, name=".") -> TreeNode:
        # Handle dict-like TreeNode serialization: {"name": ..., "children": [...]}
        if isinstance(node, dict) and "name" in node:
            node_name = node.get("name", name)
            is_dir = True
            root = TreeNode(node_name, is_directory=is_dir)
            for child in node.get("children", []):
                root.children.append(self._parse_yaml(child))
            return root

        # Fallback to previous logic
        root = TreeNode(name, is_directory=True)

        if isinstance(node, dict):
            for key, value in node.items():
                child = self._parse_yaml(value, key)
                root.children.append(child)
        elif isinstance(node, list):
            for item in node:
                if isinstance(item, dict):
                    for key, value in item.items():
                        child = self._parse_yaml(value, key)
                        root.children.append(child)
                else:
                    root.children.append(TreeNode(str(item), is_directory=False))
        elif isinstance(node, str):
            root.children.append(TreeNode(node, is_directory=False))

        return root


class TreeGenerator:
    """Generate folder structures on filesystem"""
    
    def __init__(self, base_path: str = ".", dry_run: bool = False):
        self.base_path = Path(base_path)
        self.dry_run = dry_run
        self.parser = TreeParser()
        self.created_files = []
        self.created_dirs = []
        self.skipped_items = []
    
    def _should_skip(self, name: str) -> bool:
        """Check if item should be skipped"""
        skip_patterns = [
            '__pycache__',
            '*.pyc',
            '.git',
            '.DS_Store',
            'Thumbs.db',
            '*.log',
            '.pytest_cache',
            '.venv',
            'venv',
            '.env',
            'node_modules',
            '.coverage',
            'htmlcov',
            '*.egg-info',
            'build',
            'dist',
        ]
        
        return any(
            name == pattern or 
            (pattern.startswith('*') and name.endswith(pattern[1:])) or
            (pattern.endswith('*') and name.startswith(pattern[:-1]))
            for pattern in skip_patterns
        )
    
    def _create_init_py(self, directory: Path) -> None:
        """Create __init__.py file in Python package directories"""
        init_file = directory / "__init__.py"
        if not init_file.exists():
            if not self.dry_run:
                init_file.touch()
            self.created_files.append(str(init_file))
    
    def _should_create_init_py(self, directory: Path) -> bool:
        """Check if directory should have __init__.py"""
        # Check if directory contains .py files
        if not self.dry_run and directory.exists():
            return any(f.suffix == '.py' for f in directory.iterdir() if f.is_file())
        return False
    
    def _create_file_with_comment(self, file_path: Path, comment: str) -> None:
        """Create file with initial comment"""
        if not self.dry_run:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Determine comment style
            comment_char = self.parser.comment_styles.get(file_path.suffix, '#')
            
            if comment_char == '/*':
                content = f"/* {comment} */\n"
            elif comment_char == '<!--':
                content = f"<!-- {comment} -->\n"
            else:
                content = f"{comment_char} {comment}\n"
            
            file_path.write_text(content)
        
        self.created_files.append(str(file_path))
    
    def _create_directory(self, dir_path: Path) -> None:
        """Create directory"""
        if not self.dry_run:
            dir_path.mkdir(parents=True, exist_ok=True)
        self.created_dirs.append(str(dir_path))
    
    def _create_file(self, file_path: Path) -> None:
        """Create empty file"""
        if not self.dry_run:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.touch()
        self.created_files.append(str(file_path))
    
    def _generate_recursive(self, node: TreeNode, current_path: Path) -> None:
        """Recursively generate folder structure"""
        for child in node.children:
            if self._should_skip(child.name):
                self.skipped_items.append(child.name)
                continue
            
            child_path = current_path / child.name
            
            if child.is_directory:
                self._create_directory(child_path)
                self._generate_recursive(child, child_path)
                
                # Check if we should create __init__.py after creating all children
                if self._should_create_init_py(child_path):
                    self._create_init_py(child_path)
            else:
                if child.comment:
                    self._create_file_with_comment(child_path, child.comment)
                else:
                    self._create_file(child_path)
    
    def generate(self, tree: TreeNode) -> Dict[str, List[str]]:
        """Generate folder structure from tree"""
        self.created_files = []
        self.created_dirs = []
        self.skipped_items = []
        
        # Create base directory if it doesn't exist
        if not self.dry_run:
            self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Generate structure
        self._generate_recursive(tree, self.base_path)
        
        return {
            'created_files': self.created_files,
            'created_dirs': self.created_dirs,
            'skipped_items': self.skipped_items
        }

# def main():
#     """Main CLI interface"""
#     parser = argparse.ArgumentParser(
#         description='Generate folder structures from various input formats',
#         formatter_class=argparse.RawDescriptionHelpFormatter,
#         epilog="""
# Examples:
#   # From file
#   foldertree -f structure.tree

#   # From stdin
#   echo "api/\\n  routes.py" | foldertree

#   # Single path creation
#   foldertree -p "src/utils/helper.py"
#   foldertree -p "src/components/Button.tsx" -p "src/hooks/useState.ts"

#   # Dry run
#   foldertree -f structure.tree --dry-run

#   # Specify output directory
#   foldertree -f structure.tree -o /path/to/output

#   # Force format
#   foldertree -f structure.yaml --format yaml
#         """
#     )

#     parser.add_argument(
#         '-f', '--file',
#         help='Input file containing folder structure'
#     )
#     parser.add_argument(
#         '-p', '--path',
#         action='append',
#         help='Create single path (can be used multiple times). Example: -p "src/utils/helper.py"'
#     )
#     parser.add_argument(
#         '-o', '--output',
#         default='.',
#         help='Output directory (default: current directory)'
#     )
#     parser.add_argument(
#         '--format',
#         choices=['tree', 'yaml', 'simple', 'auto'],
#         default='auto',
#         help='Input format (default: auto-detect)'
#     )
#     parser.add_argument(
#         '--dry-run',
#         action='store_true',
#         help='Show what would be created without actually creating files'
#     )
#     parser.add_argument(
#         '--verbose', '-v',
#         action='store_true',
#         help='Verbose output'
#     )
#     parser.add_argument(
#         '--version',
#         action='version',
#         version='%(prog)s "1.3.2"'
#     )
#     args = parser.parse_args()

#     # Load and filter content
#     if args.path:
#         # Path mode: treat each path as a standalone entry
#         content = '\n'.join(args.path)
#         format_type = 'simple'
#     elif args.file:
#         try:
#             with open(args.file, 'r') as f:
#                 content = f.read()
#             # force tree format for .tree extension
#             if args.format == 'auto' and args.file.lower().endswith('.tree'):
#                 format_type = 'tree'
#             else:
#                 format_type = args.format
#         except FileNotFoundError:
#             print(f"Error: File '{args.file}' not found", file=sys.stderr)
#             sys.exit(1)
#         except Exception as e:
#             print(f"Error reading file: {e}", file=sys.stderr)
#             sys.exit(1)
#     else:
#         # Read from stdin
#         if sys.stdin.isatty():
#             print("Error: No input provided. Use -f FILE, -p PATH, or provide input via stdin.", file=sys.stderr)
#             sys.exit(1)
#         content = sys.stdin.read()
#         format_type = args.format

#     # Remove lines that are just dots or ellipses
#     lines = content.splitlines()
#     filtered = []
#     for l in lines:
#         if re.match(r'^\s*(?:\.+|\u2026+)\s*$', l):
#             continue
#         filtered.append(l)
#     content = '\n'.join(filtered)

#     if not content.strip():
#         print("Error: No input provided", file=sys.stderr)
#         sys.exit(1)

#     try:
#         # Parse input
#         tree_parser = TreeParser()
#         print(f"Parsing input with format '{format_type}'")
#         print("DEBUG — Content passed to parser:\n" + content)
#         tree = tree_parser.parse(content, format_type)
#         print(f"Parsed {tree} from input")

#         # Generate structure
#         generator = TreeGenerator(base_path=args.output, dry_run=args.dry_run)
#         result = generator.generate(tree)

#         # Print results
#         if args.dry_run:
#             print("🔍 DRY RUN - No files were actually created")
#             print()

#         if result['created_dirs']:
#             print(f"📁 Created directories ({len(result['created_dirs'])}):")
#             for dir_path in result['created_dirs']:
#                 print(f"  📁 {dir_path}")
#             print()

#         if result['created_files']:
#             print(f"📄 Created files ({len(result['created_files'])}):")
#             for file_path in result['created_files']:
#                 print(f"  📄 {file_path}")
#             print()

#         if result['skipped_items']:
#             print(f"⏭️  Skipped items ({len(result['skipped_items'])}):")
#             for item in result['skipped_items']:
#                 print(f"  ⏭️  {item}")
#             print()

#         if args.verbose:
#             print(f"✅ Total: {len(result['created_dirs'])} directories, {len(result['created_files'])} files")
#             if result['skipped_items']:
#                 print(f"⏭️  Skipped: {len(result['skipped_items'])} items")
#     except Exception as e:
#         print(f"❌ Error: {e}", file=sys.stderr)
#         sys.exit(1)


# if __name__ == "__main__":
#     main()