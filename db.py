import os
import redis


class RedisDB:
    def __init__(self, host=None, port=6379, db=0):
        if host is None:
            host = os.environ.get('REDIS_HOST', 'localhost')

        self.redis_client = redis.StrictRedis(host=host, port=port, db=db)

    def get_event(self, key):
        return self.redis_client.hgetall(key)

    def save_event(self, name, key, value):
        return self.redis_client.hset(name, key, value)

    def get_keys(self):
        return self.redis_client.keys()

    def delete(self, key):
        return self.redis_client.delete(key)
