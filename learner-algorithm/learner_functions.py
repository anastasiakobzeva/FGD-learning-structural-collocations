import math
import numpy
import pandas as pd
from nltk.util import ngrams
from nltk.probability import FreqDist


def get_ngrams(seq_arr, n_gram):
    """
    Create n-grams from a sequence of container nodes.
    :param seq_arr: container node sequence as list
    :param n_gram: n-gram window size
    :return: n-grams of container nodes (list of lists)
    """
    seq_arr.insert(0, 'start')
    seq_arr.append('end')
    n_grams = list(ngrams(seq_arr, n_gram))
    return n_grams


def get_freq_dist(all_ngrams_list):
    """
    Create n-gram frequency distribution.
    param all_ngrams_list: list of all n-grams (list of lists)
    :return: FreqDist object
    """
    freq_dist = FreqDist(ngr for ngr in all_ngrams_list)
    # print(freq_dist.max())  # the most frequent n-grams
    # print(freq_dist.hapaxes())  # n-grams that occur only once
    return freq_dist


def get_prob(node_seq, freq_dist, n_gram):
    """ 
    Calculate the probability of a given container node sequence.
    :param node_seq: container node sequence as list
    :param freq_dist: FreqDist object as returned by get_freq_dist
    :param n_gram: 
    :return: log prob as int, node_seq, list of unattested n-grams
    """
    alpha = 0.5  # for unattested ngrams
    ngrams = get_ngrams(node_seq, n_gram)
    unattested = []
    # print(ngrams)
    probs = []
    for ngr in ngrams:
        if ngr in freq_dist:
            freq = freq_dist[ngr] + alpha
            ngr_prob = freq/(freq_dist.N() + len(freq_dist)*alpha)
        else:
            ngr_prob = alpha/(freq_dist.N() + len(freq_dist)*alpha)
            unattested.append(ngr)
        probs.append(ngr_prob)
    result = math.log(numpy.prod(probs))
    print(node_seq, result, '\n')
    return result, node_seq, unattested


def plot_log_prob_simple(p_short_1, p_long_1, p_short_2, p_long_2,
                         label1='No island', label2='Island', title='test plot'):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1)
    ax.set_title(title)
    ax.plot([0,1], [p_short_1, p_long_1], marker = 'o', label=label1,
            color='black')
    ax.plot([0,1], [p_short_2, p_long_2], marker = 'o', linestyle='--',
            label=label2,
            color='black')
    ax.set_ylabel('Log Probability')
    ax.set_xlabel('Distance')
    ax.set_xticks([0,1])
    ax.set_xticklabels(['Short', 'Long'])
    ax.grid(True)
    ax.legend()
    plt.tight_layout()
    plt.ylim([-38, 0])
    # plt.savefig(title+".png", format="png")  # to save the plot


def main():
    # test
    print(get_ngrams(['OBJ'], 2))


if __name__ == "__main__":
    main()
