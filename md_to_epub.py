#!/usr/bin/env python3
"""
Convert Markdown files to beautifully-styled ePub format.
"""

import os
import re
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Tuple
import argparse


class EpubConverter:
    """Convert Markdown to ePub with beautiful styling."""

    # Beautiful CSS matching the example ePub
    CSS_STYLES = """
        body {
            font-family: Georgia, serif;
            line-height: 1.6;
            margin: 2em;
            color: #333;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 0.5em;
            margin-top: 2em;
        }
        h2 {
            color: #34495e;
            border-bottom: 2px solid #95a5a6;
            padding-bottom: 0.3em;
            margin-top: 1.5em;
        }
        h3 {
            color: #7f8c8d;
            margin-top: 1.2em;
        }
        h4 {
            color: #95a5a6;
            margin-top: 1em;
        }
        pre {
            background-color: #1e1e1e;
            border-left: 4px solid #007acc;
            padding: 1.2em;
            overflow-x: auto;
            border-radius: 5px;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 0.85em;
            line-height: 1.5;
        }
        code {
            background-color: #f4f4f4;
            padding: 0.2em 0.4em;
            border-radius: 3px;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            color: #c7254e;
        }
        pre code {
            background-color: transparent;
            padding: 0;
            color: #d4d4d4;
        }

        /* Java Syntax Highlighting */
        .keyword { color: #569cd6; font-weight: bold; }
        .type { color: #4ec9b0; }
        .string { color: #ce9178; }
        .comment { color: #6a9955; font-style: italic; }
        .annotation { color: #dcdcaa; }
        .method { color: #dcdcaa; }
        .number { color: #b5cea8; }
        .operator { color: #d4d4d4; }
        .builtin { color: #4fc1ff; }

        strong {
            color: #2c3e50;
        }
        em {
            color: #7f8c8d;
        }
        ul, ol {
            margin-left: 2em;
        }
        li {
            margin-bottom: 0.5em;
        }
        p {
            margin-bottom: 1em;
        }
        blockquote {
            border-left: 4px solid #95a5a6;
            padding-left: 1em;
            margin-left: 0;
            color: #7f8c8d;
            font-style: italic;
        }
        /* Table wrapper for horizontal scrolling */
        .table-wrapper {
            overflow-x: auto;
            margin: 1em 0;
            -webkit-overflow-scrolling: touch;
        }
        table {
            border-collapse: collapse;
            min-width: 100%;
            width: max-content;
            table-layout: fixed;
            margin: 0;
        }
        th, td {
            border: 1px solid #95a5a6;
            padding: 0.6em 1em;
            text-align: left;
            vertical-align: top;
            word-wrap: break-word;
            min-width: 120px;
        }
        th {
            background-color: #34495e;
            color: white;
            font-weight: bold;
            white-space: nowrap;
        }
        td {
            background-color: #fafafa;
        }
        tr:nth-child(even) td {
            background-color: #f0f0f0;
        }
        /* Ensure colgroup widths are respected */
        colgroup col {
            width: auto;
        }
    """

    def __init__(self, md_file: str, output_file: str = None):
        """Initialize converter with markdown file path."""
        self.md_file = Path(md_file)
        if not self.md_file.exists():
            raise FileNotFoundError(f"Markdown file not found: {md_file}")

        if output_file:
            self.output_file = Path(output_file)
        else:
            self.output_file = self.md_file.with_suffix('.epub')

        self.content = self.md_file.read_text(encoding='utf-8')
        self.title = self._extract_title()
        self.sections = self._extract_sections()

    def _extract_title(self) -> str:
        """Extract title from filename or first H1."""
        # Try to find first H1
        match = re.search(r'^#\s+(.+)$', self.content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        # Fallback to filename
        return self.md_file.stem.replace('-', ' ').replace('_', ' ')

    def _extract_sections(self) -> List[Tuple[str, str, int]]:
        """Extract sections from markdown for table of contents."""
        sections = []
        # Find all headers (h1-h4)
        pattern = r'^(#{1,4})\s+(.+)$'
        for match in re.finditer(pattern, self.content, re.MULTILINE):
            level = len(match.group(1))
            title = match.group(2).strip()
            anchor = self._generate_anchor(title)
            sections.append((title, anchor, level))
        return sections

    def _generate_anchor(self, text: str) -> str:
        """Generate HTML anchor from text."""
        # Remove special characters and convert to lowercase
        anchor = re.sub(r'[^\w\s-]', '', text.lower())
        anchor = re.sub(r'[-\s]+', '-', anchor)
        return anchor

    def _markdown_to_html(self) -> str:
        """Convert markdown to HTML with syntax highlighting."""
        html = self.content

        # Process code blocks first (to avoid processing markdown inside them)
        html = self._process_code_blocks(html)

        # Headers with anchors
        def header_replace(match):
            level = len(match.group(1))
            text = match.group(2).strip()
            anchor = self._generate_anchor(text)
            return f'<h{level} id="{anchor}">{text}</h{level}>'
        html = re.sub(r'^(#{1,6})\s+(.+)$', header_replace, html, flags=re.MULTILINE)

        # Bold
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)

        # Italic
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
        html = re.sub(r'_(.+?)_', r'<em>\1</em>', html)

        # Inline code (not in code blocks)
        html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)

        # Tables (must be before lists and paragraphs)
        html = self._process_tables(html)

        # Lists
        html = self._process_lists(html)

        # Blockquotes
        html = self._process_blockquotes(html)

        # Paragraphs
        html = self._process_paragraphs(html)

        return html

    def _process_code_blocks(self, text: str) -> str:
        """Process code blocks with syntax highlighting."""
        def code_block_replace(match):
            lang = match.group(1) or ''
            code = match.group(2)

            # Apply syntax highlighting for Java
            if lang.lower() in ['java', 'javascript', 'js', 'typescript', 'ts']:
                code = self._apply_syntax_highlighting(code)
            else:
                # Basic escaping
                code = code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

            return f'<pre><code>{code}</code></pre>'

        # Match ```lang\ncode\n``` blocks
        text = re.sub(r'```(\w+)?\n(.*?)\n```', code_block_replace, text, flags=re.DOTALL)
        return text

    def _apply_syntax_highlighting(self, code: str) -> str:
        """Apply syntax highlighting to code."""
        # Escape HTML first
        code = code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        # Java keywords
        keywords = ['public', 'private', 'protected', 'class', 'interface', 'enum',
                   'extends', 'implements', 'new', 'return', 'if', 'else', 'for',
                   'while', 'do', 'switch', 'case', 'break', 'continue', 'try',
                   'catch', 'finally', 'throw', 'throws', 'import', 'package',
                   'static', 'final', 'abstract', 'synchronized', 'volatile', 'this',
                   'super', 'null', 'true', 'false', 'void', 'const', 'let', 'var',
                   'function', 'async', 'await', 'export', 'default']

        # Types
        types = ['String', 'Integer', 'Long', 'Double', 'Float', 'Boolean', 'List',
                'Map', 'Set', 'Optional', 'ResponseEntity', 'User', 'Product', 'Data',
                'HttpStatus', 'HttpHeaders', 'URI', 'Resource', 'Void', 'CacheControl',
                'TimeUnit', 'ServletUriComponentsBuilder', 'MediaType', 'Page',
                'LocalDateTime', 'ErrorResponse', 'ErrorDetails']

        # Highlight comments
        code = re.sub(r'(//.*?)$', r'<span class="comment">\1</span>', code, flags=re.MULTILINE)
        code = re.sub(r'(/\*.*?\*/)', r'<span class="comment">\1</span>', code, flags=re.DOTALL)

        # Highlight strings
        code = re.sub(r'"([^"]*)"', r'<span class="string">"\1"</span>', code)

        # Highlight annotations
        code = re.sub(r'(@\w+)', r'<span class="annotation">\1</span>', code)

        # Highlight numbers
        code = re.sub(r'\b(\d+)\b', r'<span class="number">\1</span>', code)

        # Highlight keywords
        for keyword in keywords:
            code = re.sub(rf'\b({keyword})\b', r'<span class="keyword">\1</span>', code)

        # Highlight types
        for type_name in types:
            code = re.sub(rf'\b({type_name})\b', r'<span class="type">\1</span>', code)

        # Highlight method calls (word followed by parentheses)
        code = re.sub(r'(\w+)(?=\()', r'<span class="method">\1</span>', code)

        return code

    def _process_lists(self, text: str) -> str:
        """Process ordered and unordered lists."""
        lines = text.split('\n')
        result = []
        in_ul = False
        in_ol = False

        for line in lines:
            # Unordered list
            if re.match(r'^\s*[\*\-\+]\s+', line):
                if not in_ul:
                    result.append('<ul>')
                    in_ul = True
                if in_ol:
                    result.append('</ol>')
                    in_ol = False
                item = re.sub(r'^\s*[\*\-\+]\s+', '', line)
                result.append(f'<li>{item}</li>')
            # Ordered list
            elif re.match(r'^\s*\d+\.\s+', line):
                if not in_ol:
                    result.append('<ol>')
                    in_ol = True
                if in_ul:
                    result.append('</ul>')
                    in_ul = False
                item = re.sub(r'^\s*\d+\.\s+', '', line)
                result.append(f'<li>{item}</li>')
            else:
                if in_ul:
                    result.append('</ul>')
                    in_ul = False
                if in_ol:
                    result.append('</ol>')
                    in_ol = False
                result.append(line)

        # Close any remaining lists
        if in_ul:
            result.append('</ul>')
        if in_ol:
            result.append('</ol>')

        return '\n'.join(result)

    def _process_blockquotes(self, text: str) -> str:
        """Process blockquotes."""
        lines = text.split('\n')
        result = []
        in_blockquote = False

        for line in lines:
            if line.strip().startswith('>'):
                if not in_blockquote:
                    result.append('<blockquote>')
                    in_blockquote = True
                content = re.sub(r'^\s*>\s?', '', line)
                result.append(f'<p>{content}</p>')
            else:
                if in_blockquote:
                    result.append('</blockquote>')
                    in_blockquote = False
                result.append(line)

        if in_blockquote:
            result.append('</blockquote>')

        return '\n'.join(result)

    def _process_tables(self, text: str) -> str:
        """Process markdown tables with proper alignment and wrapper."""
        lines = text.split('\n')
        result = []
        table_lines = []
        in_table = False

        for i, line in enumerate(lines):
            # Check if line is a table row (contains |)
            if '|' in line and line.strip().startswith('|'):
                if not in_table:
                    in_table = True
                    table_lines = []
                table_lines.append(line)
            else:
                if in_table:
                    # End of table, process it
                    html_table = self._convert_table(table_lines)
                    result.append(html_table)
                    in_table = False
                    table_lines = []
                result.append(line)

        # Handle table at end of file
        if in_table and table_lines:
            html_table = self._convert_table(table_lines)
            result.append(html_table)

        return '\n'.join(result)

    def _convert_table(self, lines: List[str]) -> str:
        """Convert markdown table lines to HTML table."""
        if len(lines) < 2:
            return '\n'.join(lines)

        # Parse header row
        header_row = lines[0].strip()
        if header_row.startswith('|'):
            header_row = header_row[1:]
        if header_row.endswith('|'):
            header_row = header_row[:-1]
        headers = [cell.strip() for cell in header_row.split('|')]

        # Check for separator row (---|---|---)
        separator_idx = 1
        alignments = []
        if len(lines) > 1 and re.match(r'^\|?\s*:?-+:?\s*\|', lines[1]):
            sep_row = lines[1].strip()
            if sep_row.startswith('|'):
                sep_row = sep_row[1:]
            if sep_row.endswith('|'):
                sep_row = sep_row[:-1]
            sep_cells = [cell.strip() for cell in sep_row.split('|')]

            # Determine alignment for each column
            for cell in sep_cells:
                if cell.startswith(':') and cell.endswith(':'):
                    alignments.append('center')
                elif cell.endswith(':'):
                    alignments.append('right')
                else:
                    alignments.append('left')
            separator_idx = 2
        else:
            alignments = ['left'] * len(headers)

        # Build HTML table with colgroup for fixed widths
        html = ['<div class="table-wrapper">']
        html.append('<table>')

        # Add colgroup for consistent column widths
        html.append('<colgroup>')
        for _ in headers:
            html.append('<col/>')
        html.append('</colgroup>')

        # Table header
        html.append('<thead>')
        html.append('<tr>')
        for i, header in enumerate(headers):
            align = alignments[i] if i < len(alignments) else 'left'
            html.append(f'<th style="text-align: {align};">{header}</th>')
        html.append('</tr>')
        html.append('</thead>')

        # Table body
        html.append('<tbody>')
        for line in lines[separator_idx:]:
            row = line.strip()
            if row.startswith('|'):
                row = row[1:]
            if row.endswith('|'):
                row = row[:-1]
            cells = [cell.strip() for cell in row.split('|')]

            html.append('<tr>')
            for i, cell in enumerate(cells):
                align = alignments[i] if i < len(alignments) else 'left'
                html.append(f'<td style="text-align: {align};">{cell}</td>')
            html.append('</tr>')
        html.append('</tbody>')

        html.append('</table>')
        html.append('</div>')

        return '\n'.join(html)

    def _process_paragraphs(self, text: str) -> str:
        """Wrap text in paragraph tags."""
        lines = text.split('\n')
        result = []

        for line in lines:
            stripped = line.strip()
            # Skip if already an HTML tag or empty
            if not stripped or stripped.startswith('<'):
                result.append(line)
            else:
                result.append(f'<p>{line}</p>')

        return '\n'.join(result)

    def _create_mimetype(self) -> str:
        """Create mimetype file content."""
        return "application/epub+zip"

    def _create_container_xml(self) -> str:
        """Create META-INF/container.xml content."""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>
'''

    def _create_content_opf(self) -> str:
        """Create content.opf file."""
        date = datetime.now().strftime('%Y-%m-%d')
        identifier = self.md_file.stem.lower().replace(' ', '-')

        return f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>{self.title}</dc:title>
        <dc:creator>Auto-Generated</dc:creator>
        <dc:language>en</dc:language>
        <dc:identifier id="bookid">{identifier}-{date}</dc:identifier>
        <dc:date>{date}</dc:date>
        <dc:description>Generated from {self.md_file.name}</dc:description>
        <meta property="dcterms:modified">{datetime.now().isoformat()}Z</meta>
    </metadata>
    <manifest>
        <item id="content" href="content.html" media-type="application/xhtml+xml"/>
        <item id="toc" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
    </manifest>
    <spine toc="toc">
        <itemref idref="content"/>
    </spine>
</package>
'''

    def _create_toc_ncx(self) -> str:
        """Create table of contents NCX file."""
        identifier = self.md_file.stem.lower().replace(' ', '-')
        nav_points = []
        play_order = 1

        # Add main title
        nav_points.append(f'''        <navPoint id="content" playOrder="{play_order}">
            <navLabel>
                <text>{self.title}</text>
            </navLabel>
            <content src="content.html"/>''')

        # Add sections
        for title, anchor, level in self.sections:
            if level <= 2:  # Only include h1 and h2 in TOC
                play_order += 1
                nav_points.append(f'''            <navPoint id="{anchor}" playOrder="{play_order}">
                <navLabel>
                    <text>{title}</text>
                </navLabel>
                <content src="content.html#{anchor}"/>
            </navPoint>''')

        nav_points.append('        </navPoint>')

        return f'''<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
    <head>
        <meta name="dtb:uid" content="{identifier}"/>
        <meta name="dtb:depth" content="2"/>
        <meta name="dtb:totalPageCount" content="0"/>
        <meta name="dtb:maxPageNumber" content="0"/>
    </head>
    <docTitle>
        <text>{self.title}</text>
    </docTitle>
    <navMap>
{chr(10).join(nav_points)}
    </navMap>
</ncx>
'''

    def _create_content_html(self) -> str:
        """Create main content HTML file."""
        html_content = self._markdown_to_html()

        return f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>{self.title}</title>
    <style>
{self.CSS_STYLES}
    </style>
</head>
<body>

{html_content}

</body>
</html>
'''

    def convert(self):
        """Convert markdown to ePub."""
        print(f"Converting {self.md_file} to {self.output_file}...")

        # Create ePub zip file
        with zipfile.ZipFile(self.output_file, 'w', zipfile.ZIP_DEFLATED) as epub:
            # mimetype must be first and uncompressed
            epub.writestr('mimetype', self._create_mimetype(), compress_type=zipfile.ZIP_STORED)

            # META-INF
            epub.writestr('META-INF/container.xml', self._create_container_xml())

            # Content files
            epub.writestr('content.opf', self._create_content_opf())
            epub.writestr('toc.ncx', self._create_toc_ncx())
            epub.writestr('content.html', self._create_content_html())

        print(f"✓ Successfully created {self.output_file}")


def main():
    parser = argparse.ArgumentParser(description='Convert Markdown to beautifully-styled ePub')
    parser.add_argument('input', help='Input Markdown file')
    parser.add_argument('-o', '--output', help='Output ePub file (optional)')

    args = parser.parse_args()

    try:
        converter = EpubConverter(args.input, args.output)
        converter.convert()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
