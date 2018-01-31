import argparse
from pathlib import Path

import numpy as np
import pandas as pd

parser = argparse.ArgumentParser(
    description='Split existsing speech index between people.')
parser.add_argument('input', help='Index input file')
parser.add_argument('num', help='Number of people', type=int)
parser.add_argument('output', help='Index output file')
parser.add_argument('--sort', help='Sort by column')

args = parser.parse_args()

index_in = Path(args.input)
index_out = Path(args.output)

index = pd.read_csv(index_in, delim_whitespace=True)
index.reset_index(inplace=True)

if args.sort:
    index.sort_values(by=args.sort, inplace=True)

for i in range(args.num):
    l = -np.ones(len(index.index), dtype=int)
    l[i::4] = np.arange(l[i::4].size)
    index[str(i)] = l

index.sort_index(inplace=True)

index.set_index('index', inplace=True)

index.to_csv(index_out, sep=' ', index_label='')
