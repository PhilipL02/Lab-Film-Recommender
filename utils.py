import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
from sklearn.feature_extraction.text import TfidfVectorizer
import os
import sys

def check_required_data_files() -> None:
    """
    Check that all required data files exist. Stops program execution if any file is missing.
    """
    required_data_files = [
        './data/tags.csv',
        './data/movies.csv',
        './data/ratings.csv',
    ]

    missing_files = [file for file in required_data_files if not os.path.exists(file)]

    if missing_files:
        print(f'The following required data files are missing: ({', '.join(missing_files)})')
        print('Program execution stopped.')
        sys.exit()


def get_movie_dropdown_options(df_movies: pd.DataFrame) -> list:
    """
    Create and return movie dropdown options from the provided movies DataFrame.
    """
    movie_dropdown_options = [{ 'label': title, 'value': movieId } for title, movieId in zip(df_movies['title'], df_movies['movieId'])]
    
    return sorted(movie_dropdown_options, key=lambda d: d['label'])


def filter_out_popular_movies(df_ratings: pd.DataFrame, min_amount_ratings=1000) -> pd.DataFrame:
    # Get the number of ratings per movie.
    movie_counts = df_ratings['movieId'].value_counts()

    # Get movieIds of the movies with enough amount of ratings.
    popular_movieIds = movie_counts[movie_counts >= min_amount_ratings].index

    # Return the ratings for only the filtered movies.
    return df_ratings[df_ratings['movieId'].isin(popular_movieIds)]


def filter_out_expert_users(df_ratings: pd.DataFrame, min_amount_ratings=1000) -> pd.DataFrame:
    # Get the number of ratings per user.
    user_counts = df_ratings['userId'].value_counts()
    
    # Get userIds of the users with enough amount of ratings.
    expert_userIds = user_counts[user_counts >= min_amount_ratings].index
    
    # Return the ratings for only the filtered users.
    return df_ratings[df_ratings['userId'].isin(expert_userIds)]


def process_movie_genres(df_movies: pd.DataFrame) -> pd.DataFrame:
    # Replace '(no genres listed)' with an empty string.
    df_movies.loc[df_movies['genres'] == '(no genres listed)', 'genres'] = ''
    
    # Split genres by '|' into a list.
    df_movies['genres'] = df_movies['genres'].apply(lambda x: x.split('|'))

    return df_movies


def load_app_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Reads, filter, process and return DataFrames for movies and ratings.

    Returns:
        tuple:
            - pd.DataFrame: Movies DataFrame
            - pd.DataFrame: Ratings DataFrame
    """
    df_movies = pd.read_csv('./data/movies.csv')
    df_ratings = pd.read_csv('./data/ratings.csv', usecols=['userId', 'movieId', 'rating'])

    # Filter out movies and users with at least a minimum number of ratings.
    df_ratings = filter_out_popular_movies(df_ratings, min_amount_ratings=1000)
    df_ratings = filter_out_expert_users(df_ratings, min_amount_ratings=1000)
    
    # Filter df_movies to include only those movies that have ratings in df_ratings.
    df_movies = df_movies[df_movies['movieId'].isin(df_ratings['movieId'].unique())].reset_index(drop=True)

    df_movies = process_movie_genres(df_movies)
    
    df_movies = add_movie_tags_data(df_movies)

    return df_movies, df_ratings


def add_movie_tags_data(df_movies: pd.DataFrame) -> pd.DataFrame:
    """
    Enhances the given movies DataFrame by adding a combined 'tag' column.

    This function reads the 'tags.csv'-data and adds all tags together with the genres into a single space-separated string for every movie.
    """
    df_tags = pd.read_csv('./data/tags.csv', usecols=['userId', 'movieId', 'tag'])
    df_tags.dropna(inplace=True)
    
    # Keep only tags for movies present in df_movies.
    df_tags = df_tags[df_tags['movieId'].isin(df_movies['movieId'])]

    # Combine all tags for each movie into a single string.
    tags_per_movie = df_tags.groupby('movieId')['tag'].apply(' '.join).reset_index()

    # Add the column 'tag' with all combined tags to the movies DataFrame.
    df_movies = df_movies.merge(tags_per_movie, on='movieId', how='left')

    df_movies['tag'] = df_movies['tag'].fillna('')

    # Add the genres seperated by space to the tag-column.
    df_movies['tag'] = df_movies['genres'].apply(' '.join) + ' ' + df_movies['tag']
    
    return df_movies


def normalize_similarity_scores(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """
    Normalize the values in the specified columns of a DataFrame to the range [0, 1].
    """
    scaler = MinMaxScaler()
    df[columns] = scaler.fit_transform(df[columns])
    return df


def calculate_final_similarity(
        df_movies: pd.DataFrame, 
        rating_sim_scores: np.ndarray, 
        tag_sim_scores: np.ndarray, 
        movieId: int, 
        weight_ratings: float=0.7, 
        weight_tags: float=0.3
    ) -> pd.DataFrame:
    """
    Compute a final similarity score for each movie based on a weighted combination 
    of ratings-based and tags-based similarity scores.
    """
    df_movies['ratings_similarity'] = rating_sim_scores
    df_movies['tags_similarity'] = tag_sim_scores

    # Normalize similarity scores to [0, 1].
    df_movies = normalize_similarity_scores(df_movies, ['ratings_similarity', 'tags_similarity'])

    df_movies['final_similarity'] = (
        weight_ratings * df_movies['ratings_similarity'] + 
        weight_tags * df_movies['tags_similarity']
    )

    # Exclude the provided movieId from the result.
    df_movies = df_movies[df_movies['movieId'] != movieId]

    return df_movies


def get_top_movie_recommendations(
        df_movies: pd.DataFrame, 
        movie_rating_similarity_matrix: np.ndarray, 
        movie_tags_similarity_matrix: np.ndarray, 
        movieId: int, 
        top_n=50
    ) -> pd.DataFrame:
    if movieId not in df_movies['movieId'].values:
        print(f'Movie with movieId {movieId} does not exist in the movie DataFrame.')
        return pd.DataFrame()

    # Get the index of the selected movie in the movies DataFrame.
    chosen_movie_index = df_movies.index[df_movies['movieId'] == movieId][0]

    # Get the similarity scores for the chosen movie.
    rating_sim_scores = movie_rating_similarity_matrix[chosen_movie_index]
    tag_sim_scores = movie_tags_similarity_matrix[chosen_movie_index]

    # Create copy of movies DataFrame where the similarity scores will be added.
    movie_recommendations = df_movies.copy()

    movie_recommendations = calculate_final_similarity(movie_recommendations, rating_sim_scores, tag_sim_scores, movieId)

    movie_recommendations = movie_recommendations.sort_values(by='final_similarity', ascending=False).head(top_n)

    return movie_recommendations[['movieId', 'title', 'genres', 'final_similarity']]


def create_rating_similarity_matrix(df_ratings: pd.DataFrame) -> np.ndarray:
    user_movie_rating_design_matrix = df_ratings.pivot_table(index='movieId', columns='userId', values='rating')
    user_movie_rating_design_matrix.fillna(0, inplace=True)

    # Standardize ratings per movie:
    # It ensures similarity is calculated based on rating patterns and not absolute values.
    scaler = StandardScaler(with_mean=True, with_std=True)
    scaled = scaler.fit_transform(user_movie_rating_design_matrix)
    
    return cosine_similarity(scaled)


def create_tags_similarity_matrix(df_movies: pd.DataFrame) -> np.ndarray:
    tfidf_vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf_vectorizer.fit_transform(df_movies['tag'])

    return cosine_similarity(tfidf_matrix)


def create_movie_similarity_models(df_movies: pd.DataFrame, df_ratings: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    movie_rating_similarity_matrix = create_rating_similarity_matrix(df_ratings)

    movie_tags_similarity_matrix = create_tags_similarity_matrix(df_movies)

    return movie_rating_similarity_matrix, movie_tags_similarity_matrix
