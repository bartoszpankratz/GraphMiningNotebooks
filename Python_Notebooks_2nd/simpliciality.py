import numpy as np
import random
from math import comb
from itertools import combinations as combs
from collections import Counter

# Get a dictionary of vertex -> edges containing vertex.
def get_edge_sets(V,E):
    #Initalize edge_set
    edge_sets = {v : [] for v in V}
    #iterate through E and update edge_sets
    for e in E:
        for v in e:
            edge_sets[v].append(e)

    return edge_sets

def get_simplicial_pairs(vertices, edges, as_matrix=False, edge_order=False):
    V = vertices.copy()
    E = edges.copy()
    max_size = max({len(e) for e in E})
    E = [set(e) for e in E]

    ## Getting relevant data
    edge_sets = get_edge_sets(V,E)
    degrees = {v : len(edge_sets[v]) for v in V}

    #Initializing
    if as_matrix:
        M = np.zeros((max_size,max_size))
    elif edge_order:
        M = [0,0]
    else:
        M = 0

    #We iterate through E and compute the number of pairs with e as the smaller edge
    for e in E:
        #Any edge f containing e will contain v for all v in e
        #Thus, we find v with the smallest degree for our search
        v = list(e)[0]
        for u in e:
            if degrees[u] < degrees[v]:
                v = u
        relevant_edges = edge_sets[v]
        #Now we check for f containing e
        #If order matters, we compare the index of e and f in edge_sets[v]
        #edge_sets[v] preserves edge order, so all is good
        if edge_order:
            #Note: we assume there are no multi-edges in E
            #This is precisely why we can't order edges in the Chung-Lu model
            i = relevant_edges.index(e)
            for j,f in enumerate(relevant_edges):
                if e<f:
                    if as_matrix:
                        if i<j:
                            M[len(e)-1][len(f)-1] += 1
                        else:
                            M[len(f)-1][len(e)-1] += 1
                    else:
                        if i<j:
                            M[0] += 1
                        else:
                            M[1] += 1

        #If order doesn't matter, we just count
        else:
            for f in relevant_edges:
                if e<f:
                    if as_matrix:
                        M[len(e)-1][len(f)-1] += 1
                    else:
                        M += 1

    return M

def get_simplicial_measure(V,E,samples = 1, edge_order = False, multisets = True):
    top = get_simplicial_pairs(V,E,edge_order=edge_order)
    bottom = 0
    for i in range(samples):
        E_cl = chung_lu(V,E,multisets=multisets)
        bottom += get_simplicial_pairs(V,E_cl,edge_order=False)

    if edge_order:
        bottom = [(1+bottom)/(2*samples),(1+bottom)/(2*samples)]
        return [top[0]/bottom[0],top[1]/bottom[1]]
    else:
        bottom = (1+bottom)/samples
        return top/bottom

# Get the simplicial_matrix of a graph
# The simplicial matrix is the cell-wise ratio of simplicial pairs between a real graph and a re-sampling (Chung-Lu model)
# V: vertices
# E: edges
# samples: the number of times we re-sample, set to 1 by default
def get_simplicial_matrix(V,E,samples = 1, edge_order = False, multisets=True):
    #We first get the matrix of simplicial pairs
    M_top = get_simplicial_pairs(V,E,as_matrix=True,edge_order=edge_order)

    #Next, we get the same matrix for the re-sample, depending on the model specified
    E_resampled = chung_lu(V,E,multisets=multisets)
    #We never order edges in the Chung-Lu model
    #Instead, we split the results in two equal parts
    M_bottom = get_simplicial_pairs(V,E_resampled,as_matrix=True,edge_order=False)
    for i in range(samples-1):
        E_resampled = chung_lu(V,E,multisets=multisets)
        temp = get_simplicial_pairs(V,E_resampled,as_matrix=True,edge_order=False)
        M_bottom = np.add(M_bottom, temp)
    M_bottom = (M_bottom + 1)/samples

    #Now we check for edge_order
    if edge_order:
        for i in range(len(M_bottom)):
            for j in range(i+1,len(M_bottom)):
                M_bottom[i][j] = M_bottom[i][j]/2
                M_bottom[j][i] = M_bottom[i][j]

    return M_top/M_bottom

def chung_lu(vertices,m,degrees = None, multisets = True):
    # If V is a number, we convert to a list
    if type(vertices) is int:
        V = list(range(vertices))
    else:
        V = list(vertices.copy())

    #If m is a list of edges, we get the degrees and the number of edges of each size
    if (type(m[0]) is set) or (type(m[0]) is list):
        degrees = get_degrees(V,m.copy())

        #sort edges by size
        edge_dict = sort_edges(m.copy())

        #convert m to a list of num edges per size
        sizes = edge_dict.keys()
        m = [0]*max(sizes)
        for k in sizes:
            m[k-1] = len(edge_dict[k])

    #If degrees is a list, we convert to a dictionary
    #Note: If V was given as a set, and degrees as a list of degrees, then the degrees might get shuffled
    if type(degrees) is list:
        degrees = dict(zip(V,degrees))
    L = get_volume(V,degrees)

    #choices is a dictionary with degrees[v] keys pointing to v
    #I've tested, and this is much faster than making a list
    choices = dict.fromkeys(set(range(L)))
    counter = 0
    current_vertex = 0
    #We need L keys in total
    while (counter<L):
        for i in range(degrees[V[current_vertex]]):
            choices[counter] = V[current_vertex]
            counter += 1
        current_vertex += 1

    #E is the set of edges to be returned
    E = []
    if multisets:
        for k in range(len(m)):
            #Adding all edges of size k+1
            for i in range(m[k]):
                e = []
                for j in range(k+1):
                    e.append(choices[random.randint(0,L-1)])
                E.append(e)
    else:
        for k in range(len(m)):
            #Adding all edges of size k+1
            for i in range(m[k]):
                e = []
                while len(e)<k+1:
                    v = (choices[random.randint(0,L-1)])
                    if v not in e:
                        e.append(v)
                E.append(e)
    return E

def get_degrees(V,E):
    #Initalize degrees
    degrees = {v : 0 for v in V}

    #Update degrees by iterating through E
    for e in E:
        for v in e:
            degrees[v] = degrees[v]+1

    return degrees

def get_volume(S,X):
    #initialize volume
    volume = 0

    #get degrees if X is a list of edges
    if type(X) is list:
        #We need all vertices in the graph to call get_degrees
        V = S.copy()
        for e in X:
            V.update(e)
        X = get_degrees(V,X)

    #iterate through V and sum degrees
    for v in S:
        volume += X[v]

    return volume

def sort_edges(E):
    #initialize partition
    edge_sizes = {len(e) for e in E}
    partition = {k : [] for k in edge_sizes}

    #iterate through E and update partition
    for e in E:
        partition[len(e)].append(e)

    return partition
