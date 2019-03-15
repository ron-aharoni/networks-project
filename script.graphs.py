import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

data = pd.read_csv('collated_results.csv')
data['Has loose-out-bailiwick glue'] = data['Num loose-out-bailiwick glue'] > 0
data['Has out-of-bailiwick glue'] = data['Num out-of-bailiwick glue'] > 0
data['Has glue records'] = data['Num glue records'] > 0
data['Has Mixed glue'] = data['Num glue records'] > data['Num out-of-bailiwick glue']

def plot_upper_limit(axis):
    lims = [
        np.min([ax.get_xlim(), ax.get_ylim()]),  # min of both axes
        np.max([ax.get_xlim(), ax.get_ylim()]),  # max of both axes
    ]

    # now plot both limits against eachother
    ylims = [0.0, 1.0]
    ax.plot(lims, ylims, 'k-', alpha=0.75, zorder=0)
    ax.set_aspect('equal')
    ax.set_xlim(lims)
    ax.set_ylim(lims)

def normalize_cdf(series):
    return (series - series.min()) / series.count()

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
