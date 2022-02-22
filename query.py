class Query():
    def __init__(self, name, location, startDate, endDate, keywords, frequency, maxTweets):
        self.id = None
        self.name = name
        self.location = location
        self.startDate = startDate
        self.endDate = endDate
        self.keywords = keywords
        self.frequency = frequency
        self.maxTweets = maxTweets

    def getDict(self):
        if self.id is None:
            return {
                'name': self.name,
                'location': self.location,
                'startDate': self.startDate,
                'endDate': self.endDate,
                'keywords': self.keywords,
                'frequency': self.frequency,
                'maxTweets': self.maxTweets
            }
        return {
            '_id': self.id,
            'name': self.name,
            'location': self.location,
            'startDate': self.startDate,
            'endDate': self.endDate,
            'keywords': self.keywords,
            'frequency': self.frequency,
            'maxTweets': self.maxTweets
        }

    def getJSON(self):
        if self.id is None:
            return {
                'name': self.name,
                'location': self.location,
                'startDate': self.startDate.isoformat(),
                'endDate': self.endDate.isoformat(),
                'keywords': self.keywords,
                'frequency': self.frequency,
                'maxTweets': self.maxTweets
            }
        return {
            '_id': str(self.id),
            'name': self.name,
            'location': self.location,
            'startDate': self.startDate.isoformat(),
            'endDate': self.endDate.isoformat(),
            'keywords': self.keywords,
            'frequency': self.frequency,
            'maxTweets': self.maxTweets
        }

    def __str__(self):
        return str(self.getDict())