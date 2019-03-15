#!/usr/bin/env python3

import sys
import pandas as pd


def get_all_possible_domains(input_file):
    domain_column = pd.read_csv(input_file)['Domain']
    return set(item for sublist in domain_column for item in get_superdomains(sublist))


def get_superdomains(domain):
    split = domain.split('.')
    return ['.'.join(split[i:]) for i in range(len(split) - 1)]


def main():
    files = sys.argv[1:]
    if not files:
        files = ['-']

    for f in files:
        if f == '-':
            f = sys.stdin

        for domain in get_all_possible_domains(f):
            print(domain)


if __name__ == '__main__':
    main()
