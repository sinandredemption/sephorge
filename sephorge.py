#!/usr/bin/env python3

import os
import shutil
from pathlib import Path
import markdown # For Markdown to HTML conversion
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup
import re
import glob

PAGES_DIR_NAME = "pages"
PUBLIC_DIR_NAME = "public"
DEFAULT_TEMPLATE_FILE_NAME = "page.html" # Assumed to be in the same directory as this script or specified path

_script_dir = Path(__file__).resolve().parent
_pages_dir = _script_dir / PAGES_DIR_NAME
_public_dir = _script_dir / PUBLIC_DIR_NAME
_template_file = _script_dir / DEFAULT_TEMPLATE_FILE_NAME

def process_wikilinks(rendered_html, output_file_path):
    def replace_wikilink(match):
        page_name = match.group(1)
        pages_dir = Path(_pages_dir)
        # Escape special characters in page_name to avoid glob issues
        page_name_escaped = glob.escape(page_name)
        # Search for the page in _pages_dir and its subdirectories
        matches = list(pages_dir.glob(f'**/{page_name_escaped}.md'))
        if not matches:
            print(f"Error: No page found for [[{page_name}]]")
            return f'[[{page_name}]]'  # Return original if not found
        target_md = matches[0]
        # Compute the target HTML path relative to the site's root
        target_html_rel = _public_dir / target_md.relative_to(pages_dir).with_suffix('.html')
        target_html_str = str(target_html_rel).replace('\\', '/')
        # Determine current output directory
        current_dir = os.path.dirname(output_file_path)
        # Handle root directory case
        if not current_dir:
            current_dir = '.'
        # Compute the relative link from current_dir to target_html_str
        try:
            relative_link = os.path.relpath(target_html_str, current_dir)
        except ValueError:
            # Fallback to absolute path if relpath fails (unlikely if same drive)
            relative_link = target_html_str
        # Ensure forward slashes for URLs
        relative_link = relative_link.replace('\\', '/')
        # Ensure relative links start with ./ if in the same directory
        if not relative_link.startswith(('.', '/')):
            # Check if the target is in the same directory
            if os.path.dirname(target_html_str) == current_dir:
                relative_link = f'./{relative_link}'
        return f'<a href="{relative_link}">{page_name}</a>'
    
    # Use regex to substitute all [[...]] with the generated links
    processed_html = re.sub(r'\[\[(.*?)\]\]', replace_wikilink, rendered_html)
    return processed_html

# --- Provided function by the user ---
def convert_md_to_html(input_file_path: str, output_file_path: str, template_file_path: str):
    """
    Convert markdown file to HTML using the specified template.

    Args:
        input_file_path: Path to the source markdown file.
        output_file_path: Path to the destination HTML file.
        template_file_path: Path to the HTML template file.
    """
    # Get website name from environment variable or use a default value
    website_name = os.environ.get('WEBSITE_NAME', 'Sephorge Site')

    # Extract title from the input filename (remove .md extension, replace underscores/hyphens with spaces, and title case)
    # e.g., "my-first_post.md" becomes "My First Post"
    file_stem = Path(input_file_path).stem
    title = file_stem.replace('_', ' ').replace('-', ' ').title()

    # Read the content of the markdown file
    try:
        with open(input_file_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
    except FileNotFoundError:
        print(f"Error: Markdown file not found at {input_file_path}")
        return
    except Exception as e:
        print(f"Error reading markdown file {input_file_path}: {e}")
        return

    # Convert markdown content to HTML
    # 'extra' includes extensions like fenced_code, tables, footnotes, etc.
    # 'codehilite' adds syntax highlighting to code blocks (requires Pygments)
    try:
        html_from_markdown = markdown.markdown(md_content, extensions=['extra', 'codehilite'])
    except Exception as e:
        print(f"Error converting markdown to HTML for file {input_file_path}: {e}")
        return

    # Create the output directory if it doesn't already exist
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

    # Set up Jinja2 environment
    # The loader will look for templates in the directory where the template_file_path is located
    try:
        template_dir = os.path.dirname(template_file_path)
        if not template_dir: # If template_file_path is just a filename, assume current dir
            template_dir = "."
        env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )

        # Load the template
        template_name = os.path.basename(template_file_path)
        template = env.get_template(template_name)

        # Render the HTML using the template and the converted markdown content
        # Wrap html_from_markdown in Markup() to prevent Jinja2 from auto-escaping it,
        # as it's already HTML.
        rendered_html = template.render(
            title=title,
            WebsiteName=website_name,
            content=Markup(html_from_markdown)
        )

        # Replace [[Link]] with corresponding targets
        rendered_html = process_wikilinks(rendered_html, output_file_path)
        

    except Exception as e:
        print(f"Error during templating for file {input_file_path} with template {template_file_path}: {e}")
        return

    # Write the rendered HTML to the output file
    try:
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(rendered_html)
    except Exception as e:
        print(f"Error writing HTML file {output_file_path}: {e}")

def process_files(base_dir: Path, pages_dir: Path, public_dir: Path, template_file: Path):
    """
    Processes all files in the pages_dir and generates the static site in public_dir.
    """
    if not pages_dir.is_dir():
        print(f"Error: Source directory '{pages_dir}' not found.")
        print(f"Please create a '{PAGES_DIR_NAME}' directory in '{base_dir}' and add your content.")
        return

    # Ensure the public directory exists, create if not
    public_dir.mkdir(parents=True, exist_ok=True)

    # Walk through all files and directories in the pages_dir
    for root, _, files in os.walk(pages_dir):
        source_root_path = Path(root)

        for filename in files:
            source_file_path = source_root_path / filename

            # Determine the relative path from the pages_dir
            # This helps in creating the same directory structure in public_dir
            # e.g., pages/blog/post.md -> blog/post.md
            relative_path = source_file_path.relative_to(pages_dir)

            # Construct the destination path in the public_dir
            # e.g., public/blog/post.html or public/assets/image.jpg
            destination_path_dir = public_dir / relative_path.parent
            destination_path_dir.mkdir(parents=True, exist_ok=True) # Ensure subdirectories exist

            if filename.lower().endswith(".md"):
                # For Markdown files, change extension to .html for the destination
                destination_file_path = destination_path_dir / (relative_path.stem + ".html")

                # Check if regeneration is needed (source is newer or destination doesn't exist)
                if not destination_file_path.exists() or \
                   source_file_path.stat().st_mtime > destination_file_path.stat().st_mtime:
                    print(f"Processing Markdown: {source_file_path} -> {destination_file_path}")
                    convert_md_to_html(str(source_file_path), str(destination_file_path), str(template_file))

            else:
                # For other files (static assets like images, CSS, JS), just copy them
                destination_file_path = public_dir / relative_path

                # Check if copy is needed (source is newer or destination doesn't exist)
                if not destination_file_path.exists() or \
                   source_file_path.stat().st_mtime > destination_file_path.stat().st_mtime:
                    print(f"Copying asset: {source_file_path} -> {destination_file_path}")
                    try:
                        shutil.copy2(source_file_path, destination_file_path) # copy2 preserves metadata
                    except Exception as e:
                        print(f"Error copying file {source_file_path} to {destination_file_path}: {e}")

def main():
    """
    Main function to run the static site generator.
    """
    # Determine the base directory (where the script is located)
    script_dir = Path(__file__).resolve().parent
    
    pages_abs_dir = script_dir / PAGES_DIR_NAME
    public_abs_dir = script_dir / PUBLIC_DIR_NAME
    
    # The template file is expected to be in the same directory as the script,
    # or the path provided in DEFAULT_TEMPLATE_FILE_NAME should be absolute or resolvable.
    template_abs_path = script_dir / DEFAULT_TEMPLATE_FILE_NAME
    if not template_abs_path.is_file():
        # Fallback if user provides a different path for template or places it elsewhere
        # For simplicity, this script assumes it's co-located or specified with a relative path
        # that works from the script's directory.
        # An alternative would be to allow specifying template path via command-line argument.
        print(f"Warning: Default template '{DEFAULT_TEMPLATE_FILE_NAME}' not found in script directory '{script_dir}'.")
        print(f"Ensure your template file is correctly placed or update DEFAULT_TEMPLATE_FILE_NAME.")
        # Attempt to use it as is, in case it's an absolute path or relative to CWD
        template_abs_path = Path(DEFAULT_TEMPLATE_FILE_NAME)


    print("Sephorge Static Site Generator")
    print(f"Source (Pages) Directory: {pages_abs_dir}")
    print(f"Output (Public) Directory: {public_abs_dir}")
    print(f"Using Template: {template_abs_path}")
    print("-" * 30)

    process_files(script_dir, pages_abs_dir, public_abs_dir, template_abs_path)

    print("-" * 30)
    print("Site generation process complete.")

if __name__ == "__main__":
    if not _pages_dir.exists():
        print(f"Error: Source directory '{_pages_dir}' not found.")
        print(f"Please create a '{PAGES_DIR_NAME}' directory in '{_script_dir}' and add your content.")
        import sys
        sys.exit(1) # Exit with an error code
    if not _template_file.is_file():
         print(f"Error: Default template file '{_template_file}' not found.")
         print(f"Please ensure the template file '{DEFAULT_TEMPLATE_FILE_NAME}' exists in '{_script_dir}'.")
         import sys
         sys.exit(1) # Exit with an error code

    # Start timing the main site generation process
    import time
    start_time = time.perf_counter()

    main()

    end_time = time.perf_counter()
    duration = end_time - start_time
    print(f"\nSite generation took {duration:.4f} seconds.")
