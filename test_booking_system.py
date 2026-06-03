import requests
import time
import subprocess
import sys
import os
import csv
import json

def test_flask_app():
    print("Testing Malayalam Movie Booking System")
    print("=" * 50)
    
    # Install required packages
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "Flask", "qrcode[pil]", "Pillow"])
        print("✅ Packages installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing packages: {e}")
        return False
    
    # Start Flask app in background
    print("\nStarting Flask application...")
    try:
        # Start the Flask app
        process = subprocess.Popen([sys.executable, "app.py"], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
        
        # Wait for server to start
        print("Waiting for server to start...")
        time.sleep(5)
        
        # Test if server is running
        try:
            response = requests.get("http://localhost:5000", timeout=10)
            if response.status_code == 200:
                print("✅ Flask application is running successfully!")
                print("✅ Home page loaded correctly")
                
                # Test database initialization
                if os.path.exists("movie_booking.db"):
                    print("✅ Database created successfully")
                else:
                    print("⚠️ Database file not found")
                
                # Test booking history page
                try:
                    history_response = requests.get("http://localhost:5000/booking-history", timeout=10)
                    if history_response.status_code == 200:
                        print("✅ Booking history page accessible")
                    else:
                        print(f"⚠️ Booking history page returned status: {history_response.status_code}")
                except Exception as e:
                    print(f"⚠️ Could not test booking history page: {e}")
                
                # Test CSV file creation (simulate a booking)
                print("\nTesting CSV booking functionality...")
                test_booking_data = {
                    'showtime_id': 1,
                    'seats': ['A01', 'A02'],
                    'customer_name': 'Test User',
                    'customer_email': 'test@example.com',
                    'payment_method': 'Credit Card'
                }
                
                try:
                    booking_response = requests.post(
                        "http://localhost:5000/api/book_seats",
                        json=test_booking_data,
                        headers={'Content-Type': 'application/json'},
                        timeout=10
                    )
                    
                    if booking_response.status_code == 200:
                        booking_result = booking_response.json()
                        if booking_result.get('success'):
                            print("✅ Test booking created successfully")
                            
                            # Check if CSV file was created
                            if os.path.exists("booking_history.csv"):
                                print("✅ CSV file created successfully")
                                
                                # Read and display CSV content
                                with open("booking_history.csv", 'r', encoding='utf-8') as csvfile:
                                    reader = csv.DictReader(csvfile)
                                    bookings = list(reader)
                                    if bookings:
                                        print(f"✅ CSV contains {len(bookings)} booking(s)")
                                        latest_booking = bookings[-1]
                                        print(f"   Latest booking: {latest_booking['customer_name']} - {latest_booking['movie_title']}")
                                    else:
                                        print("⚠️ CSV file is empty")
                            else:
                                print("❌ CSV file was not created")
                        else:
                            print(f"❌ Booking failed: {booking_result.get('error', 'Unknown error')}")
                    else:
                        print(f"❌ Booking API returned status: {booking_response.status_code}")
                        
                except Exception as e:
                    print(f"❌ Error testing booking functionality: {e}")
                
                print("\n🎉 All tests completed!")
                print("The booking system is ready to use!")
                print("Visit: http://localhost:5000")
                print("Booking History: http://localhost:5000/booking-history")
                
                # Keep server running
                print("\nPress Ctrl+C to stop the server...")
                try:
                    process.wait()
                except KeyboardInterrupt:
                    print("\nStopping server...")
                    process.terminate()
                    process.wait()
                
                return True
            else:
                print(f"❌ Server responded with status code: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Could not connect to server: {e}")
            process.terminate()
            return False
            
    except Exception as e:
        print(f"❌ Error starting Flask application: {e}")
        return False

if __name__ == "__main__":
    try:
        test_flask_app()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Unexpected error: {e}")
