from .base_parser import BaseParser
import logging
import markdown
import re
from bs4 import BeautifulSoup
from typing import List, Optional


class MDParser(BaseParser):
    def __init__(self):
        self.md = markdown.Markdown(
            extensions=[
                "fenced_code",  # Code blocks
                "tables",  # Tables
                "nl2br",  # Line breaks
                "sane_lists",  # Better list handling
                "def_list",  # Definition lists
                "footnotes",  # Footnotes
                "attr_list",  # Attributes
                "md_in_html",  # Nested markdown
                "smarty",  # Smart typography
            ]
        )

    def parse(self, filepath: str) -> str:
        try:
            # Read and preprocess markdown file
            with open(filepath, "r", encoding="utf-8") as file:
                content = self._preprocess_markdown(file.read())

            # Convert to HTML
            html = self.md.convert(content)
            soup = BeautifulSoup(html, "html.parser")

            processed_content = []

            # Process HTML elements
            for element in soup.find_all(self._get_elements_to_process()):
                if element.string and element.string.strip():
                    processed_text = self._process_element(element)
                    if processed_text:
                        processed_content.append(processed_text)

            final_content = "\n".join(processed_content)

            # Validate content
            if not self._validate_content(final_content):
                raise ValueError("Invalid or insufficient content in markdown")

            logging.info(f"Successfully parsed markdown file: {filepath}")
            return final_content

        except Exception as e:
            logging.error(f"Error processing markdown: {e}")
            return f"Error processing markdown file: {str(e)}"

    def _preprocess_markdown(self, content: str) -> str:
        """Clean and prepare markdown content"""
        # Remove HTML comments
        content = re.sub(r"<!--[\s\S]*?-->", "", content)
        # Remove YAML front matter
        content = re.sub(r"^---[\s\S]*?---\n", "", content)
        # Normalize line endings
        content = content.replace("\r\n", "\n")
        # Remove image references
        content = re.sub(r"!\[.*?\]\(.*?\)", "", content)
        return content.strip()

    def _get_elements_to_process(self) -> List[str]:
        """Define HTML elements to extract"""
        return [
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "p",
            "li",
            "pre",
            "code",
            "td",
            "th",
            "blockquote",
            "em",
            "strong",
            "ul",
            "ol",
            "dl",
            "dt",
            "dd",
            "hr",
        ]

    def _process_element(self, element) -> Optional[str]:
        """Process individual HTML elements"""
        try:
            if element.name.startswith("h"):
                level = int(element.name[1])
                return f"{'#' * level} {element.text.strip()}"
            elif element.name == "blockquote":
                return f"> {element.text.strip()}"
            elif element.name in ["em", "i"]:
                return f"_{element.text.strip()}_"
            elif element.name in ["strong", "b"]:
                return f"**{element.text.strip()}**"
            elif element.name == "hr":
                return "---"
            elif element.name in ["pre", "code"]:
                return f"```\n{element.text.strip()}\n```"
            elif element.name in ["td", "th"]:
                return f"| {element.text.strip()} |"
            else:
                return element.text.strip()
        except Exception as e:
            logging.error(f"Error processing element {element.name}: {e}")
            return None

    def _validate_content(self, content: str) -> bool:
        """Validate processed content"""
        if not content.strip():
            return False
        if len(content) < 10:
            return False

        # Check text/symbol ratio
        text_chars = len(re.findall(r"[a-zA-Z0-9]", content))
        total_chars = len(content)
        if total_chars == 0 or text_chars / total_chars < 0.3:
            return False

        return True
