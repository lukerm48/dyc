"""
Entry point to DYC Class

DYC (Document Your Code) Class initiator
is constructed here. It performs all the readings

"""
import click
from .utils import get_extension
from .methods.MethodBuilder import MethodBuilder
from .classes.ClassBuilder import ClassBuilder
from .top.TopBuilder import TopBuilder
from .base import Processor

class DYC(Processor):
    def __init__(self, config, details=None, placeholders=False):
        self.config = config
        self.placeholders = placeholders
        
    def document(self):
       print("\nStarting Documentation \n\r")
       for filename in self.file_list:
            add_file = click.confirm(
                    "Do you want to document file {}?".format(
                        click.style(filename, fg="green")))
            if (add_file):
               self.process_top(filename)
               self.process_classes(filename)
               self.process_methods(filename)
		         

    def process_methods(self, filename, diff_only=False, changes=[]):
        """
        Main method that documents methods in a file. To any
        file that needs to be documented. Process methods is the
        entry point for getting the whole thing done
        Parameters
        ----------
        bool diff_only: Use a diff only. Consumed by dyc diff.
        list changes: Changes in a file, mainly use also with dyc diff.
        """
        print("\nProcessing Methods for filename " + filename + "\n\r")

        try:
            change = list(filter(lambda x: x.get("path") == filename, changes))[0]
        except TypeError as e:
            click.echo(
                click.style("Error %r: USING default settings for methods" % e, fg="red")
            )
            return
        except IndexError:
            change = None

        extension = get_extension(filename)
        fmt = self.formats.get(extension)
        method_cnf = fmt.get("method", {})
        method_cnf["arguments"] = fmt.get("arguments")
        builder = MethodBuilder(
            filename, method_cnf, placeholders=self.placeholders
        )
        builder.initialize(change=change)
        builder.prompts()
        builder.apply()
        builder.clear(filename)

    def process_classes(self, filename, diff_only=False, changes=[]):
        """
        Main method that documents Classes in a file.
        """
        print("\nProcessing Classes for filename " + filename + "\n\r")

        try:
            change = list(filter(lambda x: x.get("path") == filename, changes))[0]
        except TypeError as e:
            click.echo(
                click.style("Error %r: USING default settings for classes" % e, fg="red")
            )
            return
        except IndexError:
            change = None

        extension = get_extension(filename)
        fmt = self.formats.get(extension)
        class_cnf = fmt.get("class", {})
        builder = ClassBuilder(
            filename, class_cnf, placeholders=self.placeholders
        )
        builder.initialize(change=change)
        builder.prompts()
        builder.apply()
        builder.clear(filename)

    def process_top(self, filename, diff_only=False, changes=[]):
        """
        Main method that documents a top of a file. Still
        """
        print("\nProcessing Top of File for filename " + filename + "\n\r")
        try:
            change = list(filter(lambda x: x.get("path") == filename, changes))[0]
        except TypeError as e:
            click.echo(
                click.style("Error %r: USING default settings for top" % e, fg="red")
            )
            return
        except IndexError:
            change = None

        extension = get_extension(filename)
        fmt = self.formats.get(extension)
        top_cnf = fmt.get("top", {})
        builder = TopBuilder(
            filename, top_cnf, placeholders=self.placeholders
        )
        builder.initialize(change=change)
        builder.prompts()
        builder.apply()
        builder.clear(filename)
