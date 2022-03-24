from pymongo.errors import ConnectionFailure
import pymongo
import urllib.parse
import sys

from query import Query
from tweet import Tweet

class Database():
    def __init__(self, host, username, password):
        print("- Connecting to database...", file=sys.stdout)
        try:
            # Set up the connection URI to the database
            uri = "mongodb://%s:%s@%s/?authSource=crowd-app" % (urllib.parse.quote_plus(username), urllib.parse.quote_plus(password), urllib.parse.quote_plus(host))
            
            # Connect to the database
            self.client = pymongo.MongoClient(uri)

            # Setup database and collections
            self.db = self.client['crowd-app']
            self.queriesCollection = self.db['queries']
            self.tweetsCollection = self.db['tweets']

            # Check if the database is connected
            self.client.admin.command('ismaster')
            print("✅ Connected to database", file=sys.stdout)
        except ConnectionFailure:
            print("🛑 Could not connect to database", file=sys.stderr)
            
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
        self.queriesCollection.update_one({'_id': id}, {'$set': query.getDict()}, upsert=True)

    def removeQuery(self, id):
        self.queriesCollection.delete_one({'_id': id})

    def addTweets(self, tweets):
        # Use bulk operations to insert all tweets in one go while maintaining old tweets
        operations = []
        for tweet in tweets:
            # Update existing tweet if it already exists, otherwise insert new tweet
            operations.append(pymongo.UpdateOne({'id': tweet.id}, {'$set': tweet.getDict()}, upsert=True))
        self.tweetsCollection.bulk_write(operations)

    def getBestTweetsFromQuery(self, max, query):
        tweets = []
        for tweetJSON in self.tweetsCollection.find({'qId': query.id}).sort('rs', pymongo.DESCENDING).limit(max):
            tweetJSON['qId'] = str(tweetJSON['qId'])
            tweets.append(Tweet.fromDict(tweetJSON))
        return tweets