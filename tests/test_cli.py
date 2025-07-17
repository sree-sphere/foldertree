import tempfile
from pathlib import Path
from foldertree.cli import main
import sys
from io import StringIO

class TestCLI:
    def test_file_input(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create input file
            input_file = Path(tmp_dir) / "structure.tree"
            input_file.write_text("""
            api/
              routes.py
            main.py
            """)
            
            # Create output directory
            output_dir = Path(tmp_dir) / "output"
            
            # Simulate CLI args
            sys.argv = ['foldertree', '-f', str(input_file), '-o', str(output_dir)]
            
            # Capture output
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            
            try:
                main()
                output = sys.stdout.getvalue()
                
                # Check output
                assert "Created directories" in output
                assert "Created files" in output
                
                # Check actual files
                assert (output_dir / "api" / "routes.py").exists()
                assert (output_dir / "main.py").exists()
                
            finally:
                sys.stdout = old_stdout
    
    def test_dry_run(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_file = Path(tmp_dir) / "structure.tree"
            input_file.write_text("test.py")
            
            output_dir = Path(tmp_dir) / "output"
            
            sys.argv = ['foldertree', '-f', str(input_file), '-o', str(output_dir), '--dry-run']
            
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            
            try:
                main()
                output = sys.stdout.getvalue()
                
                assert "DRY RUN" in output
                assert not (output_dir / "test.py").exists()
                
            finally:
                sys.stdout = old_stdout