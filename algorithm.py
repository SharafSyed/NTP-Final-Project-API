from prettytable import PrettyTable
import snscrape.modules.twitter as sntwitter
import math
from tweet import Tweet

def solveAlgo(query, tweets):

    # Initialize empty list of tweets
    tweetList = []

    #anti keyword list
    blacklist = ['warning', 'watch']

    for tweet in tweets:
        # Calculate the total media attached to the post
        mediaCount = 0
        media = []
        if tweet['media'] is not None:
            for m in tweet['media']:
                if type(m) == sntwitter.Photo:
                    mediaCount += 1
                    media.append({
                        'type': 'photo',
                        'url': m.fullUrl
                    })
                elif type(m) == sntwitter.Video:
                    mediaCount += 1
                    for videoType in m.variants:
                        if videoType.contentType != 'application/x-mpegURL':
                            media.append({
                                'type': 'video',
                                'url': videoType.url,
                                'contentType': videoType.contentType
                            })

        likes = tweet['likes']
        retweets = tweet['retweets']
        replies = tweet['replies']

        # Calculate the interaction score of the tweet
        interactionScore = 0
        if (likes + retweets + replies) != 0:
            interactionScore = (likes**2 + retweets**2 + replies) / math.sqrt(likes**2 + retweets**2 + replies**2)

        # Calculate the keyword count of the tweet
        keywordCount = 0
        for k in query.keywords:
            keywordCount += tweet['content'].lower().count(k.replace('(', '').replace(')', '').lower())
        
        blacklistCount = 0
        for b in blacklist:
            blacklistCount += tweet['content'].lower().count(b)

        # Calculate the relatability score of the tweet
        relatabilityScore = ((mediaCount) + (interactionScore)) * keywordCount

        if blacklistCount > 0:
            relatabilityScore = 0

        # Default to query location if tweet location is not available
        location = {
            'type': 'Point',
            'coordinates': [float(query.location.split(',')[0]), float(query.location.split(',')[1])]
        }
        if tweet['coordinates'] is not None:
            location = {
                'type': 'Point',
                'coordinates': [tweet['coordinates'].longitude, tweet['coordinates'].latitude]
            }

        # Create a new tweet object
        _tweet = Tweet(
            tweet['id'],
            query.id,
            likes, 
            retweets, 
            replies,
            tweet['date'],
            location,
            tweet['content'],
            media, 
            keywordCount, 
            interactionScore, 
            relatabilityScore
        )

        tweetList.append(_tweet)

    return tweetList

# Used for testing the algorithm and tweet fetching
def debugTweets(tweets):
    t = PrettyTable(['ID', 'Likes', 'Date', 'Location', 'Media'])
    f = open("output.txt", "w")

    for tweet in tweets:
        media = []
        if tweet['media'] is not None:
            for m in tweet['media']:
                if type(m) == sntwitter.Photo:
                    media.append(m.fullUrl)
                elif type(m) == sntwitter.Video:
                    for videoType in m.variants:
                        if videoType.contentType != 'application/x-mpegURL':
                            media.append("{} ({})".format(videoType.url, videoType.contentType))
                elif type(m) == sntwitter.Gif:
                    media = None

        t.add_row([tweet['id'], tweet['likes'], tweet['date'], tweet['coordinates'], media])

    f.write(t.get_string())
    f.close()