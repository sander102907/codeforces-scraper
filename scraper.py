from bs4 import BeautifulSoup
import requests
from tqdm import tqdm
import random
import os
from selenium import webdriver
import selenium
from selenium.webdriver.support.ui import WebDriverWait
import pandas as pd
import time
from proxies import Proxies

'''
Scraper class responsible for scraping actual contents of the codeforce website
that is not available through the API such as the code of the solutions
'''


class Scraper():
    # Fetch source code of submissions and save to txt (recursive to reselect proxies if needed)
    @staticmethod
    def get_source_code_submissions(proxies, proxy_index, contest_id, submission_ids, pbar, submission_index=0, iterations=1000):
        if iterations > 0:
            # Specify a random user agent
            headers = {'User-Agent': 'anything'}

            # if all proxies have been exhausted, get new list of proxies
            if proxy_index >= len(proxies):
                proxies = Proxies.get_proxies()
                proxy_index = 0

            # Set the proxy for the requests
            proxy_dict = {
                'http': f'{proxies[proxy_index]}',
                'https': f'{proxies[proxy_index]}',
            }

            try:
                # Go over all submissions and make a request to the submission page
                for submission in submission_ids[submission_index:]:
                    response = requests.get(
                        f'https://codeforces.com/contest/{contest_id}/submission/{submission}',
                        timeout=10,
                        headers=headers,
                        proxies=proxy_dict,
                        allow_redirects=False
                    )

                    # Transform to soup object with html parser
                    soup = BeautifulSoup(response.content, 'html.parser')

                    # Find the actual program code on page
                    solution = soup.find(
                        "pre", {"id": "program-source-text"}).text.strip()

                    os.makedirs(
                        f'data/contests_solutions_code/{contest_id}/', exist_ok=True)

                    text_file = open(
                        f'data/contests_solutions_code/{contest_id}/{submission}.txt', "w")
                    text_file.write(solution)
                    text_file.close()


                    # update where we are for if we need to update the proxy and update the progress bar
                    submission_index += 1
                    pbar.update()


            except Exception:
                proxy_index += 1
                iterations -= 1
                Scraper.get_source_code_submissions(proxies, proxy_index, contest_id,
                                submission_ids, pbar, submission_index, iterations)


    @staticmethod
    def get_tests(problem, driver):
        driver.get(f'https://codeforces.com/contest/{problem["contestId"]}/submission/{problem["solutionId"]}')

        try:
            driver.find_element_by_class_name('click-to-view-tests').click()

            WebDriverWait(driver, 5).until(lambda driver: len(driver.find_elements_by_class_name('input')) > 1)
            test_inputs = driver.find_elements_by_class_name('input')[1:]
            test_answers = driver.find_elements_by_class_name('answer')[1:]


            problem_tests = []

            for ans, inp in zip(test_answers, test_inputs):
                problem_tests.append((inp.text, ans.text))

            return problem_tests
        except selenium.common.exceptions.NoSuchElementException:
            # Requests are blocked, try again after 5 mins
            time.sleep(300)
            get_tests(problem, driver)


    @staticmethod
    def get_problem_metadata(problem):
        url = f'https://codeforces.com/contest/{problem["contestId"]}/problem/{problem["problem"]}'
        soup = BeautifulSoup(requests.get(url).content, "html.parser")

        try:
            problem_statement = soup.find('div', {'class': 'problem-statement'})
            problem_statement_children = problem_statement.findChildren(recursive=False)

            text = ''

            for child in problem_statement_children:
                try:
                    for c in child.findChildren(recursive=False):
                        try:
                            div = c.findChildren('div')
                            text += div[0].text.strip() + ': ' + c.find(text=True, recursive=False).strip() + '\n'
                        except Exception:
                            text += c.text.strip() + '\n'
                except Exception:
                    text += child.text.strip() + '\n'

            inputs = [str(inp.find('pre')).replace('<pre>', '').replace('</pre>', '').replace('<br/>', '\n').strip('\n') for inp in soup.find_all('div', {'class': 'input'})]
            outputs = [str(out.find('pre')).replace('<pre>', '').replace('</pre>', '').replace('<br/>', '\n').strip('\n') for out in soup.find_all('div', {'class': 'output'})]

            example_tests = []

            for inp, out in zip(inputs, outputs):
                example_tests.append((inp, out))

            return text.replace('$$$', '$'), example_tests
        except AttributeError:
            print(f'Skipped: {problem["contestId"]} - {problem["problem"]}')
            return ''

    @staticmethod
    def get_problems_data():

         # Get the metadata files to find submission ids to scrape solutions for
        metadata_files = [file for file in os.listdir('data/contests_solutions_metadata') if os.path.isfile(f'data/contests_solutions_metadata/{file}')]

        if len(metadata_files) == 0:
            print('Run "get_solutions_metadata" first to fetch the solutions to scrape before running this function')
            return

        for metadata_file in metadata_files:
            print(f'starting on: {metadata_file}')
            # Open the solutions metadata file where solutions will be coupled to
            data = pd.read_csv(f'data/contests_solutions_metadata/{metadata_file}')

            data = data.groupby(['contestId', 'problem']).first().reset_index()

            tqdm.pandas()
            print('getting problem metadata...')
            data[['problemDescription', 'exampleTests']] = data.progress_apply(Scraper.get_problem_metadata, axis=1, result_type='expand')

            data.to_csv('data/contests_problems/problems_data.csv', index=False)

            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            driver = webdriver.Chrome(options=options)

            print('getting problem tests...')
            data['allTests'] = data.progress_apply(Scraper.get_tests, axis=1, args=(driver,))

            driver.close()


        data.drop(columns=['solutionId', 'programmingLangauge'], inplace=True)

        os.makedirs(f'data/contests_problems/', exist_ok=True)

        data.to_csv('data/contests_problems/problems_data.csv', index=False)