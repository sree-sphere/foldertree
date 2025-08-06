#!/usr/bin/env python3
"""
Command line interface for FolderTree Generator
"""

import sys
import argparse
import re
from pathlib import Path
from foldertree.core import TreeParser, TreeGenerator


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description='Generate folder structures from various input formats',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # From file
  foldertree -f structure.tree

  # From stdin
  echo "api/\\n  routes.py" | foldertree

  # Single path creation
  foldertree -p "src/utils/helper.py"
  foldertree -p "src/components/Button.tsx" -p "src/hooks/useState.ts"

  # Dry run
  foldertree -f structure.tree --dry-run

  # Specify output directory
  foldertree -f structure.tree -o /path/to/output

  # Force format
  foldertree -f structure.yaml --format yaml
        """
    )

    parser.add_argument(
        '-f', '--file',
        help='Input file containing folder structure'
    )
    parser.add_argument(
        '-p', '--path',
        action='append',
        help='Create single path (can be used multiple times). Example: -p "src/utils/helper.py"'
    )
    parser.add_argument(
        '-o', '--output',
        default='.',
        help='Output directory (default: current directory)'
    )
    parser.add_argument(
        '--format',
        choices=['tree', 'yaml', 'simple', 'auto'],
        default='auto',
        help='Input format (default: auto-detect)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be created without actually creating files'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s "1.3.2"'
    )
    args = parser.parse_args()

    # Load and filter content
    if args.path:
        # Path mode: treat each path as a standalone entry
        content = '\n'.join(args.path)
        format_type = 'simple'
    elif args.file:
        try:
            with open(args.file, 'r') as f:
                content = f.read()
            # force tree format for .tree extension
            if args.format == 'auto' and args.file.lower().endswith('.tree'):
                format_type = 'tree'
            else:
                format_type = args.format
        except FileNotFoundError:
            print(f"Error: File '{args.file}' not found", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Read from stdin
        if sys.stdin.isatty():
            print("Error: No input provided. Use -f FILE or provide input via stdin.", file=sys.stderr)
            sys.exit(1)
        content = sys.stdin.read()
        format_type = args.format

    # Remove lines that are just dots or ellipses
    lines = content.splitlines()
    filtered = []
    for l in lines:
        if re.match(r'^\s*(?:\.+|\u2026+)\s*$', l):
            continue
        filtered.append(l)
    content = '\n'.join(filtered)

    if not content.strip():
        print("Error: No input provided", file=sys.stderr)
        sys.exit(1)

    try:
        # Parse input
        tree_parser = TreeParser()
        if args.verbose:
            print(f"Parsing input with format '{format_type}'")
            # print("debug — Content passed to parser:\n" + content)
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
        content = _inject_slashes_for_tree_format(content)
        tree = tree_parser.parse(content, format_type)
        if args.verbose:
            print(f"Parsed {tree} from input")

        # Generate structure
        generator = TreeGenerator(base_path=args.output, dry_run=args.dry_run)
        result = generator.generate(tree)

        # Print results
        if args.dry_run:
            print("🔍 DRY RUN - No files were actually created")
            print()

        if result['created_dirs']:
            print(f"📁 Created directories ({len(result['created_dirs'])}):")
            for dir_path in result['created_dirs']:
                print(f"  📁 {dir_path}")
            print()

        if result['created_files']:
            print(f"📄 Created files ({len(result['created_files'])}):")
            for file_path in result['created_files']:
                print(f"  📄 {file_path}")
            print()

        if result['skipped_items']:
            print(f"⏭️  Skipped items ({len(result['skipped_items'])}):")
            for item in result['skipped_items']:
                print(f"  ⏭️  {item}")
            print()

        if args.verbose:
            print(f"✅ Total: {len(result['created_dirs'])} directories, {len(result['created_files'])} files")
            if result['skipped_items']:
                print(f"⏭️  Skipped: {len(result['skipped_items'])} items")
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()