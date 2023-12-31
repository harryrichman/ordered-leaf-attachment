
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from subprocess import run
from ete3 import Tree
from vector_encoding import (
    to_tree, 
    to_vector,
    hamming_dist,
    hamming_dist_of_encodings,
    get_random_tree,
    random_tree_neighbor,
    get_all_vectors, 
    gen_all_newicks,
    write_newicks_of_neighborhood
)

def plot_random_spr_walks(nleaves=30, nsteps=10, nruns=2, output="test.pdf"):

    fig, ax = plt.subplots()

    for _ in range(nruns):
        run(
            f"random_spr_walk/random_spr_walk -ntax {nleaves} -niterations {nsteps-1} -sfreq 1 > temp.log", 
            shell=True
        )
        remove_line_numbering(file="temp.log")
        read_trees_to_vector_distances(
            file="temp.log",
            out_file="path_vec_dists.log"
        )
        xs = range(nsteps)
        ys = np.genfromtxt("path_vec_dists.log", delimiter=',').flat
        ax.plot(
            # xs,
            ys,
            alpha=0.8,
            rasterized=True
        )
    # ax.set_aspect("equal")

    fig.suptitle(f"random SPR walk on trees, with {nleaves} leaves and {nsteps} steps")
    ax.set_xlabel('SPR steps')
    ax.set_ylabel('vector-encoding distance')

    fig.savefig(output)

def plot_random_spr_walk_vs_spr_distance(
        nleaves=30, nsteps=10, nruns=2, output="test.pdf"
    ):

    fig, ax = plt.subplots()

    for _ in range(nruns):
        run(
            f"random_spr_walk/random_spr_walk -ntax {nleaves} -niterations {nsteps-1} -sfreq 1 > temp.log", 
            shell=True
        )
        remove_line_numbering(file="temp.log")
        run(
            f"cat temp.log | rspr/rspr -pairwise 0 1 > path_rspr_dists.log",
            shell=True
        )
        # xs = range(nsteps)
        ys = np.genfromtxt("path_rspr_dists.log", delimiter=',').flat
        ax.plot(
            # xs,
            ys,
            alpha=0.8,
            rasterized=True
        )
    # ax.set_aspect("equal")

    fig.suptitle(f"random SPR walk on trees, with {nleaves} leaves and {nsteps} steps")
    ax.set_xlabel('SPR steps')
    ax.set_ylabel('SPR distance')

    fig.savefig(output)

def make_scatterplot_from_lists(file1, file2, output="test.pdf"):
    """
    Args:
        file1 and file2: csv files that are "list-shaped"
    """
    # file listing rSPR distances
    arr1 = np.genfromtxt(file1, delimiter=',')
    # file listing vector-encoding distances
    arr2 = np.genfromtxt(file2, delimiter=',')
    xs = arr1.flat
    ys = arr2.flat

    fig, ax = plt.subplots()
    # make scatterplot
    ax.scatter(
        xs, 
        ys,
        alpha=0.2,
        rasterized=True,
    )
    ax.set_aspect('equal')

    nsteps = len(ys)
    fig.suptitle(f"random walk on trees, with 30 leaves and {nsteps} steps")
    ax.set_xlabel('rSPR distance')
    ax.set_ylabel('vector-encoding distance')

    fig.savefig(output)

def make_scatterplot_plus_histograms_from_lists(file1, file2, output="test.pdf"):
    """
    Args:
        file1 and file2: csv files that are "list-shaped"
    """
    # file listing rSPR distances
    arr1 = np.genfromtxt(file1, delimiter=',')
    # file listing vector-encoding distances
    arr2 = np.genfromtxt(file2, delimiter=',')
    xs = arr1.flat
    ys = arr2.flat

    fig, axs = plt.subplots(2, 2)
    axs[0][1].axis("off")
    # make scatterplot
    axs[1][0].scatter(
        xs, 
        ys,
        alpha=0.2,
        rasterized=True,
    )
    # show frequencies of x-values
    axs[0][0].bar(*np.unique(xs, return_counts=True))
    # show frequencies of y-values
    axs[1][1].barh(*np.unique(ys, return_counts=True))

    nsteps = len(ys)
    fig.suptitle(f"random walk on trees, with 30 leaves and {nsteps} steps")
    axs[1][0].set_xlabel('rSPR distance')
    axs[1][0].set_ylabel('vector-encoding distance')

    fig.savefig(output)

def make_scatterplot_from_matrices(file1, file2, output="test.pdf"):
    """
    Args:
        file1 and file2: csv files that are "matrix-shaped"
    """
    arr1 = np.genfromtxt(file1, delimiter=',')
    arr2 = np.genfromtxt(file2, delimiter=',')
    # why 944 ??
    xs = arr1[944].flat
    ys = arr2[944].flat
    
    fig, axs = plt.subplots(2, 2)
    axs[0][1].axis("off")
    # make scatterplot
    axs[1][0].scatter(
        xs, 
        ys,
        alpha=0.05,
        rasterized=True)
    # show frequencies of x-values
    axs[0][0].bar(*np.unique(xs, return_counts=True))
    # show frequencies of y-values
    axs[1][1].barh(*np.unique(ys, return_counts=True))

    fig.suptitle("rSPR distance vs. vector distance, at tree [0,1,2,3,4]")
    axs[1][0].set_xlabel('rSPR distance')
    axs[1][0].set_ylabel('vector-encoding distance')

    fig.savefig(output)

def make_animation_from_matrices(
        file1, file2, title_names, texts,
        output="test.gif"):
    """
    Args:
        title_names: a list of strings to use in title per frame
    """
    arr1 = np.genfromtxt(file1, delimiter=',')
    arr2 = np.genfromtxt(file2, delimiter=',')
    xs = arr1[0]
    ys = arr2[0]
    n_pts = len(xs)
    
    fig, (ax, ax_text) = plt.subplots(1, 2)
    fig.set_size_inches(8, 3)
    plt.subplots_adjust(bottom=0.15)

    sc = ax.scatter(
        xs, ys,
        alpha=0.01,
        rasterized=True,
    )

    # fig.suptitle("rSPR distance vs. vector distance, all trees on 6 leaves")
    ax.set_xlabel('rSPR distance')
    ax.set_ylabel('vector-encoding distance')

    ax_text.axis("off")
    tx = ax_text.text(0, 0, "placeholder")

    def animate(i):
    
        xs = arr1[i] + np.random.uniform(-0.05, 0.05, n_pts)
        ys = arr2[i] + np.random.uniform(-0.05, 0.05, n_pts)
        sc.set_offsets(
            list(zip(xs, ys))
        )
        vec = title_names[i]
        st = fig.suptitle(
            "distances from tree " + str(i) + ": code " + str(vec))
        print("animating step", i)
        tx.set_text(texts[i])
        return sc, st, tx

    ani = animation.FuncAnimation(
        fig,
        animate,
        interval=400,
        save_count=945
    )
    ani.save(output)

"""
Writing data to file
"""

def write_random_sample_newicks(n=30, num_trees=100, file="test.log"):
    """
    Samples a random selection of trees on n leaves, writes their newick
    strings to a file 
    """
    with open(file, 'w') as fh:
        for _ in range(num_trees):
            tree = get_random_tree(n)
            newick = tree.write(format=9)
            print(newick, file=fh)

def write_pairwise_vec_distances(n=4, file="test.log"):
    """
    Writes a matrix of vector distances to an output file,
    where rows and columns are indexed by integer vectors
    encoding trees on n leaves
    """
    with open(file, 'w') as fh:

        for vec1 in get_all_vectors(n):
            dists = []
            for vec2 in get_all_vectors(n):
                dist = hamming_dist(vec1, vec2)
                dists.append(dist)
            line = ",".join(str(d) for d in dists)
            print(line, file=fh)

def write_random_tree_pair(n=15, file="test.log"):
    tree1 = Tree(); tree1.populate(n)
    tree2 = Tree(); tree2.populate(n)
    print("first tree encoding:", to_vector(tree1))
    print("second tree encoding:", to_vector(tree2))
    print(hamming_dist_of_encodings(tree1, tree2))
    with open(file, 'w') as fh:
        print(tree1.write(format=9), file=fh)
        print(tree2.write(format=9), file=fh)

def write_random_tree_path(n_leaves=30, n_steps=10, file="test.log"):
    next_tree = Tree()
    next_tree.populate(n_leaves)
    with open(file, 'w') as fh:
        for _ in range(n_steps):
            next_tree = random_tree_neighbor(next_tree)
            print(next_tree.write(format=9), file=fh)

def read_trees_to_vector_distances(file="test.log", out_file=None):
    dists = []
    with open(file, 'r') as fh:
        newicks = fh.read().splitlines()
    first_vec = to_vector(Tree(newicks[0]))
    for newick in newicks:
        other_vec = to_vector(Tree(newick))
        dists.append(hamming_dist(first_vec, other_vec))
    if out_file is None:
        return dists
    else:
        with open(out_file, 'w') as fh:
            fh.write(",".join(str(x) for x in dists))

def remove_line_numbering(file="test.log"):
    with open(file, 'r') as fh:
        lines = fh.read().splitlines()
    newicks = []
    for line in lines:
        if ':' in line:
            (_, newick) = line.split(': ')
        else: newick = line
        newicks.append(newick)
    with open(file, 'w') as fh:
        for newick in newicks:
            print(newick, file=fh)


if __name__ == "__main__":

    plot_random_spr_walks(nleaves=1000, nsteps=15, nruns=10)

    # make_scatterplot_from_lists(
    #     "path_rspr_dists.log",
    #     "path_vec_dists.log"
    # )


    # remove_line_numbering()
    # read_trees_to_vector_distances(
    #     file="test.log",
    #     out_file="path_vec_dists.log"
    # )

    # n_leaves = 200
    # n_steps = 1000
    # file_name = f"random_treepath_{n_leaves}leaves_{n_steps}steps.txt"

    # write_random_tree_path(
    #     n_leaves=30,
    #     n_steps=100
    # )

    # write_random_sample_newicks(30, 10)
    # write_newicks_of_neighborhood(
    #     [-i for i in range(29)], file="neighborhood_30.nw")

    # make_animation_from_matrices(
    #     "all_rspr_distances_6.log",
    #     "all_vec_distances_6.log",
    #     list(make_all_vectors(6)),
    #     [to_tree(x).get_ascii(show_internal=False) for x in make_all_vectors(6)]
    # )
