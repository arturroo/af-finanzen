from sklearn import preprocessing
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn import metrics
import numpy as np

# Assigning features and label variables
# First Feature
weather = ['Sunny','Sunny','Overcast','Rainy','Rainy','Rainy','Overcast','Sunny','Sunny','Rainy','Sunny','Overcast','Overcast','Rainy']
# Second Feature
temp = ['Hot','Hot','Hot','Mild','Cool','Cool','Cool','Mild','Cool','Mild','Mild','Mild','Hot','Mild']
# Label or target variable
play = ['No','No','Yes','Yes','Yes','No','Yes','No','Yes','Yes','Yes','Yes','Yes','No']

print('Weather',len(weather))
print('Temperature',len(temp))
print('Label',len(play))

le = preprocessing.LabelEncoder()

# Converting string labels into numbers.
weather_encoded = le.fit_transform(weather)
print('Weather Encoded',weather_encoded)

# Converting string labels into numbers.
temp_encoded = le.fit_transform(temp)
print('Temperature Encoded',temp_encoded)

label = np.array(le.fit_transform(play))
print('Label Encoded',label.shape)
print('Label Encoded',label)

features = np.array(list(zip(weather_encoded,temp_encoded)))
print('Features',features.shape)
print('Features',features)

# Splitting train : test to 80 : 20 ratio
X_train, X_test, y_train, y_test = train_test_split(features,label,test_size=0.3)
print('X Train', X_train.shape)
print('Y Train', y_train.shape)
print('X Test', X_test.shape)
print('Y Test', y_test.shape)

# Training the classifier
logreg = LogisticRegression()
logreg.fit(X_train,y_train)

# Testing the classifier
y_pred = logreg.predict(X_test)
print('Predicted',y_pred)
print('Actual data',y_test)

# A confusion matrix is a table that is used to evaluate the performance of a classification model.
# Diagonal values represent accurate predictions, while non-diagonal elements are inaccurate predictions.
cnf_matrix = metrics.confusion_matrix(y_test, y_pred)
print(cnf_matrix)

print("Accuracy:",metrics.accuracy_score(y_test, y_pred))
print("Precision:",metrics.precision_score(y_test, y_pred))
print("Recall:",metrics.recall_score(y_test, y_pred))