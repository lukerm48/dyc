"""
File for classes that handles the actual business logic of
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


class MethodFormatter:

    formatted_string = "{doc_open}\n{break_after_open}{method_docstring}{break_after_docstring}{empty_line}{argument_format}{break_before_close}\n{doc_close}"
    fmt = BlankFormatter()

    def format(self):
        """
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
        method_format = copy.deepcopy(self.config)
        method_format["indent"] = (
             convert_indent(method_format["indent"]) if method_format["indent"] else "    "
        )
        method_format["indent_content"] = (
            convert_indent(method_format["indent"])
            if method_format["indent_content"]
            else ""
        )
        method_format["break_after_open"] = (
            "\n" if method_format["break_after_open"] else ""
        )
        method_format["break_after_docstring"] = (
            "\n" if method_format["break_after_docstring"] else ""
        )
        method_format["break_before_close"] = (
            "\n" if method_format["break_before_close"] else ""
        )
        method_format["empty_line"] = "\n"

        argument_format = copy.deepcopy(self.config.get("arguments"))
        argument_format["inline"] = "" if argument_format["inline"] else "\n"

        self.method_format = method_format
        self.argument_format = argument_format

    def build_docstrings(self):
        """
        Mainly adds docstrings of the method after cleaning up text
        into reasonable chunks
        """
        text = self.method_docstring or "Missing Docstring!"
        self.method_format["method_docstring"] = self.wrap_strings(text.split(" "))

    def build_arguments(self):
        """
        Main function for wrapping up argument docstrings
        """
        if not self.arguments:
            self.method_format["argument_format"] = ""
            self.method_format["break_before_close"] = ""
            self.method_format["empty_line"] = ""
            return

        config = self.config.get("arguments")
        formatted_args = "{prefix} {type} {name}: {doc}"

        title = self.argument_format.get("title")
        if title:
            underline = "-" * len(title)
            self.argument_format["title"] = (
                "{}\n{}\n".format(title, underline)
                if config.get("underline")
                else "{}\n".format(title)
            )

        result = []

        if self.arguments:  # if len(self.arguments) > 0
            for argument_details in self.arg_docstring:
                argument_details["prefix"] = self.argument_format.get("prefix")
                result.append(
                    self.fmt.format(formatted_args, **argument_details).strip()
                )

        self.argument_format["body"] = "\n".join(result)
        self.method_format["argument_format"] = self.fmt.format(
            "{title}{body}", **self.argument_format
        )

    def add_indentation(self):
        """
        Translates indent params to actual indents
        """
        temp = self.result.split("\n")
        indent_content = self.method_format.get("indent_content")
        if indent_content:
            content = [indent_content + docline for docline in temp][1:-1]
            temp[1:-1] = content
        self.result = "\n".join([self.indent + docline for docline in temp])

    def confirm(self, polished):
        """
        Pop up editor function to finally confirm if the documented
        format is accepted
        Parameters
        ----------
        str polished: complete polished string before popping up
        """
        polished = add_start_end(polished)
        try:
            message = click.edit(
                "## CONFIRM: MODIFY DOCSTRING BETWEEN START AND END LINES ONLY\n\n"
                + polished
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
        polished = "\n".join([self.leading_space + docline for docline in docstring])
        if self.placeholders:
            self.result = polished
        else:
            self.confirm(polished)
