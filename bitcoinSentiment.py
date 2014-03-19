#!/usr/bin/env python
# ----------------------------------------------------------------------
# Numenta Platform for Intelligent Computing (NuPIC)
# Copyright (C) 2013, Numenta, Inc.  Unless you have an agreement
# with Numenta, Inc., for a separate license for this software code, the
# following terms and conditions apply:
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses.
#
# http://numenta.org/licenses/
# ----------------------------------------------------------------------

"""Read Bitcoin sentiment from Twitter and predict it in real time."""

from __future__ import division
from collections import deque
import time
import datetime
import matplotlib.pyplot as plt
import numpy as np
import urllib2
import json

import re
from re import sub
import cookielib
from cookielib import CookieJar
from urllib2 import urlopen
import urllib
import csv
from string import punctuation
from tweepy import Stream
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener


from nupic.data.inference_shifter import InferenceShifter
from nupic.frameworks.opf.modelfactory import ModelFactory

import model_params

SECONDS_PER_STEP = 1
WINDOW = 60

# turn matplotlib interactive mode on (ion)
plt.ion()
fig = plt.figure()
# plot title, legend, etc
plt.title('Bitcoin prediction example')
plt.xlabel('time [s]')
plt.ylabel('Price')

ckey = '5KP8JqcXOWeDYqZuhGciBQ'
csecret = '9JyWU7SdLhaNgzEolqKILJnsaFLRtcbR5Z1s0JYZBM'
atoken = '38103557-FS3Ec9Yy1Jh9h0kpqtokujcyNsFRXlzHv0Hr8rJuu'
asecret = 'pmdPnGjdZLejzoxMONhrWDPV81olsxg4HK97D7aj45lUu'


def tweetSentiment(text):
    
    #files = ['negative.txt','positive.txt']
    
    #path = 'http://www.unc.edu/~ncaren/haphazard/'
    #for file_name in files:
    #urllib.urlretrieve(path+file_name,file_name)
    
    pos_sent = open('positive.txt').read()
    positive_words = pos_sent.split('\n')
    positive_counts = []
    
    neg_sent = open('negative.txt').read()
    negative_words = neg_sent.split('\n')
    negative_counts = []
    
    positive_counter = 0
    negative_counter = 0
    
    tweetProcessed = text.lower()
    
    for p in list(punctuation):
        tweetProcessedFurther = tweetProcessed.replace(p,'')
    
    words = tweetProcessedFurther.split(' ')
    word_count = len(words)
    
    for word in words:
        if word in positive_words:
            positive_counter += 1
        elif word in negative_words:
            negative_counter += 1
    
    positiveSentiment = positive_counter/word_count
    negativeSentiment = negative_counter/word_count
    
    rating = positiveSentiment
    return rating

def bitcoinPercent():
    btcePrices = urllib2.urlopen('https://api.bitcoinaverage.com/exchanges/USD').read()
    btceJson = json.loads(btcePrices)
    #btcelastP = btceJson['bitstamp']['last']
    btceVolumePercent = btceJson['bitstamp']['volume_percent']
    #btcelastV = btceJson['ticker']['vol']
    #btcePercent = float((btcelastVC/btcelastV) * 100)
    return btceVolumePercent

def runBitcoin():
  """Pull Bitcoin Volume and Tweet Sentiment, make predictions, and plot the results. Runs forever."""
  # Create the model for predicting Bitcoin usage.
  model = ModelFactory.create(model_params.MODEL_PARAMS)
  model.enableInference({'predictedField': 'tweet'})
  # The shifter will align prediction and actual values.
  shifter = InferenceShifter()
  # Keep the last WINDOW predicted and actual values for plotting.
  actHistory = deque([0.0] * WINDOW, maxlen=60)
  predHistory = deque([0.0] * WINDOW, maxlen=60)

  # Initialize the plot lines that we will update with each new record.
  actline, = plt.plot(range(WINDOW), actHistory)
  predline, = plt.plot(range(WINDOW), predHistory)
  # Set the y-axis range.
  actline.axes.set_ylim(0, 1)
  predline.axes.set_ylim(0, 1)


  while True:
    s = time.time()

    # Get the Bitcoin Volume usage.
    # volume = bitcoinPercent()
    
    # Get Twitter Sentiment.
    class listener(StreamListener):
        def on_data(self, data):
            try:
                tweet = data.split(',"text":"')[1].split('","source')[0]
                sentimentRating = tweetSentiment(tweet)
                tweet = sentimentRating
        
                # Run the input through the model and shift the resulting prediction.
                modelInput = {'tweet': tweet}
                result = shifter.shift(model.run(modelInput))
                
                # Update the trailing predicted and actual value deques.
                inference = result.inferences['multiStepBestPredictions'][5]
                if inference is not None:
                    actHistory.append(result.rawInput['tweet'])
                    predHistory.append(inference)
            
                # Redraw the chart with the new data.
                actline.set_ydata(actHistory)  # update the data
                predline.set_ydata(predHistory)  # update the data
                plt.draw()
                plt.legend( ('actual','predicted') )
            
                plt.pause(SECONDS_PER_STEP)
                
        
            except BaseException, e:
                print 'error in 1st try', str(e)
                time.sleep(5)
    
        def on_error(self, status):
            print status

    auth = OAuthHandler(ckey, csecret)
    auth.set_access_token(atoken, asecret)
    twitterStream = Stream(auth, listener())
    twitterStream.filter(track=['bitcoin'])

if __name__ == "__main__":
  runBitcoin()
