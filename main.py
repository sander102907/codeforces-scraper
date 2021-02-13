from scraper import Scraper
from api import Api
import pandas as pd
from tqdm import tqdm
import threading
import math
from Proxy_List_Scrapper import Scrapper, Proxy, ScrapperException
import os


def main():
    # get_solutions(40)
    scraper = Scraper()
    scraper.get_problems_data()


# Write solution metadata to csv at the output folder per 200 competitions (contest id, submission id, programming language)
def get_solutions_metadata(output_folder):
    api = Api()
    submissions_data = {}

    # Get all the contest ids first (so ids of all competitions)
    contest_ids = api.get_contest_ids()

    # Iterate over each contest
    for index, contest_id in tqdm(enumerate(contest_ids), total=len(contest_ids)):
        # Get all submission metadata of the contest
        submissions_data = api.get_accepted_submission_ids(
            contest_id, submissions_data)

        # Save the metadata to file every 200 competitions due to memory constraints
        if index % 200 == 0:
            solutions_df = pd.DataFrame(submissions_data).transpose()
            solutions_df.index.name = 'solutionId'
            solutions_df.to_csv(f'data/solutions_{index}.csv')
            del solutions_df
            submissions_data = {}

    solutions_df = pd.DataFrame(submissions_data).transpose()
    solutions_df.index.name = 'solutionId'
    solutions_df.to_csv(f'{output_folder}/solutions_{index}.csv')
    del solutions_df
    del submissions_data


# Get solutions code and save them to txt in the data/contests_solutions directory (one directory per contest will be created)
def get_solutions(amt_threads):
    scraper = Scraper()

    # Get all contests that have already been scraped
    scraped_contests = []

    for _,dirs,_ in os.walk('data/contests_solutions'):
        scraped_contests += [int(dir) for dir in dirs]

    # Get the metadata files to find submission ids to scrape solutions for
    metadata_files = [file for file in os.listdir('data') if os.path.isfile(f'data/{file}')]

    for metadata_file in metadata_files:
        # Open the solutions metadata file where solutions will be coupled to
        solutions_df = pd.read_csv(f'data/{metadata_file}')

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

            proxies = scraper.get_proxies()

            # Progress bar to indicate current progress and speed
            pbar = tqdm(total=len(contest_submissions))

            for index in range(0, len(contest_submissions), submissions_per_thread):
                # Get solutions for the contests from the scraper

                threads.append(
                    threading.Thread(
                        target=scraper.get_source_code_submissions,
                        args=(contest,
                            contest_submissions[index: index + submissions_per_thread], proxies, pbar,)
                    )
                )

            for t in threads:
                t.start()

            for t in threads:
                t.join()


if __name__ == "__main__":
    main()
