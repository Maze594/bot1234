import time
import datetime


class TokenSet:
    def __init__(self, timedelta=datetime.timedelta(days=1)):
        self.timedelta = timedelta
        self.tokens = {}

    def __contains__(self, item):
        return item in self.tokens

    def add(self, item):
        now = int(time.time())
        for token in self.tokens:
            timestamp = self.tokens[token]
            if now - timestamp >= self.timedelta.seconds:
                del self.tokens[token]

        self.tokens[item] = now
