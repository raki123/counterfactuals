# WhatIf
A solver for counterfactual inference over probabilistic logic programs.

`WhatIf` based on the [aspmc](https://github.com/raki123/aspmc/) library for probabilistic logic programming inference.

Its main functionality is the translation of counterfactual queries to marginal queries. 

For usage on Linux you may install this software as a pip package via
```
pip install counterfactuals
```
Examples for command line usage are available below.

If you have any issues please contact us, or even better create an issue on GitHub.

For academic usage cite 

 * Kiesel, R., Rückschloß, K., & Weitkämper, F. (2023, July). "What if?" in Probabilistic Logic Programming. In Proceedings of the 39th International Conference on Logic Programming.

## Development setup
For developement clone via 
```
git clone git@github.com:raki123/counterfactuals.git
```

We require Python >= 3.6. 

All required modules are listed in `requirements.txt` and can be obtained by running
```
pip install -r requirements.txt
```

To use `WhatIf` as usual but have changes to the code available run
```
pip install -e .
```
in the root directory of this repository.

## Usage

The basic usage is

```
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
```

### Examples
When using the pip package replace `python main.py` by `WhatIf` to obtain the same result.
#### ASP example:
```
python main.py -q slippery -e sprinkler,True -i sprinkler,False -k sharpsat-td
0.5::u1.
0.7::u2.
0.1::u3.
0.6::u4.
szn_spr_sum :- u1.
sprinkler :- szn_spr_sum, u2.
rain :- szn_spr_sum, u3.
rain :- \+szn_spr_sum, u4.
wet :- rain.
wet :- sprinkler.
slippery :- wet.
```
Reads the sprinkler program from stdin and adds evidence `sprinkler` and intervention `\+sprinkler`.
The query is for `slippery`. 

This results in the output
```
[WARNING] aspmc: Query for atom true was proven true during grounding.
[WARNING] aspmc: Including it has a negative impact on performance.
[INFO] aspmc: Tree Decomposition #bags: 18 unfolded treewidth: 3 #vertices: 20
[INFO] aspmc: Preprocessing disabled
[INFO] aspmc:    Stats Compilation
[INFO] aspmc: ------------------------------------------------------------
[INFO] aspmc: Compilation time:         0.005887508392333984
[INFO] aspmc: Counting time:            0.0001952648162841797
[INFO] aspmc: ------------------------------------------------------------
[INFO] WhatIf:    Results
[INFO] WhatIf: ------------------------------------------------------------
[RESULT] WhatIf: slippery:             0.09999999999999999
```
telling us that the result of the counterfactual query for `slippery` is `0.1`. 

The first two lines are a warning from `aspmc` that tell us that the atom `true` that we included to compute the probability of the evidence may lead to decreased performance. However, we need to include it as its probability is not `1.0` in general. 

The following info lines tell us some stats about the program and the inference:
* it has a treewidth upper bound of 3
* aspmc's preprocessing is disabled
* knowledge compilation took ~0.006 seconds
* counting over the resulting circuit took ~0.0002 seconds

