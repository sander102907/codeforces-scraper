import urllib.request
from Proxy_List_Scrapper import Scrapper, Proxy, ScrapperException
from bs4 import BeautifulSoup
import requests
import json

class Proxies():
    # Get a random list of proxies
    @staticmethod
    def get_proxies():
        print('getting proxies...')
        urls = ["https://free-proxy-list.net/", "https://www.sslproxies.org/", "https://free-proxy-list.net/anonymous-proxy.html",
                "https://free-proxy-list.net/uk-proxy.html", "https://www.us-proxy.org/"]
        # # get the HTTP response and construct soup object
        proxies = []

        for url in urls:
            try:
                soup = BeautifulSoup(requests.get(url).content, "html.parser")

                # Find the rows of the tables on the page
                for row in soup.find("table", attrs={"id": "proxylisttable"}).find_all("tr")[1:]:
                    tds = row.find_all("td")
                    # Check if the proxy is https compatible
                    if tds[6].text.strip() == 'yes':
                        # Find the ip and host and add it to the list of proxies
                        ip = tds[0].text.strip()
                        port = tds[1].text.strip()
                        host = f"{ip}:{port}"
                        proxies.append(host)
            except Exception:
                continue

        try:
            url = "https://api.proxyscrape.com/?request=getproxies&timeout=500"
            response =  urllib.request.urlopen(url).read().decode('utf-8').split("\r\n")
            proxies += [i for i in response if i]
        except urllib.error.HTTPError:
            pass

        try:
            scrapper = Scrapper(category='ALL', print_err_trace=False)

            proxies += [f'{proxy.ip}:{proxy.port}' for proxy in scrapper.getProxies().proxies]
        except Exception:
            pass

        try:
            url = "http://spys.me/proxy.txt"
            response =  urllib.request.urlopen(url).read().decode('utf-8').split("\n\n")[1].split("\r")[:-1][0].split("\n")
            response = [i for i in response if i]
            for line in response:
                proxies.append(line.split(" ")[0])
        except Exception:
            pass


        try:
            url = "https://www.proxy-list.download/api/v1/get?type=http"

            response =  urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib.request.urlopen(response).read().decode('utf-8').split("\r\n")
            proxies += [i for i in response if i]
        except Exception:
            pass

        try:
            url = "https://www.proxyscan.io/api/proxy?last_check=3800&limit=20&type=https"

            response = json.loads(urllib.request.urlopen(url).read().decode('utf-8'))
            for proxy in response:
                proxies.append('{}:{}'.format(proxy["Ip"], proxy["Port"]))
        except Exception:
            pass

        # Make sure to only return a list of unique proxies
        return list(set(proxies))
