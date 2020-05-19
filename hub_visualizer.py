import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from pandas import to_datetime
from os import getenv
from hub_downloader import Downloader


class Visualizer:
    '''Visualizer class for showing relevant charts and plots about a GitHub repository using the Downloader class.'''
    def __init__(self, owner, repo, useCache=True, figsize=(12, 7)):
        self.__figsize = figsize
        self.__owner = owner
        self.__repo = repo

        # uses the Downloader for getting data about a repository
        self.__downloader = Downloader(owner, repo,
                                       getenv('GITHUB_OAUTH_TOKEN'), useCache,
                                       False)

    def __fig_title(self, title):
        '''Extends the figure title with the name of the owner and the repository.'''
        return f'{title} [{self.__owner}/{self.__repo}]'

    def lines_over_time(self):
        '''Plots two graphs, one showing the total lines of code over time,
        the other the additions and deletions over time using line charts.'''

        code_frequency = self.__downloader.get_code_frequency_statistic()

        # parsing necessary data
        dates = code_frequency['date'].tolist()
        date_objects = [
            datetime.strptime(date, '%Y-%m-%d').date() for date in dates
        ]

        additions = code_frequency['additions'].to_numpy()
        deletions = code_frequency['deletions'].to_numpy()
        total = additions + deletions
        cum_total = np.cumsum(total)

        # total lines over time - line chart
        plt.figure(figsize=self.__figsize)

        plt.plot(date_objects, cum_total)
        plt.fill_between(date_objects, cum_total, alpha=0.2)

        plt.title(self.__fig_title('Total lines of code over time'))
        plt.ylabel('Lines')

        # additions and deletions over time - line chart
        plt.figure(figsize=self.__figsize)

        plt.plot(date_objects, additions, 'g-')
        plt.fill_between(date_objects, additions, alpha=0.2, color='g')
        plt.plot(date_objects, deletions, 'r-')
        plt.fill_between(date_objects, deletions, alpha=0.2, color='r')

        plt.title(self.__fig_title('Additions and deletions over time'))
        plt.ylabel('Lines')
        plt.show()

    def commits_by_author(self, limit=12):
        '''Plots a pie chart showing the top contributors based on the commit count.
        With the optional limit parameter the number of shown contributor can be modified.'''

        total_contributions, _ = self.__downloader.get_contributors_statistic()

        # overriding limit if it is out of bounds
        if limit > len(total_contributions.index):
            limit = len(total_contributions.index)

        if limit < 2:
            limit = 10

        # parsing data
        commits = total_contributions['commits'][-limit:].to_numpy()
        users = total_contributions['user'][-limit:].to_numpy()

        rest = sum(total_contributions['commits'][:-limit].to_numpy())

        commits = np.concatenate([[rest], commits])
        users = np.concatenate([['Others'], users])

        # commits by author - pie chart
        fig = plt.figure(figsize=self.__figsize)
        plt.pie(commits,
                labels=users,
                autopct='%1.1f%%',
                startangle=90,
                pctdistance=0.85,
                explode=np.full(len(commits), 0.05))

        centre_circle = plt.Circle((0, 0), 0.75, fc='white')
        fig = plt.gcf()
        fig.gca().add_artist(centre_circle)

        plt.tight_layout()
        plt.title(self.__fig_title('Commits by authors'))
        plt.show()

    def stargazer_history(self):
        '''Plots two line charts, one showing the number of stars on the repo over time and 
        the other showing the number of new stars month by month.'''

        stargazers = self.__downloader.get_stargazers()

        # parsing data
        stargazers_by_day = stargazers.groupby('starred_at',
                                               as_index=False).count()
        stargazers_by_day.columns = ['date', 'stargazer_count']

        # aggregating by weeks
        stargazers_by_week = stargazers_by_day
        stargazers_by_week['date'] = to_datetime(stargazers_by_week['date'])
        stargazers_by_week.index = stargazers_by_week['date']
        stargazers_by_week = stargazers_by_week.resample('M').sum()
        stargazers_by_week.reset_index(level=0, inplace=True)

        stargazers_by_day['cum_stargazers'] = stargazers_by_day[
            'stargazer_count'].cumsum()

        cum_stargazers = stargazers_by_day['cum_stargazers'].to_numpy()
        dates = stargazers_by_day['date'].to_numpy()

        # number of stars over time - line chart
        plt.figure(figsize=self.__figsize)
        plt.plot(dates, cum_stargazers, 'y-')
        plt.fill_between(dates, cum_stargazers, alpha=0.2, color='y')

        plt.title(self.__fig_title('Number of stars over time'))
        plt.ylabel('Stars')

        stargazer_count = stargazers_by_week['stargazer_count'].to_numpy()
        dates = stargazers_by_week['date'].to_numpy()

        # new stars aggregated by months - line chart
        plt.figure(figsize=self.__figsize)
        plt.plot(dates, stargazer_count, 'y-')
        plt.fill_between(dates, stargazer_count, alpha=0.2, color='y')

        plt.title(self.__fig_title('New stars aggregated by months'))
        plt.ylabel('Stars')
        plt.show()

    def commit_activity(self):
        '''Plots a grid/mash plot about the commit activity in the repository during the last year.'''

        commit_activity = self.__downloader.get_commit_activity()

        # parsing data
        grid = commit_activity[[
            'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'
        ]].to_numpy()
        grid = np.rot90(grid)

        # commit activity in the last year - mash/grid plot
        fig, ax = plt.subplots(1, 1, figsize=(20, 3))

        # plotting the grid itself and the colorbar next to it
        c = ax.pcolor(grid,
                      cmap='Blues',
                      edgecolor="lightgray",
                      vmin=0,
                      vmax=max(1, np.max(grid)))
        cbar = fig.colorbar(c, ax=ax)
        cbar.ax.set_ylabel('Number of commints')

        # setting the labels and tick positions
        ax.set_yticks(np.arange(grid.shape[0]) + 0.5)
        ax.set_yticklabels(['Sun', 'Sat', 'Fri', 'Thu', 'Wed', 'Tue', 'Mon'])
        ax.set_title(self.__fig_title('Commit activity in the last year'))

        ax.set_xlabel('Weeks')

        plt.show()