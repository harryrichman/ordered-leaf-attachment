"""
package to encode a phylogenetic tree on n leaves as an integer vector

The encoding works via applying a canonical edge labelling to the tree; the
vector then records where leaves are added iteratively
"""

from random import randrange
from itertools import combinations_with_replacement
from typing import (
    List
)
from ete3 import Tree

def to_vector(tree):
    """
    args:
        tree: ete3.Tree object. tree is assumed to be rooted 
            and bifurcating, and have distinct leaf names.
    """
    if not tree.is_root():
        raise ValueError("input tree should be rooted")

    n_leaves = len(tree.get_leaf_names())
    assert n_leaves >= 1
    # handle small cases, < 2 leaves
    if n_leaves == 1:
        return []
    elif n_leaves == 2:
        return [0]
    
    # tree has 3 or more leaves
    sorted_leaves = sorted(tree.get_leaf_names())
    leaf_to_idx = {}
    for (idx, name) in enumerate(sorted_leaves):
        leaf_to_idx[name] = idx
    
    # perform internal node labelling
    for node in tree.traverse(strategy='postorder'):
        if node.is_leaf():
            idx = leaf_to_idx[node.name]
            node.parent_edge_label = idx
            node.min_label_below = idx
        else:
            # `min_label_below` = minimum label of descendant subclade 
            children_mins = [child.min_label_below for child in node.children]
            node.min_label_below = min(children_mins)
            node.parent_edge_label = - max(children_mins)
    
    # initialize encoding vector
    vector = []
    # fill in vector via tree deconstruction, removing one leaf at a time
    # copy tree
    tree_copy = Tree(
        tree.write(
            features=["parent_edge_label"], 
            format_root_node=True,
            format=9))
    # add "grandparent-root" node so that every node in `tree_copy` has a parent
    tree_grandparent = Tree()
    tree_grandparent.add_child(tree_copy)
    # construct leaf dictionary for `tree_grandparent`
    leaf_dict = {}
    for node in tree_grandparent.traverse(strategy='postorder'):
        if node.is_leaf():
            idx = leaf_to_idx[node.name]
            leaf_dict[idx] = node
    for i in range(n_leaves - 1):
        idx = n_leaves - 1 - i
        # find sister node of leaf idx
        leaf = leaf_dict[idx]
        sister = leaf.get_sisters()[0]
        # assign vector entry
        vector.append(int(sister.parent_edge_label))
        # delete node, and its parent, from tree_copy
        leaf.up.up.add_child(sister)
        leaf.up.detach()
    vector.reverse()
    return vector

def to_tree(vector, names=None):
    """
    Args:
        vector: list of integers with i-th entry in range {-i, ..., i}
        names: list of strings to be used as names of leaf nodes, strings
            should be distinct
    Returns:
        ete3.Tree object encoded by vector
    """
    # check input vector is "proper"
    for i, vi in enumerate(vector):
        assert isinstance(vi, int), (
            f"input vector should should have int entries; given input={vector}"
        )
        assert abs(vi) <= i, (
            f"vector entry vector[{i}] should be between -{i} and {i} "
            f"(inclusive), given input has vector[{i}]={vi}"
        )
    n_leaves = len(vector) + 1
    if names is None:
        # generate default names ['aa', 'ab', 'ac', ...]
        names = [chr(97 + i % 26) for i in range (n_leaves)]
        period = 26
        while period < n_leaves:
            names = [names[i // period][-1] + names[i] for i in range(n_leaves)]
            period = 26 * period
    else:
        # ensure that `names` is a list of strings
        names = list(names) # names.copy()
        for i, name in enumerate(names):
            names[i] = str(name)
    # ensure that enough names are provided
    if len(names) < n_leaves:
        raise ValueError(
            "must provide at least n + 1 names, where n is the "
            "length of the encoding vector")

    # initialize label-to-node dictionary, to avoid cost of tree search
    label_to_node = {}

    # initialize tree; note `tree` has an extra "grand-root" node
    tree = Tree()
    child_0 = tree.add_child(name=names[0])
    child_0.parent_edge_label = 0
    label_to_node[0] = child_0

    # build tree iteratively
    for i in range(1, n_leaves):
        idx = vector[i - 1]
        # get node with label=idx, using stored dict
        subtree = label_to_node[idx]
        # attach i-th leaf as sister of `subtree`, subdividing its parent-edge
        # to subdivide parent edge: add new node as sister of subtree-root
        new_node = subtree.add_sister(name="int-node-" + str(i))
        new_node.parent_edge_label = -i
        label_to_node[-i] = new_node
        # to subdivide parent edge: then move current subtree to lie below new node
        subtree.detach()
        new_node.add_child(subtree)
        # add new leaf under new (internal-)node
        child = new_node.add_child(name=names[i])
        child.parent_edge_label = i
        label_to_node[i] = child

    # return tree with "grand-root" removed
    final_tree = tree.children[0]
    # `.up = None` needed so that result is considered rooted
    final_tree.up = None
    return final_tree

"""
Multifurcating versions
"""
def to_vector_multifurcating(tree, debugging=False):
    """
    WARNING: not tested
    args:
        tree: ete3.Tree object. tree is assumed to be rooted 
            If input tree is not bifurcating, method will return a vector which
            encodes a bifurcating resolution of the input.

    """
    if not tree.is_root():
        raise ValueError("input tree should be rooted")

    n_leaves = len(tree.get_leaf_names())
    # handle small cases, < 2 leaves
    if n_leaves == 0:
        return []
    elif n_leaves == 1:
        return [0]
    
    # if tree has 2 or more leaves
    sorted_leaves = sorted(tree.get_leaf_names())
    if debugging: print("sorted_leaves:", sorted_leaves)
    
    # perform (parent-)edge labelling
    for node in tree.traverse(strategy='postorder'):
        if node.is_leaf():
            idx = sorted_leaves.index(node.name)
            node.parent_edge_label = [idx]
            node.unmatched_labels = [idx]
        else:
            # edge label = union of umatched labels of children nodes, except
            # with minimum label removed
            children_labels = []
            for child in node.children:
                children_labels += child.unmatched_labels
            if debugging: print("current unmatched labels:", children_labels)
            min_label = min(children_labels)
            node.unmatched_labels = [min_label]
            children_labels.remove(min_label)
            node.parent_edge_label = sorted(children_labels)
            if debugging: print(
                    "at node above", node.get_leaf_names(),
                    "assigning edge label:", node.parent_edge_label)
    
    # initialize encoding vector
    vector = [None] * (n_leaves - 1)
    for node in tree.traverse(strategy='preorder'):
        if node.is_leaf():
            continue
        for i in node.parent_edge_label:
            ## debugging
            if debugging: print("determining vector entry at pos.", i)
            if i == 0:
                continue
            if i > min(node.parent_edge_label):
                vector[i - 1] = - min(node.parent_edge_label) - 0.5
                continue
            # determine i-th entry of encoding vector, which is the 
            # first-encountered edge label below edge (-i) which has 
            # absolute value < i
            # 
            # (this is the edge label where the i-th leaf is attached when 
            # the tree is built iteratively)
            subnode = node
            found_label = False
            while not found_label:
                children = subnode.children
                assert len(children) > 0, (
                    "ERROR: reached no children without finding vector entry"
                )
                for child in children:
                    if child.is_leaf():
                        label = child.parent_edge_label[0]
                        # check label-found condition
                        if label < i:
                            vector[i - 1] = label
                            found_label = True
                            if debugging: 
                                print(
                                    "at leaf", child.get_leaf_names(),
                                    "found vector entry=", 
                                    vector[i - 1], "at pos.", i)
                            break
                    # if `child` is not a leaf node
                    for label in child.parent_edge_label:
                        # check label-found condition
                        if abs(label) < i:
                            vector[i - 1] = - label
                            found_label = True
                            if debugging: 
                                print(
                                    "at node over", child.get_leaf_names(),
                                    "found vector entry=", vector[i - 1], "at pos.", i)
                            break
                    if found_label: break
                # if label still not found, move down tree
                for child in children:
                    # check which child has small-enough label
                    if abs(child.unmatched_labels[0]) < i:
                        subnode = child

    return vector


"""
Utils
"""

def test_vector_idempotent(n=30):
    vec = get_random_vector(n)
    assert vec == to_vector(to_tree(vec))
    print("Passed test with vector = ", vec)

def test_ete_vector_idempotent(n=30):
    t = Tree()
    t.populate(n)
    vec = to_vector(t)
    assert vec == to_vector(to_tree(vec))
    print("Passed test with tree = ", t.write(format=9), t)

def hamming_dist(vec1, vec2):
    """
    Computes hamming distance between input vectors
    """
    return sum(a != b for (a, b) in zip(vec1, vec2))

def hamming_dist_of_encodings(tree1, tree2):
    """
    Computes hamming distance between vector encodings of input trees.
    Assumes that input trees have the same leaf set.
    """
    vec1 = to_vector(tree1)
    vec2 = to_vector(tree2)
    return hamming_dist(vec1, vec2)

def combine_tree_vectors(left_vec, right_vec):
    n_left = len(left_vec) + 1
    n_right = len(right_vec) + 1
    combined_names = [
        chr(97 + i // 26) + chr(97 + i % 26) for i in range(n_left + n_right)]
    left_tree = to_tree(
        left_vec,
        names=combined_names[:n_left])
    right_tree = to_tree(
        right_vec, 
        names=combined_names[n_left:])
    t = Tree()
    t.add_child(left_tree)
    t.add_child(right_tree)
    return to_vector(t)

def split_tree_children_vectors(vec: List[int]):
    t = to_tree(vec)
    left_child = t.children[0]
    right_child = t.children[1]
    # `.up = None` needed so that result is considered rooted
    left_child.up = None
    right_child.up = None
    return (to_vector(left_child), to_vector(right_child))

def get_root_label_from_vector(vec):
    t = to_tree(vec)
    return t.parent_edge_label

"""
Produce vectors or trees or vector-iterators or tree-iterators
"""

def get_random_vector(n=30):
    """
    args:
        n: number of leaves
    """
    vec = [None for _ in range(n - 1)]
    for i in range(n - 1):
        vi = randrange(-i, i + 1)
        vec[i] = vi
    return vec

def get_random_tree(n=30):
    """
    args:
        n: number of leaves
    """
    vec = get_random_vector(n)
    return to_tree(vec)

def get_all_vectors(n=4):
    """
    Returns an iterator which yields all integer vectors of length n - 1,
    which satisfy the constraint that the i-th entry is in the range [-i, i]
    """
    vec = [-i for i in range(n - 1)]
    max_reached = False
    while not max_reached:
        yield vec.copy()

        # increment vector
        vec[-1] += 1
        # carry terms
        for i in range(n-2, 0, -1):
            if vec[i] > i:
                # carry term
                vec[i] = -i
                vec[i - 1] += 1
        # check if max reached
        if vec[0] > 0:
            max_reached = True

def get_all_treeshape_vectors(n=4):
    """
    Returns an iterator which yields vector encodings of tree on n leaves,
    representing all possible tree shapes
    """
    if n == 0:
        return iter(())
    elif n == 1:
        yield []
    elif n == 2:
        yield [0]
    else:
        # n >= 3
        for k in range(1, (n+1) // 2):
            for leftvec in get_all_treeshape_vectors(k):
                for rightvec in get_all_treeshape_vectors(n - k):
                    yield combine_tree_vectors(leftvec, rightvec)
        if n % 2 == 0:
            # n is even
            k = n // 2
            for (leftvec, rightvec) in combinations_with_replacement(
                get_all_treeshape_vectors(k), 2
            ):
                yield combine_tree_vectors(leftvec, rightvec)

def get_all_treeshapes(n=4):
    """
    Returns an iterator which yields trees on n leaves, representing all 
    possible tree shapes
    """
    for vec in get_all_treeshape_vectors(n):
        yield to_tree(vec)

def get_vector_neighborhood(start_vec):
    """
    Returns a list of vectors which have hamming distance 1 from start_vec
    """
    neighbors = []
    for i in range(len(start_vec)):
        for entry in range(-i, i + 1):
            if entry == start_vec[i]:
                continue
            new_vec = start_vec.copy()
            new_vec[i] = entry
            neighbors.append(new_vec)
    return neighbors

def get_tree_neighborhood(start_tree):
    """
    Returns a list of trees whose vector encodings have hamming distance 1 from
    the vector encoding of start_tree
    """
    start_vec = to_vector(start_tree)
    return [to_tree(vec) for vec in get_vector_neighborhood(start_vec)]

def random_vector_neighbor(start_vec):
    """
    Returns a "proper" integer vector which has hamming distance 1 
    from start_vec
    Idea of process:
        (i, j) is a randomly generated point in an n x n square, which lies
        outside the main diagonal. We then modify the vector entry at position
        max(i, j). If i = max(i, j) we modify entry to +j; if j = max(i, j) we
        modify entry to -i. However, we make a slight adjustment to guarantee
        modified entry is different from old entry 
    """
    n = len(start_vec)
    i = randrange(0, n)
    j = randrange(0, n - 1)
    # guarantee that i != j
    if j >= i:
        j += 1
    k = max(i, j)

    old_val = start_vec[k]
    # set new_val to i - j
    new_val = i - j
    if new_val > 0:
        # modify new_val to guarantee it is new
        if new_val <= old_val:
            new_val -= 1
    else: # new_val is negative
        # modify new_val to guarantee it is new
        if new_val >= old_val:
            new_val += 1
    new_vec = start_vec.copy()
    new_vec[k] = new_val
    return new_vec

def lazy_random_vector_neighbor(start_vec):
    """
    Like `get_random_vector_neighbor` but allows output to be same as `start_vec`
    """
    n = len(start_vec)
    i = randrange(0, n)
    j = randrange(0, n)
    k = max(i, j)

    # old_val = start_vec[k]
    new_val = i - j

    new_vec = start_vec.copy()
    new_vec[k] = new_val
    return new_vec

def random_tree_neighbor(start_tree):
    start_vec = to_vector(start_tree)
    new_vec = random_vector_neighbor(start_vec)
    return to_tree(new_vec)
    
def lazy_random_tree_neighbor(start_tree):
    """
    Like `get_random_tree_neighbor` but allows output to be same as `start_tree`
    """
    start_vec = to_vector(start_tree)
    new_vec = lazy_random_vector_neighbor(start_vec)
    return to_tree(new_vec)
    
def write_newicks_of_neighborhood(start_vec, file="test.log"):
    nbhd_vecs = get_vector_neighborhood(start_vec)
    with open(file, 'w') as fh:
        for vec in nbhd_vecs:
            tree = to_tree(vec)
            newick = tree.write(format=9)
            print(newick, file=fh)

def write_all_newicks(n=4, file="test.log"):
    """
    Writes all trees on n leaves in newick format, to output file
    """
    all_vecs = get_all_vectors(n)
    with open(file, 'w') as fh:
        for vec in all_vecs:
            tree = to_tree(vec)
            newick = tree.write(format=9)
            print(newick, file=fh)

def gen_all_newicks(n=4):
    """
    Returns an iterator which yields newick strings
    """
    all_vecs = get_all_vectors(n)
    for vec in all_vecs:
        tree = to_tree(vec)
        newick = tree.write(format=9)
        yield newick



if __name__ == "__main__":

    pass

    # tree1 = Tree("((0,2),(3,(4,(5,1))));")
    # tree2 = Tree("((0,2),(((3,4),5),1));")
    # print(to_vector(test_tree))
    # print(test_tree.get_ascii(attributes=['parent_edge_label', 'name']))

    # vector = get_random_vector(7)
    # print("random vector: \n", vector)
    # print(
    #     "tree form:\n", 
    #     to_tree(vector).get_ascii(attributes=['parent_edge_label', 'name']))

    