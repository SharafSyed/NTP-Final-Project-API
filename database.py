from pymongo.errors import ConnectionFailure
import pymongo
import urllib.parse
import sys

from query import Query
from tweet import Tweet
from archivedQuery import ArchivedQuery

class Database():
    def __init__(self, host, username, password):
        print("- Connecting to database...", file=sys.stdout)
        try:
            # Set up the connection URI to the database
            # uri = "mongodb://%s:%s@%s/?authSource=crowd-app" % (urllib.parse.quote_plus(username), urllib.parse.quote_plus(password), urllib.parse.quote_plus(host))
            
            uri = "mongodb://localhost:27017" 

            # Connect to the database
            self.client = pymongo.MongoClient(uri)

            # Setup database and collections
            self.db = self.client['crowd-app']
            self.queriesCollection = self.db['queries']
            self.tweetsCollection = self.db['tweets']

            # Create archived query collection
            self.archivedQueriesCollection = self.db['archive']

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
    
    def archiveQuery(self, id, query):
        for queryJSON in self.queriesCollection.find():
            if queryJSON['_id'] == query.id:
                archivedQuery = ArchivedQuery(queryJSON['name'], queryJSON['location'], queryJSON['startDate'], queryJSON['endDate'], queryJSON['keywords'], queryJSON['frequency'], queryJSON['maxTweets'], False)
                archivedQuery.id = queryJSON['_id']
                self.archivedQueriesCollection.insert_one(archivedQuery.getDict())
                self.queriesCollection.delete_one({'_id': id})
                return

    def getArchivedQueries(self):
        archivedQueries = []
        for archivedQueryJSON in self.archivedQueriesCollection.find():
            archivedQuery = ArchivedQuery(archivedQueryJSON['name'], archivedQueryJSON['location'], archivedQueryJSON['startDate'], archivedQueryJSON['endDate'], archivedQueryJSON['keywords'], archivedQueryJSON['frequency'], archivedQueryJSON['maxTweets'], archivedQueryJSON['isPublic'])
            archivedQuery.id = archivedQueryJSON['_id']
            archivedQueries.append(archivedQuery)
        return archivedQueries
        
    def removeArchivedQuery(self, id):
        self.archivedQueriesCollection.delete_one({'_id': id})
    
    def updateArchivedQuery(self, id, query):
        self.archivedQueriesCollection.update_one({'_id': id}, {'$set': query.getDict()}, upsert=True)

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
    
    def getBestTweetsFromArchivedQuery(self, max, archivedQuery):
        tweets = []
        for tweetJSON in self.tweetsCollection.find({'qId': archivedQuery.id}).sort('rs', pymongo.DESCENDING).limit(max):
            tweetJSON['qId'] = str(tweetJSON['qId'])
            tweets.append(Tweet.fromDict(tweetJSON))
        return tweets