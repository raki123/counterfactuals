#!/mnt/vg01/lv01/home/rkiesel/miniconda3/bin/python
import time
import sys
import csv
from counterfactual.counterfactualprogram import CounterfactualProgram

import logging
from aspmc.main import logger as aspmc_logger

logger = logging.getLogger("CFInfer")
logging.basicConfig(format='[%(levelname)s] %(name)s: %(message)s', level="INFO")
logger.setLevel(logging.DEBUG)
aspmc_logger.setLevel(logging.DEBUG)

from aspmc.config import config
config["decot"] = '10'

base_path = '/mnt/vg01/lv01/home/rkiesel/benchmark-tool/cf_transit/'
base_path = '/home/rafael/projects/counterfactuals/benchmarks/'
strategy = "sharpsat-td"
# parse the arguments
while len(sys.argv) > 1:
    if sys.argv[1].startswith("-"):
        if sys.argv[1] == "-k" or sys.argv[1] == "--knowledge_compiler":
            strategy = sys.argv[2]
            if sys.argv[2] != "c2d" and sys.argv[2] != "miniC2D" and sys.argv[2] != "sharpsat-td" and sys.argv[2] != "d4" and sys.argv[2] != "pysdd":
                logger.error("  Unknown knowledge compiler: " + sys.argv[2])
                exit(-1)
            del sys.argv[1:3]
    else:
        line_nr = int(sys.argv[1].split("/")[-1])
        del sys.argv[1]
with open(f'{base_path}/ei_queries.csv', 'r') as query_file:
    # reading the CSV file
    csvFile = csv.reader(query_file)

    # displaying the contents of the CSV file
    lines = list(csvFile)[1:]
    line = lines[line_nr]
    file = f"ei_instances/{line[0]}"
    program = CounterfactualProgram("", [file])
    query = line[1]
    if len(line[2]) > 0:
        evidence = { name if not name.startswith("\\+") else name[2:] : name.startswith("\\+") for name in line[2].split(";") }
    else:
        evidence = {}
    if len(line[3]) > 0:
        intervention = { name if not name.startswith("\\+") else name[2:] : name.startswith("\\+") for name in line[3].split(";") }
    else:
        intervention = {}
    logger.info(f"  Processing file {file} with query {query}, evidence {evidence}, and intervention {intervention}.")
    start = time.time()
    result = program.single_query(intervention, evidence, [query], strategy=strategy)
    end = time.time()
    logger.info(f"  Execution time: {end - start}")
    # print the results
    logger.info("   Results")
    logger.info("------------------------------------------------------------")

    logger.result(f"{query}: {' '*max(1,(20 - len(query)))}{result[0]}")