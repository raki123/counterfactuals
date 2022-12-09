
#!/usr/bin/env python3

"""
Main module providing the application logic.
"""

import sys
import logging

from counterfactual.counterfactualprogram import CounterfactualProgram

import aspmc.config as config

from aspmc.main import logger as aspmc_logger


logger = logging.getLogger("CFInfer")
logging.basicConfig(format='[%(levelname)s] %(name)s: %(message)s', level="INFO")
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

    results = program.single_query(interventions, evidence, queries, strategy=config.config["knowledge_compiler"])
    
    # print the results
    logger.info("   Results")
    logger.info("------------------------------------------------------------")

    if len(queries) > 0:
        for i,query in enumerate(queries):
            logger.result(f"{query}: {' '*max(1,(20 - len(query)))}{results[i]}")

if __name__ == "__main__":
    main()


    
