from .ClassFormatter import ClassFormatter
import click

class ClassInterface(ClassFormatter):
    def __init__(
        self,
        plain,
        name,
        start,
        end,
        indent,
        filename,
        config,
        leading_space,
        placeholders,
    ):
        self.plain = plain
        self.name = name
        self.start = start
        self.end = end
        self.indent = indent
        self.filename = filename
        self.class_docstring = ""
        self.config = config
        self.leading_space = leading_space
        self.placeholders = placeholders

    def prompt(self):
        """
        Wrapper method for prompts and calls for prompting
        classs then formats them
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

