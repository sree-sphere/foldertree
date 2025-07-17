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
    
    def parse_tree_format(self, content: str) -> TreeNode:
        """Parse tree-like structure (with ├── └── symbols)"""
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
            # indent = len(line) - len(line.lstrip())
            indent = len(re.match(r'^[│├└─\s]*', line).group())

            
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
    
    def parse_simple_format(self, content: str) -> TreeNode:
        """Parse simple indented format"""
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
            if stripped.startswith(('├', '└', '│')):
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
