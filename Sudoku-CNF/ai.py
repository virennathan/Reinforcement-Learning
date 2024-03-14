from __future__ import print_function
from game import sd_peers, sd_spots, sd_domain_num, init_domains, \
    restrict_domain, SD_DIM, SD_SIZE
import random, copy


class AI:
    def __init__(self):
        pass

    def solve(self, problem):
        domains = init_domains()
        restrict_domain(domains, problem)

        assignment = {k: v[0] for k, v in domains.items() if len(v) == 1}  # sigma assignment function
        ds = []  # decision stack

        while True:
            assignment, domains, conflict = self.propagate(assignment, domains)
            if not conflict:
                if len(assignment) == SD_SIZE ** 2:
                    for spot in sd_spots:
                        domains[spot] = [assignment[spot]]
                    return domains
                else:
                    assignment, domains, cell, val, old_assignment, old_domains = self.make_decision(assignment, domains)
                    ds.append((cell, val, old_assignment, old_domains))
            else:
                if not ds:
                    return None
                else:
                    assignment, domains, ds = self.backtrack(assignment, domains, ds)

    def propagate(self, assignment, domains):
        while True:
            terminate = True  # no more spots to propagate
            for spot in sd_spots:
                if spot not in assignment and len(domains[spot]) == 1:
                    assignment[spot] = domains[spot][0]
                    continue
                if spot in assignment and len(domains[spot]) > 1:
                    domains[spot] = [assignment[spot]]
                    continue
                if not domains[spot]:
                    return assignment, domains, True
                for peer in sd_peers[spot]:
                    if peer in assignment and assignment[peer] in domains[spot]:
                        domains[spot].remove(assignment[peer])
                        terminate = False
            if terminate:
                return assignment, domains, False

    def make_decision(self, assignment, domains):
        # Q: is there a heuristic for choosing the next spot?
        for spot in sd_spots:
            if spot not in assignment:
                old_assignment = copy.deepcopy(assignment)
                old_domains = copy.deepcopy(domains)
                val = domains[spot][0]
                assignment[spot] = val
                # Q: why can't we delete assignment from domain here?
                return assignment, domains, spot, val, old_assignment, old_domains

    def backtrack(self, assignment, domains, ds):
        cell, val, old_assignment, old_domains = ds.pop()
        assignment = old_assignment
        domains = old_domains
        domains[cell].remove(val)
        return assignment, domains, ds

    #### The following templates are only useful for the EC part #####

    # EC: parses "problem" into a SAT problem
    # of input form to the program 'picoSAT';
    # returns a string usable as input to picoSAT
    # (do not write to file)
    def sat_encode(self, problem):
        text = ""
        claues = 0

        # unit constraints for pre-assigned spots
        for x, y in sd_spots:
            c = problem[x*SD_SIZE+y] 
            if c != '.':
                text += "{}{}{} 0\n".format(x+1, y+1, int(c))
                claues += 1

        # at least one number in each cell
        for x in range(1, SD_SIZE+1):
            for y in range(1, SD_SIZE+1):
                for z in range(1, SD_SIZE+1):
                    text += "{}{}{} ".format(x, y, z)
                text += "0\n"
                claues += 1

        # each number appears at most once in each row
        for y in range(1, SD_SIZE+1):
            for z in range(1, SD_SIZE+1):
                for x in range(1, SD_SIZE):
                    for i in range(x+1, SD_SIZE+1):
                        text += "-{}{}{} -{}{}{} 0\n".format(x, y, z, i, y, z)
                        claues += 1
                    
        # each number appears at most once in each column
        for x in range(1, SD_SIZE+1):
            for z in range(1, SD_SIZE+1):
                for y in range(1, SD_SIZE):
                    for i in range(y+1, SD_SIZE+1):
                        text += "-{}{}{} -{}{}{} 0\n".format(x, y, z, x, i, z)
                        claues += 1
        
        # each number appears at most once in each subgrid
        for z in range(1, SD_SIZE+1):
            for i in range(SD_DIM):
                for j in range(SD_DIM):
                    for x in range(1, SD_DIM+1):
                        for y in range(1, SD_DIM+1):
                            for k in range(y+1, SD_DIM+1):
                                text += "-{}{}{} -{}{}{} 0\n".format(SD_DIM*i+x, SD_DIM*j+y, z, SD_DIM*i+x, SD_DIM*j+k, z)
                                claues += 1
        
        for z in range(1, SD_SIZE+1):
            for i in range(SD_DIM):
                for j in range(SD_DIM):
                    for x in range(1, SD_DIM+1):
                        for y in range(1, SD_DIM+1):
                            for k in range(x+1, SD_DIM+1):
                                for l in range(1, SD_DIM+1):
                                    text += "-{}{}{} -{}{}{} 0\n".format(SD_DIM*i+x, SD_DIM*j+y, z, SD_DIM*i+k, SD_DIM*j+l, z)
                                    claues += 1

        # at most one number in each cell
        for i, j in sd_spots:
            for k in range(1, SD_SIZE):
                for l in range(k+1, SD_SIZE+1):
                    text += "-{}{}{} -{}{}{} 0\n".format(i, j, k, i, j, l)
                    claues += 1
        
        # each number appears at least once in each row
        for y in range(1, SD_SIZE+1):
            for z in range(1, SD_SIZE+1):
                for x in range(1, SD_SIZE+1):
                    text += "{}{}{} ".format(x, y, z)
                text += "0\n"
                claues += 1
        
        # each number appears at least once in each column
        for x in range(1, SD_SIZE+1):
            for z in range(1, SD_SIZE+1):
                for y in range(1, SD_SIZE+1):
                    text += "{}{}{} ".format(x, y, z)
                text += "0\n"
                claues += 1
        
        # each number appears at least once in each subgrid
        for i in range(SD_DIM):
            for j in range(SD_DIM):
                for x in range(1, SD_DIM+1):
                    for y in range(1, SD_DIM+1):
                        for z in range(1, SD_SIZE+1):
                            text += "{}{}{} ".format(SD_DIM*i+x, SD_DIM*j+y, z)
                        text += "0\n"
                        claues += 1
        
        # add header
        text = "p cnf {} {}\n".format(999, claues) + text
        return text

    # EC: takes as input the dictionary mapping 
    # from variables to T/F assignments solved for by picoSAT;
    # returns a domain dictionary of the same form 
    # as returned by solve()
    def sat_decode(self, assignments):
        domains = {}
        for var, truth in assignments.items():
            if truth:
                spot = (int(str(var)[0])-1, int(str(var)[1])-1)
                domains[spot] = [int(str(var)[2])]
        return domains
