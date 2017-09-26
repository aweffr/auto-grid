import argparse

parser = argparse.ArgumentParser()

parser.add_argument("json")

args = parser.parse_args()

if args.json:
    print args.json
