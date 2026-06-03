#!/usr/bin/env python3
"""
Test script for Malayalam Movie Recommendation System
This script tests the core functionality without requiring user interaction
"""

def test_recommendation_system():
    """Test the recommendation system functionality"""
    try:
        from movie_recommender import MalayalamMovieRecommender, recommend_movie
        
        print("🧪 Testing Malayalam Movie Recommendation System")
        print("=" * 50)
        
        # Test 1: Initialize the system
        print("\n1. Testing system initialization...")
        recommender = MalayalamMovieRecommender("malayalam_movies_dataset.csv")
        
        if recommender.initialize_system():
            print("✅ System initialized successfully")
        else:
            print("❌ System initialization failed")
            return False
        
        # Test 2: Test standalone function
        print("\n2. Testing standalone recommend_movie function...")
        recommendations = recommend_movie("Drishyam", top_n=3)
        
        if recommendations and len(recommendations) > 0:
            print(f"✅ Found {len(recommendations)} recommendations for 'Drishyam'")
            for i, movie in enumerate(recommendations, 1):
                print(f"   {i}. {movie['title']} (Score: {movie['similarity_score']})")
        else:
            print("❌ No recommendations found")
            return False
        
        # Test 3: Test class-based approach
        print("\n3. Testing class-based recommendation...")
        recommendations = recommender.recommend_movie("Manichitrathazhu", top_n=3)
        
        if recommendations and len(recommendations) > 0:
            print(f"✅ Found {len(recommendations)} recommendations for 'Manichitrathazhu'")
            for i, movie in enumerate(recommendations, 1):
                print(f"   {i}. {movie['title']} (Score: {movie['similarity_score']})")
        else:
            print("❌ No recommendations found")
            return False
        
        # Test 4: Test with non-existent movie
        print("\n4. Testing with non-existent movie...")
        recommendations = recommender.recommend_movie("NonExistentMovie", top_n=3)
        
        if not recommendations:
            print("✅ Correctly handled non-existent movie")
        else:
            print("❌ Should not find recommendations for non-existent movie")
            return False
        
        # Test 5: Test available movies list
        print("\n5. Testing available movies list...")
        movies = recommender.get_available_movies()
        
        if movies and len(movies) > 0:
            print(f"✅ Found {len(movies)} movies in dataset")
            print(f"   Sample movies: {movies[:3]}")
        else:
            print("❌ No movies found in dataset")
            return False
        
        print("\n🎉 All tests passed! The recommendation system is working correctly.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all required packages are installed:")
        print("pip install pandas numpy scikit-learn")
        return False
        
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
        print("Make sure 'malayalam_movies_dataset.csv' exists in the current directory")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_specific_recommendations():
    """Test specific movie recommendations"""
    try:
        from movie_recommender import recommend_movie
        
        print("\n🎬 Testing Specific Movie Recommendations")
        print("=" * 40)
        
        test_movies = ["Drishyam", "Chemmeen", "Spadikam"]
        
        for movie in test_movies:
            print(f"\n📽️ Recommendations for '{movie}':")
            recommendations = recommend_movie(movie, top_n=2)
            
            if recommendations:
                for i, rec in enumerate(recommendations, 1):
                    print(f"   {i}. {rec['title']} (Score: {rec['similarity_score']})")
                    print(f"      Genre: {rec['genre']}")
                    print(f"      Director: {rec['director']}")
            else:
                print(f"   No recommendations found for '{movie}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in specific recommendations test: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Malayalam Movie Recommendation System Tests")
    print("=" * 60)
    
    # Run main tests
    main_test_passed = test_recommendation_system()
    
    if main_test_passed:
        # Run specific recommendation tests
        specific_test_passed = test_specific_recommendations()
        
        if specific_test_passed:
            print("\n✅ All tests completed successfully!")
            print("\nThe system is ready to use. You can now run:")
            print("  python demo.py          # Interactive demo")
            print("  python movie_recommender.py  # Basic functionality test")
        else:
            print("\n⚠️ Some specific tests failed, but core functionality works")
    else:
        print("\n❌ Core tests failed. Please check the installation and setup.")
        print("\nTroubleshooting:")
        print("1. Make sure Python is installed and in PATH")
        print("2. Install required packages: pip install pandas numpy scikit-learn")
        print("3. Ensure malayalam_movies_dataset.csv is in the current directory")



