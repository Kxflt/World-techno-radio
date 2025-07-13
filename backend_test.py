#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

class WorldTechnoRadioAPITester:
    def __init__(self, base_url="https://1b6f18fb-1213-49d6-ae3a-f1bc95050ef6.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_station = None

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else self.api_url
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict):
                        if 'stations' in response_data:
                            print(f"   Found {response_data.get('count', 0)} stations")
                        elif 'favorites' in response_data:
                            print(f"   Found {response_data.get('count', 0)} favorites")
                        elif 'message' in response_data:
                            print(f"   Message: {response_data['message']}")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Response: {response.text[:200]}")
                return False, {}

        except requests.exceptions.Timeout:
            print(f"❌ Failed - Request timeout (30s)")
            return False, {}
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        success, response = self.run_test(
            "Root API Endpoint",
            "GET",
            "",
            200
        )
        return success

    def test_get_all_stations(self):
        """Test getting all electronic stations"""
        success, response = self.run_test(
            "Get All Electronic Stations",
            "GET",
            "stations",
            200
        )
        if success and response.get('stations'):
            # Store first station for later tests
            stations = response['stations']
            if stations:
                self.test_station = stations[0]
                print(f"   Sample station: {self.test_station.get('name', 'Unknown')}")
        return success

    def test_get_stations_by_genre(self):
        """Test getting stations by specific genres"""
        genres = ['electronic', 'techno', 'house', 'trance', 'dance', 'edm']
        all_passed = True
        
        for genre in genres:
            success, response = self.run_test(
                f"Get {genre.title()} Stations",
                "GET",
                f"stations/{genre}",
                200
            )
            if not success:
                all_passed = False
        
        return all_passed

    def test_search_stations(self):
        """Test station search functionality"""
        search_queries = ['techno', 'electronic', 'radio']
        all_passed = True
        
        for query in search_queries:
            success, response = self.run_test(
                f"Search Stations: '{query}'",
                "GET",
                f"search/{query}",
                200
            )
            if not success:
                all_passed = False
        
        return all_passed

    def test_favorites_workflow(self):
        """Test complete favorites workflow: add, get, remove"""
        if not self.test_station:
            print("❌ No test station available for favorites testing")
            return False

        # Test adding to favorites
        favorite_data = {
            "stationuuid": self.test_station.get('stationuuid'),
            "name": self.test_station.get('name'),
            "url": self.test_station.get('url'),
            "country": self.test_station.get('country', ''),
            "tags": self.test_station.get('tags', '')
        }

        success1, response1 = self.run_test(
            "Add Station to Favorites",
            "POST",
            "favorites",
            200,
            data=favorite_data
        )

        # Test getting favorites
        success2, response2 = self.run_test(
            "Get Favorite Stations",
            "GET",
            "favorites",
            200
        )

        # Test removing from favorites
        success3, response3 = self.run_test(
            "Remove Station from Favorites",
            "DELETE",
            f"favorites/{self.test_station.get('stationuuid')}",
            200
        )

        return success1 and success2 and success3

    def test_error_handling(self):
        """Test error handling for invalid requests"""
        # Test invalid genre
        success1, _ = self.run_test(
            "Invalid Genre (should still work)",
            "GET",
            "stations/invalidgenre",
            200  # API might return empty results instead of error
        )

        # Test invalid search
        success2, _ = self.run_test(
            "Search with Special Characters",
            "GET",
            "search/%20%21%40%23",
            200  # API should handle encoded characters
        )

        # Test removing non-existent favorite
        success3, _ = self.run_test(
            "Remove Non-existent Favorite",
            "DELETE",
            "favorites/non-existent-uuid",
            404
        )

        return True  # Error handling tests are informational

def main():
    print("🎵 World Techno Radio API Testing Suite")
    print("=" * 50)
    
    tester = WorldTechnoRadioAPITester()
    
    # Run all tests
    tests = [
        ("Root API Endpoint", tester.test_root_endpoint),
        ("Get All Stations", tester.test_get_all_stations),
        ("Get Stations by Genre", tester.test_get_stations_by_genre),
        ("Search Stations", tester.test_search_stations),
        ("Favorites Workflow", tester.test_favorites_workflow),
        ("Error Handling", tester.test_error_handling),
    ]
    
    print(f"\nRunning {len(tests)} test suites...")
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            test_func()
        except Exception as e:
            print(f"❌ Test suite failed with exception: {e}")
    
    # Print final results
    print(f"\n{'='*50}")
    print(f"📊 Final Results:")
    print(f"   Tests Run: {tester.tests_run}")
    print(f"   Tests Passed: {tester.tests_passed}")
    print(f"   Success Rate: {(tester.tests_passed/tester.tests_run*100):.1f}%" if tester.tests_run > 0 else "No tests run")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed! API is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the API implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())