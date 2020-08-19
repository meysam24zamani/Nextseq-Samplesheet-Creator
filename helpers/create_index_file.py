import argparse

import pandas as pd


def main():
    parser = argparse.ArgumentParser(
        description="Script to print a Python dictionary from an index file (helper tool)")
    parser.add_argument(
        '--input-file',
        help="Path to the input file to process. It must be a tabbed file with two columns [key, value]")
    args = parser.parse_args()
    df = pd.read_csv(args.input_file, sep="\t", header=None, index_col=0)
    df_dict = df.to_dict()
    print(df_dict.get(1))



if __name__ == '__main__':
    main()