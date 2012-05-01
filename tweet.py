from __future__ import print_function, unicode_literals, division
import twitter
import redis
import os
import re
import time
import urlparse
import traceback


class Horsefly(object):
    def __init__(self, twitter, redis):
        self.twitter = twitter
        self.redis = redis
        self.max_key = 'horsefly:max-tweet'

    def update(self):
        since_id = self.redis.get(self.max_key)
        if since_id:
            tweets = self.twitter.statuses.user_timeline(
                screen_name='horse_ebooks',
                since_id=since_id
            )
        else:
            tweets = self.twitter.statuses.user_timeline(
                screen_name='horse_ebooks'
            )
        for tweet in filter(self.not_tweeted, reversed(tweets)):
            self.buzz_words(tweet['text'])
            self.update_max(tweet)

    def buzz_words(self, text):
        buzz_text = re.sub('s+(?=[\W]|\Z)', 'zzz', text)
        buzz_text = re.sub('er(?=[\W]|\Z)', 'ezz', buzz_text)
        buzz_text = re.sub('en(?=[\W]|\Z)', 'enzz', buzz_text)
        buzz_text = re.sub('S+(?=[\W]|\Z)', 'ZZZ', buzz_text)
        buzz_text = re.sub('ER(?=[\W]|\Z)', 'EZZ', buzz_text)
        if buzz_text != text and len(text) <= 140:
            self.twitter.statuses.update(status=buzz_text)
        elif len(text) > 140:
            print("tweet too long: " + buzz_text)

    def not_tweeted(self, tweet):
        return tweet['id'] > int(self.redis.get(self.max_key) or 1)

    def update_max(self, tweet):
        if self.not_tweeted(tweet):
            self.redis.set(self.max_key, tweet['id'])

if __name__ == "__main__":
    twitter_client = twitter.Twitter(auth=twitter.OAuth(
        os.environ['TWITTER_TOKEN'],
        os.environ['TWITTER_SECRET'],
        os.environ['TWITTER_CONSUMER_TOKEN'],
        os.environ['TWITTER_CONSUMER_SECRET']
    ))
    url = urlparse.urlparse(os.environ['REDISTOGO_URL'])
    redis_client = redis.StrictRedis(
        host=url.hostname,
        port=url.port,
        db=0,
        password=url.password
    )
    horsefly = Horsefly(twitter_client, redis_client)
    while True:
        try:
            horsefly.update()
            print("update run, no crashz")
        except twitter.api.TwitterHTTPError as e:
            print("error: " + e.message)
            traceback.print_exc()
        time.sleep(60 * 5)
