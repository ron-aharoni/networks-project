import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def plot_upper_limit(axis):
    lims = [
        np.min([axis.get_xlim(), axis.get_ylim()]),  # min of both axes
        np.max([axis.get_xlim(), axis.get_ylim()]),  # max of both axes
    ]

    # now plot both limits against eachother
    ylims = [0.0, 1.0]
    axis.plot(lims, ylims, 'k-', alpha=0.75, zorder=0)
    axis.set_aspect('equal')
    axis.set_xlim(lims)
    axis.set_ylim(lims)


def normalize_cdf(series):
    return (series - series.min()) / series.count()


def read_multi_csv(files, **kwargs):
    if not files:
        files = ['-']

    return pd.concat([
            pd.read_csv(sys.stdin if f == '-' else f, **kwargs)
            for f in files
        ],
        ignore_index=True
    )


def main():
    data = read_multi_csv(sys.argv[1:])

    data['Has loose-out-bailiwick glue'] = data['Num loose-out-bailiwick glue'] > 0
    data['Has out-of-bailiwick glue'] = data['Num out-of-bailiwick glue'] > 0
    data['Has glue records'] = data['Num glue records'] > 0
    data['Has Mixed glue'] = data['Num glue records'] > data['Num out-of-bailiwick glue']

    plt.figure()
    fig, ax = plt.subplots()
    normalize_cdf(data['Has out-of-bailiwick glue'].astype(int).cumsum()).plot(label='has out-of-bailiwick glue')
    plot_upper_limit(ax)
    plt.title('CDF of out-of-bailiwick glue')
    plt.axis('tight')
    plt.legend()
    plt.savefig('cdf.png')

    plt.figure()
    fig, ax = plt.subplots()
    normalize_cdf(data['Has Mixed glue'].astype(int).cumsum()).plot(label='has mixed-bailiwick glue')
    plot_upper_limit(ax)
    plt.title('CDF of mixed-bailiwick glue')
    plt.axis('tight')
    plt.legend()
    plt.savefig('cdf.mixed.png')


if __name__ == '__main__':
    main()
