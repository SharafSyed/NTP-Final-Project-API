#!/usr/bin/python3
from query import Query
import algorithm as algo
from apscheduler.schedulers.background import BackgroundScheduler
import snscrape.modules.twitter as sntwitter
import atexit
from yaspin import yaspin
from flask import Flask, request

# Requires timezone, and for NTP this is in Toronto
sched = BackgroundScheduler(daemon=True, timezone='America/Toronto')

# Testing queries
queries = [
    Query('44.3894, -79.6903, 100km', [
        'tornado',
        'storm',
        'twister',
        '(funnel cloud)',
        '(tornado warning)',
        'hurricane',
        '(dust devil)',
        '#ONStorm'
    ], 0.5, 150),
    Query('44.3894, -79.6903, 100km', [
        'tornado',
        'storm',
        'twister',
        '(funnel cloud)',
        '(tornado warning)',
        'hurricane',
        '(dust devil)'
    ], 0.5, 100)
]

# Use yaspin to show a loading bar
# Then solve the resulting tweets with the algorithm
def fetchTweets(query):
    tweetList = []
    with yaspin(text=f"Fetching tweets for {query.id}...", color="blue") as sp:
        keywordQuery = ''
        for keyword in query.keywords[:-1]:
            keywordQuery += keyword + ' OR '
        keywordQuery += query.keywords[-1]
    #
        for i,tweet in enumerate(sntwitter.TwitterSearchScraper(keywordQuery + ' since:2022-02-19 until:2022-02-20 filter:media filter:has_engagement geocode:"{}"'.format(query.location)).get_items()):
            if i >= query.maxTweets:
                break
            tweetList.append({
                    'id': tweet.id,
                    'content': tweet.content,
                    'media': tweet.media,
                    'likes': tweet.likeCount,
                    'retweets': tweet.retweetCount,
                    'replies': tweet.replyCount,
                    'date': tweet.date,
                    'location': tweet.coordinates,
                })

        sp.ok("✅ ")
        print(str(tweetList.__len__()) + '/' + str(query.maxTweets) + " tweets fetched.")
    algo.solveAlgo(query, tweetList)

# Fetch the queries then send the results to the algorithm
def fetchTweetsLite(query):
    tweetList = []

    # Format keywords for the query
    keywordQuery = ''
    for keyword in query.keywords[:-1]:
        keywordQuery += keyword + ' OR '
    keywordQuery += query.keywords[-1]

    # Fetch tweets then loop through them until the max number of tweets is reached
    for i,tweet in enumerate(sntwitter.TwitterSearchScraper(keywordQuery + ' since:2022-02-19 until:2022-02-20 filter:media filter:has_engagement geocode:"{}"'.format(query.location)).get_items()):
        if i >= query.maxTweets:
            break
        tweetList.append({
                'id': tweet.id,
                'content': tweet.content,
                'media': tweet.media,
                'likes': tweet.likeCount,
                'retweets': tweet.retweetCount,
                'replies': tweet.replyCount,
                'date': tweet.date,
                'location': tweet.coordinates,
            })

    # Solve the resulting tweets with the algorithm
    print('✅ ' + str(tweetList.__len__()) + '/' + str(query.maxTweets) + f" tweets fetched for {query.id}.")
    algo.solveAlgo(query, tweetList)

# Schedule the queries
def scheduleQuery(query):
    sched.add_job(fetchTweetsLite, 'interval', minutes=query.frequency, args=[query], id=str(query.id))
    print('✅ Scheduled fetching of tweets every ' + str(query.frequency) + ' minutes for query ' + str(query.id))

# Unschedule the queries
def unscheduleQuery(query):
    sched.remove_job(str(query.id))
    print('🛑 Unscheduled fetching of tweets for query ' + str(query.id))

# On startup, schedule the queries
for query in queries:
    scheduleQuery(query)

sched.start()

app = Flask(__name__)

# Route to create a new query
@app.route('/query/new', methods=['POST'])
def newQuery():
    args = request.args.to_dict()
    newQuery = Query(args['loc'], args['keywords'], float(args['freq']), int(args['max']))
    scheduleQuery(newQuery)
    queries.append(newQuery)
    
    return 'New query successfully created'

# Route to delete a query
@app.route('/query/remove/<uuid:id>', methods=['POST'])
def removeQuery(id):
    for query in queries:
        if query.id == id:
            unscheduleQuery(query)
            queries.remove(query)
            return 'Query successfully removed'
    return 'Query not found'

if __name__ == '__main__':
    app.run()
    atexit.register(lambda: sched.shutdown())