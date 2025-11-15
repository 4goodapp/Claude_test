#!/usr/bin/env python3
"""
Convert Markdown files to beautifully formatted ePub books.
"""

import sys
import os
from ebooklib import epub
import markdown
from datetime import datetime


def extract_title(md_file_path, md_content):
    """Extract title from filename or markdown content."""
    # First try to use the filename (without extension) as title
    base_name = os.path.splitext(os.path.basename(md_file_path))[0]
    if base_name and base_name != "Untitled":
        return base_name

    # Fallback to first heading in content
    lines = md_content.strip().split('\n')
    for line in lines:
        if line.strip().startswith('#'):
            # Remove markdown heading symbols and return
            return line.lstrip('#').strip()
    return "Untitled"


def create_beautiful_epub(md_file_path, output_path=None):
    """
    Convert a markdown file to a beautifully formatted ePub.

    Args:
        md_file_path: Path to the markdown file
        output_path: Optional output path for the ePub file
    """
    # Read the markdown file
    with open(md_file_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Extract title from filename or content
    title = extract_title(md_file_path, md_content)

    # Generate output filename if not provided
    if output_path is None:
        base_name = os.path.splitext(os.path.basename(md_file_path))[0]
        output_path = f"{base_name}.epub"

    # Create ePub book
    book = epub.EpubBook()

    # Set metadata
    book.set_identifier(f'id_{datetime.now().strftime("%Y%m%d%H%M%S")}')
    book.set_title(title)
    book.set_language('en')
    book.add_author('Technical Documentation')

    # Configure markdown with extensions for better formatting
    md = markdown.Markdown(extensions=[
        'extra',          # Tables, fenced code blocks, etc.
        'codehilite',     # Syntax highlighting
        'nl2br',          # Newline to <br>
        'sane_lists',     # Better list handling
        'toc',            # Table of contents
    ])

    # Convert markdown to HTML
    html_content = md.convert(md_content)

    # Create beautiful CSS styling
    css = '''
        @namespace epub "http://www.idpf.org/2007/ops";

        body {
            font-family: Georgia, 'Times New Roman', serif;
            line-height: 1.8;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            font-size: 1.1em;
        }

        h1 {
            font-size: 2.5em;
            color: #2c3e50;
            margin-top: 1.5em;
            margin-bottom: 0.8em;
            border-bottom: 3px solid #3498db;
            padding-bottom: 0.3em;
            font-weight: 700;
        }

        h2 {
            font-size: 2em;
            color: #34495e;
            margin-top: 1.5em;
            margin-bottom: 0.7em;
            border-bottom: 2px solid #95a5a6;
            padding-bottom: 0.3em;
            font-weight: 600;
        }

        h3 {
            font-size: 1.6em;
            color: #2c3e50;
            margin-top: 1.3em;
            margin-bottom: 0.6em;
            font-weight: 600;
        }

        h4 {
            font-size: 1.3em;
            color: #34495e;
            margin-top: 1.2em;
            margin-bottom: 0.5em;
            font-weight: 600;
        }

        p {
            margin: 1em 0;
            text-align: justify;
        }

        strong, b {
            font-weight: 700;
            color: #2c3e50;
        }

        em, i {
            font-style: italic;
            color: #555;
        }

        code {
            font-family: 'Courier New', Monaco, monospace;
            background-color: #f8f8f8;
            padding: 2px 6px;
            border: 1px solid #e1e4e8;
            border-radius: 3px;
            font-size: 0.9em;
            color: #d73a49;
        }

        pre {
            background-color: #f6f8fa;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            padding: 16px;
            overflow-x: auto;
            margin: 1.5em 0;
            line-height: 1.5;
        }

        pre code {
            background-color: transparent;
            border: none;
            padding: 0;
            color: #24292e;
            font-size: 0.95em;
        }

        blockquote {
            border-left: 4px solid #3498db;
            padding-left: 20px;
            margin-left: 0;
            font-style: italic;
            color: #555;
            background-color: #f8f9fa;
            padding: 15px 20px;
            border-radius: 0 4px 4px 0;
        }

        ul, ol {
            margin: 1em 0;
            padding-left: 2em;
        }

        li {
            margin: 0.5em 0;
            line-height: 1.6;
        }

        a {
            color: #3498db;
            text-decoration: none;
            border-bottom: 1px solid #3498db;
        }

        a:hover {
            color: #2980b9;
            border-bottom-color: #2980b9;
        }

        table {
            border-collapse: collapse;
            width: 100%;
            margin: 1.5em 0;
            font-size: 0.95em;
        }

        th, td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }

        th {
            background-color: #3498db;
            color: white;
            font-weight: 600;
        }

        tr:nth-child(even) {
            background-color: #f8f9fa;
        }

        hr {
            border: none;
            border-top: 2px solid #e1e4e8;
            margin: 2em 0;
        }

        .codehilite {
            background-color: #f6f8fa;
            border-radius: 6px;
            padding: 16px;
        }
    '''

    # Create CSS file
    nav_css = epub.EpubItem(
        uid="style_nav",
        file_name="style/nav.css",
        media_type="text/css",
        content=css
    )
    book.add_item(nav_css)

    # Create the main chapter
    chapter = epub.EpubHtml(
        title=title,
        file_name='content.xhtml',
        lang='en'
    )

    # Wrap content in proper HTML structure
    full_html = f'''
    <html>
    <head>
        <title>{title}</title>
        <link rel="stylesheet" href="style/nav.css" type="text/css"/>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    '''

    chapter.content = full_html
    chapter.add_item(nav_css)

    # Add chapter to book
    book.add_item(chapter)

    # Create table of contents
    book.toc = (epub.Link('content.xhtml', title, 'content'),)

    # Add navigation files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # Define spine (reading order)
    book.spine = ['nav', chapter]

    # Write the ePub file
    epub.write_epub(output_path, book, {})

    print(f"✓ Created: {output_path}")
    print(f"  Title: {title}")
    print(f"  Size: {os.path.getsize(output_path):,} bytes")
    return output_path


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 md_to_epub.py <markdown_file> [output_file]")
        sys.exit(1)

    md_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    if not os.path.exists(md_file):
        print(f"Error: File '{md_file}' not found")
        sys.exit(1)

    create_beautiful_epub(md_file, output_file)
