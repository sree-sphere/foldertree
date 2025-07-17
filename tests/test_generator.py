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
            assert len(result['created_files']) == 2
            
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

def test_generate_nested_structure():
    with tempfile.TemporaryDirectory() as tmp_dir:
        gen = TreeGenerator(tmp_dir)
        root = TreeNode(".", True)
        deep = TreeNode("dir", True)
        file = TreeNode("file.txt", False)
        deep.children.append(file)
        root.children.append(deep)
        result = gen.generate(root)
        assert any("file.txt" in f for f in result['created_files'])

def test_should_create_init_py_with_py_files(tmp_path):
    dir_path = tmp_path / "pkg"
    dir_path.mkdir()
    (dir_path / "module.py").touch()
    generator = TreeGenerator(str(tmp_path))
    assert generator._should_create_init_py(dir_path) is True

def test_should_create_init_py_without_py_files(tmp_path):
    dir_path = tmp_path / "pkg"
    dir_path.mkdir()
    (dir_path / "README.md").touch()
    generator = TreeGenerator(str(tmp_path))
    assert generator._should_create_init_py(dir_path) is False

def test_file_with_css_comment(tmp_path):
    node = TreeNode("styles.css", False, "Style rules")
    root = TreeNode(".", True, children=[node])
    generator = TreeGenerator(str(tmp_path))
    generator.generate(root)
    content = (tmp_path / "styles.css").read_text()
    assert "/* Style rules */" in content

def test_file_with_xml_comment(tmp_path):
    node = TreeNode("config.xml", False, "XML config")
    root = TreeNode(".", True, children=[node])
    generator = TreeGenerator(str(tmp_path))
    generator.generate(root)
    content = (tmp_path / "config.xml").read_text()
    assert "<!-- XML config -->" in content

def test_comment_style_fallback(tmp_path):
    node = TreeNode("file.xyz", False, "Unknown format comment")
    root = TreeNode(".", True, children=[node])
    generator = TreeGenerator(str(tmp_path))
    generator.generate(root)
    content = (tmp_path / "file.xyz").read_text()
    assert "# Unknown format comment" in content

def test_xml_comment_style(tmp_path):
    node = TreeNode("config.xml", False, "XML config")
    root = TreeNode(".", True, children=[node])
    generator = TreeGenerator(str(tmp_path))
    generator.generate(root)
    content = (tmp_path / "config.xml").read_text()
    assert "<!-- XML config -->" in content

def test_dry_run_no_file_creation(tmp_path):
    generator = TreeGenerator(str(tmp_path), dry_run=True)
    root = TreeNode(".", True)
    file_node = TreeNode("test.txt", False, "Test file")
    root.children.append(file_node)
    result = generator.generate(root)
    assert len(result['created_files']) == 1
    assert not (tmp_path / "test.txt").exists()
