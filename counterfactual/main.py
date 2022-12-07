
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
    write_name = None
    evidence = {}
    interventions = {}
    queries = []

    # parse the arguments
    while len(sys.argv) > 1:
        if sys.argv[1].startswith("-"):
            if sys.argv[1] == "-w" or sys.argv[1] == "--write":
                write_name = sys.argv[2]
                del sys.argv[1:3]
            elif sys.argv[1] == "-v" or sys.argv[1] == "--verbosity":
                verbosity = sys.argv[2].upper()
                if verbosity != "DEBUG" and verbosity != "INFO" and verbosity != "RESULT" and verbosity != "WARNING" and verbosity != "ERROR":
                    logger.error("  Unknown verbosity: " + verbosity)
                    exit(-1)
                logger.setLevel(verbosity)
                del sys.argv[1:3]
            elif sys.argv[1] == "-ds" or sys.argv[1] == "--decos":
                if sys.argv[2] != "flow-cutter":
                    logger.error("  Unknown tree decomposer: " + sys.argv[2])
                    exit(-1)
                config.config["decos"] = sys.argv[2]
                del sys.argv[1:3]
            elif sys.argv[1] == "-dt" or sys.argv[1] == "--decot":
                config.config["decot"] = sys.argv[2]
                del sys.argv[1:3]            
            elif sys.argv[1] == "-k" or sys.argv[1] == "--knowledge_compiler":
                config.config["knowledge_compiler"] = sys.argv[2]
                if sys.argv[2] != "c2d" and sys.argv[2] != "miniC2D" and sys.argv[2] != "sharpsat-td" and sys.argv[2] != "d4" and sys.argv[2] != "pysdd":
                    logger.error("  Unknown knowledge compiler: " + sys.argv[2])
                    exit(-1)
                del sys.argv[1:3]
            elif sys.argv[1] == "-e" or sys.argv[1] == "--evidence":
                last_comma = sys.argv[2].rfind(",")
                if last_comma == -1:
                    logger.error(f" Invalid evidence string {sys.argv[2]}.\nExpected a string of the form `name,phase`, \
                        where name is the name of an atom and phase is either `True` or `False`")
                name = sys.argv[2][:last_comma]
                phase = sys.argv[2][last_comma + 1:]
                if phase != "True" and phase != "False":
                    logger.error(f" Invalid evidence string {sys.argv[2]}.\nExpected a string of the form `name,phase`, \
                        where name is the name of an atom and phase is either `True` or `False`")
                phase = True if phase == "True" else False
                if name in evidence:
                    logger.warning(f"   Double specification of evidence for atom {name}. Using the last specified phase {phase}.")
                evidence[name] = phase
                del sys.argv[1:3]
            elif sys.argv[1] == "-i" or sys.argv[1] == "--intervene":
                last_comma = sys.argv[2].rfind(",")
                if last_comma == -1:
                    logger.error(f" Invalid intervention string {sys.argv[2]}.\nExpected a string of the form `name,phase`, \
                        where name is the name of an atom and phase is either `True` or `False`")
                name = sys.argv[2][:last_comma]
                phase = sys.argv[2][last_comma + 1:]
                if phase != "True" and phase != "False":
                    logger.error(f" Invalid intervention string {sys.argv[2]}.\nExpected a string of the form `name,phase`, \
                        where name is the name of an atom and phase is either `True` or `False`")
                phase = True if phase == "True" else False
                if name in interventions:
                    logger.warning(f"   Double specification of intervention for atom {name}. Using the last specified phase {phase}.")
                interventions[name] = phase
                del sys.argv[1:3]
            elif sys.argv[1] == "-q" or sys.argv[1] == "--query":
                query = sys.argv[2]
                queries.append(query)
                del sys.argv[1:3]
            elif sys.argv[1] == "-h" or sys.argv[1] == "--help":
                logger.info(help_string)
                exit(0)
            else:
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

    result = program.single_query(interventions, evidence, queries, strategy=config.config["knowledge_compiler"])
    print(result)
    result = program.multi_query(interventions, evidence, queries, strategy=config.config["knowledge_compiler"])
    print(result)
if __name__ == "__main__":
    main()


    
