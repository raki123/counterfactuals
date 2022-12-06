
#!/usr/bin/env python3

"""
Main module providing the application logic.
"""

import sys
import logging

from counterfactual.counterfactualprogram import CounterfactualProgram

from aspmc.compile.cnf import CNF

from aspmc.graph.treedecomposition import from_hypergraph

import aspmc.config as config

import aspmc.signal_handling

logger = logging.getLogger("CFInfer")
logging.basicConfig(format='[%(levelname)s] %(name)s: %(message)s', level="INFO")

def addLoggingLevel(levelName, levelNum, methodName=None):
    """
    Comprehensively adds a new logging level to the `logging` module and the
    currently configured logging class.

    `levelName` becomes an attribute of the `logging` module with the value
    `levelNum`. `methodName` becomes a convenience method for both `logging`
    itself and the class returned by `logging.getLoggerClass()` (usually just
    `logging.Logger`). If `methodName` is not specified, `levelName.lower()` is
    used.

    To avoid accidental clobberings of existing attributes, this method will
    raise an `AttributeError` if the level name is already an attribute of the
    `logging` module or if the method name is already present 

    Example
    -------
    >>> addLoggingLevel('TRACE', logging.DEBUG - 5)
    >>> logging.getLogger(__name__).setLevel("TRACE")
    >>> logging.getLogger(__name__).trace('that worked')
    >>> logging.trace('so did this')
    >>> logging.TRACE
    5

    """
    if not methodName:
        methodName = levelName.lower()

    if hasattr(logging, levelName):
       raise AttributeError('{} already defined in logging module'.format(levelName))
    if hasattr(logging, methodName):
       raise AttributeError('{} already defined in logging module'.format(methodName))
    if hasattr(logging.getLoggerClass(), methodName):
       raise AttributeError('{} already defined in logger class'.format(methodName))

    # This method was inspired by the answers to Stack Overflow post
    # http://stackoverflow.com/q/2183233/2988730, especially
    # http://stackoverflow.com/a/13638084/2988730
    def logForLevel(self, message, *args, **kwargs):
        if self.isEnabledFor(levelNum):
            self._log(levelNum, message, args, **kwargs)
    def logToRoot(message, *args, **kwargs):
        logging.log(levelNum, message, *args, **kwargs)

    logging.addLevelName(levelNum, levelName)
    setattr(logging, levelName, levelNum)
    setattr(logging.getLoggerClass(), methodName, logForLevel)
    setattr(logging, methodName, logToRoot)
    
addLoggingLevel("RESULT", logging.INFO + 5)
logger.setLevel(logging.INFO)

help_string = """
TODO
"""

def main():
    program_files = []
    program_str = ""

    # parse the arguments
    while len(sys.argv) > 1:
        if sys.argv[1].startswith("-"):
            logger.error("  Unknown option: " + sys.argv[1])
            logger.info(help_string)
            exit(-1)
        else:
            program_files.append(sys.argv[1])
            del sys.argv[1]

    # parse the input 
    if not program_files:
        program_str = sys.stdin.read()
   
    program = CounterfactualProgram(program_str, program_files)
    print(program._prog_string(program._program))


if __name__ == "__main__":
    main()


    
