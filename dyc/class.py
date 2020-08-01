"""
File for classes that handles the class headers in
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


class ClassBuilder(Builder):
    already_printed_filepaths = []

    def extract_and_set_information(self, filename, start, line, length):
        """
        This is a main abstract method tin the builder base
        to add result into details. Used in Class Builder to
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
        class_string = start_line
        if not is_one_line_method(start_line, self.config.get("keywords")):
            class_string = line
            linesBackwards = class_string.count("\n") - 1
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
            class_string += line
            lineno = lineno + 1
            line = linecache.getline(filename, int(lineno))
            end_of_file = True if lineno > length else False

        if not end:
            end = length

        linecache.clearcache()
        return ClassInterface(
            plain=class_string,
            name=self._get_name(initial_line),
            start=start,
            end=end,
            filename=filename,
            arguments=self.extract_arguments(initial_line.strip("\n")),
            config=self.config,
            leading_space=get_leading_whitespace(initial_line),
            placeholders=self.placeholders,
        )


class ClassFormatter:
    formatted_string = "{open}{break_after_open}{class_docstring}{break_after_docstring}{break_before_close}{close}"
    fmt = BlankFormatter()

    def format(self):
        """
        Public formatting method that executes a pattern of methods to
        complete the process
        """
        self.pre()
        self.build_docstrings()
        self.result = self.fmt.format(self.formatted_string, **self.class_format)
        self.add_indentation()
        self.polish()

    def wrap_strings(self, words):
        """
        Compact how many words should be in a line
        Parameters
        ----------
        str words: docstring given
        """
        subs = []
        n = self.config.get("words_per_line")
        for i in range(0, len(words), n):
            subs.append(" ".join(words[i : i + n]))
        return "\n".join(subs)

    def pre(self):
        """
        In the formatter, this method sets up the object that
        will be used in a formatted way. Also translates configs
        into consumable values

        TODO could this be moved to base class?
        """
        class_format = copy.deepcopy(self.config)
        class_format["indent"] = (
            get_indent(class_format["indent"]) if class_format["indent"] else "    "
        )
        class_format["indent_content"] = (
            get_indent(class_format["indent"])
            if get_indent(class_format["indent_content"])
            else ""
        )
        class_format["break_after_open"] = (
            "\n" if class_format["break_after_open"] else ""
        )
        class_format["break_after_docstring"] = (
            "\n" if class_format["break_after_docstring"] else ""
        )
        class_format["break_before_close"] = (
            "\n" if class_format["break_before_close"] else ""
        )
        class_format["empty_line"] = "\n"

        self.class_format = class_format

    def build_docstring(self):
        """
        Mainly adds docstrings of the class after cleaning up text
        into reasonable chunks
        """
        text = self.class_docstring or "Missing Docstring!"
        self.class_format["class_docstring"] = self.wrap_strings(text.split(" "))

    def add_indentation(self):
        """
        Translates indent params to actual indents
        """
        temp = self.result.split("\n")
        space = self.class_format.get("indent")
        indent_content = self.class_format.get("indent_content")
        if indent_content:
            content = temp[1:-1]
            content = [indent_content + docline for docline in temp][1:-1]
            temp[1:-1] = content
        self.result = "\n".join([space + docline for docline in temp])

    def confirm(self, polished):
        """
        Pop up editor function to finally confirm if the documented
        format is accepted
        Parameters
        ----------
        str polished: complete polished string before popping up
        """
        polished = add_start_end(polished)
        class_split = self.plain.split("\n")
        if self.config.get("within_scope"):
            # Check if method comes in an unusual format
            keywords = self.config.get("keywords")
            firstLine = class_split[0]
            pos = 1
            while not is_one_line_method(firstLine, keywords):
                firstLine += class_split[pos]
                pos += 1
            class_split.insert(pos, polished)
        else:
            class_split.insert(0, polished)

        try:
            result = "\n".join(class_split)
            message = click.edit(
                "## CONFIRM: MODIFY DOCSTRING BETWEEN START AND END LINES ONLY\n\n"
                + result
            )
            message = "\n".join(message.split("\n")[2:])
        except:
            print("Quitting the program in the editor terminates the process. Thanks")
            sys.exit()

        final = []
        start = False
        end = False

        for x in message.split("\n"):
            stripped = x.strip()
            if stripped == "## END":
                end = True
            if start and not end:
                final.append(x)
            if stripped == "## START":
                start = True

        self.result = "\n".join(final)

    def polish(self):
        """
        Editor wrapper to confirm result
        """
        docstring = self.result.split("\n")
        polished = "\n".join([self.leading_space + docline for docline in docstring])
        if self.placeholders:
            self.result = polished
        else:
            self.confirm(polished)


class ClassInterface(ClassFormatter):
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
        self.class_docstring = ""
        self.config = config
        self.leading_space = leading_space
        self.placeholders = placeholders

    def prompt(self):
        """
        Wrapper method for prompts and calls for prompting classes then formats them
        """
        self._prompt_docstring()
        self.format()

    def _prompt_docstring(self):
        """
        Simple prompt for a class's docstring
        """
        if self.placeholders:
            self.class_docstring = "<docstring>"
        else:
            echo_name = click.style(self.name, fg="green")
            self.class_docstring = click.prompt(
                "\n({}) Class docstring ".format(echo_name)
            )
        pass