from tkinter import E
import pymongo
import urllib.parse
import sys

from query import Query
from tweet import Tweet

class Database():
    def __init__(self, host, username, password):
        print("- Connecting to database...", file=sys.stdout)
        try:
            uri = "mongodb://%s:%s@%s/?authSource=crowd-app" % (urllib.parse.quote_plus(username), urllib.parse.quote_plus(password), urllib.parse.quote_plus(host))
            self.client = pymongo.MongoClient(uri)
            self.db = self.client['crowd-app']
            self.queriesCollection = self.db['queries']
            self.tweetsCollection = self.db['tweets']
            print("- Connected to database", file=sys.stdout)
        except Exception as e:
            raise e
            
    def addQuery(self, query):
        _object = self.queriesCollection.insert_one(query.getDict())
        return _object.inserted_id

    def getQueries(self):
        queries = []
        for queryJSON in self.queriesCollection.find():
            query = Query(queryJSON['name'], queryJSON['location'], queryJSON['startDate'], queryJSON['endDate'], queryJSON['keywords'], queryJSON['frequency'], queryJSON['maxTweets'])
            query.id = queryJSON['_id']
            queries.append(query)
        return queries
    
    def updateQuery(self, id, query):
        self.queriesCollection.update_one({'_id': id}, {'$set': query.getDict()})

    def removeQuery(self, id):
        self.queriesCollection.delete_one({'_id': id})

    def addTweets(self, tweets):
        operations = []
        for tweet in tweets:
            operations.append(pymongo.UpdateOne({'id': tweet.id}, {'$set': tweet.getDict()}, upsert=True))
        self.tweetsCollection.bulk_write(operations)

    def getBestTweetsFromQuery(self, max, query):
        tweets = []
        for tweetJSON in self.tweetsCollection.find({'qId': query.id}).sort('rs', pymongo.DESCENDING).limit(max):
            tweetJSON['qId'] = str(tweetJSON['qId'])
            tweets.append(Tweet.fromDict(tweetJSON))
        return tweets