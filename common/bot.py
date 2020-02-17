from cqhttp import CQHttp


class CountdownBot(CQHttp):
    def __init__(self, api_root: str = None, access_token: str = None, secret: str = None):
        super.__init__(self, api_root, access_token, secret)
    