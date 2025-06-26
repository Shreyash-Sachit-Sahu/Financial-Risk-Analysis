import requests
import json
import unittest
import sys
from datetime import datetime

class FinancialAdvisorAPITester:
    def __init__(self, base_url="https://827cc846-429c-4211-a15a-6fb1f89affe4.preview.emergentagent.com"):
        self.base_url = base_url
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = {}

    def run_test(self, name, method, endpoint, expected_status, data=None, check_json=True):
        """Run a single API test"""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)

            success = response.status_code == expected_status
            
            # Try to parse JSON response
            response_data = None
            if check_json:
                try:
                    response_data = response.json()
                except:
                    success = False
                    print(f"❌ Failed - Could not parse JSON response: {response.text}")
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                if response_data:
                    print(f"Response: {json.dumps(response_data, indent=2)[:500]}...")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                if response.text:
                    print(f"Response: {response.text[:500]}...")

            self.test_results[name] = {
                'success': success,
                'status_code': response.status_code,
                'expected_status': expected_status,
                'response': response_data if response_data else response.text[:500]
            }

            return success, response_data if success and check_json else None

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.test_results[name] = {
                'success': False,
                'error': str(e)
            }
            return False, None

    def test_health_check(self):
        """Test the health check endpoint"""
        return self.run_test(
            "Health Check",
            "GET",
            "/",
            200
        )

    def test_market_data(self):
        """Test the market data endpoint"""
        return self.run_test(
            "Market Data",
            "GET",
            "/api/market-data",
            200
        )

    def test_create_profile(self):
        """Test creating a user profile"""
        test_profile = {
            "name": "Test User",
            "age": 30,
            "monthly_income": 75000,
            "monthly_expenses": 40000,
            "current_savings": 500000,
            "dependents": 2,
            "financial_goals": ["Retirement Planning", "Children Education"],
            "investment_experience": "intermediate",
            "risk_preference": "moderate",
            "investment_horizon": "medium",
            "emergency_fund": 200000
        }
        
        success, response = self.run_test(
            "Create Profile",
            "POST",
            "/api/profile",
            200,
            data=test_profile
        )
        
        if success and response and 'user_id' in response:
            self.user_id = response['user_id']
            print(f"Created user profile with ID: {self.user_id}")
        
        return success, response

    def test_risk_assessment(self):
        """Test the risk assessment endpoint"""
        if not self.user_id:
            print("❌ Cannot test risk assessment without a user ID")
            return False, None
        
        test_profile = {
            "user_id": self.user_id,
            "name": "Test User",
            "age": 30,
            "monthly_income": 75000,
            "monthly_expenses": 40000,
            "current_savings": 500000,
            "dependents": 2,
            "financial_goals": ["Retirement Planning", "Children Education"],
            "investment_experience": "intermediate",
            "risk_preference": "moderate",
            "investment_horizon": "medium",
            "emergency_fund": 200000
        }
        
        return self.run_test(
            "Risk Assessment",
            "POST",
            "/api/risk-assessment",
            200,
            data=test_profile
        )

    def test_recommendations(self):
        """Test the recommendations endpoint"""
        if not self.user_id:
            print("❌ Cannot test recommendations without a user ID")
            return False, None
        
        test_profile = {
            "user_id": self.user_id,
            "name": "Test User",
            "age": 30,
            "monthly_income": 75000,
            "monthly_expenses": 40000,
            "current_savings": 500000,
            "dependents": 2,
            "financial_goals": ["Retirement Planning", "Children Education"],
            "investment_experience": "intermediate",
            "risk_preference": "moderate",
            "investment_horizon": "medium",
            "emergency_fund": 200000
        }
        
        return self.run_test(
            "Investment Recommendations",
            "POST",
            "/api/recommendations",
            200,
            data=test_profile
        )

    def test_chat(self, message="What are the best investment options for a 30-year-old with moderate risk tolerance?"):
        """Test the chat endpoint with a specific message"""
        chat_data = {
            "message": message,
            "user_context": {
                "risk_category": "Moderate Risk",
                "age": 30,
                "income": 75000
            }
        }
        
        return self.run_test(
            f"AI Chat: {message[:30]}...",
            "POST",
            "/api/chat",
            200,
            data=chat_data
        )
        
    def test_chat_scenarios(self):
        """Test the chat endpoint with various financial questions"""
        chat_questions = [
            "How much emergency fund should I keep?",
            "What should I invest in?",
            "Should I start SIP?",
            "Which mutual funds are good?",
            "How to save taxes?",
            "Should I invest in stocks?",
            "How to plan for retirement?"
        ]
        
        results = []
        for question in chat_questions:
            success, response = self.test_chat(question)
            results.append({
                "question": question,
                "success": success,
                "response": response
            })
            
        # Print summary of chat tests
        print("\n" + "=" * 80)
        print("📱 Chat Functionality Test Results:")
        for result in results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} Question: {result['question']}")
            if result["success"] and result["response"]:
                print(f"   Response: {result['response']['response'][:100]}...")
        
        # Return overall success
        return all(result["success"] for result in results), results

    def test_portfolio(self):
        """Test the portfolio endpoint"""
        if not self.user_id:
            print("❌ Cannot test portfolio without a user ID")
            return False, None
        
        return self.run_test(
            "Portfolio Summary",
            "GET",
            f"/api/portfolio/{self.user_id}",
            200
        )

    def run_all_tests(self):
        """Run all API tests in sequence"""
        print("🚀 Starting API Tests for AI Financial Advisor")
        print(f"Base URL: {self.base_url}")
        print("=" * 80)
        
        # Test health check
        self.test_health_check()
        
        # Test market data
        self.test_market_data()
        
        # Test user profile creation
        self.test_create_profile()
        
        # Test risk assessment
        self.test_risk_assessment()
        
        # Test recommendations
        self.test_recommendations()
        
        # Test chat
        self.test_chat()
        
        # Test multiple chat scenarios
        self.test_chat_scenarios()
        
        # Test portfolio
        self.test_portfolio()
        
        # Print summary
        print("\n" + "=" * 80)
        print(f"📊 Tests passed: {self.tests_passed}/{self.tests_run}")
        print(f"Success rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Return overall success
        return self.tests_passed == self.tests_run, self.test_results

class TestFinancialAdvisorAPI(unittest.TestCase):
    def test_api_endpoints(self):
        tester = FinancialAdvisorAPITester()
        success, results = tester.run_all_tests()
        self.assertTrue(success, f"API tests failed: {json.dumps(results, indent=2)}")

if __name__ == "__main__":
    # Run as standalone script
    tester = FinancialAdvisorAPITester()
    success, results = tester.run_all_tests()
    sys.exit(0 if success else 1)