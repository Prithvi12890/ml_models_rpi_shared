import numpy as np
import pickle

crop_recommendation_model_path = './m-project-rpi-shared/RandomForest.pkl'
crop_recommendation_model = pickle.load(
    open(crop_recommendation_model_path, 'rb'))

data = np.array([[60, 40, 50, 6.7]])
my_prediction = crop_recommendation_model.predict(data)
final_prediction = my_prediction[0]
print("my_prediction:", my_prediction)
print("final_prediction:", final_prediction)
print("type - my_prediction:", type(my_prediction))
