import argparse
from pathlib import Path

import pandas as pd

parser = argparse.ArgumentParser(
    description='Convert the output of find_bad_utts.sh program to a WER/Edits index for Corrector.')
parser.add_argument('exp', help='Experiment directory containing the edits.txt file')
parser.add_argument('index', help='Index output file')

args = parser.parse_args()

exp = Path(args.exp)
index_path = Path(args.index)

edits = pd.read_csv(exp / 'edits.txt', header=None, delim_whitespace=True, index_col=0)
length = pd.read_csv(exp / 'length.txt', header=None, delim_whitespace=True, index_col=0)
edits.columns = ['edits']
length.columns = ['length']
data = pd.merge(edits, length, left_index=True, right_index=True)
data['wer'] = data['edits'] / data['length']

default_index = data.index
wer_index = data.sort_values(by=['wer'], ascending=False).index
edits_index = data.sort_values(by=['edits'], ascending=False).index

index = {}
for utt in default_index:
    index[utt] = []
for i, utt in enumerate(wer_index):
    index[utt].append(i)
for i, utt in enumerate(edits_index):
    index[utt].append(i)

with open(index_path.absolute(), 'w') as f:
    f.write('wer edits\n')
    for utt, ind in index.items():
        f.write(f'{utt} {ind[0]} {ind[1]}\n')
