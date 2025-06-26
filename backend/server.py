from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import requests
import openai
from datetime import datetime
import json
import uuid
from motor.motor_asyncio import AsyncIOMotorClient

app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB setup
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(MONGO_URL)
db = client.financial_advisor

# API Configuration
ALPHA_VANTAGE_KEY = os.environ.get('ALPHA_VANTAGE_KEY', '6LPXA9N13LNCU6IC')
COINGECKO_KEY = os.environ.get('COINGECKO_KEY', 'CG-A7YUyvKL6by2PcNsLtB6AjLm')
OPENAI_KEY = os.environ.get('OPENAI_KEY', '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')

openai.api_key = OPENAI_KEY

# Pydantic Models
class UserProfile(BaseModel):
    user_id: str = None
    name: str
    age: int
    monthly_income: float
    monthly_expenses: float
    current_savings: float
    dependents: int
    financial_goals: List[str]
    investment_experience: str
    risk_preference: str
    investment_horizon: str
    emergency_fund: float

class RiskAssessment(BaseModel):
    user_id: str
    risk_score: float
    risk_category: str
    assessment_factors: Dict[str, Any]

class InvestmentRecommendation(BaseModel):
    user_id: str
    recommendations: List[Dict[str, Any]]
    allocation: Dict[str, float]
    reasoning: str
    timestamp: datetime

class ChatMessage(BaseModel):
    message: str
    user_context: Optional[Dict[str, Any]] = None

# Indian Market Data - Top stocks and mutual funds
INDIAN_STOCKS = {
    'large_cap': ['RELIANCE.BSE', 'TCS.BSE', 'HDFCBANK.BSE', 'ICICIBANK.BSE', 'INFY.BSE'],
    'mid_cap': ['TITAN.BSE', 'BAJFINANCE.BSE', 'MARUTI.BSE', 'ASIANPAINT.BSE'],
    'small_cap': ['TATAPOWER.BSE', 'ZEEL.BSE', 'SAIL.BSE']
}

MUTUAL_FUNDS = {
    'equity': {
        'large_cap': ['SBI Bluechip Fund', 'HDFC Top 100 Fund', 'ICICI Pru Bluechip Fund'],
        'mid_cap': ['HDFC Mid-Cap Opportunities Fund', 'SBI Magnum Midcap Fund'],
        'small_cap': ['SBI Small Cap Fund', 'HDFC Small Cap Fund']
    },
    'debt': ['SBI Short Term Debt Fund', 'HDFC Short Term Debt Fund', 'ICICI Pru Short Term Fund'],
    'hybrid': ['SBI Equity Hybrid Fund', 'HDFC Balanced Advantage Fund']
}

@app.get("/")
async def root():
    return {"message": "AI Financial Advisor API is running"}

@app.post("/api/profile")
async def create_user_profile(profile: UserProfile):
    try:
        if not profile.user_id:
            profile.user_id = str(uuid.uuid4())
        
        profile_dict = profile.dict()
        await db.user_profiles.insert_one(profile_dict)
        
        return {"status": "success", "user_id": profile.user_id, "message": "Profile created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/profile/{user_id}")
async def get_user_profile(user_id: str):
    try:
        profile = await db.user_profiles.find_one({"user_id": user_id})
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Remove MongoDB _id for JSON serialization
        profile.pop('_id', None)
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/risk-assessment")
async def assess_risk(profile: UserProfile):
    try:
        # Advanced Risk Assessment Algorithm
        risk_factors = {}
        total_score = 0
        
        # Age factor (0-25 points)
        if profile.age < 25:
            age_score = 25
        elif profile.age < 35:
            age_score = 20
        elif profile.age < 45:
            age_score = 15
        elif profile.age < 55:
            age_score = 10
        else:
            age_score = 5
        
        risk_factors['age'] = age_score
        total_score += age_score
        
        # Income vs Expenses ratio (0-20 points)
        disposable_income = profile.monthly_income - profile.monthly_expenses
        income_ratio = disposable_income / profile.monthly_income if profile.monthly_income > 0 else 0
        
        if income_ratio > 0.5:
            income_score = 20
        elif income_ratio > 0.3:
            income_score = 15
        elif income_ratio > 0.2:
            income_score = 10
        elif income_ratio > 0.1:
            income_score = 5
        else:
            income_score = 0
            
        risk_factors['income_ratio'] = income_score
        total_score += income_score
        
        # Investment experience (0-20 points)
        experience_scores = {
            'beginner': 5,
            'intermediate': 12,
            'experienced': 20
        }
        exp_score = experience_scores.get(profile.investment_experience.lower(), 5)
        risk_factors['experience'] = exp_score
        total_score += exp_score
        
        # Investment horizon (0-15 points)
        horizon_scores = {
            'short': 5,
            'medium': 10,
            'long': 15
        }
        horizon_score = horizon_scores.get(profile.investment_horizon.lower(), 5)
        risk_factors['horizon'] = horizon_score
        total_score += horizon_score
        
        # Emergency fund adequacy (0-10 points)
        emergency_months = profile.emergency_fund / profile.monthly_expenses if profile.monthly_expenses > 0 else 0
        if emergency_months >= 6:
            emergency_score = 10
        elif emergency_months >= 3:
            emergency_score = 7
        elif emergency_months >= 1:
            emergency_score = 4
        else:
            emergency_score = 0
            
        risk_factors['emergency_fund'] = emergency_score
        total_score += emergency_score
        
        # Determine risk category
        if total_score >= 70:
            risk_category = "High Risk"
        elif total_score >= 45:
            risk_category = "Moderate Risk"
        else:
            risk_category = "Low Risk"
        
        risk_assessment = RiskAssessment(
            user_id=profile.user_id,
            risk_score=total_score,
            risk_category=risk_category,
            assessment_factors=risk_factors
        )
        
        # Save to database
        await db.risk_assessments.insert_one(risk_assessment.dict())
        
        return risk_assessment.dict()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/market-data")
async def get_market_data():
    try:
        market_data = {}
        
        # Get data for top Indian stocks
        for category, stocks in INDIAN_STOCKS.items():
            market_data[category] = []
            for stock in stocks[:2]:  # Limit to 2 stocks per category to avoid API limits
                try:
                    # Alpha Vantage API call for Indian stocks
                    symbol = stock.replace('.BSE', '.BSE')
                    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_VANTAGE_KEY}"
                    response = requests.get(url, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if 'Global Quote' in data:
                            quote = data['Global Quote']
                            stock_data = {
                                'symbol': stock,
                                'price': float(quote.get('05. price', 0)),
                                'change': float(quote.get('09. change', 0)),
                                'change_percent': quote.get('10. change percent', '0%'),
                                'volume': int(quote.get('06. volume', 0))
                            }
                            market_data[category].append(stock_data)
                except Exception as stock_error:
                    print(f"Error fetching data for {stock}: {stock_error}")
                    # Add mock data if API fails
                    market_data[category].append({
                        'symbol': stock,
                        'price': 1000 + (hash(stock) % 500),
                        'change': (hash(stock) % 20) - 10,
                        'change_percent': f"{((hash(stock) % 20) - 10) / 10:.2f}%",
                        'volume': hash(stock) % 100000
                    })
        
        # Add Nifty 50 index data
        try:
            nifty_url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=NSEI&apikey={ALPHA_VANTAGE_KEY}"
            nifty_response = requests.get(nifty_url, timeout=10)
            if nifty_response.status_code == 200:
                nifty_data = nifty_response.json()
                if 'Global Quote' in nifty_data:
                    quote = nifty_data['Global Quote']
                    market_data['nifty50'] = {
                        'price': float(quote.get('05. price', 18500)),
                        'change': float(quote.get('09. change', 0)),
                        'change_percent': quote.get('10. change percent', '0%')
                    }
        except:
            market_data['nifty50'] = {'price': 18500, 'change': 45.2, 'change_percent': '0.24%'}
        
        return market_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/recommendations")
async def get_investment_recommendations(profile: UserProfile):
    try:
        # Get risk assessment
        risk_assessment = await db.risk_assessments.find_one({"user_id": profile.user_id})
        if not risk_assessment:
            # Create risk assessment if not exists
            risk_data = await assess_risk(profile)
            risk_category = risk_data['risk_category']
            risk_score = risk_data['risk_score']
        else:
            risk_category = risk_assessment['risk_category']
            risk_score = risk_assessment['risk_score']
        
        # Calculate investment capacity
        monthly_investable = profile.monthly_income - profile.monthly_expenses
        
        # Asset allocation based on risk profile
        if risk_category == "High Risk":
            allocation = {
                'equity_large_cap': 35,
                'equity_mid_cap': 25,
                'equity_small_cap': 15,
                'mutual_funds_equity': 15,
                'debt_funds': 5,
                'emergency_buffer': 5
            }
        elif risk_category == "Moderate Risk":
            allocation = {
                'equity_large_cap': 30,
                'equity_mid_cap': 15,
                'mutual_funds_equity': 25,
                'debt_funds': 20,
                'emergency_buffer': 10
            }
        else:  # Low Risk
            allocation = {
                'equity_large_cap': 20,
                'mutual_funds_equity': 15,
                'debt_funds': 45,
                'emergency_buffer': 20
            }
        
        # Generate specific recommendations
        recommendations = []
        
        # Equity recommendations
        if allocation.get('equity_large_cap', 0) > 0:
            recommendations.append({
                'type': 'Large Cap Stocks',
                'allocation_percent': allocation['equity_large_cap'],
                'amount': (monthly_investable * allocation['equity_large_cap'] / 100),
                'instruments': INDIAN_STOCKS['large_cap'][:3],
                'rationale': 'Stable large-cap stocks for steady growth with lower volatility'
            })
        
        if allocation.get('equity_mid_cap', 0) > 0:
            recommendations.append({
                'type': 'Mid Cap Stocks',
                'allocation_percent': allocation['equity_mid_cap'],
                'amount': (monthly_investable * allocation['equity_mid_cap'] / 100),
                'instruments': INDIAN_STOCKS['mid_cap'][:2],
                'rationale': 'Growth-oriented mid-cap stocks for higher returns'
            })
        
        # Mutual fund recommendations
        if allocation.get('mutual_funds_equity', 0) > 0:
            recommendations.append({
                'type': 'Equity Mutual Funds',
                'allocation_percent': allocation['mutual_funds_equity'],
                'amount': (monthly_investable * allocation['mutual_funds_equity'] / 100),
                'instruments': MUTUAL_FUNDS['equity']['large_cap'][:2],
                'rationale': 'Diversified equity exposure through professional fund management'
            })
        
        # Debt recommendations
        if allocation.get('debt_funds', 0) > 0:
            recommendations.append({
                'type': 'Debt Funds',
                'allocation_percent': allocation['debt_funds'],
                'amount': (monthly_investable * allocation['debt_funds'] / 100),
                'instruments': MUTUAL_FUNDS['debt'][:2],
                'rationale': 'Stable debt instruments for capital preservation and steady returns'
            })
        
        # Generate AI reasoning
        reasoning_prompt = f"""
        Based on user profile:
        - Age: {profile.age}
        - Monthly Income: ₹{profile.monthly_income:,.0f}
        - Monthly Expenses: ₹{profile.monthly_expenses:,.0f}
        - Risk Category: {risk_category}
        - Investment Experience: {profile.investment_experience}
        - Goals: {', '.join(profile.financial_goals)}
        
        Provide a brief explanation (2-3 sentences) of why this investment allocation makes sense for this user.
        """
        
        try:
            openai_response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a financial advisor specializing in Indian markets. Provide concise, practical investment advice."},
                    {"role": "user", "content": reasoning_prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            ai_reasoning = openai_response.choices[0].message.content
        except:
            ai_reasoning = f"Based on your {risk_category.lower()} profile and investment goals, this allocation balances growth potential with risk management. The diversified approach across large-cap stocks and mutual funds aligns with your investment experience and time horizon."
        
        investment_recommendation = InvestmentRecommendation(
            user_id=profile.user_id,
            recommendations=recommendations,
            allocation=allocation,
            reasoning=ai_reasoning,
            timestamp=datetime.now()
        )
        
        # Save to database
        await db.investment_recommendations.insert_one(investment_recommendation.dict())
        
        return investment_recommendation.dict()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def financial_chat(chat_message: ChatMessage):
    try:
        # Get user context for personalized advice
        user_context = chat_message.user_context or {}
        user_age = user_context.get('age', 30)
        user_income = user_context.get('income', 50000)
        risk_category = user_context.get('risk_category', 'Moderate Risk')
        
        # Normalize the message for pattern matching
        message_lower = chat_message.message.lower()
        
        # Financial Advisory Knowledge Base
        ai_response = generate_financial_advice(message_lower, user_age, user_income, risk_category)
        
        # Fallback to OpenAI if available (but handle quota exceeded gracefully)
        try:
            if OPENAI_KEY and len(OPENAI_KEY) > 20:  # Basic validation
                openai_response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an AI Financial Advisor specializing in Indian markets. Provide helpful, accurate financial advice. Keep responses concise (2-3 sentences)."},
                        {"role": "user", "content": f"{chat_message.message}\nUser: {user_age} years old, ₹{user_income} income, {risk_category}"}
                    ],
                    max_tokens=150,
                    temperature=0.7
                )
                ai_response = openai_response.choices[0].message.content
        except Exception as openai_error:
            # Continue with fallback response if OpenAI fails
            print(f"OpenAI API unavailable, using fallback: {openai_error}")
        
        # Save chat history
        chat_record = {
            "user_message": chat_message.message,
            "ai_response": ai_response,
            "timestamp": datetime.now(),
            "user_context": chat_message.user_context
        }
        await db.chat_history.insert_one(chat_record)
        
        return {"response": ai_response}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

def generate_financial_advice(message_lower, user_age, user_income, risk_category):
    """Generate intelligent financial advice based on user query and profile"""
    
    # Emergency fund queries (check first to avoid "fund" matching mutual funds)
    if 'emergency' in message_lower or ('emergency fund' in message_lower):
        emergency_fund = user_income * 6
        return f"Maintain 6-12 months of expenses (approximately ₹{emergency_fund:,.0f}) in liquid funds or high-yield savings accounts. Consider SBI Liquid Fund, HDFC Liquid Fund, or sweep-in FDs. This should be your first priority before any other investment."
    
    # SIP related queries
    elif any(word in message_lower for word in ['sip', 'systematic', 'monthly']):
        sip_amount = min(user_income // 10, 10000)
        return f"SIP is excellent for disciplined investing! Start with ₹{sip_amount} monthly across 2-3 diversified equity funds. Consider SBI Bluechip Fund, HDFC Top 100, and Mirae Asset Large Cap Fund. Increase SIP by 10% annually as your income grows."
    
    # Tax saving queries
    elif any(word in message_lower for word in ['tax', 'save', '80c', 'elss']):
        return f"For tax saving under Section 80C, ELSS mutual funds are best with 3-year lock-in and market-linked returns. Top ELSS funds: Axis Long Term Equity Fund, Mirae Asset Tax Saver Fund. You can save ₹46,800 tax annually on ₹1.5L investment. Also consider PPF, NSC, and ULIP."
    
    # Retirement planning
    elif any(word in message_lower for word in ['retirement', 'pension', 'retire']):
        if user_age < 35:
            return f"Start early for retirement! Invest ₹{min(user_income//5, 20000)} monthly in equity funds for 25-30 years. Consider NPS for additional tax benefits. With inflation, you'll need ₹5-10 crores for comfortable retirement. Time is your biggest asset!"
        else:
            return f"Retirement planning is crucial at {user_age}. Increase equity allocation to 60-70% if possible. Consider NPS, PPF, and equity mutual funds. Calculate your retirement corpus needs and invest accordingly. Consider consulting a certified financial planner."
    
    # Stock market queries
    elif any(word in message_lower for word in ['stock', 'share', 'equity', 'nse', 'bse']):
        return f"For direct stock investing, start with blue-chip stocks like Reliance, TCS, HDFC Bank, ICICI Bank. Invest only 20-30% of your portfolio in individual stocks. Consider sectors like IT, Banking, and Consumer goods. Always diversify and invest only surplus money."
    
    # Mutual fund queries
    elif any(word in message_lower for word in ['mutual fund', 'fund', 'mf']):
        if risk_category == 'High Risk':
            return "For high-risk tolerance, consider small-cap and mid-cap funds like SBI Small Cap Fund, HDFC Mid-Cap Opportunities Fund. Mix with large-cap funds for stability. Aim for 15-18% long-term returns but expect volatility."
        elif risk_category == 'Low Risk':
            return "For conservative investors, focus on large-cap funds, hybrid funds, and debt funds. SBI Bluechip Fund, HDFC Balanced Advantage Fund, and ICICI Pru Short Term Fund are good options. Target 10-12% returns with lower risk."
        else:
            return "For moderate risk, blend large-cap (50%), mid-cap (30%), and debt funds (20%). Top picks: HDFC Top 100, SBI Magnum Midcap, HDFC Short Term Debt Fund. This gives 12-15% potential returns with manageable risk."
    
    # Risk assessment queries
    elif any(word in message_lower for word in ['risk', 'safe', 'conservative', 'aggressive']):
        return f"Your risk profile is {risk_category}. This means you should allocate your portfolio accordingly. Conservative investors: 30% equity, 70% debt. Moderate: 60% equity, 40% debt. Aggressive: 80% equity, 20% debt. Always align investments with your risk tolerance and goals."
    
    # Investment advice patterns (more general, so put after specific queries)
    elif any(word in message_lower for word in ['invest', 'investment', 'money', 'portfolio', 'asset']):
        if user_age < 30:
            return f"At {user_age}, you have time on your side! Consider 70-80% equity allocation through SIP in diversified mutual funds like HDFC Top 100 or SBI Bluechip. Start with ₹{min(user_income//10, 10000)} monthly SIP. Focus on large-cap and mid-cap funds for long-term wealth creation."
        elif user_age < 45:
            return f"For your age ({user_age}), a balanced 60-70% equity and 30-40% debt allocation works well. Consider index funds, ELSS for tax saving, and debt funds for stability. Monthly SIP of ₹{min(user_income//8, 15000)} across diversified equity funds is recommended."
        else:
            return f"At {user_age}, focus on capital preservation with 50-60% debt and 40-50% equity. Consider balanced hybrid funds, FDs, and PPF. Prioritize liquid funds for emergency corpus and stable income sources."
    
    # General advice or unclear queries
    else:
        return f"Based on your profile (₹{user_income:,.0f} income, {user_age} years, {risk_category}), focus on: 1) Build 6-month emergency fund first, 2) Start SIP in diversified equity funds, 3) Consider ELSS for tax saving, 4) Review and rebalance annually. For personalized advice, consult a certified financial planner."

@app.get("/api/portfolio/{user_id}")
async def get_portfolio_summary(user_id: str):
    try:
        # Get user profile and recommendations
        profile = await db.user_profiles.find_one({"user_id": user_id})
        recommendations = await db.investment_recommendations.find_one({"user_id": user_id})
        
        if not profile or not recommendations:
            raise HTTPException(status_code=404, detail="Portfolio data not found")
        
        # Calculate portfolio metrics
        monthly_investment = profile['monthly_income'] - profile['monthly_expenses']
        annual_investment = monthly_investment * 12
        
        # Projected growth calculations (simplified)
        growth_rates = {
            'equity_large_cap': 0.12,  # 12% annual return
            'equity_mid_cap': 0.15,    # 15% annual return
            'equity_small_cap': 0.18,  # 18% annual return
            'mutual_funds_equity': 0.14, # 14% annual return
            'debt_funds': 0.08,        # 8% annual return
        }
        
        portfolio_value_projections = {}
        for years in [1, 5, 10, 20]:
            total_value = 0
            for rec in recommendations['recommendations']:
                allocation_percent = rec['allocation_percent'] / 100
                annual_amount = annual_investment * allocation_percent
                growth_rate = growth_rates.get(rec['type'].lower().replace(' ', '_'), 0.10)
                
                # Simple compound interest calculation
                future_value = annual_amount * (((1 + growth_rate) ** years - 1) / growth_rate)
                total_value += future_value
            
            portfolio_value_projections[f"{years}_years"] = total_value
        
        portfolio_summary = {
            "user_id": user_id,
            "current_monthly_investment": monthly_investment,
            "annual_investment_capacity": annual_investment,
            "risk_profile": recommendations.get('risk_category', 'Moderate'),
            "asset_allocation": recommendations['allocation'],
            "projected_values": portfolio_value_projections,
            "recommendations_count": len(recommendations['recommendations'])
        }
        
        return portfolio_summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)