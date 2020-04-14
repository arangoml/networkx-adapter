'''
Adapted implementation of Aditya Grover's node2vec reference implementation
@author Rajiv Sambasivan

'''

import argparse
import os
import node2vec
from gensim.models import Word2Vec
from fb_arango_graph_loader import FBArangoDBN2VGraph


from pathlib import Path


def parse_args():
    '''
    Parses the node2vec arguments.
    '''
    parser = argparse.ArgumentParser(description="Run node2vec.")

    parser.add_argument('--input', nargs='?', default='datasets/karate_club.csv',
                        help='Input graph path')

    parser.add_argument('--output', nargs='?', default='emb/karate.emb',
                        help='Embeddings path')

    parser.add_argument('--dimensions', type=int, default=128,
                        help='Number of dimensions. Default is 128.')

    parser.add_argument('--walk-length', type=int, default=80,
                        help='Length of walk per source. Default is 80.')

    parser.add_argument('--num-walks', type=int, default=10,
                        help='Number of walks per source. Default is 10.')

    parser.add_argument('--window-size', type=int, default=10,
                        help='Context size for optimization. Default is 10.')

    parser.add_argument('--iter', default=1, type=int,
                      help='Number of epochs in SGD')

    parser.add_argument('--workers', type=int, default=8,
                        help='Number of parallel workers. Default is 8.')

    parser.add_argument('--p', type=float, default=1,
                        help='Return hyperparameter. Default is 1.')

    parser.add_argument('--q', type=float, default=1,
                        help='Inout hyperparameter. Default is 1.')

    parser.add_argument('--weighted', dest='weighted', action='store_true',
                        help='Boolean specifying (un)weighted. Default is unweighted.')
    parser.add_argument('--unweighted', dest='unweighted', action='store_false')
    parser.set_defaults(weighted=False)

    parser.add_argument('--directed', dest='directed', action='store_true',
                        help='Graph is (un)directed. Default is undirected.')
    parser.add_argument('--undirected', dest='undirected', action='store_false')
    parser.set_defaults(directed=False)

    return parser.parse_args()

def read_graph():
    G = FBArangoDBN2VGraph()
    G.load_subgraph(['3447', '0'], 2)
    return G

def learn_embeddings(walks, emb_param):
    '''
    Learn embeddings by optimizing the Skipgram objective using SGD.
    '''
    walks = [list(map(str, walk)) for walk in walks]
#    model = Word2Vec(walks, size=args.dimensions, window=args.window_size, min_count=0, sg=1, workers=args.workers, iter=args.iter)
    model = Word2Vec(walks, size = emb_param['size'], window = emb_param['window'],\
                     min_count = emb_param['min_count'], sg = emb_param['sg'],\
                     workers = emb_param['workers'], iter = emb_param['iter'])
    
    return model

def run_driver():
    fpo = '/home/admin2/arangopipe/git_node2vec/node2vec/emb/fb_subgraph.emd'
    nx_G = read_graph()
    G = node2vec.Graph(nx_G, False, 1, 1)
    G.preprocess_transition_probs()
    walks = G.simulate_walks(10, 80)
    emb_params = {'size': 128, 'window': 10,\
                  'min_count': 0, 'sg': 1, 'workers': 8,\
                  'iter': 1}
    model = learn_embeddings(walks, emb_params)
    model.wv.save_word2vec_format(fpo)
    return
    

def main(args):
    '''
    Pipeline for representational learning for all nodes in a graph.
    '''
    nx_G = read_graph(args.input)
    G = node2vec.Graph(nx_G, args.directed, args.p, args.q)
    G.preprocess_transition_probs()
    walks = G.simulate_walks(args.num_walks, args.walk_length)
    emb_params = {'size': args.dimensions, 'window': args.window_size,\
                  'min_count': 0, 'sg': 1, 'workers': args.workers,\
                  'iter': args.iter}
    model = learn_embeddings(walks, emb_params)
    model.wv.save_word2vec_format(args.output)
if __name__ == "__main__":
    args = parse_args()
    main(args)
