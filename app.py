import pickle
import streamlit as st
import requests
from fuzzywuzzy import process
from sklearn.neighbors import NearestNeighbors
from functools import lru_cache

# Set page configuration
st.set_page_config(page_title="Movie Recommender", page_icon=":clapper:", layout="wide")

# Load pickled data (replace file paths with your actual locations)
@st.cache_data
def load_data():
    return {
        'movies_tamil': pickle.load(open('Tamil_movies.pkl', 'rb')),
        'features_tamil': pickle.load(open('T_matrix.pkl', 'rb')),
        'movies_international': pickle.load(open('movie_list.pkl', 'rb')),
        'features_international': pickle.load(open('matrix.pkl', 'rb')),
        'movies_indian': pickle.load(open('Indian_movies.pkl', 'rb')),
        'features_indian': pickle.load(open('I_matrix.pkl', 'rb'))
    }

data = load_data()

# Fetch movie data from OMDb API
@st.cache_resource
@lru_cache(maxsize=128)
def fetch_data(movie_name):
    api_key = "4a7c8e91"  # Replace with your OMDb API key
    url = f"https://www.omdbapi.com/?apikey={api_key}&t={movie_name}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return (
            data.get('Year', 'N/A'),
            data.get('Director', 'N/A'),
            data.get('Actors', 'N/A'),
            data.get('Plot', 'N/A'),
            data.get('Poster', None)
        )
    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error occurred: {http_err}")
    except requests.exceptions.RequestException as err:
        st.error(f"Error: {err}")
    return None, None, None, None, None

def recommend(movie, movies_df, features):
    try:
        index = movies_df[movies_df['Title'].str.lower() == movie.lower()].index[0]
        knn = NearestNeighbors(n_neighbors=6, algorithm='auto')
        knn.fit(features)
        distances, indices = knn.kneighbors(features[index].reshape(1, -1))
        return [movies_df.iloc[i].Title for i in indices.flatten()[1:]]
    except IndexError:
        st.warning("Movie not found in the database.")
        return []

def fuzzy_search(search_term, movie_list, threshold=80):
    return [movie for movie, score in process.extract(search_term, movie_list, limit=10) if score >= threshold]

def display(selected_movie, features, movies):
    col1, col2 = st.columns([1, 2])
    movie_details = fetch_data(selected_movie)

    if movie_details:
        with col1:
            if movie_details[4]:  # Check if poster URL is available
                poster_html = f'<a href="https://www.google.com/search?q={selected_movie}" target="_blank"><img src="{movie_details[4]}" width="230"></a>'
                st.markdown(poster_html, unsafe_allow_html=True)
            else:
                st.write("Poster not available.")

        with col2:
            st.markdown(f"### {selected_movie}")
            st.write("---")
            st.write(f"**Year**: {movie_details[0]}")
            st.write(f"**Director**: {movie_details[1]}")
            st.write(f"**Actors**: {movie_details[2]}")
            st.write(f"**Plot**: {movie_details[3]}")

        st.markdown('## Similar Movies:')
        
        recommended_movie_names = recommend(selected_movie.lower(), movies, features)
        if recommended_movie_names:
            cols = st.columns(5)
            for col, movie_name in zip(cols, recommended_movie_names):
                col.text(movie_name)
                recommended_details = fetch_data(movie_name)
                if recommended_details and recommended_details[4]:
                    poster_html = f'<a href="https://www.google.com/search?q={movie_name}" target="_blan "><img src="{recommended_details[4]}" width="100%"></a>'
                    col.markdown(poster_html, unsafe_allow_html=True)
                else:
                    col.write("Poster not available.")
        else:
            st.write("No similar movies found.")
    else:
        st.warning("Movie details not available.")

# Sidebar for language selection and search
with st.sidebar:
    st.header('🎬 Movie Recommender System')
    language_option = st.selectbox(
        'Choose your movie language:',
        ('International', 'Tamil', 'Indian')
    )

    # Search functionality
    search_term = st.text_input("🔍 Search for a movie:")
    if language_option == "Tamil":
        movies = data['movies_tamil']
        features = data['features_tamil']
        top_movies = ["Singam", "Billa", "Sivaji", "Vaaranam Aayiram", "Indian"]
    elif language_option == "Indian":
        movies = data['movies_indian']
        features = data['features_indian']
        top_movies = ["Jersey", "3 Idiots", "Dangal", "Pink", "Mahanati"]
    else:
        movies = data['movies_international']
        features = data['features_international']
        top_movies = ["Avengers: Age of Ultron", "2012", "The Dark Knight", "Spider-Man", "X-Men"]

    filtered_movies = fuzzy_search(search_term, movies['Title'].tolist()) if search_term else movies['Title'].tolist()
    selected_movie = st.selectbox("Select a Movie:", filtered_movies)

    if st.button('Recommend Movies'):
        if selected_movie:
            lowercase_movie = selected_movie.lower()
            if lowercase_movie in movies['Title'].str.lower().values:
                st.session_state["selected_movie"] = selected_movie
            else:
                st.warning("The selected movie is not found in the database.")
                st.session_state["selected_movie"] = None
        else:
            st.warning("Please select a movie before recommending.")


    if st.button('Clear Selection'):
        st.session_state["selected_movie"] = None

# Main content area
st.markdown('### Top Rated Movies:')

# Display the posters of the top 5 movies in a row
cols = st.columns(7)
for col, top_movie in zip(cols, top_movies):
    movie_details = fetch_data(top_movie)
    if movie_details and movie_details[4]:
        poster_html = f'<a href="https://www.google.com/search?q={top_movie}" target="_blank"><img src="{movie_details[4]}" width="100%"></a>'
        col.markdown(poster_html, unsafe_allow_html=True)
        if col.button(f"Select {top_movie}", key=top_movie):
            st.session_state["selected_movie"] = top_movie

# Placeholder for displaying selected movie details and recommendations
placeholder = st.empty()

if "selected_movie" in st.session_state and st.session_state["selected_movie"]:
    selected_movie = st.session_state["selected_movie"]
    with placeholder.container():
        display(selected_movie, features, movies)


# Footer section
st.markdown("---")
st.markdown("© 2024 Gowri Venkat| KeertheVasan T S . All rights reserved.")