from utils import (
    BlankFormatter,
    add_start_end,
    convert_indent,
)
import copy
import sys
import click


class ClassFormatter:
    formatted_string = "{doc_open}\n{break_after_open}{class_docstring}{break_after_docstring}{empty_line}{break_before_close}\n{doc_close}"
    fmt = BlankFormatter()

    def format(self):
        """
        Public formatting method that executes a pattern of classs to
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
        will be used in a formatted way,. Also translates configs
        into consumable values
        """
        class_format = copy.deepcopy(self.config)
        class_format["indent"] = (
            convert_indent(class_format["indent"]) if class_format["indent"] else "    "
        )
        class_format["indent_content"] = (
            convert_indent(class_format["indent"])
            if class_format["indent_content"]
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

    def build_docstrings(self):
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


