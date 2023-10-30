import config
import numpy as np
import scipy.sparse as sp
from sklearn.preprocessing import normalize
from data import data
import argparse
import random
from cluster import cluster

p = argparse.ArgumentParser(description='Set parameter')
p.add_argument('--data', type=str, default='coauthorship', help='for hypergraph to choose data type (coauthorship/cocitation)')
p.add_argument('--dataset', type=str, default='imdb', help='dataset name (e.g.: cora/dblp for coauthorship, cora/citeseer for cocitation)')
p.add_argument('--tmax', type=int, default=100, help='t_max parameter')
p.add_argument('--seeds', type=int, default=0, help='seed for randomness')
p.add_argument('--alpha', type=float, default=0.2, help='mhc parameter')
p.add_argument('--beta', type=float, default=0.5, help='weight of knn random walk')
p.add_argument('--metric', type=bool, default=False, help='calculate additional metrics: modularity')
p.add_argument('--weighted_p', type=int, default=0, help='use transition matrix p weighted by attribute similarity')
p.add_argument('--verbose', action='store_true', help='print verbose logs')
p.add_argument('--scale', action='store_true', help='use configurations for large-scale data')
p.add_argument('--interval', type=int, default=5, help='interval between cluster predictions during orthogonal iterations')
p.add_argument('--knn_k', type=int, default=50, help='knn k to build graph neighbors')
p.add_argument('--init_iter', type=int, default=25, help='BCM iteration')
p.add_argument('--graph_type', type=str, default='Multi', help='graph type'
                '(e.g.: Hypergraph, Multi, Undirected, Directed)')

args = p.parse_args()

def random_walk(adj,type):

    if type == "Hypergraph":
        p_mat = [normalize(adj.T, norm='l1', axis=1), normalize(adj, norm='l1', axis=1)]
    elif type =="Multi":
        config.num_view = len(adj)
        P = [normalize(layer_adj, norm='l1', axis=1) for layer_adj in adj]
        p_mat = [sum([pm*1./config.num_view for i, pm in enumerate(P)])]
    else:
        p_mat = [normalize(adj, norm='l1', axis=1)]
    return p_mat

def run_ancka():

    dataset = data.load(config.dataset,config.data,config.graph_type)
    features = dataset['features_sp']
    labels = dataset['labels']
    adj = dataset['adj_sp']
    num_nodes = dataset['n']
    config.adj = adj

    labels = np.asarray(np.argmax(labels, axis=1)) if labels.ndim == 2 else labels
    config.labels = labels
    k = len(np.unique(labels))

    seed = config.seeds
    np.random.seed(seed)
    random.seed(seed)

    config.features = features.copy()
    p_mat = random_walk(config.adj,config.graph_type)

    if config.graph_type=="Multi":
        config.num_view = len(adj)
        d_tvec = [np.asarray(layer_adj.sum(0)).flatten() for layer_adj in adj]
        deg_dict = {i: sum([layer_dvec[i] for layer_dvec in d_tvec]) for i in range(len(d_tvec[0]))}
    else:
        d_vec = np.asarray(config.adj.sum(0)).flatten()
        deg_dict = {i: d_vec[i] for i in range(len(d_vec))}

    results = None
    results = cluster(p_mat, num_nodes, features, k, deg_dict, alpha=config.alpha, beta=config.beta, tmax=config.tmax, ri=False, weighted_p=config.weighted_p)
    return results

if __name__ == '__main__':
    config.data = args.data
    config.dataset = args.dataset
    config.metric = args.metric
    config.tmax = args.tmax
    config.beta = args.beta
    config.alpha = args.alpha
    config.seeds = args.seeds
    config.verbose = args.verbose
    config.cluster_interval = args.interval
    config.graph_type = args.graph_type
    config.knn_k = args.knn_k
    config.init_iter = args.init_iter

    if args.scale:
        config.approx_knn = True
        config.init_iter = 1

    print(f"{config.knn_k} {config.init_iter} {config.beta}")
    results = run_ancka()