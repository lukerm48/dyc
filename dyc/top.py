"""
File for classes that handles the file headers
the application. Here is the the place where the actual reading,
parsing and validation of the files happens.
"""
import sys
import re
import fileinput
import copy
import linecache
import click
from .utils import (
    get_leading_whitespace,
    BlankFormatter,
    get_indent,
    add_start_end,
    is_one_line_method,
)
from .base import Builder
import os

class TopBuilder(Builder):
    already_printed_filepaths = []

    def extract_and_set_information(self, filename, start, line, length):
        """
        This is a main abstract method tin the builder base
        to add result into details. Used in Method Builder to
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
        method_string = start_line
        if not is_one_line_method(start_line, self.config.get("keywords")):
            method_string = line
            linesBackwards = method_string.count("\n") - 1
            start_leading_space = get_leading_whitespace(
                linecache.getline(filename, start - linesBackwards)
            )
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
            method_string += line
            lineno = lineno + 1
            line = linecache.getline(filename, int(lineno))
            end_of_file = True if lineno > length else False

        if not end:
            end = length

        linecache.clearcache()
        return TopInterface(
            plain=method_string,
            name=self._get_name(initial_line),
            start=start,
            end=end,
            filename=filename,
            arguments=self.extract_arguments(initial_line.strip("\n")),
            config=self.config,
            leading_space=get_leading_whitespace(initial_line),
            placeholders=self.placeholders,
        )

class TopFormatter:
    """
    TODO
    """
    formatted_string = "{open}{break_after_open}{method_docstring}{break_after_docstring}{empty_line}{argument_format}{break_before_close}{close}"
    fmt = BlankFormatter()

    def format(self):
        """
        TODO
        Public formatting method that executes a pattern of methods to
        complete the process
        """
        self.pre()
        self.build_docstrings()
        self.build_arguments()
        self.result = self.fmt.format(self.formatted_string, **self.method_format)
        self.add_indentation()
        self.polish()

    def wrap_strings(self, words):
        pass

    def pre(self):
        pass

    def build_docstring(self):
        pass

    def build_arguments(self):
        pass

    def add_indentation(self):
        pass

    def confirm(self, polished):
        pass

    def polish(self):
        pass

class TopInterface(TopFormatter):
    """
    TODO
    """
    def __init__(
        self,
        plain,
        name,
        start,
        end,
        filename,
        arguments,
        config,
        leading_space,
        placeholders,
    ):
        self.plain = plain
        self.name = name
        self.start = start
        self.end = end
        self.filename = filename
        self.arguments = arguments
        self.method_docstring = ""
        self.arg_docstring = []
        self.config = config
        self.leading_space = leading_space
        self.placeholders = placeholders

    def prompt(self):
        """
        Wrapper method for prompts and calls for prompting args and
        methods then formats them
        """
        self._prompt_docstring()
        self._prompt_args()
        self.format()

    def _prompt_docstring(self):
        """
        TODO
        """
        pass

    def _prompt_args(self):
        """
        TODO
        """

        def _echo_arg_style(argument):
            """
            TODO
            """
            pass

        pass
