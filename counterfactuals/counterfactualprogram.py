from aspmc.programs.problogprogram import ProblogProgram

"""
Program module providing the algebraic progam class.
"""

import logging


import tempfile
import os 

import networkx as nx

import numpy as np
from ctypes import *
from array import array

from aspmc.programs.program import Rule

import aspmc.graph.treedecomposition as treedecomposition
from aspmc.compile.vtree import TD_to_vtree, TD_vtree
from aspmc.compile.dtree import TD_dtree
from pysdd.sdd import SddManager, Vtree, WmcManager
from aspmc.compile.cnf import CNF
from aspmc.compile.circuit import Circuit

from aspmc.config import config
from aspmc.util import *
from aspmc.programs.naming import *


import aspmc.signal_handling as my_signals

logger = logging.getLogger("WhatIf")

class SDDOperation(object):
    AND = 0
    OR = 1
    NEGATE = 2

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
            logger.warning("Queries should not be included in the program specification. I will ignore them.")
            self.queries = []
        
        # attributes for the bottom up multi-query case
        self._sdd_manager = None
        self._topological_ordering = None
        self._applyCache = {}
        # attributes for the top down multi-query case
        self._nnf = None
        self._intervention_conditioners = {}
        self._vtree = None

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
        new_program.append(Rule([self.true],[]))

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
        tmp_program = [ ]
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

        
        # evaluate the query using the given strategy
        if strategy in ['c2d', 'miniC2D', 'd4', 'sharpsat-td']:
            # reduce the program to the relevant part
            # set up the and/or graph
            graph = nx.DiGraph()
            graph.add_nodes_from(i + 1 for i in range(self._max))
            for r in tmp_program:
                for atom in r.head:
                    graph.add_edge(r, atom)
                for atom in r.body:
                    graph.add_edge(abs(atom), r)
                    
            # reduce to relevant part by using only the ancestors of evidence and or queries
            relevant = set()
            for query in queries:
                relevant.add(self.intervention_atoms[query])
                relevant.update(nx.ancestors(graph, self.intervention_atoms[query]))
            for atom in evidence:
                relevant.add(self.evidence_atoms[atom])
                relevant.update(nx.ancestors(graph, self.evidence_atoms[atom]))

            tmp_program = [ r for r in tmp_program if r in relevant ]
            tmp_program.append(Rule([self.true], []))

            # finalize the program with the evidence and the queries
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
            # create a new probabilistic program for inference
            inference_program = ProblogProgram(program_string, [])
            # perform CNF conversion, followed by top down knowledge compilation
            inference_program.td_guided_both_clark_completion(adaptive = False, latest = True)
            cnf = inference_program.get_cnf()
            result = cnf.evaluate(strategy = "compilation")
            # reorder the query results
            other_queries = inference_program.get_queries()
            to_idx = { query : idx for idx, query in enumerate(other_queries) }
            sorted_result = [ ]
            for query in self.queries:
                if query in to_idx:
                    sorted_result.append(result[to_idx[query]])
                else:
                    sorted_result.append(0.0)
            if sorted_result[0] <= 0.0:
                raise Exception("Contradictory evidence! Probablity given evidence is zero.")
            final_results = [ value/sorted_result[0] for value in sorted_result[1:] ] 
        elif strategy == 'pysdd':
            # perform bottom up compilation using pysdd
            # set up the sdd manager
            sdd = self.setup_sdd_manager(tmp_program)
            vars = list(sdd.vars)
            guesses = list(self._guess)
            vertex_to_sdd = { v : vars[i] for i,v in enumerate(guesses) }

            # set up the and/or graph
            graph = nx.DiGraph()
            graph.add_nodes_from(i + 1 for i in range(self._max))
            for r in tmp_program:
                for atom in r.head:
                    graph.add_edge(r, atom)
                for atom in r.body:
                    graph.add_edge(abs(atom), r)

            # reduce to relevant part by using only the ancestors of evidence and or queries
            relevant = set()
            for query in queries:
                relevant.add(self.intervention_atoms[query])
                relevant.update(nx.ancestors(graph, self.intervention_atoms[query]))
            for atom in evidence:
                relevant.add(self.evidence_atoms[atom])
                relevant.update(nx.ancestors(graph, self.evidence_atoms[atom]))

            # build the relevant sdds by traversing the graph in topological order
            ts = nx.topological_sort(graph)
            for cur in ts:
                if isinstance(cur, Rule):
                    new_sdd = sdd.true()
                    for b in cur.body:
                        if b < 0:
                            vertex_to_sdd[b] = ~vertex_to_sdd[-b]
                        new_sdd = new_sdd & vertex_to_sdd[b]
                    vertex_to_sdd[cur] = new_sdd
                elif cur not in self._guess:
                    ins = list(graph.in_edges(nbunch=cur))
                    new_sdd = sdd.false()
                    for r in ins:
                        new_sdd = new_sdd | vertex_to_sdd[r[0]]
                    vertex_to_sdd[cur] = new_sdd
            
            # conjoin all the evidence atoms
            conjoined_evidence = sdd.true()
            for name, phase in evidence.items():
                if phase:
                    conjoined_evidence = conjoined_evidence & ~vertex_to_sdd[self.evidence_atoms[name]]
                else:
                    conjoined_evidence = conjoined_evidence & vertex_to_sdd[self.evidence_atoms[name]]

            # get all the query sdds and conjoin them with the evidence
            query_sdds = [ vertex_to_sdd[self.intervention_atoms[query]] for query in queries ]
            query_sdds = [ query_sdd & conjoined_evidence for query_sdd in query_sdds ]

            # compute the actual probabilities
            # first the probability of the evidence
            evidence_manager = WmcManager(conjoined_evidence, log_mode = False)
            weights = [ 1.0 for _ in range(2*len(self._guess)) ]
            varMap = { name : var for var, name in self._nameMap.items() }
            rev_mapping = { guesses[i] : i + 1 for i in range(len(self._guess)) }
            for name in self.weights:
                sdd_var = rev_mapping[varMap[name]]
                weights[len(self._guess) + sdd_var - 1] = self.weights[name]
                weights[len(self._guess) - sdd_var] = 1 - self.weights[name]
            python_array = np.array(weights)
            c_weights = array('d', python_array.astype('float'))
            evidence_manager.set_literal_weights_from_array(c_weights)
            evidence_weight = evidence_manager.propagate()
            if evidence_weight <= 0.0:
                raise Exception("Contradictory evidence! Probablity given evidence is zero.")
            
            # then the probabilities of the queries given the evidence
            final_results = []
            for query_sdd in query_sdds:
                query_manager = WmcManager(query_sdd, log_mode = False)
                query_manager.set_literal_weights_from_array(c_weights)
                query_weight = query_manager.propagate()
                final_results.append(query_weight/evidence_weight)

        self.queries = []
        return final_results

    def _setup_multiquery_bottom_up(self):
        graph = nx.DiGraph()
        for r in self._program:
            for atom in r.head:
                graph.add_edge(r, atom)
            for atom in r.body:
                graph.add_edge(abs(atom), r)
        
        self._topological_ordering = list(nx.topological_sort(graph))
        self._sdd_manager = self.setup_sdd_manager(self._program)

    def _setup_multiquery_top_down(self, strategy = "sharpsat-td"):
        # create the atoms to condition on for interventions
        for original_name, atom in self.intervention_atoms.items():
            pos_var = self._new_var(f"do({original_name})")
            neg_var = self._new_var(f"dont({original_name})")
            self._intervention_conditioners[atom] = (pos_var, neg_var)
            self._guess.add(pos_var)
            self._guess.add(neg_var)
            self.weights[f"do({original_name})"] = 0.0
            self.weights[f"dont({original_name})"] = 0.0

        # change the rules
        interventions = set(self.intervention_atoms.values())
        
        for rule in self._program:
            if len(rule.head) > 0:
                if rule.head[0] in interventions:
                    rule.body.append(-self._intervention_conditioners[rule.head[0]][1])
        
        # TODO: see what happens if we put this be for the other rule changes
        for atom in interventions:
            self._program.append(Rule([ atom ], [ self._intervention_conditioners[atom][0] ]))

        self.td_guided_both_clark_completion(adaptive=False, latest=True)
        cnf_fd, cnf_tmp = tempfile.mkstemp()
        my_signals.tempfiles.add(cnf_tmp)
        
        # prepare everything for the compilation
        if strategy == "c2d":
            with os.fdopen(cnf_fd, 'wb') as cnf_file:
                self._cnf.to_stream(cnf_file)
            d3 = TD_dtree(self._cnf, solver = config["decos"], timeout = config["decot"])
            d3.write(cnf_tmp + '.dtree')
            my_signals.tempfiles.add(cnf_tmp + '.dtree')
        elif strategy == "miniC2D":            
            with os.fdopen(cnf_fd, 'wb') as cnf_file:
                self._cnf.to_stream(cnf_file)
            self._vtree = TD_vtree(self._cnf, solver = config["decos"], timeout = config["decot"])
            self._vtree.write(cnf_tmp + ".vtree")
            my_signals.tempfiles.add(cnf_tmp + '.vtree')
        elif strategy == "sharpsat-td":
            with os.fdopen(cnf_fd, 'wb') as cnf_file:
                self._cnf.write_kc_cnf(cnf_file)
        elif strategy == "d4":
            with os.fdopen(cnf_fd, 'wb') as cnf_file:
                self._cnf.to_stream(cnf_file)
                
        # perform the actual compilation
        CNF.compile_single(cnf_tmp, knowledge_compiler = strategy)
        
        # remove the temporary files
        os.remove(cnf_tmp)
        my_signals.tempfiles.remove(cnf_tmp)
        self._nnf = cnf_tmp + ".nnf"
        if strategy == "c2d":
            os.remove(cnf_tmp + ".dtree")
            my_signals.tempfiles.remove(cnf_tmp + '.dtree')
        elif strategy == "miniC2D":
            os.remove(cnf_tmp + ".vtree")
            my_signals.tempfiles.remove(cnf_tmp + '.vtree')
        
    def _cached_apply(self, node1, node2, operation):
        if not (node1, node2, operation) in self._applyCache:
            if operation == SDDOperation.AND:
                self._applyCache[(node1, node2, operation)] = node1 & node2
            elif operation == SDDOperation.OR:
                self._applyCache[(node1, node2, operation)] = node1 | node2
            elif operation == SDDOperation.NEGATE:
                assert(node2 is None)
                self._applyCache[(node1, node2, operation)] = ~node1
        return self._applyCache[(node1, node2, operation)]

    def multi_query(self, interventions, evidence, queries, strategy="sharpsat-td"):
        """Evaluates one of many single counterfactual queries using the given strategy.

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
        if strategy in ['c2d', 'miniC2D', 'd4', 'sharpsat-td']:
            return self._multi_query_top_down(interventions, evidence, queries, strategy=strategy)
        elif strategy == "pysdd":
            return self._multi_query_bottom_up(interventions, evidence, queries, strategy=strategy)
        else:
            raise Exception(f"Unknown compilation strategy {strategy}.")

    def _multi_query_top_down(self, interventions, evidence, queries, strategy="sharpsat-td"):
        """Evaluates one of many single counterfactual queries using the given strategy.

        Args:
            interventions (dict): A dictionary mapping names to phases, 
                indicating that the atom with name `name` should be intervened positively (phase == False) or negatively.
            evidence (dict): A dictionary mapping names to phases, 
                indicating that the atom with name `name` must have been true (phase == False) or false.
            queries (list): A list of strings, indicating that we want to query the probabilities of the atoms
                under the given interventions and evidence.
            strategy (:obj:`string`, optional): The knowledge compiler to use. Possible values are 
                * `c2d` for top down compilation to sd-DNNF with c2d,
                * `miniC2D` for top down compilation to sd-DNNF with miniC2D,
                * `d4` for top down compilation to sd-DNNF with d4,
                * `sharpsat-td` for top down compilation to sd-DNNF with sharpsat-td.
                Defaults to `sharpsat-td`.
        Returns:
            list: A list containing the results of the counterfactual queries in the order they were given in `queries`.
        """
        if self._nnf is None:
            self._setup_multiquery_top_down(strategy=strategy)

        # prepare the weights for this query
        actual_queries = [ "true" ] + [ self._external_name(self.intervention_atoms[query]) for query in queries ]
        query_cnt = len(actual_queries)
        varMap = { name : var for var, name in self._nameMap.items() }
        weight_list = [ np.full(query_cnt, self.semiring.one(), dtype=self.semiring.dtype) for _ in range(self._max*2) ]
        for name in self.weights:
            weight_list[to_pos(varMap[name])] = np.full(query_cnt, self.weights[name], dtype=self.semiring.dtype)
            weight_list[neg(to_pos(varMap[name]))] = np.full(query_cnt, self.semiring.negate(self.weights[name]), dtype=self.semiring.dtype)
        for i, query in enumerate(actual_queries):
            weight_list[neg(to_pos(varMap[query]))][i] = self.semiring.zero()
        
        for name, phase in interventions.items():
            intervention_atom = self.intervention_atoms[name]
            if phase:
                conditioner_atom = self._intervention_conditioners[intervention_atom][1]
            else:
                conditioner_atom = self._intervention_conditioners[intervention_atom][0]
            weight_list[to_pos(conditioner_atom)] = np.full(query_cnt, 1.0, dtype=self.semiring.dtype)
            weight_list[neg(to_pos(conditioner_atom))] = np.full(query_cnt, 0.0, dtype=self.semiring.dtype)

        for name, phase in evidence.items():
            evidence_atom = self.evidence_atoms[name]
            if phase:
                weight_list[to_pos(evidence_atom)] = np.full(query_cnt, 0.0, dtype=self.semiring.dtype)
            else:
                weight_list[neg(to_pos(evidence_atom))] = np.full(query_cnt, 0.0, dtype=self.semiring.dtype)

        for v in range(self._max*2):
            self._cnf.weights[to_dimacs(v)] = weight_list[v]
        self._cnf.semirings = [ self.semiring ]
        self._cnf.quantified = [ list(range(1, self._max + 1)) ]

        # perform the counting on the circuit
        weights, zero, one, dtype = self._cnf.get_weights()
        results = Circuit.parse_wmc(self._nnf, weights, zero = zero, one = one, dtype = dtype, solver = strategy, vtree = self._vtree)
        
        if results[0] <= 0.0:
            raise Exception("Contradictory evidence! Probablity given evidence is zero.")
        
        final_results = [ result/results[0] for result in results[1:] ]
        return final_results
        




    def _multi_query_bottom_up(self, interventions, evidence, queries, strategy="pysdd"):
        """Evaluates one of many single counterfactual queries using the given strategy.

        Args:
            interventions (dict): A dictionary mapping names to phases, 
                indicating that the atom with name `name` should be intervened positively (phase == False) or negatively.
            evidence (dict): A dictionary mapping names to phases, 
                indicating that the atom with name `name` must have been true (phase == False) or false.
            queries (list): A list of strings, indicating that we want to query the probabilities of the atoms
                under the given interventions and evidence.
            strategy (:obj:`string`, optional): The knowledge compiler to use. Possible values are 
                * `pysdd` for bottom up compilation to SDDs,
                Defaults to `pysdd`.
        Returns:
            list: A list containing the results of the counterfactual queries in the order they were given in `queries`.
        """
        # check if setup already happened, if not do it now
        if self._sdd_manager is None:
            self._setup_multiquery_bottom_up()

        # perform the interventions 
        # differently from the single query case we do not remove atoms that are intervened on
        # but only the rules that derive them
        # this is to enable the use of the same topological ordering for different queries
        # but should not decrease performance, since the intervened atoms are always either true or false
        tmp_program = [ ]
        atom_interventions = { self.intervention_atoms[name] : phase for name, phase in interventions.items() }
        for rule in self._program:
            if len(rule.head) > 0:
                if rule.head[0] in atom_interventions:
                    continue
            take = True
            for atom in rule.body:
                if abs(atom) in atom_interventions:
                    if atom_interventions[abs(atom)] != (atom < 0):
                        take = False
                        break
            if take:
                tmp_program.append(rule)

        # additional rules to ensure that atoms positively intervened upon are derived
        intervention_rules = []
        for name, phase in interventions.items():
            if not phase:
                atom = self.intervention_atoms[name]
                intervention_rule = Rule([ atom ], [])
                tmp_program.append(intervention_rule)
                intervention_rules.append(intervention_rule)

        # perform bottom up compilation using pysdd
        vars = list(self._sdd_manager.vars)
        guesses = list(self._guess)
        vertex_to_sdd = { v : vars[i] for i,v in enumerate(guesses) }

        # set up the and/or graph
        graph = nx.DiGraph()
        for r in tmp_program:
            for atom in r.head:
                graph.add_edge(r, atom)
            for atom in r.body:
                graph.add_edge(abs(atom), r)
        
        # reduce to relevant part by using only the ancestors of evidence and or queries
        relevant = set()
        for query in queries:
            relevant.add(self.intervention_atoms[query])
            relevant.update(nx.ancestors(graph, self.intervention_atoms[query]))
        for atom in evidence:
            relevant.add(self.evidence_atoms[atom])
            relevant.update(nx.ancestors(graph, self.evidence_atoms[atom]))

        graph = nx.subgraph(graph, relevant)

        # build the relevant sdds by traversing the graph in topological order
        # for better reuse we always take the same topological order 
        # however, we need to make sure that we only have things in there that are relevant
        # additionally, we now have new rules for the atoms that were intervened on
        ts = intervention_rules + [ v for v in self._topological_ordering if v in relevant ]
        for cur in ts:
            if isinstance(cur, Rule):
                new_sdd = self._sdd_manager.true()
                for b in cur.body:
                    if b < 0:
                        vertex_to_sdd[b] = self._cached_apply(vertex_to_sdd[-b], None, SDDOperation.NEGATE)
                    new_sdd = self._cached_apply(new_sdd, vertex_to_sdd[b], SDDOperation.AND)
                vertex_to_sdd[cur] = new_sdd
            elif cur not in self._guess:
                ins = list(graph.in_edges(nbunch=cur))
                new_sdd = self._sdd_manager.false()
                for r in ins:
                    new_sdd = self._cached_apply(new_sdd, vertex_to_sdd[r[0]], SDDOperation.OR)
                vertex_to_sdd[cur] = new_sdd
        
        # conjoin all the evidence atoms
        conjoined_evidence = self._sdd_manager.true()
        for name, phase in evidence.items():
            if phase:
                evidence_atom = self._cached_apply(vertex_to_sdd[self.evidence_atoms[name]], None, SDDOperation.NEGATE)
            else:
                evidence_atom = vertex_to_sdd[self.evidence_atoms[name]]
            conjoined_evidence = self._cached_apply(conjoined_evidence, evidence_atom, SDDOperation.AND)

        # get all the query sdds and conjoin them with the evidence
        query_sdds = [ vertex_to_sdd[self.intervention_atoms[query]] for query in queries ]
        query_sdds = [ self._cached_apply(query_sdd, conjoined_evidence, SDDOperation.AND) for query_sdd in query_sdds ]

        # compute the actual probabilities
        # first the probability of the evidence
        evidence_manager = WmcManager(conjoined_evidence, log_mode = False)
        weights = [ 1.0 for _ in range(2*len(self._guess)) ]
        varMap = { name : var for var, name in self._nameMap.items() }
        rev_mapping = { guesses[i] : i + 1 for i in range(len(self._guess)) }
        for name in self.weights:
            sdd_var = rev_mapping[varMap[name]]
            weights[len(self._guess) + sdd_var - 1] = self.weights[name]
            weights[len(self._guess) - sdd_var] = 1 - self.weights[name]
        python_array = np.array(weights)
        c_weights = array('d', python_array.astype('float'))
        evidence_manager.set_literal_weights_from_array(c_weights)
        evidence_weight = evidence_manager.propagate()
        if evidence_weight <= 0.0:
            raise Exception("Contradictory evidence! Probablity given evidence is zero.")
        
        # then the probabilities of the queries given the evidence
        final_results = []
        for query_sdd in query_sdds:
            query_manager = WmcManager(query_sdd, log_mode = False)
            query_manager.set_literal_weights_from_array(c_weights)
            query_weight = query_manager.propagate()
            final_results.append(query_weight/evidence_weight)

        return final_results

    def setup_sdd_manager(self, program):
        # first generate a vtree for the program that is probably good
        OR = 0
        AND = 1
        GUESS = 3
        INPUT = 4
        # approximate final width when using none strategy
        nodes = { a : (OR, set()) for a in self._deriv }

        cur_max = self._max
        for a in self._exactlyOneOf:
            cur_max += 1
            nodes[cur_max] = (GUESS, set(abs(v) for v in a))

        for atom in self._guess:
            nodes[atom] = (INPUT, set())

        for r in program:
            cur_max += 1
            nodes[cur_max] = (AND, set(abs(v) for v in r.body))
            if len(r.head) != 0:
                nodes[abs(r.head[0])][1].add(cur_max)

        # set up the and/or graph
        graph = nx.Graph()
        for a, inputs in nodes.items():
            graph.add_edges_from([ (a, v) for v in inputs[1] ])
            
        td = treedecomposition.from_graph(graph, solver = config["decos"], timeout = str(float(config["decot"])))
        td.remove(set(range(1, cur_max + 1)).difference(self._guess))
        my_vtree = TD_to_vtree(td)
        guesses = list(self._guess)
        rev_mapping = { guesses[i] : i + 1 for i in range(len(self._guess)) }
        for node in my_vtree:
            if node.val != None:
                assert(node.val in self._guess)
                node.val = rev_mapping[node.val]

        (_, vtree_tmp) = tempfile.mkstemp()
        my_vtree.write(vtree_tmp)
        vtree = Vtree(filename=vtree_tmp)
        os.remove(vtree_tmp)
        sdd = SddManager.from_vtree(vtree)
        
        return sdd



