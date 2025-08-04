import numpy as np
import pandas as pd
import scipy.optimize
from .models import Movie, Myrating # Make sure these are imported from your app's models

# --- Normalization function ---
def normalizeRatings(Y, R):
    Ymean = np.zeros((Y.shape[0], 1))
    Ynorm = np.zeros(Y.shape)
    for i in range(Y.shape[0]):
        idx = np.where(R[i, :] == 1)[0]
        if idx.size > 0: # Avoid division by zero if no ratings for a movie
            Ymean[i] = np.mean(Y[i, idx])
            Ynorm[i, idx] = Y[i, idx] - Ymean[i]
        else:
            Ymean[i] = 0 # If no ratings, mean is 0
            Ynorm[i, :] = Y[i, :] # No change
    return Ynorm, Ymean

# --- Flatten/Reshape parameters ---
def flattenParams(X, Theta):
    return np.concatenate((X.flatten(), Theta.flatten()))

def reshapeParams(flattened_params, num_movies, num_users, num_features):
    X = flattened_params[0:num_movies * num_features].reshape((num_movies, num_features))
    Theta = flattened_params[num_movies * num_features:].reshape((num_users, num_features))
    return X, Theta

# --- CORRECTED: Cost function for Collaborative Filtering (returns only scalar J) ---
def cofiCostFunc(params, Y, R, num_features, reg_param=0.01):
    num_movies, num_users = Y.shape
    X, Theta = reshapeParams(params, num_movies, num_users, num_features)

    J = 0.5 * np.sum(np.square((X.dot(Theta.T) - Y) * R)) + \
        0.5 * reg_param * np.sum(np.square(X)) + \
        0.5 * reg_param * np.sum(np.square(Theta))
    return J # Only return the scalar cost

# --- NEW: Gradient function for Collaborative Filtering (returns only gradient array) ---
def cofiGradFunc(params, Y, R, num_features, reg_param=0.01):
    num_movies, num_users = Y.shape
    X, Theta = reshapeParams(params, num_movies, num_users, num_features)

    X_grad = ((X.dot(Theta.T) - Y) * R).dot(Theta) + reg_param * X
    Theta_grad = ((X.dot(Theta.T) - Y) * R).T.dot(X) + reg_param * Theta

    grad = flattenParams(X_grad, Theta_grad)
    return grad # Only return the gradient array

# --- Myrecommend function ---
def Myrecommend():
    df = pd.DataFrame(list(Myrating.objects.all().values()))

    # Handle case where there are no ratings yet
    if df.empty:
        # Return empty matrices or handle as per your application's logic
        # For recommendations, returning 0-sized matrices or specific defaults might be necessary
        # Here, returning small matrices with 0 predictions and 0 mean
        # You might need to adjust logic in views.py if these are empty
        return np.array([[0]]), np.array([0]) 

    # Create ID to index mappings for robust matrix indexing
    unique_movie_ids = sorted(df['movie_id'].unique())
    movie_id_to_idx = {movie_id: idx for idx, movie_id in enumerate(unique_movie_ids)}

    unique_user_ids = sorted(df['user_id'].unique())
    user_id_to_idx = {user_id: idx for idx, user_id in enumerate(unique_user_ids)}

    num_movies = len(unique_movie_ids)
    num_users = len(unique_user_ids)
    num_features = 10 # Number of latent features

    Y = np.zeros((num_movies, num_users))
    R = np.zeros((num_movies, num_users))

    for index, row in df.iterrows():
        movie_idx = movie_id_to_idx[row['movie_id']]
        user_idx = user_id_to_idx[row['user_id']]
        Y[movie_idx, user_idx] = row['rating']
        R[movie_idx, user_idx] = 1

    Ynorm, Ymean = normalizeRatings(Y, R)

    X = np.random.rand(num_movies, num_features)
    Theta = np.random.rand(num_users, num_features)
    initial_params = flattenParams(X, Theta)

    max_iter = 100
    reg_param = 1.0

    # CORRECTED: Call fmin_cg with separate fun (cost) and fprime (gradient)
    result = scipy.optimize.fmin_cg(
        f=cofiCostFunc,     # Function that returns scalar cost
        x0=initial_params,
        fprime=cofiGradFunc, # Function that returns gradient vector
        args=(Ynorm, R, num_features, reg_param), # Arguments common to both functions
        maxiter=max_iter,
        disp=False
    )

    optimized_params = result[0] if isinstance(result, tuple) else result
    resX, resTheta = reshapeParams(optimized_params, num_movies, num_users, num_features)

    prediction_matrix = resX.dot(resTheta.T)

    return prediction_matrix, Ymean