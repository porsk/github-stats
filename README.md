# GitHub statistics

This project downloads data about a given public GitHub repository and helps to visualize some statistics with different plots. The data is downloaded from the official [GitHub API](https://developer.github.com/v3/)

## Usage

1. Install the dependencies with `pip install -r requirements.txt`
2. (Optional) Set the `GITHUB_OAUTH_TOKEN` environment variable to your personal GitHub Oauth token ([GitHub - Creating a personal access token](https://help.github.com/en/github/authenticating-to-github/creating-a-personal-access-token-for-the-command-line)).
3. Instantiate a new Visualizer and specify the `owner` and `repository` parameters.

```python
pandas_visualizer = Visualizer('porsk', 'github-stats')
```

4. Use the provided methods for plotting statistics about the repository.

**Note:** If you have not turned the cache functionality off with the `useCache` parameter of the visualizer subsequent calls should be faster.

## Downloader (`hub_downloader.py`)

- expects an **owner** and a **repository** name
- optionally a githab oauth **token** (by default as an anonymous user the limit is 100 request per hour, but with a token 5000)
- it caches the downloadad data by default into the `data` directory
- can be forsed to ignore the cache and redownload the data with the `useCacheIfAvailable` parameter
- by default it logs some information about the status, but it can be disabled with the `verbose` paramter

### Methods for fetching data

#### `get_contributors_statistic()`

Returns two lists, one with the total commit counts by user and another list with additions, deletions, and commit counts by week and user.

Total contributions example:

| index | user         | commits |
| ----- | ------------ | ------- |
| 0     | xhochy       | 10      |
| 1     | Bharat123rox | 10      |
| ...   | ...          | ...     |
| 98    | jreback      | 2758    |
| 99    | wesm         | 2994    |

Weekly contributions example:

| index | user   | week_unix_ts | date       | additions | deletions | commits |
| ----- | ------ | ------------ | ---------- | --------- | --------- | ------- |
| 0     | xhochy | 1249171200   | 2009-08-02 | 0         | 0         | 0       |
| 1     | xhochy | 1249776000   | 2009-08-09 | 0         | 0         | 0       |
|       |        |              |            |           |           |         |
| ...   | ...    | ...          | ...        | ...       | ...       | ...     |
| 56398 | wesm   | 1589068800   | 2020-05-10 | 0         | 0         | 0       |
| 56399 | wesm   | 1589673600   | 2020-05-17 | 0         | 0         | 0       |

#### `get_code_frequency_statistic()`

Returns a weekly aggregate of the number of additions and deletions pushed to the repository.

Example:

| index | week_unix_ts | additions | deletions | date       |
| ----- | ------------ | --------- | --------- | ---------- |
| 0     | 1249171200   | 21659     | -4        | 2009-08-02 |
| 1     | 1249776000   | 0         | 0         | 2009-08-09 |
| ...   | ...          | ...       | ...       | ...        |
| 562   | 1589068800   | 7253      | -5247     | 2020-05-10 |
| 563   | 1589673600   | 1723      | -986      | 2020-05-17 |

#### `get_issues()`

Returns the list of open issues in the repository.

Example:

| index | id        | state | created_at |
| ----- | --------- | ----- | ---------- |
| 0     | 621098694 | open  | 2020-05-19 |
| 1     | 621095664 | open  | 2020-05-19 |
| ...   | ...       | ...   | ...        |
| 3542  | 4485088   | open  | 2012-05-09 |
| 3543  | 4217456   | open  | 2012-04-20 |

#### `get_commit_activity()`

Returns the last year of commit activity grouped by week.

Example:

| index | week_unix_ts | mon | tue | wed | thu | fri | sat | sun | week       |
| ----- | ------------ | --- | --- | --- | --- | --- | --- | --- | ---------- |
| 0     | 1558828800   | 2   | 4   | 5   | 6   | 1   | 15  | 4   | 2019-05-26 |
| 1     | 1559433600   | 7   | 2   | 11  | 5   | 10  | 9   | 4   | 2019-06-02 |
| ...   | ...          | ... | ... | ... | ... | ... | ... | ... | ...        |
| 50    | 1589068800   | 15  | 14  | 12  | 2   | 7   | 1   | 14  | 2020-05-10 |
| 51    | 1589673600   | 10  | 7   | 0   | 0   | 0   | 0   | 11  | 2020-05-17 |

#### `get_stargazers()`

Returns the lists of people that have starred the repository.

Example:

| index | user      | starred_at |
| ----- | --------- | ---------- |
| 0     | sbusso    | 2010-08-24 |
| 1     | auser     | 2010-08-24 |
| ...   | ...       | ...        |
| 24975 | Badboy-16 | 2020-05-19 |
| 24976 | ejungwoo  | 2020-05-19 |

## Visualizer (`hub_visualizer.py`)

- expects an **owner** and a **repository** name
- uses the downloader in the background for getting the data
- by default it will try to get the GitHub oauth token from the `GITHUB_OAUTH_TOKEN` environment variable

### Methods for plotting graphs

#### `commit_activity()`

Plots a grid plot about the commit activity in the repository during the last year.

Commit activity example:
![Commit activity](/figs/pandas-commit-activity.png)

#### `lines_over_time()`

Plots two graphs, one showing the total lines of code over time, the other the additions and deletions over time using line charts.

Total lines over time example:
![Total lines over time](/figs/pandas-lines-over-times.png)

Additions and deletions over time example:
![Additions and deletions over time](/figs/pandas-changes-over-time.png)

#### `commits_by_author()`

Plots a pie chart showing the top contributors based on the commit count. With the optional limit parameter the number of shown contributor can be modified.

Commits by author example:
![Commits by author](/figs/pandas-commits-by-author.png)

#### `stargazer_history()`

Plots two line charts, one showing the number of stars on the repo over time and the other showing the number of new stars month by month.

Number of stars over time example:
![Number of stars over time](/figs/pandas-stars-over-time.png)

New stars aggregated by months example:
![New stars aggregated by months](/figs/pandas-new-stars-aggregated-by-months.png)
