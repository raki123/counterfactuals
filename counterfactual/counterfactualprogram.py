from aspmc.programs.problogprogram import ProblogProgram

"""
Program module providing the algebraic progam class.
"""

import numpy as np
import logging

from aspmc.programs.program import Rule



from aspmc.util import *
from aspmc.programs.naming import *

logger = logging.getLogger("CFInfer")

class CounterfactualProgram(ProblogProgram):
    """A class for probabilistic programs that enables counterfactual inference. 

    Should be specified in ProbLog syntax, but allows for stratification negation.

    Grounding of these programs (and subclasses thereof) should follow the following strategy:

    * `_prepare_grounding(self, program)` should take the output of the parser 
        (i.e. a list of rules and special objects) and process all the rules and special objects
        transforming them either into other rules or into strings that can be given to the grounder.
    * the output of `_prepare_grounding(self, program)` is transformed to one program string via

            '\\n'.join([ str(r) for r in program ])
        
        This string will be given to the grounder, which produces a clingo control object.
    * `_process_grounding(self, clingo_control)` should take this clingo control object and process the
        grounding in an appropriate way (and draw some information from it optionally about weights, special objects).
        The resulting processed clingo_control object must only know about the 
        rules that should be seen in the base program class.

    Thus, subclasses can override `_prepare_grounding` and `_process_grounding` (and optionally call the superclass methods) 
    to handle their extras. See aspmc.programs.meuprogram or aspmc.programs.smprogram for examples.

    Args:
        program_str (:obj:`string`): A string containing a part of the program in ProbLog syntax. 
        May be the empty string.
        program_files (:obj:`list`): A list of string that are paths to files which contain programs in 
        ProbLog syntax that should be included. May be an empty list.

    Attributes:
        weights (:obj:`dict`): The dictionary from atom names to their weight.
        queries (:obj:`list`): The list of atoms to be queries in their string representation.
    """
    def __init__(self, program_str, program_files):
        # initialize the superclass
        ProblogProgram.__init__(self, program_str, program_files)
        if len(self.queries) > 0:
            logger.warning("Queries should not be included in counterfactual programs. I will ignore them.")
            self.queries = []
        
        # duplicate the program such that we obtain an evidence part and a part for the intervention
        self.evidence_atoms = {}
        self.intervention_atoms = { self._external_name(var) : var for var in self._deriv }

        def to_external(atom, postfix):
            assert(atom in self._deriv)
            cur_name = self._external_name(atom)
            if cur_name not in self.evidence_atoms:
                idx = cur_name.find("(")
                new_name = cur_name[:idx]
                new_name += "_" + postfix
                new_name += cur_name[idx:]
                new_var = self._new_var(new_name) 
                self.evidence_atoms[cur_name] = new_var
                self._deriv.add(new_var)
            else:
                new_var = self.evidence_atoms[cur_name]
            return new_var

        new_program = []
        for rule in self._program:
            new_program.append(rule)
            new_head = []
            if len(rule.head) > 0:
                assert(len(rule.head) == 1)
                new_head = [ to_external(rule.head[0], "e") ]

            new_body = []
            for atom in rule.body:
                if abs(atom) in self._deriv:
                    # we only change derived atoms
                    if atom > 0:
                        new_body.append(to_external(atom, "e"))
                    else: 
                        new_body.append(-to_external(-atom, "e"))
                else:
                    # guessed atoms stay unchanged
                    new_body.append(atom)

            new_rule = Rule(new_head, new_body)
            new_program.append(new_rule)

        # now we can change the names of the intervention atoms
        for original_name, atom in self.intervention_atoms.items():
            idx = original_name.find("(")
            new_name = original_name[:idx]
            new_name += "_i"
            new_name += original_name[idx:]
            self._nameMap[atom] = new_name

        self._program = new_program


    def _prog_string(self, program):
        result = ""
        for v in self._guess:
            result += f"{self.weights[self._internal_name(v)]}::{self._external_name(v)}.\n"
        for r in program:
            result += ";".join([self._external_name(v) for v in r.head])
            if len(r.body) > 0:
                result += ":-"
                result += ",".join([("\\+ " if v < 0 else "") + self._external_name(abs(v)) for v in r.body])
            result += ".\n"
        return result

    def _finalize_cnf(self):
        weight_list = self.get_weights()
        for v in range(self._max*2):
            self._cnf.weights[to_dimacs(v)] = weight_list[v]
        self._cnf.semirings = [ self.semiring ]
        self._cnf.quantified = [ list(range(1, self._max + 1)) ]

    def get_weights(self):
        query_cnt = max(len(self.queries), 1)
        varMap = { name : var for var, name in self._nameMap.items() }
        weight_list = [ np.full(query_cnt, self.semiring.one(), dtype=self.semiring.dtype) for _ in range(self._max*2) ]
        for name in self.weights:
            weight_list[to_pos(varMap[name])] = np.full(query_cnt, self.weights[name], dtype=self.semiring.dtype)
            weight_list[neg(to_pos(varMap[name]))] = np.full(query_cnt, self.semiring.negate(self.weights[name]), dtype=self.semiring.dtype)
        for i, query in enumerate(self.queries):
            weight_list[neg(to_pos(varMap[query]))][i] = self.semiring.zero()
        return weight_list

    def get_queries(self):
        return self.queries