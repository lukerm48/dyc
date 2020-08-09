"""
File for classes that handles the file headers
the application. Here is the the place where the actual reading,
parsing and validation of the files happens.
"""
import click
from .TopFormatter import TopFormatter


class TopInterface(TopFormatter):
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
        self.top_docstring = ""
        self.config = config
        self.leading_space = leading_space
        self.placeholders = placeholders

    def prompt(self):
        """
        Wrapper method for prompts and calls for prompting
        file then formats them
        """
        self._prompt_docstring()
        self.format()

    def _prompt_docstring(self):
        """
        Simple prompt for a file's docstring
        """
        if self.placeholders:
            self.top_docstring = "<docstring>"
        else:
            echo_name = click.style(self.name, fg="green")
            self.top_docstring = click.prompt(
                "\n({}) Top docstring ".format(echo_name)
            )
        pass
