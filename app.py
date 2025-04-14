from dash import Dash, html, dcc, Input, Output, callback
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from utils import load_app_data, create_movie_options, get_recommended_movies, load_tags_data, create_design_matrix, make_model

df_movies, df_ratings = load_app_data()
df_movie_tags = load_tags_data(df_movies)
df_ratings = df_ratings.merge(df_movies, on="movieId")
movie_options = create_movie_options(df_movies)

design_matrix = create_design_matrix(df_ratings)
model = make_model(design_matrix)

tfidf_vectorizer = TfidfVectorizer(stop_words="english")

tfidf_matrix = tfidf_vectorizer.fit_transform(df_movie_tags['tag'])

cosine_sim = cosine_similarity(tfidf_matrix)

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], title="Movie Recommender")

app.layout = dbc.Container([
    dbc.Card([
        dbc.CardBody([
            html.H4("Movie Recommender", style={"margin": "0"}),
        ])
    ], style={"marginBottom": "1rem"}),
    dbc.Card(
        dbc.CardBody([
            html.Div([
                html.Label('Select a movie:'),
                dcc.Dropdown(movie_options, id='movie-select-dropdown'),
            ], style={"marginBottom": "1rem"}),
            # html.Div([
            #     'Välj genre:',
            #     dcc.Dropdown([{'label': "Alla", 'value': 0}], id='genre-select-dropdown'),
            # ]),
            dcc.Loading([
                dag.AgGrid(
                    id="movie-grid-table",
                    persistence=False,
                    columnDefs = [
                        {
                            "field": "title",
                            "headerName": "Title",
                            "cellStyle": {"fontWeight": "bold"},
                        },
                        {
                            "field": "genres",
                            "headerName": "Genres",
                        },
                        {
                            "headerName": "Recommendation Match",
                            "field": "similarity_percent",
                            "valueFormatter": {"function": "params.value + '%'"},
                            "cellStyle": {
                                "function": "RecommendationMatchStyle(params.value)"
                            }
                        },
                        {
                            "field": "ratings_similarity",
                        },
                        {
                            "field": "tags_similarity",
                        },
                    ],
                    rowData=[],
                    columnSize="sizeToFit",
                    dashGridOptions={
                        "pagination": True,
                        "paginationPageSizeSelector": False,
                        "animateRows": False,
                        "paginationPageSize": 10,
                    },
                    defaultColDef={"sortable": False},
                ),
            ]),
        ]),
        className="mt-3",
    )
])


def get_selected_movie(movieId):
    return df_movies[df_movies['movieId'] == movieId].iloc[0]


# @callback(
#     Output('genre-select-dropdown', 'options'),
#     Input('movie-select-dropdown', 'value'),
#     prevent_initial_call=True
# )
# def update_genre_options(movieId):
#     if movieId is None:
#         raise PreventUpdate
    
#     selected_movie = get_selected_movie(movieId)
#     genres = selected_movie["genres"]

#     genre_options = [{'label': "Alla", 'value': 0}]
#     for genre in genres:
#         genre_options.append({'label': genre, 'value': genre})

#     return genre_options


@callback(
    Output('movie-grid-table', 'rowData'),
    Output('movie-grid-table', 'paginationGoTo'),
    Input('movie-select-dropdown', 'value'),
    prevent_initial_call=True
)
def update_output(movieId):
    if movieId is None:
        raise PreventUpdate
    
    movie_recommendations = get_recommended_movies(movieId, df_movies, design_matrix, model, df_movie_tags, cosine_sim)

    movie_recommendations['genres'] = movie_recommendations['genres'].apply(', '.join)

    movie_recommendations['similarity_percent'] = (movie_recommendations['final_similarity'] * 100).round(0).astype(int)

    records = movie_recommendations.to_dict('records')

    return records, 'first'


if __name__ == '__main__':
    app.run()