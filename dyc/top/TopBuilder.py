"""
File for classes that handles the file headers
the application. Here is the the place where the actual reading,
parsing and validation of the files happens.
"""
import linecache
from ..utils import (
    get_leading_whitespace,
)
from ..base import Builder
from .TopInterface import TopInterface


class TopBuilder(Builder):
    already_printed_filepaths = []

    def extract_and_set_information(self, filename, start, line, length):
        """
        This is a main abstract method tin the builder base
        to add result into details. Used in Top Builder to
        pull the candidates that are subject to docstrings
        Parameters
        ----------
        str filename: The file's name
        int start: Starting line
        str line: Full line text
        int length: The length of the extracted data
        """
        start_line = linecache.getline(filename, start)
        initial_line = line
        start_leading_space = get_leading_whitespace(
            start_line
        )  # Where function started
        top_string = start_line
        line_within_scope = True
        lineno = start + 1
        line = linecache.getline(filename, lineno)
        end_of_file = False
        end = None
        while line_within_scope and not end_of_file:
            current_leading_space = get_leading_whitespace(line)
            if len(current_leading_space) <= len(start_leading_space) and line.strip():
                end = lineno - 1
                break
            top_string += line
            lineno = lineno + 1
            line = linecache.getline(filename, int(lineno))
            end_of_file = True if lineno > length else False

        if not end:
            end = length

        linecache.clearcache()
        return TopInterface(
            plain=top_string,
            name=self._get_name(initial_line),
            start=start,
            end=end,
            filename=filename,
            arguments=self.extract_arguments(initial_line.strip("\n")),
            config=self.config,
            leading_space=get_leading_whitespace(initial_line),
            placeholders=self.placeholders,
        )