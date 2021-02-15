import json
import requests

class Api():
    # Returns a list of submission ids for a contest with the verdict 'OK' (hence they have no errors and solve the problem)
    @staticmethod
    def get_accepted_submission_ids(contest_id, accepted_submissions):
        url = f'https://codeforces.com/api/contest.status?contestId={contest_id}'

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
        except Exception:
            pass

        return accepted_submissions

    @staticmethod
    def get_contest_ids():
        url = f'https://codeforces.com/api/contest.list'

        response = requests.get(url)

        contests = response.json()['result']

        contest_ids = [
            contest['id'] for contest in contests if contest['phase'] == 'FINISHED']

        return contest_ids
