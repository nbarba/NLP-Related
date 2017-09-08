#!/usr/bin/python

import numpy as np
import pandas as pd
import sys, getopt
from sklearn.svm import SVC
from sklearn.metrics import classification_report
from sklearn.metrics import accuracy_score
from sklearn.metrics import confusion_matrix
import math
import os.path
import argparse


class EmbeddingFeaturesGenerator:

	def __init__(self,embeddings_file="./wiki_embeddings.txt",embedding_size=200,verbose=1):
		#read embeddings from txt and add header
		self._verbose=verbose;
		if self._verbose:
			print "Reading word embeddings...."
		embd_df=pd.read_csv(embeddings_file, header=None, delimiter=r"\s+", index_col = False)
		cols=["embd_"+str(i) for i in range(embedding_size+1)]
		cols[0]="word";	
		embd_df.columns= cols;
		self._embedding_size=embedding_size;
		self.embeddings=embd_df


	@property
	def embeddings(self):
		return self._embeddings


	@embeddings.setter
	def embeddings(self,value):
		self._embeddings=value

	def get_word_embedding(self,word):
		return self.embeddings.loc[self.embeddings['word'] == word, self.embeddings.dtypes == float].as_matrix();

	def extract_features(self,filename):

		if self._verbose:
			print "Extracting embedding representation for file",filename,":"

		X=np.empty(shape=[0, 2*self._embedding_size])
		Y=[]

		#get number of lines
		num_lines = sum(1 for line in open(filename))
	
		f = open(filename)
		line = f.readline()
		cnt=0

		while line:
			parts=line.split('\t');
			label=parts[0];
			sentence=parts[1];
		
			utternace=sentence.strip();

			words=sentence.split();	

			arr = np.empty(shape=[0, self._embedding_size])
	
			#put all embeddings for this sentence in an array
			for word in words:
				arr=np.append(arr,self.get_word_embedding(word),axis=0)
			#get the min & max, and concatenate them.
			
			if arr.size==0:
				arr=np.zeros((2,self._embedding_size));
		
			#keep min and max embeddings as representative of a sentence
			min_embedding=np.amin(arr,axis=0)
			max_embedding=np.amax(arr,axis=0)
			feature=np.concatenate((min_embedding,max_embedding),axis=0)
			
			#append to X,Y
			X=np.append(X,np.reshape(feature,(1,2*self._embedding_size)),axis=0);
			Y.append(label);


			if self._verbose:
				percentage=cnt/(num_lines*1.0)
				sys.stdout.write('\r')
				sys.stdout.write("[%-100s] %d%%" % ('='*int(percentage*100), percentage*100))
				sys.stdout.flush()

			cnt=cnt+1;
			line = f.readline()
		f.close()

		if self._verbose:
			sys.stdout.write("\n");

		return X,Y


def main(train_set,test_set,embeddings_file="./wiki_embeddings.txt"):
	
	if not os.path.exists(embeddings_file):
		print "Downloading pre-trained word embeddings...."
		os.system('wget https://www.dropbox.com/s/h87tstu4awtvgew/wiki_embeddings.txt')

	feature_gen=EmbeddingFeaturesGenerator(embeddings_file);

	print "-------- Feature Extraction --------";

	X_train,Y_train=feature_gen.extract_features(train_set)
	X_test,Y_test=feature_gen.extract_features(test_set)

	print "-------- Training SVM --------";

	classifier = SVC()
	classifier.fit(X_train, np.asarray(Y_train))
	
	print "-------- Predicting --------";

	predicted=classifier.predict(X_test)

	print "-------- Classification Results --------";
	print(classification_report(Y_test, predicted))
	print(accuracy_score(Y_test, predicted))
	print(confusion_matrix(Y_test, predicted))


if __name__ == "__main__":

	parser = argparse.ArgumentParser(description='Text-based classification using word-embedding representation')
	parser.add_argument('--train_set', metavar='path', required=True, help='File containing sentences to be used for training')
	parser.add_argument('--test_set', metavar='path', required=True, help='File containing sentences to be used for testing')
	parser.add_argument('--embeddings_file', metavar='path', required=False, help='Text file containing pre-trained word embeddings')
	args = parser.parse_args()
	
	main(train_set=args.train_set,test_set=args.test_set,embeddings_file=args.embeddings_file)