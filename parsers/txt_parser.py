from .base_parser import BaseParser
import logging


class TxtParser(BaseParser):
    def parse(self, filepath: str) -> str:
        """Parses a text file and returns its content."""
        try:
            # Try UTF-8 first
            with open(filepath, "r", encoding="utf-8", errors="ignore") as file:
                content = file.read()
                # Remove NUL characters
                content = content.replace("\x00", "")
                if not content.strip():
                    raise ValueError("File is empty after cleaning")
                return content
        except UnicodeDecodeError:
            # Try different encodings if UTF-8 fails
            try:
                with open(filepath, "r", encoding="latin-1", errors="ignore") as file:
                    content = file.read()
                    content = content.replace("\x00", "")
                    if not content.strip():
                        raise ValueError("File is empty after cleaning")
                    return content
            except Exception as e:
                logging.error(f"Error reading text file with latin-1 encoding: {e}")
                return "Error reading text file"
        except Exception as e:
            logging.error(f"Error reading text file: {e}")
            return "Error reading text file"
