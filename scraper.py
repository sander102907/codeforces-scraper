from bs4 import BeautifulSoup
import requests
from tqdm import tqdm
import random
import os
from Proxy_List_Scrapper import Scrapper, Proxy, ScrapperException
import urllib.request
import json
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
import pandas as pd

'''
Scraper class responsible for scraping actual contents of the codeforce website
that is not available through the API such as the code of the solutions
'''


class Scraper():
    # Function to get source code of submissions
    def get_source_code_submissions(self, contest_id, submission_ids, proxies, pbar):
        # Get list of proxies to work with to avoid getting temporarily blocked
        proxy_index = random.randrange(0, len(proxies))

        self.get_request(
            proxies, proxy_index, contest_id, submission_ids, 0, pbar)

    # Fetch the actual code via requests (recursive to reselect proxies if needed)
    def get_request(self, proxies, proxy_index, contest_id, submission_ids, submission_index, pbar, iterations=10000):
        if iterations > 0:
            # Specify a random user agent
            headers = {'User-Agent': 'anything'}

            # if all proxies have been exhausted, get new list of proxies
            if proxy_index >= len(proxies):
                proxies = self.get_proxies()
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
                        f'data/contests_solutions/{contest_id}/', exist_ok=True)

                    text_file = open(
                        f'data/contests_solutions/{contest_id}/{submission}.txt', "w")
                    text_file.write(solution)
                    text_file.close()


                    # update where we are for if we need to update the proxy and update the progress bar
                    submission_index += 1
                    pbar.update()


            except Exception:
                proxy_index += 1
                iterations -= 1
                self.get_request(proxies, proxy_index, contest_id,
                                submission_ids, submission_index, pbar, iterations)

    # Get a random list of proxies
    def get_proxies(self):
        print('getting proxies...')
        urls = ["https://free-proxy-list.net/", "https://www.sslproxies.org/", "https://free-proxy-list.net/anonymous-proxy.html",
                "https://free-proxy-list.net/uk-proxy.html", "https://www.us-proxy.org/"]
        # # get the HTTP response and construct soup object
        proxies = []

        for url in urls:
            soup = BeautifulSoup(requests.get(url).content, "html.parser")

            # Find the rows of the tables on the page
            for row in soup.find("table", attrs={"id": "proxylisttable"}).find_all("tr")[1:]:
                tds = row.find_all("td")
                try:
                    # Check if the proxy is https compatible
                    if tds[6].text.strip() == 'yes':
                        # Find the ip and host and add it to the list of proxies
                        ip = tds[0].text.strip()
                        port = tds[1].text.strip()
                        host = f"{ip}:{port}"
                        proxies.append(host)
                except IndexError:
                    continue

        url = "https://api.proxyscrape.com/?request=getproxies&timeout=500"
        response =  urllib.request.urlopen(url).read().decode('utf-8').split("\r\n")
        proxies += [i for i in response if i]

        scrapper = Scrapper(category='ALL', print_err_trace=False)

        proxies += [f'{proxy.ip}:{proxy.port}' for proxy in scrapper.getProxies().proxies]

        url = "http://spys.me/proxy.txt"
        response =  urllib.request.urlopen(url).read().decode('utf-8').split("\n\n")[1].split("\r")[:-1][0].split("\n")
        response = [i for i in response if i]
        for line in response:
            proxies.append(line.split(" ")[0])


        url = "https://www.proxy-list.download/api/v1/get?type=http"

        response =  urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(response).read().decode('utf-8').split("\r\n")
        proxies += [i for i in response if i]

        url = "https://www.proxyscan.io/api/proxy?last_check=3800&limit=20&type=https"

        response = json.loads(urllib.request.urlopen(url).read().decode('utf-8'))
        for proxy in response:
            proxies.append('{}:{}'.format(proxy["Ip"], proxy["Port"]))

        return list(set(proxies))


    def get_tests(self, problem, driver):
        driver.get(f'https://codeforces.com/contest/{problem["contestId"]}/submission/{problem["solutionId"]}')

        driver.find_element_by_class_name('click-to-view-tests').click()

        WebDriverWait(driver, 5).until(lambda driver: len(driver.find_elements_by_class_name('input')) > 1)
        test_inputs = driver.find_elements_by_class_name('input')[1:]
        test_answers = driver.find_elements_by_class_name('answer')[1:]


        problem_tests = []

        for ans, inp in zip(test_answers, test_inputs):
            problem_tests.append((inp.text, ans.text))

        return problem_tests


    def get_problem_metadata(self, problem):
        url = f'https://codeforces.com/contest/{problem["contestId"]}/problem/{problem["problem"]}'
        soup = BeautifulSoup(requests.get(url).content, "html.parser")

        problem_statement = soup.find('div', {'class': 'problem-statement'})
        problem_statement_children = problem_statement.findChildren(recursive=False)

        text = ''

        try:
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

    def get_problems_data(self):

         # Get the metadata files to find submission ids to scrape solutions for
        metadata_files = [file for file in os.listdir('data') if os.path.isfile(f'data/{file}')]

        for metadata_file in metadata_files:
            print(f'starting on: {metadata_file}')
            # Open the solutions metadata file where solutions will be coupled to
            data = pd.read_csv(f'data/{metadata_file}')

            data = data.groupby(['contestId', 'problem']).first().reset_index()

            tqdm.pandas()
            print('getting problem metadata...')
            data[['problemDescription', 'exampleTests']] = data.progress_apply(self.get_problem_metadata, axis=1, result_type='expand')

            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            driver = webdriver.Chrome(options=options)

            print('getting problem tests...')
            data['allTests'] = data.progress_apply(self.get_tests, axis=1, args=(driver,))

            driver.close()


        data.drop(columns=['solutionId', 'programmingLangauge'], inplace=True)

        data.to_csv('data/contests_problems/problems_data.csv', index=False)