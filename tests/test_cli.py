import pytest
import tempfile
from pathlib import Path
from foldertree.cli import main
import sys
from io import StringIO
import re

def strip_emojis_and_special_chars(text):
    return re.sub(r'[^\w\s:/\.-]', '', text)

class TestCLI:
    def test_file_input(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_file = Path(tmp_dir) / "structure.tree"
            input_file.write_text(
                "api/\n"
                "  routes.py\n"
                "main.py\n"
            )
            
            output_dir = Path(tmp_dir) / "output"
            sys.argv = ['foldertree', '-f', str(input_file), '-o', str(output_dir)]

            old_stdout = sys.stdout
            sys.stdout = StringIO()
            
            try:
                main()
                output = sys.stdout.getvalue()
                output = strip_emojis_and_special_chars(output)
                assert "created" in output.lower()
                assert "files" in output.lower()

                assert "routes.py" in output
                assert "main.py" in output

            finally:
                sys.stdout = old_stdout
    
    def test_cli_invalid_file(self, monkeypatch, capsys):
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_file = Path(tmp_dir) / "missing.tree"
            output_dir = Path(tmp_dir) / "output"
            monkeypatch.setattr(sys, 'argv', ['foldertree', '-f', str(input_file), '-o', str(output_dir)])
            with pytest.raises(SystemExit):
                main()
            captured = capsys.readouterr()
            err_output = strip_emojis_and_special_chars(captured.err)
            assert "not found" in err_output.lower()

    
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
    

def test_cli_help(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['foldertree', '--help'])
    sys.stdout = StringIO()
    try:
        with pytest.raises(SystemExit):
            main()
        output = sys.stdout.getvalue()
        assert "usage:" in output.lower()
    finally:
        sys.stdout = sys.__stdout__

def test_cli_empty_file(tmp_path, monkeypatch, capsys):
    input_file = tmp_path / "empty.tree"
    input_file.write_text("")

    monkeypatch.setattr(sys, 'argv', ['foldertree', '-f', str(input_file)])
    
    with pytest.raises(SystemExit):
        main()

    captured = capsys.readouterr()
    assert "no input provided" in captured.err.lower()

def test_cli_verbose_output(tmp_path, monkeypatch, capsys):
    input_file = tmp_path / "structure.tree"
    input_file.write_text("hello.py")

    output_dir = tmp_path / "out"

    monkeypatch.setattr(sys, 'argv', ['foldertree', '-f', str(input_file), '-o', str(output_dir), '--verbose'])

    main()

    captured = capsys.readouterr()
    assert "Total:" in captured.out
    assert "hello.py" in captured.out

def test_cli_invalid_format(monkeypatch, tmp_path, capsys):
    input_file = tmp_path / "invalid.tree"
    input_file.write_text("invalid content")
    monkeypatch.setattr(sys, 'argv', ['foldertree', '-f', str(input_file), '--format', 'invalid'])
    with pytest.raises(SystemExit):
        main()
    captured = capsys.readouterr()
    assert "error: argument --format: invalid choice: 'invalid'" in captured.err

def test_cli_file_read_exception(monkeypatch, tmp_path, capsys):
    input_file = tmp_path / "structure.tree"
    input_file.write_text("some content")
    
    def mock_open(*args, **kwargs):
        raise IOError("Permission denied")

    monkeypatch.setattr("builtins.open", mock_open)
    monkeypatch.setattr(sys, 'argv', ['foldertree', '-f', str(input_file)])
    
    with pytest.raises(SystemExit):
        main()
    captured = capsys.readouterr()
    assert "permission denied" in captured.err.lower()

def test_cli_stdin_isatty(monkeypatch, capsys):
    monkeypatch.setattr(sys, 'argv', ['foldertree'])  # No file
    monkeypatch.setattr(sys.stdin, 'isatty', lambda: True)
    with pytest.raises(SystemExit):
        main()
    captured = capsys.readouterr()
    assert "use -f file or provide input via stdin" in captured.err.lower()

def test_cli_skipped_items(tmp_path, monkeypatch, capsys):
    file = tmp_path / "structure.tree"
    file.write_text("__pycache__/\nmain.py")

    monkeypatch.setattr(sys, 'argv', ['foldertree', '-f', str(file), '-o', str(tmp_path / "out")])

    main()
    captured = capsys.readouterr()
    assert "Skipped items" in captured.out
    assert "__pycache__" in captured.out

def test_cli_tree_generator_throws(monkeypatch, tmp_path, capsys):
    file = tmp_path / "structure.tree"
    file.write_text("main.py")

    def mock_generate(*args, **kwargs):
        raise RuntimeError("some error")

    monkeypatch.setattr("foldertree.cli.TreeGenerator.generate", mock_generate)
    monkeypatch.setattr(sys, 'argv', ['foldertree', '-f', str(file)])

    with pytest.raises(SystemExit):
        main()
    captured = capsys.readouterr()
    assert "some error" in captured.err.lower()
