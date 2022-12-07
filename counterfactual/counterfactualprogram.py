from aspmc.programs.problogprogram import ProblogProgram

"""
Program module providing the algebraic progam class.
"""

import logging

from aspmc.programs.program import Rule


from aspmc.config import config
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
                if idx == -1:
                    idx = len(cur_name)
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
            if idx == -1:
                idx = len(original_name)
            new_name = original_name[:idx]
            new_name += "_i"
            new_name += original_name[idx:]
            self._nameMap[atom] = new_name

        # make sure there is always an atom true that is true
        self.true = self._new_var("true")
        self._deriv.add(self.true)

        self._program = new_program


    def single_query(self, interventions, evidence, queries, strategy="sharpsat-td"):
        """Evaluates a single counterfactual query using the given strategy.

        Args:
            interventions (dict): A dictionary mapping names to phases, 
                indicating that the atom with name `name` should be intervened positively (phase == False) or negatively.
            evidence (dict): A dictionary mapping names to phases, 
                indicating that the atom with name `name` must have been true (phase == False) or false.
            queries (list): A list of strings, indicating that we want to query the probabilities of the atoms
                under the given interventions and evidence.
            strategy (:obj:`string`, optional): The knowledge compiler to use. Possible values are 
                * `pysdd` for bottom up compilation to SDDs,
                * `c2d` for top down compilation to sd-DNNF with c2d,
                * `miniC2D` for top down compilation to sd-DNNF with miniC2D,
                * `d4` for top down compilation to sd-DNNF with d4,
                * `sharpsat-td` for top down compilation to sd-DNNF with sharpsat-td.
                Defaults to `sharpsat-td`.
        Returns:
            list: A list containing the results of the counterfactual queries in the order they were given in `queries`.
        """
        tmp_program = [ Rule([self.true],[]) ]
        atom_interventions = { self.intervention_atoms[name] : phase for name, phase in interventions.items() }
        for rule in self._program:
            if len(rule.head) > 0:
                if rule.head[0] in atom_interventions:
                    continue
            take = True
            new_body = []
            for atom in rule.body:
                if not abs(atom) in atom_interventions:
                    new_body.append(atom)
                else:
                    if atom_interventions[abs(atom)] != (atom < 0):
                        take = False
                        break
            if take:
                tmp_program.append(Rule(rule.head, new_body))

        for name, phase in interventions.items():
            if not phase:
                atom = self.intervention_atoms[name]
                tmp_program.append(Rule([ atom ], []))

        for name, phase in evidence.items():
            atom = self.evidence_atoms[name]
            if phase:
                body = [ atom ]
            else:
                body = [ -atom ]
            tmp_program.append(Rule([],body))

        self.queries = [ "true" ]
        self.queries += [ self._external_name(self.intervention_atoms[name]) for name in queries ]
        program_string = self._prog_string(tmp_program)
        inference_program = ProblogProgram(program_string, [])
        
        # evaluate the query using the given strategy
        if strategy in ['c2d', 'miniC2D', 'd4', 'sharpsat-td']:
            # perform CNF conversion, followed by top down knowledge compilation
            inference_program.tpUnfold()
            inference_program.td_guided_both_clark_completion(adaptive = False, latest = True)
            cnf = inference_program.get_cnf()
            result = cnf.evaluate()
            # reorder the query results
            other_queries = inference_program.get_queries()
            to_idx = { query : idx for idx, query in enumerate(other_queries) }
            sorted_result = [ ]
            for query in self.queries:
                sorted_result.append(result[to_idx[query]])
            if sorted_result[0] <= 0.0:
                raise Exception("Contradictory evidence! Probablity given evidence is zero.")
            final_results = [ value/sorted_result[0] for value in sorted_result[1:] ] 
        elif strategy == 'pysdd':
            # perform bottom up compilation using pysdd
            pass
        self.queries = []
        return final_results





