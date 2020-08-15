"""
File for classes that handles the actual business logic of
the application. Here is the the place where the actual reading,
parsing and validation of the files happens.
"""
import click
from .MethodFormatter import MethodFormatter


class MethodInterface(MethodFormatter):
    def __init__(
        self,
        plain,
        name,
        start,
        end,
        indent,
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
        self.indent = indent
        self.filename = filename
        self.arguments = arguments
        self.method_docstring = ""
        self.arg_docstring = []
        self.ret_docstring = []
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
        #self._prompt_return()
        self.format()

    def _prompt_docstring(self):
        """
        Simple prompt for a method's docstring
        """
        if self.placeholders:
            self.method_docstring = "<docstring>"
        else:
            echo_name = click.style(self.name, fg="green")
            self.method_docstring = click.prompt(
                "\n({}) Method docstring ".format(echo_name)
            )

    def _prompt_args(self):
        """
        Wrapper for prompting arguments
        """

        def _echo_arg_style(argument):
            """
            Just a small wrapper for echoing args
            Parameters
            ----------
            str argument: argument name
            """
            return click.style("{}".format(argument), fg="red")

        for arg in self.arguments:
            doc_placeholder = "<arg docstring>"
            arg_doc = (
                click.prompt("\n({}) Argument docstring ".format(_echo_arg_style(arg)))
                if not self.placeholders
                else doc_placeholder
            )
            show_arg_type = self.config.get("arguments", {}).get("add_type", False)
            if show_arg_type:
                arg_placeholder = "<type>"
                arg_type = (
                    click.prompt("({}) Argument type ".format(_echo_arg_style(arg)))
                    if not self.placeholders
                    else arg_placeholder
                )
            self.arg_docstring.append(dict(type=arg_type, doc=arg_doc, name=arg))

    def _prompt_return(self):
        echo_name = click.style(self.name, fg="red")
        doc_placeholder = "<return docstring>"
        return_doc = (
            click.prompt("\n({}) Return docstring(hit enter to skip)".format(echo_name),default="")
            if not self.placeholders
            else doc_placeholder
        )
        if return_doc == "":
            return
        show_ret_type = self.config.get("returns", {}).get("add_type", False)
        if show_ret_type:
            ret_placeholder = "<type>"
            ret_type = (
                click.prompt("({}) Argument type ".format(echo_name))
                if not self.placeholders
                else arg_placeholder
            )

        self.ret_docstring = dict(type=ret_type, doc=ret_doc, name=arg)

        return

