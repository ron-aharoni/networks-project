import pandas as pd
import matplotlib.pyplot as plt

data = pd.read_csv('collated_results.csv')
data['Has loose-out-bailiwick glue'] = data['Num loose-out-bailiwick glue'] > 0
data['Has out-of-bailiwick glue'] = data['Num out-of-bailiwick glue'] > 0
data['Has glue records'] = (data['Num glue records'] > 0)
data['Has Mixed glue'] = data['Num glue records'] > data['Num out-of-bailiwick glue']
data['Has Mixed glue'].sum()
