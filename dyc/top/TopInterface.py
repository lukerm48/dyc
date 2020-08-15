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
        filename,
        config,
        placeholders,
    ):
        self.filename = filename
        self.top_docstring = ""
        self.config = config
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
            echo_name = click.style(self.filename, fg="green")
            self.top_docstring = click.prompt(
                "\n({}) Top docstring ".format(echo_name)
            )
        pass
