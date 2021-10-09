from scraper import Scraper
from api import Api
from proxies import Proxies
import pandas as pd
from tqdm import tqdm
import threading
import math
import os
import random
import sys
import numpy as np

def main(args):
    if 'get_solutions_metadata' in args:
        get_solutions_metadata()
    elif 'get_solutions' in args:
        if len(args) > 1:
            try:
                amt_threads = int(args[1])
                get_solutions(amt_threads)
            except Exception:
                print('Please input the number of threads to fetch solutions as the second argument')
        else:
            get_solutions()
    elif 'get_problems_data' in args:
        Scraper.get_problems_data()
    elif 'merge_solutions_metadata_code' in args:
        merge_solutions_metadata_code()
    else:
        # Run this method by default
        get_solutions()


# Write solution metadata to csv at the output folder per 200 competitions (contest id, submission id, programming language)
def get_solutions_metadata():
    submissions_data = {}

    # Get all the contest ids first (so ids of all competitions)
    contest_ids = Api.get_contest_ids()

    # Create folder to save data if it does not exist yet
    os.makedirs(f'data/contests_solutions_metadata', exist_ok=True)

    # Iterate over each contest
    for index, contest_id in tqdm(enumerate(contest_ids), total=len(contest_ids)):
        # Get all submission metadata of the contest
        submissions_data = Api.get_accepted_submission_ids(
            contest_id, submissions_data)

        # Save the metadata to file every 200 competitions due to memory constraints
        if index % 200 == 0 and index > 0:
            solutions_df = pd.DataFrame(submissions_data).transpose()
            solutions_df.index.name = 'solutionId'
            solutions_df.to_csv(f'data/contests_solutions_metadata/solutions_{index}.csv')
            del solutions_df
            submissions_data = {}

    solutions_df = pd.DataFrame(submissions_data).transpose()
    solutions_df.index.name = 'solutionId'
    solutions_df.to_csv(f'data/contests_solutions_metadata/solutions_{index}.csv')
    del solutions_df
    del submissions_data


# Get solutions code and save them to txt in the data/contests_solutions directory (one directory per contest will be created)
def get_solutions(amt_threads=40):
    # Get all contests that have already been scraped
    scraped_contests = []

    for _,dirs,_ in os.walk('data/contests_solutions_code'):
        scraped_contests += [int(dir) for dir in dirs]

    # Get the metadata files to find submission ids to scrape solutions for
    metadata_files = [file for file in os.listdir('data/contests_solutions_metadata') if os.path.isfile(f'data/contests_solutions_metadata/{file}')]

    if len(metadata_files) == 0:
        print('Run "get_solutions_metadata" first to fetch the solutions to scrape before running this function')

    for metadata_file in metadata_files:
        # Open the solutions metadata file where solutions will be coupled to
        solutions_df = pd.read_csv(f'data/contests_solutions_metadata/{metadata_file}')

        # Get all unique contests in this dataset that are not scraped yet
        contests = list(solutions_df[~solutions_df['contestId'].isin(scraped_contests)]['contestId'].unique())

        for contest in contests:
            print(f'starting with contest {contest}...')
            contest_submissions = solutions_df[solutions_df['contestId']
                                            == contest]['solutionId']

            # Work with amt of threads to parallelize the requests
            threads = []

            submissions_per_thread = math.ceil(
                len(contest_submissions)/amt_threads)

            proxies = Proxies.get_proxies()

            # Progress bar to indicate current progress and speed
            pbar = tqdm(total=len(contest_submissions))

            for index in range(0, len(contest_submissions), submissions_per_thread):
                # Let every thread start with a random proxy to spread the search space
                proxy_index = random.randrange(0, len(proxies))

                # Get solutions for the contests from the scraper
                threads.append(
                    threading.Thread(
                        target=Scraper.get_source_code_submissions,
                        args=(proxies, proxy_index, contest, contest_submissions[index: index + submissions_per_thread], pbar,)
                    )
                )

            for t in threads:
                t.start()

            for t in threads:
                t.join()

def merge_solutions_metadata_code():
     # Get the metadata files to find submission ids to scrape solutions for
    metadata_files = [file for file in os.listdir('data/contests_solutions_metadata') if os.path.isfile(f'data/contests_solutions_metadata/{file}')]

    if len(metadata_files) == 0:
        print('Run "get_solutions_metadata" first to fetch the solutions to scrape before running this function')

    for metadata_file in metadata_files:
        # Open the solutions metadata file where solutions will be coupled to
        data = pd.read_csv(f'data/contests_solutions_metadata/{metadata_file}')

        def get_solution_code(solution):
            folder = f'data/contests_solutions_code/{solution["contestId"]}'
            try:
                return open(f'{folder}/{solution["solutionId"]}.txt', 'r').read()
            except Exception:
                return np.nan

        tqdm.pandas()
        data['solution'] = data.progress_apply(get_solution_code, axis=1)
        data.to_csv(f'data/contests_solutions/{metadata_file}', index=False)


if __name__ == "__main__":
    args = sys.argv[1:]
    main(args)
