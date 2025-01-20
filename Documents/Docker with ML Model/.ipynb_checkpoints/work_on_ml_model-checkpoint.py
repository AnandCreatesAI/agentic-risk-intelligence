from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split

from sklearn.ensemble import RandomForestClassifier

iris=load_iris()


X_train,X_test,y_train,y_test=train_test_split(iris.data,iris.target,test_size=0.2,random_state=42)

model=RandomForestClassifier(n_estimators=100,random_state=42)

