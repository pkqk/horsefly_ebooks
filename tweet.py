from __future__ import print_function, unicode_literals, division
import twitter, redis, re
import os

class Horsefly(object):
    def __init__(self, twitter, redis):
      self.twitter = twitter
      self.redis = redis
      self.max_key = 'horsefly:max-tweet'

    def update(self):
      since_id = False #self.redis.get(self.max_key)
      if since_id:
        tweets = self.twitter.statuses.home_timeline(since_id=since_id)
      else:
        tweets = self.twitter.statuses.home_timeline()
      for tweet in filter(self.not_tweeted, reversed(tweets)):
        self.buzz_words(tweet['text'])
        self.update_max(tweet)

    def buzz_words(self, text):
      buzz_text = re.sub('s+(?=[\W]|\Z)','zzz', text)
      buzz_text = re.sub('er(?=[\W]|\Z)','ezz', text)
      buzz_text = re.sub('en(?=[\W]|\Z)','enzz', text)
      buzz_text = re.sub('S+(?=[\W]|\Z)','ZZZ', text)
      buzz_text = re.sub('ER(?=[\W]|\Z)','EZZ', text)
      if buzz_text != text:
        tweet_it(buzz_text)
    
    def not_tweeted(self, tweet):
      return True
      return tweet['id'] > int(self.redis.get(self.max_key))
    
    def update_max(self, tweet):
      if tweet['id'] > int(self.redis.get(self.max_key)):
        self.redis.set(self.max_key, tweet['id'])

if __name__ == "__main__":
    twitter_client = twitter.Twitter(auth=twitter.OAuth(
      os.environ['TWITTER_TOKEN'],
      os.environ['TWITTER_SECRET'],
      os.environ['TWITTER_CONSUMER_TOKEN'],
      os.environ['TWITTER_CONSUMER_SECRET']
    ))
    redis_client = redis.StrictRedis(
      host=os.environ['REDIS_HOST'],
      port=int(os.environ['REDIS_PORT']),
      db=int(os.environ['REDIS_DB']))
    horsefly = Horsefly(twitter_client, redis_client)
    horsefly.update()
