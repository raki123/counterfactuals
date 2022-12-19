
import csv
import subprocess

base_args = [ "python", "/home/staff/rkiesel/projects/counterfactual/main.py" , "-dt", "-1" ]

with open('queries.csv', 'r') as query_file:
   
    # reading the CSV file
    csvFile = csv.reader(query_file)

    # displaying the contents of the CSV file
    lines = list(csvFile)[1:]
    for line in lines:
        file = f"instances/{line[0]}"
        query = line[1]
        if len(line[2]) > 0:
            evidence = [ (name,False) if not name.startswith("\\+") else (name[2:],True) for name in line[2].split(";") ]
        else:
            evidence = []
        if len(line[3]) > 0:
            intervention = [ (name,False) if not name.startswith("\\+") else (name[2:],True) for name in line[3].split(";") ]
        else:
            intervention = []
        args = base_args + [ "-q", query ]
        args += sum(([ "-e", f"{name},{phase}" ] for name, phase in evidence), [])
        args += sum(([ "-i", f"{name},{phase}" ] for name, phase in intervention), [])
        args += [ file ]
        print(args)
        p = subprocess.Popen(args)
        p.wait()
