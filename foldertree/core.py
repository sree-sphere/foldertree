#!/usr/bin/env python3

import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Union
from dataclasses import dataclass


@dataclass
class TreeNode:
    name: str
    is_directory: bool
    comment: Optional[str] = None
    children: Optional[List['TreeNode']] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []


class TreeParser:
    
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
    
    def parse_tree_format(self, content: str) -> TreeNode:
        lines = content.strip().split('\n')
        root = TreeNode(".", True)
        stack = [(root, -1)]  # (node, indent_level)
        
        for line in lines:
            if not line.strip():
                continue
                
            # Remove tree symbols and get the actual content
            clean_line = re.sub(r'^[│├└─\s]*', '', line)
            if not clean_line:
                continue
                
            # Calculate indentation level
            indent = len(line) - len(line.lstrip())
            
            # Extract comment if present
            comment = None
            if '#' in clean_line:
                parts = clean_line.split('#', 1)
                clean_line = parts[0].strip()
                comment = parts[1].strip()
            
            # Skip lines with only comments or ignore patterns
            if not clean_line or clean_line.startswith('(') or 'git ignored' in clean_line.lower():
                continue
                
            # Determine if it's a directory
            is_directory = clean_line.endswith('/') or clean_line.endswith('\\')
            name = clean_line.rstrip('/\\')
            
            # Find the correct parent based on indentation
            while stack and stack[-1][1] >= indent:
                stack.pop()
            
            parent = stack[-1][0] if stack else root
            
            # Create new node
            node = TreeNode(name, is_directory, comment)
            parent.children.append(node)
            stack.append((node, indent))
        
        return root
    
    def parse_yaml_format(self, content: str) -> TreeNode:
        try:
            data = yaml.safe_load(content)
            return self._yaml_to_tree(data, ".")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {e}")
    
    def _yaml_to_tree(self, data: Union[Dict, List, str], name: str) -> TreeNode:
        if isinstance(data, dict):
            node = TreeNode(name, True)
            for key, value in data.items():
                child = self._yaml_to_tree(value, key)
                node.children.append(child)
            return node
        elif isinstance(data, list):
            node = TreeNode(name, True)
            for item in data:
                if isinstance(item, str):
                    child = TreeNode(item, not self._has_extension(item))
                    node.children.append(child)
                else:
                    child = self._yaml_to_tree(item, str(item))
                    node.children.append(child)
            return node
        else:
            return TreeNode(str(data), not self._has_extension(str(data)))
    
    def parse_simple_format(self, content: str) -> TreeNode:
        lines = content.strip().split('\n')
        root = TreeNode(".", True)
        stack = [(root, -1)]
        
        for line in lines:
            if not line.strip():
                continue
                
            # Calculate indentation
            indent = len(line) - len(line.lstrip())
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
            
            # Find parent
            while stack and stack[-1][1] >= indent:
                stack.pop()
            
            parent = stack[-1][0] if stack else root
            
            # Create node
            node = TreeNode(name, is_directory, comment)
            parent.children.append(node)
            stack.append((node, indent))
        
        return root
    
    def _has_extension(self, filename: str) -> bool:
        return '.' in filename and not filename.startswith('.')
    
    def parse(self, content: str, format_type: str = 'auto') -> TreeNode:
        if format_type == 'auto':
            # Auto-detect format
            if content.strip().startswith(('├', '└', '│')):
                format_type = 'tree'
            elif content.strip().startswith(('-', 'name:', 'structure:')):
                format_type = 'yaml'
            else:
                format_type = 'simple'
        
        if format_type == 'tree':
            return self.parse_tree_format(content)
        elif format_type == 'yaml':
            return self.parse_yaml_format(content)
        elif format_type == 'simple':
            return self.parse_simple_format(content)
        else:
            raise ValueError(f"Unsupported format: {format_type}")


class TreeGenerator:
    
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
            '.gitignore',
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
        
        init_file = directory / "__init__.py"
        if not init_file.exists():
            if not self.dry_run:
                init_file.touch()
            self.created_files.append(str(init_file))
    
    def _should_create_init_py(self, directory: Path) -> bool:
        # Check if directory contains .py files
        if not self.dry_run and directory.exists():
            return any(f.suffix == '.py' for f in directory.iterdir() if f.is_file())
        return False
    
    def _create_file_with_comment(self, file_path: Path, comment: str) -> None:

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
        if not self.dry_run:
            dir_path.mkdir(parents=True, exist_ok=True)
        self.created_dirs.append(str(dir_path))
    
    def _create_file(self, file_path: Path) -> None:
        if not self.dry_run:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.touch()
        self.created_files.append(str(file_path))
    
    def _generate_recursive(self, node: TreeNode, current_path: Path) -> None:
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