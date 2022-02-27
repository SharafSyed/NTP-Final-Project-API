#!/usr/bin/python3
from database import Database
from query import Query
import algorithm as algo
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from bson.objectid import ObjectId
import snscrape.modules.twitter as sntwitter
import json
from six.moves.urllib.request import urlopen
from jose import jwt
import os
import sys
import atexit

from functools import wraps
from flask import Flask, request, jsonify, _request_ctx_stack
from flask_cors import CORS, cross_origin

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Timeout the queries?
timeoutQueries = False

# Requires timezone, and for NTP this is in Toronto
sched = BackgroundScheduler(daemon=True, timezone='America/Toronto')

# Start the database connection
db = Database(str(os.environ.get("MONGODB_HOST")), str(os.environ.get("MONGODB_USER")), str(os.environ.get("MONGODB_PASS")))

# Populate local queries
queries = db.getQueries()

# Fetch the queries then send the results to the algorithm
def fetchTweetsLite(query):

    # If timeout is enabled, check if the query has timed out
    if timeoutQueries:
        if datetime.datetime.today() > query.endDate:
            print(f'- Ending fetching of tweets for query {str(query.id)} - {query.name}', file=sys.stdout)
            removeQuery(str(query.id))
            return

    print(f'🔎 Fetching tweets for query {query.id}', file=sys.stdout)

    tweetList = []

    # Format keywords for the query
    keywordQuery = ''
    for keyword in query.keywords[:-1]:
        keywordQuery += keyword + ' OR '
    keywordQuery += query.keywords[-1]

    # Fetch tweets then loop through them until the max number of tweets is reached
    for i,tweet in enumerate(sntwitter.TwitterSearchScraper(f'{keywordQuery} since:{query.startDate.strftime("%Y-%m-%d")} until:{query.endDate.strftime("%Y-%m-%d")} filter:media filter:has_engagement geocode:"{query.location}"').get_items()):
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
                'coordinates': tweet.coordinates,
            })

    # Solve the resulting tweets with the algorithm
    print(f'✅ {str(tweetList.__len__())}/{str(query.maxTweets)} tweets fetched for {query.id} - {query.name}', file=sys.stdout)
    db.addTweets(algo.solveAlgo(query, tweetList))

# Schedule the queries
def scheduleQuery(query):
    sched.add_job(fetchTweetsLite, 'interval', minutes=query.frequency, args=[query], id=str(query.id))
    print(f'✅ Scheduled fetching of tweets every {str(query.frequency)} minutes for query {str(query.id)} - {query.name}', file=sys.stdout)

# Unschedule the queries
def unscheduleQuery(query):
    sched.remove_job(str(query.id))
    print(f'🛑 Unscheduled fetching of tweets for query {str(query.id)} - {query.name}', file=sys.stdout)

# On startup, schedule the queries
for query in queries:
    scheduleQuery(query)

sched.start()

app = Flask(__name__)
CORS(app)

class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

@app.errorhandler(AuthError)
def handle_auth_error(ex):
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response

# Format error response and append status code
def get_token_auth_header():
    """Obtains the Access Token from the Authorization Header
    """
    auth = request.headers.get("Authorization", None)
    if not auth:
        raise AuthError({"code": "authorization_header_missing",
                        "description":
                            "Authorization header is expected"}, 401)

    parts = auth.split()

    if parts[0].lower() != "bearer":
        raise AuthError({"code": "invalid_header",
                        "description":
                            "Authorization header must start with"
                            " Bearer"}, 401)
    elif len(parts) == 1:
        raise AuthError({"code": "invalid_header",
                        "description": "Token not found"}, 401)
    elif len(parts) > 2:
        raise AuthError({"code": "invalid_header",
                        "description":
                            "Authorization header must be"
                            " Bearer token"}, 401)

    token = parts[1]
    return token

def requires_auth(f):
    """Determines if the Access Token is valid
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_auth_header()
        jsonurl = urlopen(os.environ.get("AUTH0_DOMAIN")+"/.well-known/jwks.json")
        jwks = json.loads(jsonurl.read())
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
        if rsa_key:
            try:
                payload = jwt.decode(
                    token,
                    rsa_key,
                    algorithms=["RS256"],
                    audience=os.environ.get("API_AUDIENCE"),
                    issuer=os.environ.get("AUTH0_DOMAIN")+"/"
                )
            except jwt.ExpiredSignatureError:
                raise AuthError({"code": "token_expired",
                                "description": "token is expired"}, 401)
            except jwt.JWTClaimsError:
                raise AuthError({"code": "invalid_claims",
                                "description":
                                    "incorrect claims,"
                                    "please check the audience and issuer"}, 401)
            except Exception:
                raise AuthError({"code": "invalid_header",
                                "description":
                                    "Unable to parse authentication"
                                    " token."}, 401)

            _request_ctx_stack.top.current_user = payload
            return f(*args, **kwargs)
        raise AuthError({"code": "invalid_header",
                        "description": "Unable to find appropriate key"}, 401)
    return decorated

# Route to create a new query
@app.route('/', methods=['GET'])
def homeRoute():
    return {
        'status': 200,
        'message': 'Server is running'
    }

# Route to create a new query
@app.route('/query/new', methods=['POST'])
# @cross_origin(headers=["Content-Type", "Authorization"])
# @requires_auth
def newQuery():
    args = request.args.to_dict()

    # Edit time to make sure it ends at the end of the day
    endTime = datetime.datetime.strptime(args['end'], '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=0)

    keywords = args['keywords'].split(',')
    for i, keyword in enumerate(keywords):
        if " " in keywords[i]:
            keywords[i] = '(' + keywords[i] + ')'

    # Create the query & if there are any errors when inserting into the database, return an error code
    try:
        newQuery = Query(args['name'], args['loc'], datetime.datetime.strptime(args['start'], '%Y-%m-%d'), endTime, keywords, float(args['freq']), int(args['max']))
        newQuery.id = db.addQuery(newQuery)

        scheduleQuery(newQuery)
        queries.append(newQuery)
        
        return {
            'status': 200,
            'message': 'New query successfully created'
        }
    except:
        return {
            'status': 500,
            'message': 'Error creating query, check the arguments'
        }

# Route to delete a query
@app.route('/query/<string:id>/remove', methods=['POST'])
# @cross_origin(headers=["Content-Type", "Authorization"])
# @requires_auth
def removeQuery(id):
    print('- Removing query ' + id + '...', file=sys.stdout)
    for query in queries:
        if query.id == ObjectId(id):
            print('- Found query ' + id, file=sys.stdout)
            db.removeQuery(ObjectId(id))
            unscheduleQuery(query)
            queries.remove(query)
            return {
                'status': 200,
                'message': 'Query successfully removed'
            }
    return {
        'status': 500,
        'message': 'Query not found'
    }

@app.route('/query/<string:id>', methods=['GET'])
def getQuery(id):
    # Sometimes in the application, we will recieve an undefined ID, this is to prevent that
    if (id == 'undefined'):
        return {
            'status': 400,
            'message': 'Query ID not specified'
        }

    for query in queries:
        if query.id == ObjectId(id):
            return {
                'status': 200,
                'message': 'Successfully retrieved query',
                'query': query.getJSON()
            }
    return {
        'status': 500,
        'message': 'Query not found'
    }

@app.route('/query/<string:id>/tweets', methods=['GET'])
def getTweetsFromQuery(id):
    for query in queries:
        if query.id == ObjectId(id):
            tweets = db.getBestTweetsFromQuery(int(request.args.to_dict()['max']), query)
            return {
                'status': 200,
                'message': 'Successfully retrieved tweets',
                'tweets': [tweet.getDict() for tweet in tweets]
            }
    return {
        'status': 500,
        'message': 'Query not found'
    }

@app.route('/query/<string:id>/geojson', methods=['GET'])
def getTweetsFromQueryGeoJSON(id):
    for query in queries:
        if query.id == ObjectId(id):
            tweets = db.getBestTweetsFromQuery(query.maxTweets, query)
            response = {
                'type': 'FeatureCollection',
                'features': []
            }
            for tweet in tweets:
                response['features'].append({
                    'type': 'Feature',
                    'properties': {
                        'id': str(tweet.id),
                        'score': tweet.relatabilityScore
                    },
                    'geometry': tweet.location
                })
            return {
                'status': 200,
                'message': 'Successfully retrieved GeoJSON',
                'geojson': response
            }
    return {
        'status': 500,
        'message': 'Query not found'
    }

@app.route('/queries/active/list/geojson', methods=['GET'])
def getGeoJSONFromAllActiveQueries():
    response = {
        'type': 'FeatureCollection',
        'features': []
    }
    for query in queries:
        try:
            tweets = db.getBestTweetsFromQuery(query.maxTweets, query)
        except:
            return {
                'status': 500,
                'message': 'Query not found'
            }
        for tweet in tweets:
            response['features'].append({
                'type': 'Feature',
                'properties': {
                    'id': str(tweet.id),
                    'score': tweet.relatabilityScore,
                    'query': str(query.id)
                },
                'geometry': tweet.location
            })
    return {
        'status': 200,
        'message': 'Successfully retrieved tweets',
        'geojson': response
    }

@app.route('/queries/active/list/tweets', methods=['GET'])
def getTweetsFromAllActiveQueries():
    response = []
    for query in queries:
        try:
            tweets = db.getBestTweetsFromQuery(query.maxTweets, query)
        except:
            return {
                'status': 500,
                'message': 'Query not found'
            }
        for tweet in tweets:
            response.append(tweet.getJSON())

    response.sort(key=lambda x: x['rs'], reverse=True)

    if (request.args.to_dict()['limit'] != None):
        response = response[:int(request.args.to_dict()['limit'])]

    return {
        'status': 200,
        'message': 'Successfully retrieved tweets',
        'tweets': response
    }

@app.route('/queries/active/list', methods=['GET'])
def getActiveQueries():
    return {
        'status': 200,
        'message': 'Successfully retrieved queries',
        'queries': [query.getJSON() for query in queries]
    }

if __name__ == '__main__':
    app.run()
    atexit.register(lambda: sched.shutdown())
    atexit.register(lambda: db.client.close())