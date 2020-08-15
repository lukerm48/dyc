"""
File for classes that handles the file headers
the application. Here is the the place where the actual reading,
parsing and validation of the files happens.
"""
import sys
import copy
import click
from ..utils import (
    BlankFormatter,
    convert_indent,
    add_start_end,
)


class TopFormatter:
    formatted_string = "{doc_open}{break_after_open}{top_docstring}{break_after_docstring}{break_before_close}{doc_close}"
    fmt = BlankFormatter()

    def format(self):
        """
        Public formatting method that executes a pattern of methods to
        complete the process
        """
        self.pre()
        self.build_docstrings()
        self.result = self.fmt.format(self.formatted_string, **self.top_format)
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
        will be used in a formatted way,. Also translates configs
        into consumable values
        """
        top_format = copy.deepcopy(self.config)
        top_format["indent"] = (
            convert_indent(top_format["indent"]) if top_format["indent"] else "    "
        )
        top_format["indent_content"] = (
            convert_indent(top_format["indent"])
            if top_format["indent_content"]
            else ""
        )
        top_format["break_after_open"] = (
            "\n" if top_format["break_after_open"] else ""
        )
        top_format["break_after_docstring"] = (
            "\n" if top_format["break_after_docstring"] else ""
        )
        top_format["break_before_close"] = (
            "\n" if top_format["break_before_close"] else ""
        )
        top_format["empty_line"] = "\n"

        self.top_format = top_format

    def build_docstrings(self):
        """
        Mainly adds docstrings of the file after cleaning up text
        into reasonable chunks
        """
        text = self.top_docstring or "Missing Docstring!"
        self.top_format["top_docstring"] = self.wrap_strings(text.split(" "))

    def add_indentation(self):
        """
        Translates indent params to actual indents
        """
        temp = self.result.split("\n")
        space = self.top_format.get("indent")
        indent_content = self.top_format.get("indent_content")
        if indent_content:
            content = temp[1:-1]
            content = [indent_content + docline for docline in temp][1:-1]
            temp[1:-1] = content
        self.result = "\n".join([docline for docline in temp])

    def confirm(self, polished):
        """
        Pop up editor function to finally confirm if the documented
        format is accepted
        Parameters
        ----------
        str polished: complete polished string before popping up
        """
        polished = add_start_end(polished)
        top_split = polished.split("\n")

        try:
            result = "\n".join(top_split)
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

        self.result = "\n".join(final)+"\n"

    def polish(self):
        """
        Editor wrapper to confirm result
        """
        docstring = self.result.split("\n")
        polished = "\n".join([docline for docline in docstring])
        if self.placeholders:
            self.result = polished
        else:
            self.confirm(polished)
