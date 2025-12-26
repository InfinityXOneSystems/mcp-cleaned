import argparse
import asyncio
from crawler import engine

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--seed", default="crawler/seeds/business_loans.yaml")
    args = p.parse_args()
    asyncio.run(engine.run_from_seed(args.seed))

if __name__ == "__main__":
    main()
