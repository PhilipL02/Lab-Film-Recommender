import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler


def filter_out_popular_movies(df_ratings, min_ratings=100):
    movie_counts = df_ratings['movieId'].value_counts()
    popular_movie_ids = movie_counts[movie_counts >= min_ratings].index
    return df_ratings[df_ratings['movieId'].isin(popular_movie_ids)]


def filter_out_popular_users(df_ratings, min_ratings=100):
    user_counts = df_ratings['userId'].value_counts()
    expert_user_ids = user_counts[user_counts >= min_ratings].index
    return df_ratings[df_ratings['userId'].isin(expert_user_ids)]


def load_app_data():
    movies = pd.read_csv('./data/movies.csv')
    ratings = pd.read_csv('./data/ratings.csv')

    ratings.drop('timestamp', axis='columns', inplace=True)

    ratings = filter_out_popular_movies(ratings, min_ratings=1000)
    ratings = filter_out_popular_users(ratings, min_ratings=1000)

    # Fully ignore non-popular movies
    movieIds = ratings['movieId'].unique()
    movies = movies[movies['movieId'].isin(movieIds)].reset_index()

    mean_ratings = ratings.groupby('movieId')['rating'].mean().reset_index()

    mean_ratings.rename(columns={'rating': 'meanRating'}, inplace=True)

    ratings = ratings.merge(mean_ratings, on='movieId', how='left')

    ratings['rating'] = ratings['rating'] - ratings['meanRating']

    movies = movies.merge(mean_ratings, on='movieId', how='left')

    scaler = MinMaxScaler()

    ratings[['rating']] = scaler.fit_transform(ratings[['rating']])

    ratings.drop(['meanRating'], axis='columns', inplace=True)
    
    movies['genres'] = movies['genres'].apply(lambda x: x.split('|'))

    return movies, ratings


def create_movie_options(df_movies):
    movie_options = []
    for i, movie in df_movies.iterrows():
        movie_options.append({'label': movie['title'], 'value': movie['movieId']})

    movie_options = sorted(movie_options, key=lambda d: d['label'])

    return movie_options


def rating_recommendations(movieId, df_movies, design_matrix, similarity_score):
    where_value = np.where(design_matrix.index==movieId)

    if not len(where_value) or not len(where_value[0]):
        print("Movie does not exist")
        return

    main_movie_index = where_value[0][0]

    similar_movies = sorted(list(enumerate(similarity_score[main_movie_index])), key=lambda x: x[1], reverse=True)

    data = []
    for index, _ in similar_movies:
        index_value = design_matrix.index[index]
        if index_value in design_matrix.index:
            df_row = df_movies[df_movies['movieId'] == index_value].iloc[0]

            similarity_score_for_movie = similarity_score[main_movie_index][index]
            df_row["similarity"] = similarity_score_for_movie

            data.append(df_row)
        else:
            print(f"Index {index_value} finns inte i design_matrix.")
        
    data = pd.DataFrame(data)

    return data


def create_design_matrix(df_merged):
    design_matrix = df_merged.pivot_table(index='movieId', columns='userId', values='rating')
    design_matrix.fillna(0, inplace=True)

    return design_matrix


def make_model(matrix):
    scaler = StandardScaler(with_mean=True, with_std=True)
    scaled = scaler.fit_transform(matrix)
    sim_score = cosine_similarity(scaled)
    return sim_score


def load_tags_data(movies):
    tags = pd.read_csv('./data/tags.csv')
    
    tags.drop("timestamp", axis="columns", inplace=True)

    movieIds = movies["movieId"]

    tags = tags[tags["movieId"].isin(movieIds)]
    tags['tag'] = tags['tag'].astype(str)
    tags_per_movie = tags.groupby("movieId")[["tag"]].agg(' '.join)
    df_merged = movies.merge(tags_per_movie, on="movieId")
    df_merged['tag'] = movies['genres'].apply(' '.join) + " " + df_merged['tag']
    df_merged['tag'] = df_merged['tag'].fillna('')
    df_merged.drop("genres", axis="columns", inplace=True)
    
    return df_merged


def tag_similarity(df_movie_tags, cosine_sim, movieId):
    if movieId not in df_movie_tags["movieId"].values:
        raise ValueError(f"movieId {movieId} not found in dataframe.")
    
    chosen_movie_index = df_movie_tags.index[df_movie_tags["movieId"] == movieId][0]
    
    similarity_scores = cosine_sim[chosen_movie_index]

    similar_movies = []

    for i in range(len(similarity_scores)):
        similar_movies.append((i, similarity_scores[i]))

    similar_movies_sorted = sorted(similar_movies, key=lambda x: x[1], reverse=True)

    top_similar_movies = similar_movies_sorted

    indices, similarities = zip(*top_similar_movies)

    list_to_return = df_movie_tags.iloc[list(indices)].copy()

    list_to_return["similarity"] = similarities

    return list_to_return


def normalize_series(series):
    min_val = series.min()
    max_val = series.max()
    range_val = max_val - min_val

    # Hantera ifall range_val är 0, så vi inte delar med 0
    if range_val == 0:
        return pd.Series(0, index=series.index)
    else:
        return (series - min_val) / range_val


def get_recommended_movies(movieId, df_movies, design_matrix, model, df_movie_tags, cosine_sim):
    movie_recommendations = rating_recommendations(movieId, df_movies, design_matrix, model)

    tag_similarity_movies = tag_similarity(df_movie_tags, cosine_sim, movieId)

    movie_recommendations["similarity"] = normalize_series(movie_recommendations["similarity"])
    tag_similarity_movies["similarity"] = normalize_series(tag_similarity_movies["similarity"])

    for index, movie in movie_recommendations.iterrows():
        match = tag_similarity_movies[tag_similarity_movies["movieId"] == movie["movieId"]]
        
        if not match.empty:
            tags_sim = match.iloc[0]["similarity"]
            ratings_sim = movie["similarity"]

            # Weighted combination
            combined_sim = 0.7 * ratings_sim + 0.3 * tags_sim
            
            movie_recommendations.at[index, "ratings_similarity"] = ratings_sim
            movie_recommendations.at[index, "tags_similarity"] = tags_sim
            movie_recommendations.at[index, "final_similarity"] = combined_sim


    movie_recommendations = movie_recommendations[movie_recommendations["movieId"] != movieId]
    # Get top 50 recommended movies
    movie_recommendations = movie_recommendations.sort_values(by="final_similarity", ascending=False).head(50)

    return movie_recommendations
