
#!/usr/bin/env python3

"""
Main module providing the application logic.
"""

import sys
import logging

from counterfactuals.counterfactualprogram import CounterfactualProgram

import aspmc.config as config

from aspmc.main import logger as aspmc_logger


logger = logging.getLogger("WhatIf")
logging.basicConfig(format='[%(levelname)s] %(name)s: %(message)s', level="INFO")
logger.setLevel(logging.INFO)

help_string = """
WhatIf: A solver for counterfactual inference.
WhatIf version 1.0.2, Feb 5, 2024

WhatIf [-e .] [-ds .] [-dt .] [-k .] [-v .] [-h] [<INPUT-FILES>]
    --knowlege          -k  COMPILER    set the knowledge compiler to COMPILER:
                                        * sharpsat-td       : uses a compilation version of sharpsat-td (default)
                                        * d4                : uses the (slightly modified) d4 compiler. 
                                        * c2d               : uses the c2d compiler. 
                                        * miniC2D           : uses the miniC2D compiler. 
                                        * pysdd             : uses the PySDD compiler. 
    --evidence          -e  NAME,VALUE  add evidence NAME:
                                        * the evidence is not negated if VALUE is `True`.
                                        * the evidence is negated if VALUE is `False`.
    --intervene         -i  NAME,VALUE  intervene on NAME:
                                        * the intervention is not negated if VALUE is `True`.
                                        * the intervention is negated if VALUE is `False`.
    --query             -q  NAME        query for the probability of NAME.
    --decos             -ds SOLVER      set the solver that computes tree decompositions to SOLVER:
                                        * flow-cutter       : uses flow_cutter_pace17 (default)
    --decot             -dt SECONDS     set the timeout for computing tree decompositions to SECONDS (default: 1)
    --verbosity         -v  VERBOSITY   set the logging level to VERBOSITY:
                                        * debug             : print everything
                                        * info              : print as usual
                                        * result            : only print results, warnings and errors
                                        * warning           : only print warnings and errors
                                        * errors            : only print errors
    --help              -h              print this help and exit
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
                aspmc_logger.setLevel(verbosity)
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
                    logger.error(f" Invalid evidence string {sys.argv[2]}.\nExpected a string of the form `name,value`, \
                        where name is the name of an atom and value is either `True` or `False`")
                name = sys.argv[2][:last_comma]
                value = sys.argv[2][last_comma + 1:]
                if value != "True" and value != "False":
                    logger.error(f" Invalid evidence string {sys.argv[2]}.\nExpected a string of the form `name,value`, \
                        where name is the name of an atom and value is either `True` or `False`")
                phase = False if value == "True" else True
                if name in evidence:
                    logger.warning(f"   Double specification of evidence for atom {name}. Using the last specified value {value}.")
                evidence[name] = phase
                del sys.argv[1:3]
            elif sys.argv[1] == "-i" or sys.argv[1] == "--intervene":
                last_comma = sys.argv[2].rfind(",")
                if last_comma == -1:
                    logger.error(f" Invalid intervention string {sys.argv[2]}.\nExpected a string of the form `name,value`, \
                        where name is the name of an atom and value is either `True` or `False`")
                name = sys.argv[2][:last_comma]
                value = sys.argv[2][last_comma + 1:]
                if value != "True" and value != "False":
                    logger.error(f" Invalid intervention string {sys.argv[2]}.\nExpected a string of the form `name,value`, \
                        where name is the name of an atom and value is either `True` or `False`")
                phase = False if value == "True" else True
                if name in interventions:
                    logger.warning(f"   Double specification of intervention for atom {name}. Using the last specified value {value}.")
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

    results = program.single_query(interventions, evidence, queries, strategy=config.config["knowledge_compiler"])
    
    # print the results
    logger.info("   Results")
    logger.info("------------------------------------------------------------")

    if len(queries) > 0:
        for i,query in enumerate(queries):
            logger.result(f"{query}: {' '*max(1,(20 - len(query)))}{results[i]}")

if __name__ == "__main__":
    main()


    
