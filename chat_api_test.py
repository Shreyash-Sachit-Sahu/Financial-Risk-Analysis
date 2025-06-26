import requests
import json
import time

def test_chat_api():
    """Test the chat API directly with various financial questions"""
    base_url = "https://827cc846-429c-4211-a15a-6fb1f89affe4.preview.emergentagent.com"
    chat_endpoint = f"{base_url}/api/chat"
    
    # User context for personalized advice
    user_context = {
        "risk_category": "Moderate Risk",
        "age": 35,
        "income": 80000
    }
    
    # Test questions
    chat_questions = [
        "How much emergency fund should I keep?",
        "What should I invest in?",
        "Should I start SIP?",
        "Which mutual funds are good?",
        "How to save taxes?",
        "Should I invest in stocks?",
        "How to plan for retirement?"
    ]
    
    print("🤖 Testing AI Financial Advisor Chat API")
    print("=" * 80)
    
    results = []
    
    for question in chat_questions:
        print(f"\n📝 Testing question: '{question}'")
        
        try:
            # Prepare request data
            data = {
                "message": question,
                "user_context": user_context
            }
            
            # Send request
            response = requests.post(
                chat_endpoint,
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            
            # Process response
            if response.status_code == 200:
                response_data = response.json()
                print(f"✅ Success (Status: {response.status_code})")
                print(f"🤖 Response: {response_data['response']}")
                results.append({
                    "question": question,
                    "success": True,
                    "response": response_data['response']
                })
            else:
                print(f"❌ Failed (Status: {response.status_code})")
                print(f"Error: {response.text}")
                results.append({
                    "question": question,
                    "success": False,
                    "error": response.text
                })
        
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            results.append({
                "question": question,
                "success": False,
                "error": str(e)
            })
        
        # Small delay between requests
        time.sleep(1)
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 Chat API Test Results:")
    
    success_count = sum(1 for result in results if result["success"])
    print(f"Success rate: {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)")
    
    for result in results:
        status = "✅" if result["success"] else "❌"
        print(f"{status} Question: {result['question']}")
        if result["success"]:
            print(f"   Response: {result['response'][:100]}...")
        else:
            print(f"   Error: {result.get('error', 'Unknown error')}")
    
    return results

if __name__ == "__main__":
    test_chat_api()