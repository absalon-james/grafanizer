import logging
import time

logger = logging.getLogger('grafanizer.config')
_limiters = {}


class TokenBucket(object):
    """
    Rate based limiter. Tokens are generated at a constant rate up to
    a maximum. Actions that need to be limited acquire a token or wait
    for a token to be available.

    """

    def __init__(self, rate_tokens, rate_seconds):
        """
        @param rate_tokens - Float number of tokens to generate over time
        @param rate_seconds - Float number of seconds to generate tokens over

        """
        self.token_count = 0
        self.start = time.time()
        self.fill_rate = float(rate_tokens) / float(rate_seconds)
        self.capacity = self.fill_rate
        self._tokens = float(0)
        self.updated = self.start

    def get_usage_rate(self):
        """
        Returns the usage rate since the start of the limiter.

        """
        return float(self.token_count) / float(time.time() - self.start)

    def get_token(self):
        """
        Gets one token. Sleeps in a loop until a token is available.

        """
        while self.tokens < 1:
            time.sleep(1 / self.fill_rate)
        self._tokens -= 1
        self.token_count += 1
        return True

    @property
    def tokens(self):
        """
        Getter for tokens. Updates number of tokens on every access.

        @returns Float

        """
        if self._tokens < self.capacity:
            now = time.time()
            delta_tokens = self.fill_rate * (now - self.updated)
            self._tokens = min(self.capacity, self._tokens + delta_tokens)
            self.updated = now
        return self._tokens


def start_limiter(name, rate_tokens, rate_seconds):
    """
    Starts the limiter

    @param name - String name of the limiter
    @param rate_tokens - Float number of tokens per period of time
    @param rate_seconds - Float number of seconds in a period of time
    @return - TokenBucket

    """
    _limiters[name] = TokenBucket(rate_tokens, rate_seconds)
    return _limiters[name]


def get_limiter(name):
    """
    Returns an already existing limiter or None

    @param name - String name of the limiter.
    @return - TokenBucket
    """
    return _limiters.get(name)
