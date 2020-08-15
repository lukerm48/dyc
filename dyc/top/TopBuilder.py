"""
File for classes that handles the file headers
the application. Here is the the place where the actual reading,
parsing and validation of the files happens.
"""
from ..base import Builder
from .TopInterface import TopInterface
import re
import click
import os
class TopBuilder(Builder):
    already_printed_filepaths = []


    def initialize(self, change=None):
        
        if not self.config.get("enabled"):
            return
        patches = []
        if change:
            patches = change.get("additions")
        with open(self.filename, 'r') as file:
            file_lines = file.read()
            doc_open = self.config.get("doc_open")
            regex = re.compile("^(.*?)"+"("+re.escape(doc_open)+")",flags=re.DOTALL|re.MULTILINE)
            match_list = list(regex.finditer(file_lines))
            top_already_doced = False
            if len(match_list) > 0:
                top_already_doced = match_list[0].group(1).isspace() or match_list[0].group(1) == ""
            
            if not self.details.get(self.filename):
                self.details[self.filename] = dict()

            if not top_already_doced:
                result = TopInterface(
                        filename=self.filename,
                        config=self.config,
                        placeholders=self.placeholders,
                    )

                if self.validate(result):
                    self.details[self.filename] = result

    def validate(self, result):
        """
        An abstract validator method that checks if the file is
        still valid and gives the final decision
        Parameters
        ----------
        ClassInterface result: The Class Interface result
        """
        if not result:
            return False
        if self.filename not in self.already_printed_filepaths:  
            # Print file of file to document
            click.echo(
                "\n\nIn file {} :\n".format(
                    click.style(
                        os.path.join(*self.filename.split(os.sep)[-3:]), fg="red"
                    )
                )
            )
            self.already_printed_filepaths.append(self.filename)
        return True
 
    def prompts(self):
        """
        Abstract prompt method in builder to execute prompts over candidates
        """
        self.details[self.filename].prompt() if self.details[self.filename] else None

    def apply(self):
        """
        Over here we are looping over the result of the
        chosen top to document and applying the changes to the
        files as confirmed
        """
        if not self.details[self.filename]:
            return
        with open(self.filename, 'r+') as file_handle:
            file_text = file_handle.read()
            file_handle.seek(0)
            file_handle.write(self.details[self.filename].result + file_text)

 
