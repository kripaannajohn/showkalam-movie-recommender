import webbrowser
import time
import subprocess
import sys
import os

def start_flask_and_view():
    print("Starting Malayalam Movie Booking System...")
    print("=" * 50)
    
    # Start Flask app
    print("Starting Flask application...")
    try:
        # Start Flask in background
        process = subprocess.Popen([sys.executable, "app.py"], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
        
        # Wait for server to start
        print("Waiting for server to start...")
        time.sleep(3)
        
        # Open browser
        print("Opening browser...")
        webbrowser.open("http://localhost:5000")
        
        print("\n" + "=" * 50)
        print("SUCCESS! The booking system is now running!")
        print("URL: http://localhost:5000")
        print("=" * 50)
        print("\nFeatures available:")
        print("- Browse Malayalam movies")
        print("- Select showtimes and theatres")
        print("- Interactive seat selection")
        print("- Payment processing")
        print("- QR-coded tickets")
        print("\nPress Ctrl+C to stop the server")
        
        # Keep the process running
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\nStopping server...")
            process.terminate()
            process.wait()
            print("Server stopped.")
            
    except Exception as e:
        print(f"Error starting Flask app: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure Flask is installed: pip install Flask")
        print("2. Check if port 5000 is available")
        print("3. Run manually: python app.py")

if __name__ == "__main__":
    start_flask_and_view()


