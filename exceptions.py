class NotFoundError(Exception):
    '''raise this when requested repository is not found'''
    pass

class ApiRateLimitError(Exception):
    '''raise this when API rate limit exceeded'''
    pass

class BadCredentialsError(Exception):
    '''raise this when bad credentials were provided for the API'''
    pass