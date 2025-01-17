# Uses a Gaussian Naive Bayes classifier on a set of documents
# converted to tf (term frequency) arrays. Trains classifier on known documents
# Then runs trained classifier on a set of new documents to predict authors.
# Returns textual description of testing classifier results as a list.
# Background corpus: 1 long document each from 7 known authors from given directory.

# Training document set: 2 documents each from 7 randomly-chosen authors, two
# parts of the user's submitted writing sample.
# Testing document set: 2 more documents each from the same 7 authors,
# the rest of the submitted writing sample, message user wishes to test for
# anonymity.


import toponly, datetime, time
from  more_itertools import chunked
from sklearn.naive_bayes import GaussianNB
#sklearn 0.23+ has removed the sklearn.externals.joblib.
import joblib
from random import randint
from classif import tfidf

timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('_%Y-%m-%d_%H-%M-%S')

def classifydocs(listdir, authsfile, sampletext, messagetext, topnum = 1000):
    """Naive Bayes classifier returns classification for a given document,
    compared to another document by the same author, and 2 documents each from 7
    randomly chosen authors in the given directory. tf arrays created for (topnum)
    characters: 100, 1000, 10000 of the most common English words."""
    printclassify = []
    otherauths = []
    comparedocs = []
    comparedocstest = []
    targets = []
    authcount = 0

    # Choose other random authors from the background corpus
    while len(otherauths) < 3: #number of authors to compare to
        with open(authsfile) as listauths:
            allauths = listauths.readlines()
            auth = allauths[randint(0,len(allauths)-1)]
            if auth[:-1] in otherauths:
                pass
            else:
                otherauths.append(auth[:-1])

    # Each author has one long document of at least 50,000 words
    # Split this into 7,000-word non-consec chunks
    for a in otherauths:
        with open(listdir + a) as fulltext:
            fulltext = fulltext.read().split()
            fulltextdocs = chunked(fulltext,7000)
            fulltextdocs = list(fulltextdocs)
            comparedocs.append(toponly.top(' '.join(fulltextdocs[0]),topnum))
            comparedocs.append(toponly.top(' '.join(fulltextdocs[2]),topnum))
            comparedocstest.append(toponly.top(' '.join(fulltextdocs[4]),topnum))
            comparedocstest.append(toponly.top(' '.join(fulltextdocs[6]),topnum))
            targets.append(authcount)
            targets.append(authcount)
            authcount += 1

    # Set up targets list [0,0,1,1,...7,7]
    anontarget = targets[-1] + 1

    targets.append(anontarget)
    targets.append(anontarget)

    # Add submitted documents to the training and testing mini-corpora
    # Sample text is split into 3 chunks; 2 > train, 1 > test
    # Message text is added to test
    sampletext= sampletext.split()
    sampletext = chunked(sampletext, (len(sampletext) / 3))
    sampletext = list(sampletext)
    
    comparedocs.append(toponly.top(' '.join(sampletext[0]),topnum))
    comparedocs.append(toponly.top(' '.join(sampletext[1]),topnum))

    comparedocstest.append(toponly.top(' '.join(sampletext[2]),topnum))
    comparedocstest.append(toponly.top(messagetext,topnum))

    # Set up term frequency arrays for train and test document sets
    tfarray = tfidf(comparedocs).toarray()
    tfarraynew = tfidf(comparedocstest).toarray()

    # Set up classifier 
    gnb = GaussianNB()
    preds = gnb.fit(tfarray, targets).predict(tfarray)
    classifiername = 'useclassifier' + timestamp
    classif = joblib.dump(gnb,classifiername) #save classifier

    # Use trained classifier on new text, return score and message-specific report
    gnbtest = joblib.load(classif[0]) #must have saved a classifier previously
    predstest = gnbtest.predict(tfarraynew)
    scoretest =  "%.3f" % gnbtest.score(tfarraynew,targets)
    if predstest[-1] == anontarget:
        printclassify.append("Message is still attributed to you by this classifier.")
    else:
        printclassify.append("Message successfully anonymized for this classifier.")
    printclassify.append("Overall (testing) classifier score: " + str(scoretest))

    return printclassify
