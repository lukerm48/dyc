from ..base import Builder
import re
from .ClassInterface import ClassInterface
from ..utils import (
    get_leading_whitespace,
    count_lines,
    get_indent,
)
import click
import os
import sys

class ClassBuilder(Builder):
    already_printed_filepaths = []  # list of already printed files

    def initialize(self, change=None):
        result = dict()

        patches = []
        if change:
            patches = change.get("additions")

        with open(self.filename, 'r') as file:
            file_lines = file.read()
            class_support_regex = self.config.get("regex")
            class_indicator = self.config.get("class_indicator")
            class_end_name = self.config.get("class_end_name")
            class_end = self.config.get("class_end")
            doc_open = self.config.get("doc_open")
            doc_close = self.config.get("doc_close")
            before_class = self.config.get("before_class")
            if not class_support_regex:
                class_indicator = re.escape(class_indicator)
                #doc_open = re.escape(doc_open)
                #doc_close = re.escape(doc_close)
                class_end_name = re.escape(class_end_name)
                class_end = re.escape(class_end)
            pattern = "("+class_indicator+")"+"\s+"+"(\S*)"+"\s*("+class_end_name+"(.*?))?("+class_end+")"
            if before_class:
                pattern = "(" + doc_close + ")?\s*" + pattern
            else:
                pattern = pattern + "\s*(" + doc_open + ")?"
            regex = re.compile(pattern,flags=re.DOTALL)
            match_iter = regex.finditer(file_lines)
            match_list = []
            #only add classes that don't have documentatino before or after them
            for i in match_iter:
                if (before_class and i.groups()[0] is None) or (not before_class and i.groups()[len(i.groups())-1] is None):
                    match_list.append(i)
            #NOTE: handling of self.config.get('comments') was taken out. Doesn't seem real useful
            found = (len(match_list) > 0)
            for i in match_list:
                start = 0
                end = 0
                class_name = ""

                if before_class:
                    class_name = i.groups()[2]
                    start = i.start(2)
                    end = i.end(5)
                    if end == -1: #no inheritance
                        end = i.end(3)
                else:
                    class_name = i.groups()[1]
                    start = i.start(1)
                    end = i.end(4)
                    if end == -1: #no inheritance
                        end = i.end(2)

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
                    result = ClassInterface(
                            plain=all_string,
                            name=class_name,
                            start=start,
                            end=end,
                            indent=get_indent(file_lines,start-1),
                            filename=self.filename,
                            config=self.config,
                            leading_space=get_leading_whitespace(all_string),
                            placeholders=self.placeholders,
                        )

                    if self.validate(result):
                        self.details[self.filename][result.name] = result

    def validate(self, result):
        """
        An abstract validator method that checks if the class is
        still valid and gives the final decision
        Parameters
        ----------
        ClassInterface result: The Class Interface result
        """
        if not result:
            return False
        name = result.name
        if name not in self.config.get("ignore", []):
            if self.filename not in self.already_printed_filepaths:  
                # Print file of class to document
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

    def prompts(self):
        """
        Abstract prompt method in builder to execute prompts over candidates
        """
        for class_interface in self._class_interface_gen():
            class_interface.prompt() if class_interface else None

    def apply(self):
        """
        Over here we are looping over the result of the
        chosen classs to document and applying the changes to the
        files as confirmed
        """
        #reverse list to edit file from bottom to top
        for class_interface in self._class_interface_gen(reverse=True):
            if not class_interface:
                continue
            with open(class_interface.filename, 'r+') as file_handle:
                file_text = file_handle.read()
                file_handle.seek(0)
                if self.config.get("before_class"):
                    #write before new line
                    new_line_index = file_text[0:class_interface.start].rfind("\n")
                    #are we at top of file?
                    if new_line_index == -1:
                        new_line_index = class_interface.start-1
                    file_handle.write(file_text[0:new_line_index+1] + class_interface.result + file_text[new_line_index+1:])
    
                else:
                    #write after new line
                    new_line_index = file_text[class_interface.end:].find("\n")
                    add_line = ""
                    #are we at bottom of the file?
                    if new_line_index == -1:
                        add_line = "\n"
                        new_line_index = 0
                    file_handle.write(file_text[0:class_interface.end+new_line_index+1] + add_line + class_interface.result + file_text[class_interface.end+new_line_index+1:])

    def _class_interface_gen(self,reverse=False):
        """
        A generator that yields the class interfaces
        """
        if not self.details:
            yield None

        for filename, func_pack in self.details.items():
            if(reverse):
                for class_interface in reversed(func_pack.values()):
                    yield class_interface
            else:
                for class_interface in func_pack.values():
                    yield class_interface
 
