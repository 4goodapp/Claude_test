# Markdown to ePub Converter

This repository contains a Python script to convert Markdown files to beautifully-styled ePub format.

## Features

- **Beautiful Styling**: Professional typography with Georgia serif font
- **Syntax Highlighting**: Dark-themed code blocks with Java/JavaScript syntax highlighting
- **Proper ePub Structure**: Compliant with ePub 3.0 standards
- **Table of Contents**: Automatically generated from markdown headers
- **Responsive Design**: Clean, readable layout optimized for e-readers

## Usage

### Basic Usage

```bash
python3 md_to_epub.py input.md
```

This will create `input.epub` in the same directory.

### Specify Output File

```bash
python3 md_to_epub.py input.md -o output.epub
```

### Examples

Convert the Spring ResponseEntity guide:
```bash
python3 md_to_epub.py "Spring Controller ResponseEntity - Deep Dive.md"
```

Convert HTTP guide with custom output name:
```bash
python3 md_to_epub.py "HTTP Parameters vs HTTP Headers - A Deep Dive.md" -o "HTTP Guide.epub"
```

## Styling Features

The generated ePub includes:

- **Headers**: Color-coded with bottom borders (H1: blue, H2: gray)
- **Code Blocks**: Dark background (#1e1e1e) with blue left border
- **Inline Code**: Light gray background with red text
- **Syntax Highlighting**:
  - Keywords: Blue
  - Types: Teal
  - Strings: Orange
  - Comments: Green (italic)
  - Annotations: Yellow
  - Methods: Yellow
  - Numbers: Light green

## Example

See `spring-responseentity.epub` for an example of the beautiful output this converter produces.

## Requirements

- Python 3.6+
- No external dependencies (uses only standard library)

## File Structure

The script generates a standard ePub structure:
```
epub-file.epub
├── mimetype
├── META-INF/
│   └── container.xml
├── content.opf
├── toc.ncx
└── content.html
```

## License

Free to use and modify.
