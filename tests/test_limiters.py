import sys
import time
import unittest
from os.path import dirname, realpath
sys.path.append(dirname(dirname(realpath(__file__))))

from grafanizer import limiters


class TokenBucketTest(unittest.TestCase):
    """
    Tests the token bucket rate limiter.

    """
    def test_fill_rate(self):
        """
        Tests the fill rate.
        The fill rate should be the rate tokens divided by
        the rate seconds. In addition, it should be a float.

        """
        rate_tokens = 1
        rate_seconds = 1
        rate = float(rate_tokens) / float(rate_seconds)
        bucket = limiters.TokenBucket(rate_tokens, rate_seconds)
        self.assertEquals(bucket.fill_rate, rate)
        self.assertTrue(isinstance(bucket.fill_rate, float))

    def test_capacity(self):
        """
        Tests the capacity. The capacity should be the fill rate.
        The number of available tokens should not exceed the
        capacity. The capacity should also be a float.

        """
        rate_tokens = 1
        rate_seconds = 1
        bucket = limiters.TokenBucket(rate_tokens, rate_seconds)
        capacity = float(rate_tokens) / float(rate_seconds)
        self.assertEquals(bucket.capacity, capacity)
        self.assertTrue(isinstance(bucket.capacity, float))

        # Should generate 1 tokens in 1 second
        time.sleep(1)
        self.assertEquals(bucket.tokens, capacity)
        self.assertTrue(isinstance(bucket.tokens, float))

        # Tokens should be capped at 1 token.
        time.sleep(1)
        self.assertEquals(bucket.tokens, bucket.capacity)
        self.assertTrue(isinstance(bucket.tokens, float))

    def test_limiting(self):
        """
        Tests that it takes at least rate_seconds to consume
        rate_tokens.

        """
        rate_tokens = 20
        rate_seconds = 1
        bucket = limiters.TokenBucket(rate_tokens, rate_seconds)
        start = time.time()
        for i in xrange(rate_tokens):
            bucket.get_token()
        stop = time.time()
        self.assertTrue(stop - start >= 1)
        self.assertTrue(stop - start < 2)


class TestLimiterDict(unittest.TestCase):
    """
    Tests the module dictionary that holds longlived limiters.

    """
    def setUp(self):
        """
        Set the limiters._limiters dict to the empty dict {}

        """
        limiters._limiters = {}

    def test_start_limiter(self):
        """
        Tests the start_limiter() function.
        Start limiter should return a TokenBucket limiter.
        In addition, a key with the value of the the limiter
        should be in the limiters._limiter dict.

        """
        tokens = 1
        seconds = 1
        ret_limiter = limiters.start_limiter('test', tokens, seconds)
        self.assertTrue(isinstance(ret_limiter, limiters.TokenBucket))
        self.assertTrue('test' in limiters._limiters)

    def test_get_limiter(self):
        """
        Tests the get_limiter() function. A limiter should be able to be
        retrieved by name.

        """
        tokens = 1
        seconds = 1
        ret_limiter = limiters.start_limiter('test', tokens, seconds)
        self.assertEquals(ret_limiter, limiters.get_limiter('test'))
