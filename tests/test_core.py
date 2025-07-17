from foldertree.core import TreeNode, TreeGenerator

def test_tree_node_repr():
    node = TreeNode("test", True, "folder")
    assert "test" in repr(node)
    assert "folder" in repr(node)


def test_tree_node_dict():
    node = TreeNode("test.py", False, "entry file")
    result = node.to_dict()
    assert result['name'] == "test.py"
    assert result['comment'] == "entry file"
    assert result['is_directory'] is False

def test_create_init_py_skipped_if_exists(tmp_path):
    dir_path = tmp_path / "pkg"
    dir_path.mkdir()
    init_file = dir_path / "__init__.py"
    init_file.write_text("already here")

    generator = TreeGenerator(str(tmp_path))
    generator._create_init_py(dir_path)

    assert "__init__.py" in init_file.name
    assert init_file.read_text() == "already here"  # Still intact
    assert str(init_file) not in generator.created_files  # Not added

def test_file_with_html_comment(tmp_path):
    node = TreeNode("index.html", False, "Main page")
    root = TreeNode(".", True, children=[node])

    generator = TreeGenerator(str(tmp_path))
    generator.generate(root)

    content = (tmp_path / "index.html").read_text()
    assert "<!-- Main page -->" in content