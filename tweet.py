class Tweet():
    def __init__(self, id, queryId, likes, retweets, replies, date, location, content, media, keywordCount, interactionScore, relatabilityScore):
        self.id = id
        self.queryId = queryId
        self.likes = likes
        self.retweets = retweets
        self.replies = replies
        self.date = date
        self.location = location
        self.content = content
        self.media = media
        self.keywordCount = keywordCount
        self.interactionScore = interactionScore
        self.relatabilityScore = relatabilityScore

    def __str__(self):
        return str(self.getDict())

    def getDict(self):
        return {
            'id': self.id,
            'qId': self.queryId,
            'likes': self.likes,
            'rt': self.retweets,
            'rp': self.replies,
            'date': self.date,
            'loc': self.location,
            'content': self.content,
            'media': self.media,
            'kc': self.keywordCount,
            'is': self.interactionScore,
            'rs': self.relatabilityScore
        }

    def fromDict(dict):
        return Tweet(
            dict['id'],
            dict['qId'],
            dict['likes'],
            dict['rt'],
            dict['rp'],
            dict['date'],
            dict['loc'],
            dict['content'],
            dict['media'],
            dict['kc'],
            dict['is'],
            dict['rs']
        )