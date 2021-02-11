from bs4 import BeautifulSoup
import requests
from tqdm import tqdm
import random
from fake_useragent import UserAgent


'''
Scraper class responsible for scraping actual contents of the codeforce website
that is not available through the API such as the code of the solutions
'''


class Scraper():
    # Function to get source code of submissions
    def get_source_code_submissions(self, submissions_data, pbar):
        # Get list of proxies to work with to avoid getting temporarily blocked
        proxies = self.get_proxies()
        proxy_index = 0

        self.get_request(
            proxies, 0, submissions_data, 0, pbar)

    # Fetch the actual code via requests (recursive to reselect proxies if needed)
    def get_request(self, proxies, proxy_index, submissions_data, submission_index, pbar):
        # Specify a random user agent
        ua = UserAgent()
        headers = {'User-Agent': ua.random}

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
            for submission in submissions_data[submission_index:].iterrows():
                response = requests.get(
                    f'https://codeforces.com/contest/{submission[1]["contestId"]}/submission/{submission[1]["solutionId"]}',
                    timeout=2,
                    headers=headers,
                    proxies=proxy_dict,
                    allow_redirects=False
                )

                # Transform to soup object with html parser
                soup = BeautifulSoup(response.content, 'html.parser')

                # Find the actual program code on page
                solution = soup.find(
                    "pre", {"id": "program-source-text"}).text.strip()

                # Set the code at the correct row of the CSV
                submissions_data.loc[
                    (submissions_data['solutionId']
                     == submission[1]["solutionId"])
                    & (submissions_data['contestId'] == submission[1]["contestId"]),
                    'solution'] = solution

                # update where we are for if we need to update the proxy and update the progress bar
                submission_index += 1
                pbar.update()

            # Save the output to csv
            output.to_csv(
                f'data/contests_solutions/{contest}.csv', index=False)

            print(f'Solutions for contest: {contest} collected and saved')

        except Exception as e:
            proxy_index += 1
            self.get_request(proxies, proxy_index,
                             submissions_data, submission_index, pbar)

    # Get a random list of proxies
    def get_proxies(self):
        url = "https://free-proxy-list.net/"
        # get the HTTP response and construct soup object
        soup = BeautifulSoup(requests.get(url).content, "html.parser")
        proxies = []

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

        return proxies
