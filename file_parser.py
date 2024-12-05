import os
from typing import Type, Dict

# Import all parsers
from parsers.base_parser import BaseParser
from parsers import TxtParser, PdfParser, DocxParser, MDParser, ImageParser


# Parser factory with registration system
class ParserFactory:
    _parsers: Dict[str, Type[BaseParser]] = {}

    @classmethod
    def register_parser(cls, extension: str, parser: Type[BaseParser]) -> None:
        cls._parsers[extension] = parser

    @classmethod
    def get_parser(cls, extension: str) -> BaseParser:
        parser = cls._parsers.get(extension)
        if not parser:
            raise ValueError(f"No parser found for extension: {extension}")
        return parser()


ParserFactory.register_parser("txt", TxtParser)
ParserFactory.register_parser("pdf", PdfParser)
ParserFactory.register_parser("docx", DocxParser)
ParserFactory.register_parser("md", MDParser)
ParserFactory.register_parser("png", ImageParser)
ParserFactory.register_parser("jpg", ImageParser)
ParserFactory.register_parser("jpeg", ImageParser)


# FileParser class
class FileParser:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.parser = self._get_parser()

    def _get_parser(self) -> BaseParser:
        extension = self.filepath.split(".")[-1]
        if extension not in ParserFactory._parsers:
            raise ValueError(f"Unsupported file extension: {extension}")
        return ParserFactory.get_parser(extension)

    def parse(self) -> str:
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"File not found: {self.filepath}")
        return self.parser.parse(self.filepath)
