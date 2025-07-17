import pytest
from foldertree.core import TreeParser, TreeNode


class TestTreeParser:
    def test_parse_tree_format(self):
        parser = TreeParser()
        content = """
        ├── api/
        │   └── routes.py
        ├── core/
        │   └── classifier.py
        └── main.py
        """
        tree = parser.parse_tree_format(content)
        assert tree.name == "."
        assert len(tree.children) == 3
        assert tree.children[0].name == "api"
        assert tree.children[0].is_directory
        assert tree.children[0].children[0].name == "routes.py"
        assert not tree.children[0].children[0].is_directory
    
    def test_parse_simple_format(self):
        parser = TreeParser()
        content = """
        api/
          routes.py
        core/
          classifier.py
        main.py
        """
        tree = parser.parse_simple_format(content)
        assert tree.name == "."
        assert len(tree.children) == 3
    
    def test_parse_with_comments(self):
        parser = TreeParser()
        content = """
        api/
          routes.py  # FastAPI endpoints
        main.py      # Main application
        """
        tree = parser.parse_simple_format(content)
        assert tree.children[0].children[0].comment == "FastAPI endpoints"
        assert tree.children[1].comment == "Main application"
    
    def test_auto_detect_format(self):
        parser = TreeParser()
        
        # Should detect tree format
        tree_content = "├── api/\n│   └── routes.py"
        tree = parser.parse(tree_content)
        assert tree.name == "."
        
        # Should detect simple format
        simple_content = "api/\n  routes.py"
        tree = parser.parse(simple_content)
        assert tree.name == "."
