from bs4 import BeautifulSoup
import requests
from tqdm import tqdm
import random
import os
from Proxy_List_Scrapper import Scrapper, Proxy, ScrapperException
import urllib.request
import json


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
    def get_request(self, proxies, proxy_index, contest_id, submission_ids, submission_index, pbar):
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
            self.get_request(proxies, proxy_index, contest_id,
                             submission_ids, submission_index, pbar)

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
