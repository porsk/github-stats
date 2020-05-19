from requests import session
from pandas import DataFrame, read_csv
from datetime import datetime
from os import makedirs, path
from os.path import isdir, isfile
from shutil import rmtree
from exceptions import ApiRateLimitError, NotFoundError, BadCredentialsError

TOTAL_CONTRIBUTION_FILE_NAME = 'total_contributions'
WEEKLY_CONTRIBUTIONS_FILE_NAME = 'weekly_contributions'
CODE_FREQUENCY_FILE_NAME = 'code_frequency'
ISSUES_FILE_NAME = 'issues'
STARGAZERS_FILE_NAME = 'stargazers'
COMMIT_ACTIVITY_FILE_NAME = 'commit_activity'
CACHE_DIR = 'data'


class Downloader:
    '''Downloader class for fetching, pre-process and caching data about a given github repository.'''
    def __init__(self,
                 owner,
                 repo,
                 token='',
                 useCacheIfAvailable=True,
                 verbose=True):
        self.__url = f'https://api.github.com/repos/{owner}/{repo}'
        self.__repo = repo
        self.__owner = owner
        self.__session = session()
        self.__cache_path = path.join(CACHE_DIR, owner, repo)
        self.__useCache = useCacheIfAvailable
        self.__verbose = verbose

        # create cache directory if does not exists yet
        if not isdir(self.__cache_path):
            makedirs(self.__cache_path)

        # if the user provided a GitHub Oauth token then the downloader will use it in every request
        if token:
            self.__session.headers.update({f'Authorization': 'token {token}'})

        # checking if the requested repository exists
        response = self.__session.get(self.__url)

        if response.ok:
            self.__log(
                f'The maximum number of requests you are permitted to make per hour: {response.headers["X-RateLimit-Limit"]}'
            )
            self.__log(
                f'The number of requests remaining in the current rate limit window: {response.headers["X-RateLimit-Remaining"]}'
            )
        else:
            self.__rasie_error(response)

    def __rasie_error(self, response):
        '''Raises a proper error in case of known problems or a general exception in case of unknown problem.'''

        if response.status_code == 403:
            raise ApiRateLimitError(
                'API rate limit exceeded. Try to specify an OAuth token to increase your rate limit.'
            )

        if response.status_code == 404:
            raise NotFoundError(
                f"Repository '{self.__repo}' of user '{self.__owner}' not found."
            )

        if response.status_code == 401:
            raise BadCredentialsError(
                'Bad credentials were provided for the API.')

        raise Exception(response.json()['message'])

    def __call_api(self, path, headers={}):
        response = self.__session.get(f'{self.__url}/{path}', headers=headers)

        if response.ok:
            return response.json()
        else:
            self.__rasie_error(response)

    def __save_cache(self, dataFrame, file_name):
        '''Method for saving (caching) a dataframe into a given file.'''
        dataFrame.to_csv(path.join(self.__cache_path, f'{file_name}.csv'),
                         sep='\t',
                         encoding='utf-8')

    def __read_cache(self, file_name):
        '''Method for reading the cahced data into a pandas dataframe.'''
        return read_csv(path.join(self.__cache_path, f'{file_name}.csv'),
                        sep='\t',
                        encoding='utf-8',
                        index_col=0)

    def __is_cache_available(self, file_name):
        '''Checks whether there is cached data available or not.'''
        return isfile(path.join(self.__cache_path, f'{file_name}.csv'))

    def __log(self, text, end='\n'):
        '''Prints out the message of the downloader is in verbose mode.'''
        if self.__verbose:
            print(text, end=end)

    def delete_cache(self):
        '''Deletes all cache of the current repository.'''
        rmtree(self.__cache_path)
        makedirs(self.__cache_path)

    def get_contributors_statistic(self):
        '''Get contributors list with additions, deletions, and commit counts.'''

        # return cached data if it is available and requested by the user
        if self.__useCache and self.__is_cache_available(
                TOTAL_CONTRIBUTION_FILE_NAME) and self.__is_cache_available(
                    WEEKLY_CONTRIBUTIONS_FILE_NAME):
            return self.__read_cache(
                TOTAL_CONTRIBUTION_FILE_NAME), self.__read_cache(
                    WEEKLY_CONTRIBUTIONS_FILE_NAME)

        data = self.__call_api('stats/contributors')

        total_contributions = []
        weekly_contributions = []

        # parsing data into dataframes
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
        '''Returns a weekly aggregate of the number of additions and deletions pushed to a repository.'''
        if self.__useCache and self.__is_cache_available(
                CODE_FREQUENCY_FILE_NAME):
            return self.__read_cache(CODE_FREQUENCY_FILE_NAME)

        data = self.__call_api('stats/code_frequency')

        self.code_frequency = DataFrame(
            data, columns=['week_unix_ts', 'additions', 'deletions'])
        self.code_frequency['date'] = self.code_frequency.apply(
            lambda row: datetime.fromtimestamp(row.week_unix_ts).date(),
            axis=1)
        self.__save_cache(self.code_frequency, CODE_FREQUENCY_FILE_NAME)

        return self.code_frequency

    def get_issues(self):
        '''List issues in a repository.'''

        if self.__useCache and self.__is_cache_available(ISSUES_FILE_NAME):
            return self.__read_cache(ISSUES_FILE_NAME)

        self.__log('Fetching repository issues ', end='')

        page = 1
        issues = []

        while (True):
            self.__log('.', end='')

            data = self.__call_api(f'issues?per_page=100&page={page}')

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

    def get_commit_activity(self):
        '''Returns the last year of commit activity grouped by week.'''

        if self.__useCache and self.__is_cache_available(
                COMMIT_ACTIVITY_FILE_NAME):
            return self.__read_cache(COMMIT_ACTIVITY_FILE_NAME)

        data = self.__call_api('stats/commit_activity')

        commit_activity = []

        for item in data:
            commit_activity.append({
                'week_unix_ts': item['week'],
                'mon': item['days'][1],
                'tue': item['days'][2],
                'wed': item['days'][3],
                'thu': item['days'][4],
                'fri': item['days'][5],
                'sat': item['days'][6],
                'sun': item['days'][0],
            })

        self.commit_activity = DataFrame(commit_activity,
                                         columns=[
                                             'week_unix_ts', 'mon', 'tue',
                                             'wed', 'thu', 'fri', 'sat', 'sun'
                                         ])
        self.commit_activity['week'] = self.commit_activity.apply(
            lambda row: datetime.fromtimestamp(row.week_unix_ts).date(),
            axis=1)

        self.__save_cache(self.commit_activity, COMMIT_ACTIVITY_FILE_NAME)

        return self.commit_activity

    def get_stargazers(self):
        '''Lists the people that have starred the repository.'''

        if self.__useCache and self.__is_cache_available(STARGAZERS_FILE_NAME):
            return self.__read_cache(STARGAZERS_FILE_NAME)

        self.__log('Fetching stargazers ', end='')

        page = 1
        stargazers = []

        while (True):
            self.__log('.', end='')

            data = self.__call_api(
                f'stargazers?per_page=100&page={page}',
                {'Accept': 'application/vnd.github.v3.star+json'})

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