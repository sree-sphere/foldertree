import pytest
import tempfile
from pathlib import Path
from foldertree.core import TreeGenerator, TreeNode

class TestTreeGenerator:
    def test_generate_structure(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            generator = TreeGenerator(tmp_dir)
            
            # Create test tree
            root = TreeNode(".", True)
            api_dir = TreeNode("api", True)
            routes_file = TreeNode("routes.py", False)
            api_dir.children.append(routes_file)
            root.children.append(api_dir)
            
            result = generator.generate(root)
            
            # Check results
            assert len(result['created_dirs']) == 1
            assert len(result['created_files']) == 1
            
            # Check actual files
            api_path = Path(tmp_dir) / "api"
            routes_path = api_path / "routes.py"
            assert api_path.exists()
            assert routes_path.exists()
    
    def test_dry_run(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            generator = TreeGenerator(tmp_dir, dry_run=True)
            
            root = TreeNode(".", True)
            test_file = TreeNode("test.py", False)
            root.children.append(test_file)
            
            result = generator.generate(root)
            
            # Should report creation but not actually create
            assert len(result['created_files']) == 1
            assert not (Path(tmp_dir) / "test.py").exists()
    
    def test_skip_patterns(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            generator = TreeGenerator(tmp_dir)
            
            root = TreeNode(".", True)
            pycache = TreeNode("__pycache__", True)
            normal_file = TreeNode("test.py", False)
            root.children.extend([pycache, normal_file])
            
            result = generator.generate(root)
            
            # Should skip __pycache__
            assert len(result['skipped_items']) == 1
            assert result['skipped_items'][0] == "__pycache__"
            assert len(result['created_files']) == 1
    
    def test_comment_insertion(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            generator = TreeGenerator(tmp_dir)
            
            root = TreeNode(".", True)
            py_file = TreeNode("test.py", False, "Main module")
            js_file = TreeNode("test.js", False, "JavaScript module")
            root.children.extend([py_file, js_file])
            
            result = generator.generate(root)
            
            # Check comment insertion
            py_path = Path(tmp_dir) / "test.py"
            js_path = Path(tmp_dir) / "test.js"
            
            assert py_path.read_text() == "# Main module\n"
            assert js_path.read_text() == "// JavaScript module\n"
