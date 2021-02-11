import json
import requests


class Api():
    def __init__(self):
        self.site = 'https://codeforces.com/api/'

    # Returns a list of submission ids for a contest with the verdict 'OK' (hence they have no errors and solve the problem)
    def get_accepted_submission_ids(self, contestId, accepted_submissions):
        url = f'{self.site}contest.status?contestId={contestId}'

        response = requests.get(url, headers={'User-agent': 'anything'})

        try:
            submissions = response.json()['result']

            for sol in submissions:
                if sol['verdict'] == 'OK':
                    accepted_submissions[sol['id']] = {
                        'contestId': sol['contestId'],
                        'problem': sol['problem']['index'],
                        'programmingLangauge': sol['programmingLanguage']
                    }
        except:
            pass

        return accepted_submissions

    def get_contest_ids(self):
        url = f'{self.site}contest.list'

        response = requests.get(url)

        contests = response.json()['result']

        contest_ids = [
            contest['id'] for contest in contests if contest['phase'] == 'FINISHED']

        return contest_ids
