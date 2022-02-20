from prettytable import PrettyTable
import snscrape.modules.twitter as sntwitter
import math

def solveAlgo(query, tweets):
    # Use PrettyTable to print the tweets
    t = PrettyTable(['ID', 'Likes', 'Retweets', 'Replies', 'Media Count', 'Keyword Count', 'Interaction Score', 'Relatability Score', 'URL'])

    for tweet in tweets:
        # Calculate the total media attached to the post
        mediaCount = 0
        if tweet['media'] is not None:
            mediaCount = tweet['media'].__len__()

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

        # Calculate the relatability score of the tweet
        relatabilityScore = ((mediaCount) + (interactionScore)) * keywordCount
        t.add_row([tweet['id'], likes, retweets, replies, mediaCount, keywordCount, interactionScore, relatabilityScore, 'https://twitter.com/anyuser/status/' + str(tweet['id'])])

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

        t.add_row([tweet['id'], tweet['likes'], tweet['date'], tweet['location'], media])

    f.write(t.get_string())
    f.close()