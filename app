from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
import qrcode
import io
import base64
from datetime import datetime, timedelta
import os
import csv
import pandas as pd

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# CSV files
BOOKING_CSV_FILE = 'booking_history.csv'
MOVIES_CSV_FILE = 'malayalam_movies_dataset.csv'

def save_booking_to_csv(booking_data):
    """
    Save booking details to CSV file
    """
    csv_exists = os.path.exists(BOOKING_CSV_FILE)
    
    with open(BOOKING_CSV_FILE, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['booking_id', 'customer_name', 'customer_email', 'movie_title', 
                     'theatre_name', 'show_date', 'show_time', 'seat_numbers', 
                     'total_amount', 'payment_method', 'booking_time']
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        # Write header if file is new
        if not csv_exists:
            writer.writeheader()
        
        writer.writerow(booking_data)

def load_movies_from_csv():
    """
    Load movies from CSV dataset
    """
    movies = []
    
    if os.path.exists(MOVIES_CSV_FILE):
        try:
            with open(MOVIES_CSV_FILE, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    # Convert CSV row to tuple format compatible with existing templates
                    movie = (
                        int(row['movie_id']),  # id
                        row['title'],          # title
                        row['genre'],          # genre
                        row['description'],   # description
                        row['director'],      # director
                        row['cast'],           # cast
                        '/static/posters/default.jpg',  # poster_url (placeholder)
                        'U/A',                # rating (default)
                        120                   # duration (default)
                    )
                    movies.append(movie)
        except Exception as e:
            print(f"Error loading movies from CSV: {e}")
    
    return movies

def search_movies_in_csv(query):
    """
    Search movies in CSV dataset
    """
    movies = load_movies_from_csv()
    
    if not query:
        return movies
    
    query_lower = query.lower()
    filtered_movies = []
    
    for movie in movies:
        # Search in title, genre, description, director, and cast
        if (query_lower in movie[1].lower() or  # title
            query_lower in movie[2].lower() or  # genre
            query_lower in movie[3].lower() or  # description
            query_lower in movie[4].lower() or  # director
            query_lower in movie[5].lower()):   # cast
            filtered_movies.append(movie)
    
    return filtered_movies

def generate_showtimes_for_movie(movie_id):
    """
    Generate showtimes for a movie (simulated data)
    """
    from datetime import datetime, timedelta
    
    # Sample theatres
    theatres = [
        {'id': 1, 'name': 'PVR Cinemas', 'location': 'Kochi'},
        {'id': 2, 'name': 'INOX', 'location': 'Thiruvananthapuram'},
        {'id': 3, 'name': 'Cinepolis', 'location': 'Kozhikode'},
        {'id': 4, 'name': 'Sree Padmanabha Theatre', 'location': 'Thiruvananthapuram'}
    ]
    
    # Sample showtimes
    time_slots = ['10:00', '14:00', '18:00', '22:00']
    showtimes = []
    
    for i, theatre in enumerate(theatres):
        for j, time_slot in enumerate(time_slots):
            showtime_id = movie_id * 100 + i * 10 + j + 1
            showtimes.append({
                'id': showtime_id,
                'movie_id': movie_id,
                'theatre_id': theatre['id'],
                'theatre_name': theatre['name'],
                'location': theatre['location'],
                'show_date': (datetime.now() + timedelta(days=j)).strftime('%Y-%m-%d'),
                'show_time': time_slot,
                'price': 150.00,
                'available_seats': 100 - (j * 10)  # Simulate some seats already booked
            })
    
    return showtimes

def get_movie_recommendations(movie_id, limit=6):
    """
    Get AI-powered recommendations for a movie
    """
    movies = load_movies_from_csv()
    
    # Find the target movie
    target_movie = None
    for movie in movies:
        if movie[0] == movie_id:
            target_movie = movie
            break
    
    if not target_movie:
        return []
    
    recommendations = []
    target_genre = target_movie[2]
    target_director = target_movie[4]
    
    # Score movies based on similarity
    for movie in movies:
        if movie[0] == movie_id:  # Skip the same movie
            continue
            
        score = 0
        
        # Genre match (highest priority)
        if movie[2] == target_genre:
            score += 10
        
        # Director match
        if movie[4] == target_director:
            score += 5
        
        # Cast similarity (simple check for common actors)
        target_cast = set(target_movie[5].lower().split(', '))
        movie_cast = set(movie[5].lower().split(', '))
        common_cast = target_cast.intersection(movie_cast)
        if common_cast:
            score += len(common_cast) * 2
        
        # Description similarity (simple keyword matching)
        target_desc_words = set(target_movie[3].lower().split())
        movie_desc_words = set(movie[3].lower().split())
        common_words = target_desc_words.intersection(movie_desc_words)
        if common_words:
            score += len(common_words) * 0.5
        
        if score > 0:
            recommendations.append((movie, score))
    
    # Sort by score and return top recommendations
    recommendations.sort(key=lambda x: x[1], reverse=True)
    return [rec[0] for rec in recommendations[:limit]]

# Database initialization
def init_db():
    conn = sqlite3.connect('movie_booking.db')
    cursor = conn.cursor()
    
    # Create movies table
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
    
    # Create theatres table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS theatres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            location TEXT,
            total_seats INTEGER DEFAULT 100
        )
    ''')
    
    # Create showtimes table
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
    
    # Create seats table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS seats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            showtime_id INTEGER,
            seat_number TEXT,
            is_booked BOOLEAN DEFAULT FALSE,
            booking_id INTEGER,
            FOREIGN KEY (showtime_id) REFERENCES showtimes (id),
            FOREIGN KEY (booking_id) REFERENCES bookings (id)
        )
    ''')
    
    # Create bookings table
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

# Initialize database with sample data
def populate_sample_data():
    conn = sqlite3.connect('movie_booking.db')
    cursor = conn.cursor()
    
    # Check if data already exists
    cursor.execute('SELECT COUNT(*) FROM movies')
    if cursor.fetchone()[0] > 0:
        conn.close()
        return
    
    # Insert sample movies
    movies = [
        ('Drishyam', 'Thriller', 'A father goes to extreme lengths to protect his family', 'Mohanlal', 'Mohanlal, Meena, Ansiba Hassan', '/static/posters/drishyam.jpg', 160, 'U/A'),
        ('Manichitrathazhu', 'Horror', 'A newlywed couple moves into a haunted mansion', 'Fazil', 'Mohanlal, Shobana, Vincent', '/static/posters/manichitrathazhu.jpg', 180, 'U/A'),
        ('Chemmeen', 'Romance', 'A tragic love story between a fisherman and a woman', 'Ramu Kariat', 'Sathyan, Sheela', '/static/posters/chemmeen.jpg', 120, 'U'),
        ('Spadikam', 'Action', 'A rebellious young man\'s journey from childhood', 'Bhadran', 'Mohanlal, Urvashi, Thilakan', '/static/posters/spadikam.jpg', 150, 'U/A'),
        ('Kireedam', 'Drama', 'A young man\'s life changes when he intervenes', 'Sibi Malayil', 'Mohanlal, Parvathy, Thilakan', '/static/posters/kireedam.jpg', 140, 'U/A')
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
    for movie_id in range(1, 6):  # 5 movies
        for theatre_id in range(1, 5):  # 4 theatres
            for time_slot in ['10:00', '14:00', '18:00', '22:00']:
                showtimes.append((movie_id, theatre_id, today, time_slot, 150.00))
                showtimes.append((movie_id, theatre_id, today + timedelta(days=1), time_slot, 150.00))
    
    cursor.executemany('''
        INSERT INTO showtimes (movie_id, theatre_id, show_date, show_time, price)
        VALUES (?, ?, ?, ?, ?)
    ''', showtimes)
    
    # Initialize seats for each showtime
    cursor.execute('SELECT id FROM showtimes')
    showtime_ids = cursor.fetchall()
    
    for (showtime_id,) in showtime_ids:
        for row in range(1, 11):  # 10 rows
            for seat in range(1, 11):  # 10 seats per row
                seat_number = f"{chr(64 + row)}{seat:02d}"  # A01, A02, etc.
                cursor.execute('''
                    INSERT INTO seats (showtime_id, seat_number, is_booked)
                    VALUES (?, ?, FALSE)
                ''', (showtime_id, seat_number))
    
    conn.commit()
    conn.close()

@app.route('/')
def home():
    """
    Homepage displaying movie gallery from CSV dataset
    """
    movies = load_movies_from_csv()
    return render_template('movie_gallery.html', movies=movies)

@app.route('/search')
def search():
    """
    Search for movies in CSV dataset
    """
    query = request.args.get('q', '')
    if not query:
        return redirect(url_for('home'))
    
    movies = search_movies_in_csv(query)
    return render_template('movie_gallery.html', movies=movies, search_query=query)

@app.route('/recommendations/<int:movie_id>')
def get_recommendations(movie_id):
    """
    Get AI-powered recommendations for a movie from CSV dataset
    """
    movies = load_movies_from_csv()
    
    # Find the movie by ID
    movie = None
    for m in movies:
        if m[0] == movie_id:
            movie = m
            break
    
    if not movie:
        flash('Movie not found!', 'error')
        return redirect(url_for('home'))
    
    # Get AI-powered recommendations
    recommendations = get_movie_recommendations(movie_id, limit=6)
    
    return render_template('recommendation.html', movie=movie, recommendations=recommendations)

@app.route('/movie/<int:movie_id>')
def movie_details(movie_id):
    """
    Integrated movie details page with recommendations and booking
    """
    movies = load_movies_from_csv()
    
    # Find the movie by ID
    movie = None
    for m in movies:
        if m[0] == movie_id:
            movie = m
            break
    
    if not movie:
        flash('Movie not found!', 'error')
        return redirect(url_for('home'))
    
    # Get AI recommendations
    recommendations = get_movie_recommendations(movie_id, limit=4)
    
    # Generate showtimes for this movie
    showtimes = generate_showtimes_for_movie(movie_id)
    
    return render_template('movie_details_integrated.html', 
                         movie=movie, 
                         recommendations=recommendations,
                         showtimes=showtimes)

@app.route('/booking/<int:showtime_id>')
def booking(showtime_id):
    """
    Seat selection and booking page for CSV-based movies
    """
    # Extract movie_id from showtime_id (since we're using simulated showtimes)
    movie_id = showtime_id // 100
    
    movies = load_movies_from_csv()
    movie = None
    for m in movies:
        if m[0] == movie_id:
            movie = m
            break
    
    if not movie:
        flash('Movie not found!', 'error')
        return redirect(url_for('home'))
    
    # Generate showtimes for this movie
    showtimes = generate_showtimes_for_movie(movie_id)
    
    # Find the specific showtime
    showtime = None
    for st in showtimes:
        if st['id'] == showtime_id:
            showtime = st
            break
    
    if not showtime:
        flash('Showtime not found!', 'error')
        return redirect(url_for('movie_details', movie_id=movie_id))
    
    # Generate seat layout (simulated)
    seats = []
    for row in range(1, 11):  # 10 rows
        for seat_num in range(1, 11):  # 10 seats per row
            seat_number = f"{chr(64 + row)}{seat_num:02d}"
            is_booked = (row + seat_num) % 7 == 0  # Simulate some booked seats
            seats.append({
                'seat_number': seat_number,
                'is_booked': is_booked,
                'row': chr(64 + row),
                'number': seat_num
            })
    
    return render_template('booking.html', 
                         movie=movie,
                         showtime=showtime, 
                         seats=seats)

@app.route('/api/book_seats', methods=['POST'])
def book_seats():
    """
    API endpoint to book seats for CSV-based movies
    """
    data = request.json
    showtime_id = data['showtime_id']
    selected_seats = data['seats']
    customer_name = data['customer_name']
    customer_email = data['customer_email']
    payment_method = data['payment_method']
    
    try:
        # Extract movie_id from showtime_id
        movie_id = showtime_id // 100
        
        # Get movie details from CSV
        movies = load_movies_from_csv()
        movie = None
        for m in movies:
            if m[0] == movie_id:
                movie = m
                break
        
        if not movie:
            return jsonify({'success': False, 'error': 'Movie not found'})
        
        # Get showtime details
        showtimes = generate_showtimes_for_movie(movie_id)
        showtime = None
        for st in showtimes:
            if st['id'] == showtime_id:
                showtime = st
                break
        
        if not showtime:
            return jsonify({'success': False, 'error': 'Showtime not found'})
        
        # Calculate total amount
        price_per_seat = showtime['price']
        total_amount = price_per_seat * len(selected_seats)
        
        # Generate booking ID
        booking_id = int(datetime.now().strftime('%Y%m%d%H%M%S'))
        
        # Save booking details to CSV
        booking_data = {
            'booking_id': booking_id,
            'customer_name': customer_name,
            'customer_email': customer_email,
            'movie_title': movie[1],
            'theatre_name': showtime['theatre_name'],
            'show_date': showtime['show_date'],
            'show_time': showtime['show_time'],
            'seat_numbers': ','.join(selected_seats),
            'total_amount': total_amount,
            'payment_method': payment_method,
            'booking_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        save_booking_to_csv(booking_data)
        
        return jsonify({
            'success': True,
            'booking_id': booking_id,
            'total_amount': total_amount,
            'movie_title': movie[1],
            'theatre_name': showtime['theatre_name'],
            'show_date': showtime['show_date'],
            'show_time': showtime['show_time']
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/confirmation/<int:booking_id>')
def confirmation(booking_id):
    """
    Booking confirmation page with QR code for CSV-based bookings
    """
    # Read booking details from CSV
    booking = None
    if os.path.exists(BOOKING_CSV_FILE):
        try:
            with open(BOOKING_CSV_FILE, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if int(row['booking_id']) == booking_id:
                        booking = row
                        break
        except Exception as e:
            flash(f'Error reading booking details: {str(e)}', 'error')
    
    if not booking:
        flash('Booking not found!', 'error')
        return redirect(url_for('home'))
    
    # Generate QR code
    qr_data = f"""
ShowKaalam - When It's Showtime, It's ShowKaalam

Movie: {booking['movie_title']}
Theatre: {booking['theatre_name']}
Date: {booking['show_date']}
Time: {booking['show_time']}
Seats: {booking['seat_numbers']}
Total: ₹{booking['total_amount']}
Booking ID: {booking['booking_id']}
Customer: {booking['customer_name']}
    """.strip()
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 for HTML display
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return render_template('confirmation.html', booking=booking, qr_code=qr_code_base64)

@app.route('/booking-history')
def booking_history():
    """
    Display booking history from CSV file
    """
    bookings = []
    
    if os.path.exists(BOOKING_CSV_FILE):
        try:
            with open(BOOKING_CSV_FILE, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                bookings = list(reader)
        except Exception as e:
            flash(f'Error reading booking history: {str(e)}', 'error')
    
    return render_template('booking_history.html', bookings=bookings)

if __name__ == '__main__':
    print("Initializing database...")
    init_db()
    print("Populating sample data...")
    populate_sample_data()
    print("Starting Flask app...")
    print("Available routes:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule.rule} -> {rule.endpoint}")
    app.run(debug=True, host='127.0.0.1', port=5000)
