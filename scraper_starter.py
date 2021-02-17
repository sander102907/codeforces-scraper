from subprocess import run
from time import sleep

'''
 This script will start main.py.
 When an exception happens, the script will be restarted and thus run indefinately until manually stopped
 '''

# Arguments to pass into the run command
arguments = ""

def start_scraper():
    try:
        run(f"python3 main.py {arguments}", shell=True, check=True)
    except Exception as e:
        print(e)
        print('Scraper crashed, restarting....')
        start_scraper()


start_scraper()

