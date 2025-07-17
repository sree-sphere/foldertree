#!/usr/bin/env python3
"""
Command line interface for FolderTree Generator
"""

import sys
import argparse
from pathlib import Path
from .core import TreeParser, TreeGenerator


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
        version='%(prog)s "1.3.0"'
    )
    
    args = parser.parse_args()
    
    # Get input content
    if args.file:
        try:
            with open(args.file, 'r') as f:
                content = f.read()
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
    
    if not content.strip():
        print("Error: No input provided", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Parse input
        tree_parser = TreeParser()
        tree = tree_parser.parse(content, args.format)
        
        # Generate structure
        generator = TreeGenerator(args.output, args.dry_run)
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