from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length

from tweepy import API
from tweepy import Cursor
from tweepy import OAuthHandler

import pandas as pd
import numpy as np

import twitter_credentials


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sys.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SECRET_KEY'] = 'so unsecured'

CORS(app, resources={r"/api/*": {"origins": "*"}})

db = SQLAlchemy(app)
session = db.session

class loginStatus1():
    loginStatus = False

    def changeLoginStatus(this):
        if(this.loginStatus == False):
            this.loginStatus = True

        else:
            if(this.loginStatus == True):
                this.loginStatus = False
    
    def getLoginStatus(this):
        return this.loginStatus

login1 = loginStatus1()
## Login Stuff ##

class user(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80))
    email = db.Column(db.String(120))
    password = db.Column(db.String(80))

# # # # TWITTER AUTHENTICATER # # # #
class TwitterAuthenticator():

    def authenticate_twitter_app(self):
        auth = OAuthHandler(twitter_credentials.CONSUMER_KEY, twitter_credentials.CONSUMER_SECRET)# import consumer credentials from twitter_credentials.py file
        auth.set_access_token(twitter_credentials.ACCESS_TOKEN, twitter_credentials.ACCESS_TOKEN_SECRET)# import access credentials from twitter_credentials.py file
        return auth

# # # # TWITTER CLIENT # # # #
class TwitterClient():
    def __init__(self, twitter_user=None):
        self.auth = TwitterAuthenticator().authenticate_twitter_app()
        self.twitter_client = API(self.auth)
        self.twitter_user = twitter_user

    def get_twitter_client_api(self):
        return self.twitter_client

    def get_user_timeline_tweets(self, num_tweets):
        tweets = []
        for tweet in Cursor(self.twitter_client.user_timeline, id=self.twitter_user).items(num_tweets):
            tweets.append(tweet)
        return tweets

    def get_friend_list(self, num_friends):
        friend_list = []
        for friend in Cursor(self.twitter_client.friends, id=self.twitter_user).items(num_friends):
            friend_list.append(friend)
        return friend_list

    def get_home_timeline_tweets(self, num_tweets):
        home_timeline_tweets = []
        for tweet in Cursor(self.twitter_client.home_timeline, id=self.twitter_user).items(num_tweets):
            home_timeline_tweets.append(tweet)
        return home_timeline_tweets

class TweetAnalyzer():

    def tweets_to_data_frame(self, tweets):
        df = pd.DataFrame(data=[tweet.text for tweet in tweets], columns=['tweets']) # stores the text field of a tweet object into a panda Dataframe
        df['id'] = [tweet.id for tweet in tweets] # stores the id field of a tweet object
        df['len'] = np.array([len(tweet.text) for tweet in tweets]) # stores the text length of a tweet object
        df['date'] = np.array([tweet.created_at for tweet in tweets])  # stores the timestamp of a tweet object
        df['source'] = np.array([tweet.source for tweet in tweets])  # stores the source of a tweet object
        df['likes'] = np.array([tweet.favorite_count for tweet in tweets]) # stores the likes count of a tweet object
        df['retweets'] = np.array([tweet.retweet_count for tweet in tweets]) # stores the retweet count of a tweet object"""

        return df


class SentimentAnalysis:

    def __init__(self):
        self.tweets = []
        self.tweetText = []

    def DownloadData(self,api,searchTerm,noOfTerms):
        # searching for tweets
        for tweet in Cursor(api.search, q=searchTerm, lang="en").items(noOfTerms):
            self.tweets.append(tweet._json)

        return self.tweets



twitter_client = TwitterClient()
api = twitter_client.get_twitter_client_api()
tweet_analyzer = TweetAnalyzer()

@app.before_first_request
def setup():
    db.Model.metadata.drop_all(bind=db.engine)
    db.Model.metadata.create_all(bind=db.engine)

@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()

@app.route('/')
def hello():
    return redirect(url_for('homepage'))

@app.route('/api')
def homepage():
    return render_template('index')


@app.route('/api/hashtag')
def getHashtag():
    if((login1.getLoginStatus()) == False):
       return redirect(url_for("login"))
    
    return render_template('hashtag')


@app.route('/api/hashtag_search', methods=['POST'])
def sendHashtag():
    index = request.form['hashtag_name']
    num = int(request.form['num_vals'])
    sa = SentimentAnalysis()
    tweets = sa.DownloadData(api,index,num)
    #return jsonify(tweets)
    return render_template('display', tweets = tweets)


@app.route('/api/hashtag/<index>', methods=['GET'])
def hashtagData(index):
    return str(index)

@app.route("/api/login",methods=["GET", "POST"])
def login():
    if request.method == "POST":
        uname = request.form["uname"]
        passw = request.form["passw"]
        
        login = user.query.filter_by(username=uname, password=passw).first()
        if login is not None:
            login1.changeLoginStatus()
            return redirect(url_for("homepage"))
    return render_template("login")

@app.route("/api/logoff")
def logoff():
    if((login1.getLoginStatus) != False):
        login1.changeLoginStatus
        return redirect(url_for("homepage"))
    else:
        return redirect(url_for("homepage"))



@app.route("/api/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        uname = request.form['uname']
        mail = request.form['mail']
        passw = request.form['passw']

        register = user(username = uname, email = mail, password = passw)
        db.session.add(register)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("register")

if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)