from dash import Dash, html, dcc, Input, Output, callback
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from utils import check_required_files, load_app_data, get_movie_dropdown_options, create_movie_similarity_models, get_top_movie_recommendations

# Läsa igenom labb-instruktioner igen och måste skriva README

# Skapa en requirements.txt när det är klart. (pip installs som jag kan uninstall innan?)


# Check that the required files exists.
# If a file is missing, the program will stop executing.
check_required_files()

df_movies, df_ratings = load_app_data()
movie_rating_similarity_matrix, movie_tags_similarity_matrix = create_movie_similarity_models(df_movies, df_ratings)

movie_options = get_movie_dropdown_options(df_movies)

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], title='Movie Recommender')

app.layout = dbc.Container([
    dbc.Card([
        dbc.CardBody([
            html.H4('Movie Recommender', style={ 'margin': '0' }),
        ])
    ]),
    dbc.Card(
        dbc.CardBody([
            html.Div([
                html.Label('Select a movie:', htmlFor='movie-select-dropdown'),
                dcc.Dropdown(movie_options, id='movie-select-dropdown'),
            ], style={ 'marginBottom': '1rem' }),
            dcc.Loading([
                dag.AgGrid(
                    id='movie-recommendations-table',
                    columnDefs = [
                        {
                            'field': 'title',
                            'headerName': 'Title',
                            'cellStyle': { 'fontWeight': 'bold' },
                        },
                        {
                            'field': 'genres',
                            'headerName': 'Genres',
                        },
                        {
                            'field': 'similarity_percent',
                            'headerName': 'Recommendation Match',
                            'valueFormatter': { 'function': 'params.value + "%"' },
                            'cellStyle': {
                                'function': 'recommendationMatchStyle(params.value)' # Style the column rows by the recommendation match value.
                            }
                        },
                    ],
                    rowData=[],
                    columnSize='sizeToFit', # Make the columns fill upp the full table width.
                    dashGridOptions={
                        'pagination': True,
                        'paginationPageSize': 10,
                        'paginationPageSizeSelector': False, # Prevent user from selecting amount of rows per page.
                    },
                    defaultColDef={
                        'sortable': False, # The columns are not sortable. Table should always be sorted by recommendation match.
                    },
                ),
            ]),
        ]),
        className='mt-3',
    )
])


# Callback function for when a movie in 'movie-select-dropdown' is selected.
@callback(
    Output('movie-recommendations-table', 'rowData'),
    Output('movie-recommendations-table', 'paginationGoTo'), # Using Output 'paginationGoTo', and returning the value 'first', makes the table go to first page whenever a new movie is selected.
    Input('movie-select-dropdown', 'value'),
    prevent_initial_call=True # Prevent the callback to be called on initial page load.
)
def update_movie_recommendations(movieId):
    if movieId is None:
        # If the movieId is not defined, exit the callback function and prevent update.
        raise PreventUpdate
    
    try:
        # Get recommended movies based on the selected movieId.
        movie_recommendations = get_top_movie_recommendations(movieId, df_movies, movie_rating_similarity_matrix, movie_tags_similarity_matrix)

        movie_recommendations['genres'] = movie_recommendations['genres'].apply(', '.join)
        movie_recommendations['similarity_percent'] = (movie_recommendations['final_similarity'] * 100).round(0).astype(int)

        # Convert the DataFrame to a list with every row as a dictionary.
        records = movie_recommendations.to_dict('records') 

        return records, 'first'
    
    except Exception as e:
        print(f"Error while getting movie recommendations: {e}")
        return [], 'first'  # Return empty data if error occurred.


if __name__ == '__main__':
    app.run()
