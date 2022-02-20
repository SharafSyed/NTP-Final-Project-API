import uuid

class Query():
    def __init__(self, location, keywords, frequency, maxTweets):
        self.id = uuid.uuid4()
        self.location = location
        self.keywords = keywords
        self.frequency = frequency
        self.maxTweets = maxTweets

    def __str__(self):
        return 'Query: ID - ' + str(self.id) + ' ' + self.location + ' ' + self.keywords + ' ' + self.frequency + ' ' + self.maxTweets