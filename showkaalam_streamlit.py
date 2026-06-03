"""
ShowKaalam - Streamlit Integrated Movie Recommendation and Booking System
Complete system with AI recommendations, search, and booking functionality
"""

import streamlit as st
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import sqlite3
import qrcode
import io
import base64
from datetime import datetime, timedelta
import re

# Page configuration
st.set_page_config(
    page_title="ShowKaalam - Movie Booking & Recommendations",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #ff6b35, #004e89);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .movie-card {
        background: linear-gradient(135deg, #2d2d2d, #1a1a1a);
        padding: 1.5rem;
        border-radius: 15px;
        border: 2px solid #ff6b35;
        margin-bottom: 1rem;
        color: white;
    }
    .recommendation-card {
        background: linear-gradient(135deg, #667eea, #764ba2);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        color: white;
    }
    .seat-grid {
        display: grid;
        grid-template-columns: repeat(10, 1fr);
        gap: 5px;
        max-width: 500px;
        margin: 0 auto;
    }
    .seat {
        width: 30px;
        height: 30px;
        border-radius: 5px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.7rem;
        font-weight: bold;
        cursor: pointer;
    }
    .seat.available {
        background: #28a745;
        color: white;
    }
    .seat.selected {
        background: #ff6b35;
        color: white;
    }
    .seat.occupied {
        background: #6c757d;
        color: white;
    }
    .search-box {
        background: rgba(255,255,255,0.1);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

class MovieRecommender:
    """AI Movie Recommendation System"""
    
    def __init__(self):
        self.tfidf_matrix = None
        self.tfidf_vectorizer = None
        self.similarity_matrix = None
        self.movies_df = None
        
    def load_movies_from_csv(self):
        """Load movies from CSV file"""
        try:
            self.movies_df = pd.read_csv('malayalam_movies_dataset.csv')
            return True
        except Exception as e:
            st.error(f"Error loading movies: {e}")
            return False
    
    def preprocess_text(self, text):
        """Clean and preprocess text data"""
        if pd.isna(text):
            return ""
        text = str(text).lower()
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def create_feature_matrix(self):
        """Create TF-IDF feature matrix"""
        try:
            # Create combined features
            self.movies_df['combined_features'] = (
                self.movies_df['genre'].fillna('') + ' ' +
                self.movies_df['description'].fillna('') + ' ' +
                self.movies_df['director'].fillna('') + ' ' +
                self.movies_df['cast'].fillna('')
            )
            
            # Clean the text data
            self.movies_df['combined_features'] = self.movies_df['combined_features'].apply(
                self.preprocess_text
            )
            
            # Initialize TF-IDF vectorizer
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2)
            )
            
            # Fit and transform
            self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(
                self.movies_df['combined_features']
            )
            
            return True
        except Exception as e:
            st.error(f"Error creating TF-IDF matrix: {e}")
            return False
    
    def calculate_similarity_matrix(self):
        """Calculate cosine similarity matrix"""
        try:
            self.similarity_matrix = cosine_similarity(self.tfidf_matrix)
            return True
        except Exception as e:
            st.error(f"Error calculating similarity: {e}")
            return False
    
    def initialize_system(self):
        """Initialize the complete recommendation system"""
        if not self.load_movies_from_csv():
            return False
        if not self.create_feature_matrix():
            return False
        if not self.calculate_similarity_matrix():
            return False
        return True
    
    def get_recommendations(self, movie_title, top_n=5):
        """Get movie recommendations"""
        if self.movies_df is None or self.similarity_matrix is None:
            return []
        
        # Find movie index
        movie_indices = self.movies_df[
            self.movies_df['title'].str.lower().str.strip() == movie_title.lower().strip()
        ].index
        
        if len(movie_indices) == 0:
            return []
        
        movie_index = movie_indices[0]
        
        # Get similarity scores
        similarity_scores = list(enumerate(self.similarity_matrix[movie_index]))
        similarity_scores = sorted(similarity_scores, key=lambda x: x[1], reverse=True)
        
        # Get top N similar movies
        top_similar_movies = similarity_scores[1:top_n+1]
        
        recommendations = []
        for idx, score in top_similar_movies:
            movie_info = {
                'title': self.movies_df.iloc[idx]['title'],
                'genre': self.movies_df.iloc[idx]['genre'],
                'description': self.movies_df.iloc[idx]['description'],
                'director': self.movies_df.iloc[idx]['director'],
                'cast': self.movies_df.iloc[idx]['cast'],
                'similarity_score': round(score, 4)
            }
            recommendations.append(movie_info)
        
        return recommendations
    
    def search_movies(self, query):
        """Search for movies"""
        if self.movies_df is None:
            return []
        
        matching_movies = self.movies_df[
            self.movies_df['title'].str.lower().str.contains(query.lower(), na=False)
        ]
        
        return matching_movies.to_dict('records')

def init_database():
    """Initialize SQLite database"""
    conn = sqlite3.connect('database/movies.db')
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            genre TEXT,
            description TEXT,
            director TEXT,
            cast TEXT,
            poster_url TEXT,
            duration INTEGER,
            rating TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS theatres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location TEXT,
            total_seats INTEGER DEFAULT 100
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS showtimes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id INTEGER,
            theatre_id INTEGER,
            show_date DATE,
            show_time TIME,
            price DECIMAL(10,2),
            FOREIGN KEY (movie_id) REFERENCES movies (id),
            FOREIGN KEY (theatre_id) REFERENCES theatres (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS seats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            showtime_id INTEGER,
            seat_number TEXT,
            is_booked BOOLEAN DEFAULT FALSE,
            booking_id INTEGER,
            FOREIGN KEY (showtime_id) REFERENCES showtimes (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id INTEGER,
            showtime_id INTEGER,
            seat_numbers TEXT,
            total_amount DECIMAL(10,2),
            payment_method TEXT,
            booking_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            customer_name TEXT,
            customer_email TEXT,
            FOREIGN KEY (movie_id) REFERENCES movies (id),
            FOREIGN KEY (showtime_id) REFERENCES showtimes (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def populate_sample_data():
    """Populate database with sample data"""
    conn = sqlite3.connect('database/movies.db')
    cursor = conn.cursor()
    
    # Check if data exists
    cursor.execute('SELECT COUNT(*) FROM movies')
    if cursor.fetchone()[0] > 0:
        conn.close()
        return
    
    # Insert movies
    movies = [
        ('Drishyam', 'Thriller', 'A father goes to extreme lengths to protect his family after his daughter commits a crime', 'Mohanlal', 'Mohanlal, Meena, Ansiba Hassan', '/static/posters/drishyam.jpg', 160, 'U/A'),
        ('Manichitrathazhu', 'Horror', 'A newlywed couple moves into a haunted mansion with a dark past', 'Fazil', 'Mohanlal, Shobana, Vincent', '/static/posters/manichitrathazhu.jpg', 180, 'U/A'),
        ('Chemmeen', 'Romance', 'A tragic love story between a fisherman and a woman from a different caste', 'Ramu Kariat', 'Sathyan, Sheela, Kottarakkara Sreedharan Nair', '/static/posters/chemmeen.jpg', 120, 'U'),
        ('Spadikam', 'Action', 'A rebellious young man\'s journey from childhood to adulthood', 'Bhadran', 'Mohanlal, Urvashi, Thilakan', '/static/posters/spadikam.jpg', 150, 'U/A'),
        ('Kireedam', 'Drama', 'A young man\'s life changes when he intervenes in a fight', 'Sibi Malayil', 'Mohanlal, Parvathy, Thilakan', '/static/posters/kireedam.jpg', 140, 'U/A'),
        ('Thaniyavarthanam', 'Drama', 'A teacher struggles with mental illness and societal stigma', 'Sibi Malayil', 'Mohanlal, Shobana, Murali', '/static/posters/thaniyavarthanam.jpg', 130, 'U/A'),
        ('Chithram', 'Comedy', 'A man pretends to be married to avoid his family\'s pressure', 'Priyadarshan', 'Mohanlal, Ranjini, Kanaka', '/static/posters/chithram.jpg', 120, 'U'),
        ('Vadakkunokkiyantram', 'Comedy', 'A man\'s obsession with his neighbor leads to comedic situations', 'Sathyan Anthikad', 'Mohanlal, Shobana, Jagathy Sreekumar', '/static/posters/vadakkunokkiyantram.jpg', 110, 'U'),
        ('Devasuram', 'Action', 'A powerful man\'s fall from grace and his path to redemption', 'I.V. Sasi', 'Mohanlal, Revathi, Innocent', '/static/posters/devasuram.jpg', 170, 'U/A'),
        ('Thoovanathumbikal', 'Romance', 'A complex love triangle involving a man and two women', 'P. Padmarajan', 'Mohanlal, Parvathy, Sumalatha', '/static/posters/thoovanathumbikal.jpg', 160, 'U/A')
    ]
    
    cursor.executemany('''
        INSERT INTO movies (title, genre, description, director, cast, poster_url, duration, rating)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', movies)
    
    # Insert theatres
    theatres = [
        ('PVR Cinemas', 'Kochi', 100),
        ('INOX', 'Thiruvananthapuram', 120),
        ('Cinepolis', 'Kozhikode', 80),
        ('Sree Padmanabha Theatre', 'Thiruvananthapuram', 150)
    ]
    
    cursor.executemany('''
        INSERT INTO theatres (name, location, total_seats)
        VALUES (?, ?, ?)
    ''', theatres)
    
    # Insert showtimes
    today = datetime.now().date()
    showtimes = []
    for movie_id in range(1, 11):
        for theatre_id in range(1, 5):
            for time_slot in ['10:00', '14:00', '18:00', '22:00']:
                showtimes.append((movie_id, theatre_id, today, time_slot, 150.00))
                showtimes.append((movie_id, theatre_id, today + timedelta(days=1), time_slot, 150.00))
    
    cursor.executemany('''
        INSERT INTO showtimes (movie_id, theatre_id, show_date, show_time, price)
        VALUES (?, ?, ?, ?, ?)
    ''', showtimes)
    
    # Initialize seats
    cursor.execute('SELECT id FROM showtimes')
    showtime_ids = cursor.fetchall()
    
    for (showtime_id,) in showtime_ids:
        for row in range(1, 11):
            for seat in range(1, 11):
                seat_number = f"{chr(64 + row)}{seat:02d}"
                cursor.execute('''
                    INSERT INTO seats (showtime_id, seat_number, is_booked)
                    VALUES (?, ?, FALSE)
                ''', (showtime_id, seat_number))
    
    conn.commit()
    conn.close()

def generate_qr_code(booking_data):
    """Generate QR code for booking"""
    qr_data = f"""
ShowKaalam - When It's Showtime, It's ShowKaalam

Movie: {booking_data['movie_title']}
Theatre: {booking_data['theatre_name']}
Date: {booking_data['show_date']}
Time: {booking_data['show_time']}
Seats: {booking_data['seat_numbers']}
Total: ₹{booking_data['total_amount']}
Booking ID: {booking_data['booking_id']}
    """.strip()
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return qr_code_base64

# Initialize session state
if 'recommender' not in st.session_state:
    st.session_state.recommender = MovieRecommender()
    st.session_state.recommender.initialize_system()

if 'selected_seats' not in st.session_state:
    st.session_state.selected_seats = []

if 'booking_data' not in st.session_state:
    st.session_state.booking_data = None

# Initialize database
init_database()
populate_sample_data()

# Main App
def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🎬 ShowKaalam</h1>
        <p>When It's Showtime, It's ShowKaalam - AI-Powered Movie Recommendations & Booking</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("🎭 Navigation")
    page = st.sidebar.selectbox("Choose a page:", [
        "🏠 Home & Search",
        "🧠 AI Recommendations", 
        "🎫 Book Tickets",
        "📱 My Bookings"
    ])
    
    if page == "🏠 Home & Search":
        home_page()
    elif page == "🧠 AI Recommendations":
        recommendations_page()
    elif page == "🎫 Book Tickets":
        booking_page()
    elif page == "📱 My Bookings":
        bookings_page()

def home_page():
    """Homepage with search functionality"""
    st.header("🔍 Search Movies")
    
    # Search box
    st.markdown('<div class="search-box">', unsafe_allow_html=True)
    search_query = st.text_input("Search for a Malayalam movie:", placeholder="Enter movie title...")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if search_query:
        # Search movies
        search_results = st.session_state.recommender.search_movies(search_query)
        
        if search_results:
            st.success(f"Found {len(search_results)} movies matching '{search_query}'")
            
            for movie in search_results:
                with st.container():
                    st.markdown(f"""
                    <div class="movie-card">
                        <h3>{movie['title']}</h3>
                        <p><strong>Genre:</strong> {movie['genre']}</p>
                        <p><strong>Director:</strong> {movie['director']}</p>
                        <p><strong>Cast:</strong> {movie['cast']}</p>
                        <p><strong>Description:</strong> {movie['description']}</p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.warning(f"No movies found matching '{search_query}'")
    
    # Show all movies
    st.header("🎬 All Movies")
    
    if st.session_state.recommender.movies_df is not None:
        movies = st.session_state.recommender.movies_df.to_dict('records')
        
        for movie in movies:
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"""
                    <div class="movie-card">
                        <h3>{movie['title']}</h3>
                        <p><strong>Genre:</strong> {movie['genre']}</p>
                        <p><strong>Director:</strong> {movie['director']}</p>
                        <p><strong>Cast:</strong> {movie['cast']}</p>
                        <p><strong>Description:</strong> {movie['description']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    if st.button(f"Get Recommendations", key=f"rec_{movie['title']}"):
                        st.session_state.selected_movie = movie['title']
                        st.rerun()

def recommendations_page():
    """AI Recommendations page"""
    st.header("🧠 AI Movie Recommendations")
    
    if 'selected_movie' in st.session_state:
        movie_title = st.session_state.selected_movie
    else:
        # Movie selection
        if st.session_state.recommender.movies_df is not None:
            movie_options = st.session_state.recommender.movies_df['title'].tolist()
            movie_title = st.selectbox("Select a movie to get recommendations:", movie_options)
        else:
            st.error("No movies available")
            return
    
    if movie_title:
        st.subheader(f"🎬 Recommendations for: {movie_title}")
        
        # Get recommendations
        recommendations = st.session_state.recommender.get_recommendations(movie_title, top_n=5)
        
        if recommendations:
            st.success(f"Found {len(recommendations)} similar movies!")
            
            for i, rec in enumerate(recommendations, 1):
                similarity_percent = round(rec['similarity_score'] * 100, 1)
                
                with st.container():
                    st.markdown(f"""
                    <div class="recommendation-card">
                        <h4>{i}. {rec['title']}</h4>
                        <p><strong>Match:</strong> {similarity_percent}%</p>
                        <p><strong>Genre:</strong> {rec['genre']}</p>
                        <p><strong>Director:</strong> {rec['director']}</p>
                        <p><strong>Cast:</strong> {rec['cast']}</p>
                        <p><strong>Description:</strong> {rec['description']}</p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.warning("No recommendations found for this movie")

def booking_page():
    """Movie booking page"""
    st.header("🎫 Book Movie Tickets")
    
    # Get movies from database
    conn = sqlite3.connect('database/movies.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, title FROM movies')
    movies = cursor.fetchall()
    
    if not movies:
        st.error("No movies available for booking")
        return
    
    # Movie selection
    movie_options = {f"{movie[1]} (ID: {movie[0]})": movie[0] for movie in movies}
    selected_movie_display = st.selectbox("Select a movie:", list(movie_options.keys()))
    selected_movie_id = movie_options[selected_movie_display]
    
    # Get showtimes
    cursor.execute('''
        SELECT s.id, s.show_date, s.show_time, s.price, t.name as theatre_name, t.location
        FROM showtimes s
        JOIN theatres t ON s.theatre_id = t.id
        WHERE s.movie_id = ? AND s.show_date >= DATE('now')
        ORDER BY s.show_date, s.show_time
    ''', (selected_movie_id,))
    
    showtimes = cursor.fetchall()
    
    if not showtimes:
        st.warning("No showtimes available for this movie")
        return
    
    # Showtime selection
    showtime_options = {f"{showtime[4]} - {showtime[1]} {showtime[2]} (₹{showtime[3]})": showtime[0] for showtime in showtimes}
    selected_showtime_display = st.selectbox("Select showtime:", list(showtime_options.keys()))
    selected_showtime_id = showtime_options[selected_showtime_display]
    
    # Get seat availability
    cursor.execute('''
        SELECT seat_number, is_booked
        FROM seats
        WHERE showtime_id = ?
        ORDER BY seat_number
    ''', (selected_showtime_id,))
    
    seats = cursor.fetchall()
    conn.close()
    
    # Seat selection
    st.subheader("🎯 Select Your Seats")
    
    # Create seat grid
    seat_grid = {}
    for seat_number, is_booked in seats:
        seat_grid[seat_number] = is_booked
    
    # Display seat grid
    st.markdown("""
    <div style="text-align: center; margin: 20px 0;">
        <div style="background: #ff6b35; color: white; padding: 10px; border-radius: 5px; margin-bottom: 20px;">
            🎬 SCREEN
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Seat legend
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("🟢 Available")
    with col2:
        st.markdown("🟠 Selected")
    with col3:
        st.markdown("🔴 Occupied")
    
    # Seat selection interface
    selected_seats = []
    
    # Create seat buttons in grid format
    rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
    
    for row in rows:
        cols = st.columns(10)
        for i, col in enumerate(cols, 1):
            seat_number = f"{row}{i:02d}"
            is_booked = seat_grid.get(seat_number, False)
            
            if is_booked:
                col.markdown(f"🔴")
            else:
                if col.button(seat_number, key=f"seat_{seat_number}", disabled=is_booked):
                    if seat_number not in st.session_state.selected_seats:
                        st.session_state.selected_seats.append(seat_number)
                    else:
                        st.session_state.selected_seats.remove(seat_number)
                    st.rerun()
    
    # Show selected seats
    if st.session_state.selected_seats:
        st.success(f"Selected seats: {', '.join(st.session_state.selected_seats)}")
        
        # Customer details
        st.subheader("👤 Customer Details")
        customer_name = st.text_input("Full Name:", placeholder="Enter your full name")
        customer_email = st.text_input("Email:", placeholder="Enter your email")
        
        # Payment method
        payment_method = st.selectbox("Payment Method:", ["Cash", "Card", "UPI"])
        
        # Calculate total
        if showtimes:
            price_per_seat = showtimes[0][3]  # Get price from first showtime
            total_amount = price_per_seat * len(st.session_state.selected_seats)
            
            st.subheader("💰 Booking Summary")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Selected Seats:** {', '.join(st.session_state.selected_seats)}")
                st.write(f"**Price per seat:** ₹{price_per_seat}")
                st.write(f"**Total Amount:** ₹{total_amount}")
            
            with col2:
                st.write(f"**Movie:** {selected_movie_display}")
                st.write(f"**Showtime:** {selected_showtime_display}")
                st.write(f"**Payment:** {payment_method}")
            
            # Book button
            if st.button("🎫 Book Now", type="primary"):
                if customer_name and customer_email:
                    # Create booking
                    conn = sqlite3.connect('database/movies.db')
                    cursor = conn.cursor()
                    
                    try:
                        # Insert booking
                        cursor.execute('''
                            INSERT INTO bookings (movie_id, showtime_id, seat_numbers, total_amount, payment_method, customer_name, customer_email)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (selected_movie_id, selected_showtime_id, ','.join(st.session_state.selected_seats), total_amount, payment_method, customer_name, customer_email))
                        
                        booking_id = cursor.lastrowid
                        
                        # Mark seats as booked
                        for seat in st.session_state.selected_seats:
                            cursor.execute('''
                                UPDATE seats SET is_booked = TRUE, booking_id = ?
                                WHERE showtime_id = ? AND seat_number = ?
                            ''', (booking_id, selected_showtime_id, seat))
                        
                        conn.commit()
                        
                        # Store booking data for confirmation
                        st.session_state.booking_data = {
                            'booking_id': booking_id,
                            'movie_title': selected_movie_display,
                            'theatre_name': showtimes[0][4],
                            'show_date': showtimes[0][1],
                            'show_time': showtimes[0][2],
                            'seat_numbers': ', '.join(st.session_state.selected_seats),
                            'total_amount': total_amount,
                            'customer_name': customer_name,
                            'customer_email': customer_email,
                            'payment_method': payment_method
                        }
                        
                        st.success("🎉 Booking successful!")
                        st.balloons()
                        
                        # Clear selected seats
                        st.session_state.selected_seats = []
                        
                    except Exception as e:
                        st.error(f"Booking failed: {e}")
                        conn.rollback()
                    
                    finally:
                        conn.close()
                else:
                    st.error("Please fill in all customer details")

def bookings_page():
    """View bookings and generate QR codes"""
    st.header("📱 My Bookings")
    
    if st.session_state.booking_data:
        booking = st.session_state.booking_data
        
        st.success("🎫 Your Latest Booking")
        
        # Display booking details
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Booking ID:** {booking['booking_id']}")
            st.write(f"**Movie:** {booking['movie_title']}")
            st.write(f"**Theatre:** {booking['theatre_name']}")
            st.write(f"**Date:** {booking['show_date']}")
            st.write(f"**Time:** {booking['show_time']}")
        
        with col2:
            st.write(f"**Seats:** {booking['seat_numbers']}")
            st.write(f"**Total:** ₹{booking['total_amount']}")
            st.write(f"**Payment:** {booking['payment_method']}")
            st.write(f"**Customer:** {booking['customer_name']}")
        
        # Generate QR code
        st.subheader("📱 Digital Ticket (QR Code)")
        
        qr_code = generate_qr_code(booking)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(f"data:image/png;base64,{qr_code}", width=300)
        
        # Download button
        st.download_button(
            label="📥 Download QR Code",
            data=base64.b64decode(qr_code),
            file_name=f"showkaalam_ticket_{booking['booking_id']}.png",
            mime="image/png"
        )
        
        # Clear booking data
        if st.button("🗑️ Clear Booking Data"):
            st.session_state.booking_data = None
            st.rerun()
    
    else:
        st.info("No bookings found. Book a ticket to see your bookings here!")

if __name__ == "__main__":
    main()
