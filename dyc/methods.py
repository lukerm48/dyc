"""
File for classes that handles the actual business logic of
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
    convert_indent,
    add_start_end,
    is_one_line_method,
    count_lines,
)
from .base import Builder
import os


class MethodBuilder(Builder):
    already_printed_filepaths = []  # list of already printed files

    def initialize(self, change=None):
        result = dict()

        patches = []
        if change:
            patches = change.get("additions")

        with open(self.filename, 'r') as file:
            file_lines = file.read()
            method_support_regex = self.config.get("regex")
            argument_support_regex = self.config.get("arguments").get("regex")
            method_indicator = self.config.get("method_indicator")
            start_parameter = self.config.get("arguments").get("start_parameter")
            end_parameter = self.config.get("arguments").get("end_parameter")
            parameter_split = self.config.get("arguments").get("parameter_split")
            method_end = self.config.get("method_end")
            doc_open = self.config.get("doc_open")
            doc_close = self.config.get("doc_close")
            before_method = self.config.get("before_method")
            if not method_support_regex:
                method_indicator = re.escape(method_indicator)
                #doc_open = re.escape(doc_open)
                #doc_close = re.escape(doc_close)
                method_end = re.escape(method_end)
            if not argument_support_regex:
                start_parameter = re.escape(start_parameter)
                end_parameter = re.escape(end_parameter)
                parameter_split = re.escape(parameter_split)
            pattern = "("+method_indicator+")"+"\s+"+"(.*?)"+"\s*"+start_parameter+"(.*?)"+end_parameter+"\s*"+"("+method_end+")"
            if before_method:
                pattern = "(" + doc_close + ")?\s*" + pattern
            else:
                pattern = pattern + "\s*(" + doc_open + ")?"
            regex = re.compile(pattern,flags=re.DOTALL)
            match_iter = regex.finditer(file_lines)
            match_list = []
            #only add methods that don't have documentatino before or after them
            for i in match_iter:
                if (before_method and i.groups()[0] is None) or (not before_method and i.groups()[len(i.groups())-1] is None):
                    match_list.append(i)
            #NOTE: handling of self.config.get('comments') was taken out. Doesn't seem real useful
            found = (len(match_list) > 0)
            for i in match_list:
                start = 0
                end = 0
                parameter_list = ""
                method_name = ""

                if before_method:
                    method_name = i.groups()[2]
                    parameter_list = i.groups()[3].split(parameter_split)
                    start = i.start(2)
                    end = i.end(5)
                else:
                    method_name = i.groups()[1]
                    parameter_list = i.groups()[2].split(parameter_split)
                    start = i.start(1)
                    end = i.end(4)

                if change and found:
                    #get match from file
                    line = file_lines[start:end+1]
                    #index to start counting at 
                    lineno = count_lines(file_lines,start)
                    found = self._is_line_part_of_patches(lineno, line, patches)

                if not self.details.get(self.filename):
                    self.details[self.filename] = dict()

                if found:
                    all_string = file_lines[start:end+1] # entire match
                    result = MethodInterface(
                            plain=all_string,
                            name=method_name,
                            start=start,
                            end=end,
                            indent=get_indent(file_lines,start-1),
                            filename=self.filename,
                            arguments=self.extract_arguments(parameter_list),
                            config=self.config,
                            leading_space=get_leading_whitespace(all_string),
                            placeholders=self.placeholders,
                        )

                    if self.validate(result):
                        self.details[self.filename][result.name] = result

    def validate(self, result):
        """
        An abstract validator method that checks if the method is
        still valid and gives the final decision
        Parameters
        ----------
        MethodInterface result: The Method Interface result
        """
        if not result:
            return False
        name = result.name
        if name not in self.config.get("ignore", []):
            if self.filename not in self.already_printed_filepaths:  
                # Print file of method to document
                click.echo(
                    "\n\nIn file {} :\n".format(
                        click.style(
                            os.path.join(*self.filename.split(os.sep)[-3:]), fg="red"
                        )
                    )
                )
                self.already_printed_filepaths.append(self.filename)
            return True
        return False

    def extract_arguments(self, args_list):
        """
        Public extract argument method that calls ArgumentDetails
        class to extract args
        Parameters
        ----------
        """
        args = ArgumentDetails(args_list, self.config.get("arguments", {}))
        args.extract()
        return args.sanitize()

    def prompts(self):
        """
        Abstract prompt method in builder to execute prompts over candidates
        """
        for method_interface in self._method_interface_gen():
            method_interface.prompt() if method_interface else None

    def apply(self):
        """
        Over here we are looping over the result of the
        chosen methods to document and applying the changes to the
        files as confirmed
        """
        #reverse list to edit file from bottom to top
        for method_interface in self._method_interface_gen(reverse=True):
            if not method_interface:
                continue
            with open(method_interface.filename, 'r+') as file_handle:
                file_text = file_handle.read()
                file_handle.seek(0)
                if self.config.get("before_method"):
                    #write before new line
                    new_line_index = file_text[0:method_interface.start].rfind("\n")
                    #are we at top of file?
                    if new_line_index == -1:
                        new_line_index = method_interface.start-1
                    file_handle.write(file_text[0:new_line_index+1] + method_interface.result + file_text[new_line_index+1:])
                else:
                    #write after new line
                    new_line_index = file_text[method_interface.end:].find("\n")
                    add_line = ""
                    #are we at bottom of file?
                    if new_line_index == -1:
                        add_line = "\n"
                        new_line_index = 0
                    file_handle.write(file_text[0:method_interface.end+new_line_index+1] + add_line + method_interface.result + file_text[method_interface.end+new_line_index+1:])
    def _method_interface_gen(self,reverse=False):
        """
        A generator that yields the method interfaces
        """
        if not self.details:
            yield None

        for filename, func_pack in self.details.items():
            if(reverse):
                for method_interface in reversed(func_pack.values()):
                    yield method_interface
            else:
                for method_interface in func_pack.values():
                    yield method_interface

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
        space = self.method_format.get("indent")
        indent_content = self.method_format.get("indent_content")
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


class ArgumentDetails(object):
    def __init__(self, args_list, config):
        self.args_list = args_list
        self.config = config
        self.args = []

    def extract(self):
        """
        Retrieves arguments from a line
        """
        try:
            ignore = self.config.get("ignore")
            self.args = filter(
                lambda x: x not in ignore,
                filter(
                    None,
                    self.args_list
                )
            )
            self.args = list(self.args)
        except:
            pass

    def sanitize(self):
        """
        Sanitizes arguments to validate all arguments are correct
        """
        if( len(self.args) > 0):
            return list(map(lambda arg: re.findall(r"[a-zA-Z0-9_]+", arg)[0], self.args))
        else:
            return []
