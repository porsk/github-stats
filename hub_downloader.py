from requests import session
from pandas import DataFrame, read_csv
from datetime import datetime
from exceptions import ApiRateLimitError, NotFoundError, BadCredentialsError
from os.path import isdir, join, isfile
from os import makedirs
from shutil import rmtree

TOTAL_CONTRIBUTION_FILE_NAME = 'total_contributions'
WEEKLY_CONTRIBUTIONS_FILE_NAME = 'weekly_contributions'
CODE_FREQUENCY_FILE_NAME = 'code_frequency'
ISSUES_FILE_NAME = 'issues'
STARGAZERS_FILE_NAME = 'stargazers'
CACHE_DIR = 'data'


class Downloader:
    def __init__(self,
                 owner,
                 repo,
                 token='',
                 useCacheIfAvailable=True,
                 verbose=True):
        self.__url = 'https://api.github.com/repos/{}/{}'.format(owner, repo)
        self.__session = session()
        self.__cache_path = join(CACHE_DIR, owner, repo)
        self.__useCache = useCacheIfAvailable
        self.__verbose = verbose

        if not isdir(self.__cache_path):
            makedirs(self.__cache_path)

        if token:
            self.__session.headers.update(
                {'Authorization': 'token {}'.format(token)})

        # checking if the requested repository exists or not
        response = self.__session.get(self.__url)
        if response.ok:
            self.__log(
                'The maximum number of requests you are permitted to make per hour: {}'
                .format(response.headers['X-RateLimit-Limit']))
            self.__log(
                'The number of requests remaining in the current rate limit window: {}'
                .format(response.headers['X-RateLimit-Remaining']))
        else:
            if (response.status_code == 403):
                raise ApiRateLimitError(
                    'API rate limit exceeded. Try to specifyan OAuth token to increase your rate limit.'
                )
            if (response.status_code == 404):
                raise NotFoundError(
                    "Repository '{}' of user '{}' not found.".format(
                        repo, owner))
            if (response.status_code == 401):
                raise BadCredentialsError(
                    'Bad credentials were provided for the API.')

            raise Exception(response.json()['message'])

    def __save_cache(self, dataFrame, file_name):
        dataFrame.to_csv(join(self.__cache_path, '{}.csv'.format(file_name)),
                         sep='\t',
                         encoding='utf-8')

    def __read_cache(self, file_name):
        return read_csv(join(self.__cache_path, '{}.csv'.format(file_name)),
                        sep='\t',
                        encoding='utf-8',
                        index_col=0)

    def __is_cache_available(self, file_name):
        return isfile(join(self.__cache_path, '{}.csv'.format(file_name)))

    def __log(self, text, end='\n'):
        if self.__verbose:
            print(text, end)

    def delete_cache(self):
        rmtree(self.__cache_path)
        makedirs(self.__cache_path)

    def get_contributors_statistic(self):
        '''Get contributors list with additions, deletions, and commit counts'''

        if self.__useCache and self.__is_cache_available(
                TOTAL_CONTRIBUTION_FILE_NAME) and self.__is_cache_available(
                    WEEKLY_CONTRIBUTIONS_FILE_NAME):
            return self.__read_cache(
                TOTAL_CONTRIBUTION_FILE_NAME), self.__read_cache(
                    WEEKLY_CONTRIBUTIONS_FILE_NAME)

        data = self.__session.get('{}/stats/contributors'.format(
            self.__url)).json()

        total_contributions = []
        weekly_contributions = []

        for item in data:
            total_contributions.append({
                'commits': item['total'],
                'user': item['author']['login']
            })

            for week in item['weeks']:
                weekly_contributions.append({
                    'user':
                    item['author']['login'],
                    'week_unix_ts':
                    week['w'],
                    'date':
                    datetime.fromtimestamp(week['w']).date(),
                    'additions':
                    week['a'],
                    'deletions':
                    week['d'],
                    'commits':
                    week['c'],
                })

        self.total_contributions = DataFrame(total_contributions,
                                             columns=['user', 'commits'])
        self.__save_cache(self.total_contributions,
                          TOTAL_CONTRIBUTION_FILE_NAME)

        self.weekly_contributions = DataFrame(weekly_contributions,
                                              columns=[
                                                  'user', 'week_unix_ts',
                                                  'date', 'additions',
                                                  'deletions', 'commits'
                                              ])
        self.__save_cache(self.weekly_contributions,
                          WEEKLY_CONTRIBUTIONS_FILE_NAME)

        return self.total_contributions, self.weekly_contributions

    def get_code_frequency_statistic(self):
        '''Returns a weekly aggregate of the number of additions and deletions pushed to a repository'''
        if self.__useCache and self.__is_cache_available(
                CODE_FREQUENCY_FILE_NAME):
            return self.__read_cache(CODE_FREQUENCY_FILE_NAME)

        data = self.__session.get('{}/stats/code_frequency'.format(
            self.__url)).json()

        self.code_frequency = DataFrame(
            data, columns=['week_unix_ts', 'additions', 'deletions'])
        self.code_frequency['date'] = self.code_frequency.apply(
            lambda row: datetime.fromtimestamp(row.week_unix_ts).date(),
            axis=1)
        self.__save_cache(self.code_frequency, CODE_FREQUENCY_FILE_NAME)

        return self.code_frequency

    def get_user_data(self, username):
        '''Provides publicly available information about someone with a GitHub account'''
        return self.__session.get(
            'https://api.github.com/users/{}'.format(username)).json()

    def get_issues(self):
        '''List issues in a repository'''
        if self.__useCache and self.__is_cache_available(ISSUES_FILE_NAME):
            return self.__read_cache(ISSUES_FILE_NAME)

        self.__log('Fetching repository issues ', end='')

        page = 1
        issues = []

        while (True):
            self.__log('.', end='')

            data = self.__session.get('{}/issues?per_page=100&page={}'.format(
                self.__url, page)).json()

            if len(data) == 0:
                break

            for issue in data:
                issues.append({
                    'id':
                    issue['id'],
                    'state':
                    issue['state'],
                    'created_at':
                    datetime.strptime(issue['created_at'],
                                      '%Y-%m-%dT%H:%M:%SZ').date()
                })

            page = page + 1

        self.__log('.')

        self.issues = DataFrame(issues, columns=['id', 'state', 'created_at'])
        self.__save_cache(self.issues, ISSUES_FILE_NAME)

        return self.issues

    def get_stargazers(self):
        '''Lists the people that have starred the repository'''
        if self.__useCache and self.__is_cache_available(STARGAZERS_FILE_NAME):
            return self.__read_cache(STARGAZERS_FILE_NAME)

        self.__log('Fetching stargazers ', end='')

        page = 1
        stargazers = []

        while (True):
            self.__log('.', end='')

            data = self.__session.get(
                '{}/stargazers?per_page=100&page={}'.format(self.__url, page),
                headers={
                    'Accept': 'application/vnd.github.v3.star+json'
                }).json()

            if len(data) == 0:
                break

            for stargazer in data:
                stargazers.append({
                    'user':
                    stargazer['user']['login'],
                    'starred_at':
                    datetime.strptime(stargazer['starred_at'],
                                      '%Y-%m-%dT%H:%M:%SZ').date()
                })

            page = page + 1

        self.__log('.')

        self.stargazers = DataFrame(stargazers, columns=['user', 'starred_at'])
        self.__save_cache(self.stargazers, STARGAZERS_FILE_NAME)

        return self.stargazers