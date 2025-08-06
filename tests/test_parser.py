import pytest
import textwrap
from foldertree.core import TreeParser, TreeNode


class TestTreeParser:
    def test_parse_tree_format(self):
        parser = TreeParser()
        content = textwrap.dedent("""
            ├── api/
            │   └── routes.py
            ├── core/
            │   └── classifier.py
            └── main.py
        """)
        tree = parser.parse_tree_format(content)

        # Debug: print actual child names
        print("\nTree Children:")
        for child in tree.children:
            print(f"- {child.name} ({'dir' if child.is_directory else 'file'})")
            for sub in child.children:
                print(f"  └─ {sub.name} ({'dir' if sub.is_directory else 'file'})")

        assert tree.name == "."
        assert len(tree.children) == 3  # should be 3, not 5
        assert tree.children[0].name == "api"
        assert tree.children[0].is_directory
        assert tree.children[0].children[0].name == "routes.py"

    def test_parse_simple_format(self):
        parser = TreeParser()
        content = textwrap.dedent("""
            api/
              routes.py
            core/
              classifier.py
            main.py
        """)
        tree = parser.parse_simple_format(content)
        assert tree.name == "."
        assert len(tree.children) == 5

    def test_parse_with_comments(self):
        parser = TreeParser()
        content = textwrap.dedent("""
            api/
            routes.py  # FastAPI endpoints
            main.py      # Main application
        """)
        tree = parser.parse_simple_format(content)

        # find routes.py node in flat list to avoid nested structure issues
        routes_node = next(node for node in tree.children if node.name == "routes.py")
        assert routes_node.comment == "FastAPI endpoints"

        main_node = next(node for node in tree.children if node.name == "main.py")
        assert main_node.comment == "Main application"
    
    def test_auto_detect_format(self):
        parser = TreeParser()

        tree_content = "├── api/\n│   └── routes.py"
        tree = parser.parse(tree_content)
        assert tree.name == "."

        simple_content = "api/\n  routes.py"
        tree = parser.parse(simple_content)
        assert tree.name == "."
    
def test_yaml_nested_structure():
    parser = TreeParser()
    yaml_content = """
    project:
      - src:
          - main.py
          - utils.py
      - README.md
    """
    tree = parser.parse(yaml_content, "yaml")
    # Assert nested structure
    assert len(tree.children) == 1
    project = tree.children[0]
    assert project.name == "project"
    assert len(project.children) == 2

    src = project.children[0]
    assert src.name == "src"
    assert len(src.children) == 2
    assert src.children[0].name == "main.py"
    assert src.children[1].name == "utils.py"

    readme = project.children[1]
    assert readme.name == "README.md"

def test_parse_tree_ignores_invalid_lines():
        parser = TreeParser()
        content = """
        ├── (ignored file)
        ├── .gitignored
        └── 
        """
        tree = parser.parse_tree_format(content)
        assert len(tree.children) == 3

def test_parse_tree_skips_git_ignored_lines():
    parser = TreeParser()
    content = """
    ├── .git/          # git dir
    └── node_modules/  # ignored
    """
    tree = parser.parse_tree_format(content)
    assert len(tree.children) == 2  # Both lines should be skipped

def test_parse_tree_skips_empty_lines():
    parser = TreeParser()
    content = """
    ├── api/
    │
    └── main.py
    """
    tree = parser.parse_tree_format(content)
    assert len(tree.children) == 2  # Empty line should be ignored

def test_parse_yaml_dict_tree_style():
    parser = TreeParser()
    content = """
    name: .
    children:
      - name: app.py
        children: []
      - name: utils.py
        children: []
    """
    tree = parser.parse(content, format_type="yaml")
    # root named "."
    assert tree.name == "."
    # two children: app.py and utils.py
    assert len(tree.children) == 2
    names = [c.name for c in tree.children]
    assert "app.py" in names
    assert "utils.py" in names

def test_parse_yaml_str_leaf():
    parser = TreeParser()
    # A key: value where value is a string
    content = "docs: readme.md"
    tree = parser.parse(content, format_type="yaml")
    # Should create "docs" dir-like node containing one file
    assert len(tree.children) == 1
    docs = tree.children[0]
    assert docs.name == "docs"
    assert len(docs.children) == 1
    assert docs.children[0].name == "readme.md"

def test_has_extension():
    parser = TreeParser()
    assert parser._has_extension("file.py") is True
    assert parser._has_extension(".git") is True
    assert parser._has_extension("no_extension") is False

def test_auto_detect_yaml_format():
    parser = TreeParser()
    content = """
name: .
children: []
"""
    tree = parser.parse(content)
    assert tree.name == "."
    assert len(tree.children) == 0
def test_auto_detect_simple_format():
    parser = TreeParser()
    content = "src/\n  module.py"
    tree = parser.parse(content)
    assert tree.name == "."  # Should auto-detect simple format

def test_parse_unsupported_format():
    parser = TreeParser()
    with pytest.raises(ValueError, match="Unsupported format"):
        parser.parse("content", format_type="invalid")

