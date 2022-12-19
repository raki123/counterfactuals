import sys
import csv
import subprocess
from counterfactual.counterfactualprogram import CounterfactualProgram

import logging
from aspmc.main import logger as aspmc_logger

logger = logging.getLogger("CFInfer")
logging.basicConfig(format='[%(levelname)s] %(name)s: %(message)s', level="INFO")
logger.setLevel(logging.DEBUG)
aspmc_logger.setLevel(logging.DEBUG)

from aspmc.config import config
config["decot"] = '10'

with open('/mnt/vg01/lv01/home/rkiesel/benchmark-tool/cf_transit/hard_queries.csv', 'r') as query_file:
   
    # reading the CSV file
    csvFile = csv.reader(query_file)

    # displaying the contents of the CSV file
    lines = list(csvFile)[1:]
    line_nr = int(sys.argv[1])
    line = lines[line_nr]
    file = f"/mnt/vg01/lv01/home/rkiesel/benchmark-tool/cf_transit/hard_instances/{line[0]}"
    query = line[1]
    if len(line[2]) > 0:
        evidence = { name if not name.startswith("\\+") else name[2:] : name.startswith("\\+") for name in line[2].split(";") }
    else:
        evidence = {}
    if len(line[3]) > 0:
        intervention = { name if not name.startswith("\\+") else name[2:] : name.startswith("\\+") for name in line[3].split(";") }
    else:
        intervention = {}

    program = CounterfactualProgram("", [file])
    result = program.single_query(intervention, evidence, [query], strategy="sharpsat-td")
    # print the results
    logger.info("   Results")
    logger.info("------------------------------------------------------------")

    logger.result(f"{query}: {' '*max(1,(20 - len(query)))}{result[0]}")
