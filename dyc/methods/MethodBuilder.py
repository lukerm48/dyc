"""
File for classes that handles the actual business logic of
the application. Here is the the place where the actual reading,
parsing and validation of the files happens.
"""
import re
import click
from .MethodInterface import MethodInterface
from ..utils import (
    get_leading_whitespace,
    get_indent_forward,
    get_indent_backward,
    count_lines,
)
from ..base import Builder
import os


class MethodBuilder(Builder):
    already_printed_filepaths = []  # list of already printed files

    def initialize(self, change=None):

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
            within_scope = self.config.get("within_scope")
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
            if not within_scope:
                pattern = "(" + doc_close + ")?\s*" + pattern
            else:
                pattern = pattern + "\s*(" + doc_open + ")?"
            regex = re.compile(pattern,flags=re.DOTALL)
            match_iter = regex.finditer(file_lines)
            match_list = []
            #only add methods that don't have documentatino before or after them
            for i in match_iter:
                if (not within_scope and i.groups()[0] is None) or (within_scope and i.groups()[len(i.groups())-1] is None):
                    match_list.append(i)
            #NOTE: handling of self.config.get('comments') was taken out. Doesn't seem real useful
            found = (len(match_list) > 0)
            for i in match_list:
                start = 0
                end = 0
                parameter_list = ""
                method_name = ""

                if not within_scope:
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
                    indent = ""
                    if(within_scope):
                        indent = get_indent_forward(file_lines,end+1)
                    else:
                        indent = get_indent_backward(file_lines,start-1)
                    result = MethodInterface(
                            plain=all_string,
                            name=method_name,
                            start=start,
                            end=end,
                            indent=indent,
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
                if not self.config.get("within_scope"):
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
        if len(self.args) > 0:
            return list(map(lambda arg: re.findall(r"[a-zA-Z0-9_]+", arg)[0], self.args))
        else:
            return []
