import React, { useState, useEffect } from 'react';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [currentStep, setCurrentStep] = useState('profile');
  const [userProfile, setUserProfile] = useState({
    name: '',
    age: '',
    monthly_income: '',
    monthly_expenses: '',
    current_savings: '',
    dependents: '',
    financial_goals: [],
    investment_experience: '',
    risk_preference: '',
    investment_horizon: '',
    emergency_fund: ''
  });
  const [riskAssessment, setRiskAssessment] = useState(null);
  const [recommendations, setRecommendations] = useState(null);
  const [marketData, setMarketData] = useState(null);
  const [chatMessage, setChatMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [userId, setUserId] = useState(null);

  const financialGoals = [
    'Retirement Planning',
    'House Purchase',
    'Children Education',
    'Emergency Fund',
    'Wealth Creation',
    'Tax Saving',
    'Travel',
    'Marriage'
  ];

  useEffect(() => {
    fetchMarketData();
  }, []);

  const fetchMarketData = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/market-data`);
      const data = await response.json();
      setMarketData(data);
    } catch (error) {
      console.error('Error fetching market data:', error);
    }
  };

  const handleInputChange = (field, value) => {
    setUserProfile(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleGoalToggle = (goal) => {
    setUserProfile(prev => ({
      ...prev,
      financial_goals: prev.financial_goals.includes(goal)
        ? prev.financial_goals.filter(g => g !== goal)
        : [...prev.financial_goals, goal]
    }));
  };

  const submitProfile = async () => {
    setLoading(true);
    try {
      // Create profile
      const profileResponse = await fetch(`${API_BASE_URL}/api/profile`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userProfile),
      });
      const profileData = await profileResponse.json();
      setUserId(profileData.user_id);

      // Get risk assessment
      const riskResponse = await fetch(`${API_BASE_URL}/api/risk-assessment`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ...userProfile, user_id: profileData.user_id }),
      });
      const riskData = await riskResponse.json();
      setRiskAssessment(riskData);

      // Get recommendations
      const recResponse = await fetch(`${API_BASE_URL}/api/recommendations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ...userProfile, user_id: profileData.user_id }),
      });
      const recData = await recResponse.json();
      setRecommendations(recData);

      setCurrentStep('results');
    } catch (error) {
      console.error('Error submitting profile:', error);
      alert('Error processing your profile. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const sendChatMessage = async () => {
    if (!chatMessage.trim()) return;

    const userMsg = chatMessage;
    setChatMessage('');
    setChatHistory(prev => [...prev, { type: 'user', message: userMsg }]);

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMsg,
          user_context: riskAssessment ? {
            risk_category: riskAssessment.risk_category,
            age: userProfile.age,
            income: userProfile.monthly_income
          } : null
        }),
      });
      const data = await response.json();
      setChatHistory(prev => [...prev, { type: 'ai', message: data.response }]);
    } catch (error) {
      console.error('Error sending chat message:', error);
      setChatHistory(prev => [...prev, { type: 'ai', message: 'Sorry, I encountered an error. Please try again.' }]);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const renderMarketOverview = () => {
    if (!marketData) return null;

    return (
      <div className="market-overview">
        <h3 className="text-xl font-bold mb-4 text-blue-800">Market Overview</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {marketData.nifty50 && (
            <div className="market-card">
              <h4 className="font-semibold text-gray-700">Nifty 50</h4>
              <p className="text-2xl font-bold text-blue-600">{marketData.nifty50.price.toLocaleString()}</p>
              <p className={`text-sm ${marketData.nifty50.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {marketData.nifty50.change >= 0 ? '+' : ''}{marketData.nifty50.change} ({marketData.nifty50.change_percent})
              </p>
            </div>
          )}
          {Object.entries(marketData).filter(([key]) => key !== 'nifty50').map(([category, stocks]) => (
            stocks.slice(0, 1).map(stock => (
              <div key={stock.symbol} className="market-card">
                <h4 className="font-semibold text-gray-700">{stock.symbol.replace('.BSE', '')}</h4>
                <p className="text-lg font-bold text-blue-600">{formatCurrency(stock.price)}</p>
                <p className={`text-sm ${stock.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {stock.change >= 0 ? '+' : ''}{stock.change} ({stock.change_percent})
                </p>
              </div>
            ))
          ))}
        </div>
      </div>
    );
  };

  const renderProfileForm = () => (
    <div className="profile-form">
      <div className="form-header">
        <h2 className="text-3xl font-bold text-blue-800 mb-2">AI Financial Advisor</h2>
        <p className="text-gray-600 mb-8">Let's build your personalized investment strategy</p>
      </div>

      {renderMarketOverview()}

      <div className="form-grid">
        <div className="form-section">
          <h3 className="section-title">Personal Information</h3>
          <div className="input-group">
            <label>Full Name</label>
            <input
              type="text"
              value={userProfile.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              placeholder="Enter your full name"
            />
          </div>
          <div className="input-group">
            <label>Age</label>
            <input
              type="number"
              value={userProfile.age}
              onChange={(e) => handleInputChange('age', e.target.value)}
              placeholder="Your age"
            />
          </div>
          <div className="input-group">
            <label>Number of Dependents</label>
            <input
              type="number"
              value={userProfile.dependents}
              onChange={(e) => handleInputChange('dependents', e.target.value)}
              placeholder="0"
            />
          </div>
        </div>

        <div className="form-section">
          <h3 className="section-title">Financial Details</h3>
          <div className="input-group">
            <label>Monthly Income (₹)</label>
            <input
              type="number"
              value={userProfile.monthly_income}
              onChange={(e) => handleInputChange('monthly_income', e.target.value)}
              placeholder="50000"
            />
          </div>
          <div className="input-group">
            <label>Monthly Expenses (₹)</label>
            <input
              type="number"
              value={userProfile.monthly_expenses}
              onChange={(e) => handleInputChange('monthly_expenses', e.target.value)}
              placeholder="30000"
            />
          </div>
          <div className="input-group">
            <label>Current Savings (₹)</label>
            <input
              type="number"
              value={userProfile.current_savings}
              onChange={(e) => handleInputChange('current_savings', e.target.value)}
              placeholder="100000"
            />
          </div>
          <div className="input-group">
            <label>Emergency Fund (₹)</label>
            <input
              type="number"
              value={userProfile.emergency_fund}
              onChange={(e) => handleInputChange('emergency_fund', e.target.value)}
              placeholder="150000"
            />
          </div>
        </div>

        <div className="form-section">
          <h3 className="section-title">Investment Profile</h3>
          <div className="input-group">
            <label>Investment Experience</label>
            <select
              value={userProfile.investment_experience}
              onChange={(e) => handleInputChange('investment_experience', e.target.value)}
            >
              <option value="">Select experience level</option>
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="experienced">Experienced</option>
            </select>
          </div>
          <div className="input-group">
            <label>Risk Preference</label>
            <select
              value={userProfile.risk_preference}
              onChange={(e) => handleInputChange('risk_preference', e.target.value)}
            >
              <option value="">Select risk preference</option>
              <option value="conservative">Conservative</option>
              <option value="moderate">Moderate</option>
              <option value="aggressive">Aggressive</option>
            </select>
          </div>
          <div className="input-group">
            <label>Investment Horizon</label>
            <select
              value={userProfile.investment_horizon}
              onChange={(e) => handleInputChange('investment_horizon', e.target.value)}
            >
              <option value="">Select time horizon</option>
              <option value="short">Short Term (1-3 years)</option>
              <option value="medium">Medium Term (3-7 years)</option>
              <option value="long">Long Term (7+ years)</option>
            </select>
          </div>
        </div>

        <div className="form-section full-width">
          <h3 className="section-title">Financial Goals</h3>
          <div className="goals-grid">
            {financialGoals.map(goal => (
              <div
                key={goal}
                className={`goal-card ${userProfile.financial_goals.includes(goal) ? 'selected' : ''}`}
                onClick={() => handleGoalToggle(goal)}
              >
                {goal}
              </div>
            ))}
          </div>
        </div>
      </div>

      <button
        className="submit-btn"
        onClick={submitProfile}
        disabled={loading || !userProfile.name || !userProfile.age}
      >
        {loading ? 'Analyzing Your Profile...' : 'Get My Investment Plan'}
      </button>
    </div>
  );

  const renderResults = () => (
    <div className="results-container">
      <div className="results-header">
        <h2 className="text-3xl font-bold text-blue-800 mb-2">Your Personalized Investment Plan</h2>
        <p className="text-gray-600 mb-6">Based on AI analysis of your financial profile</p>
      </div>

      {riskAssessment && (
        <div className="risk-card">
          <h3 className="text-xl font-bold mb-4">Risk Assessment</h3>
          <div className="risk-details">
            <div className="risk-score">
              <span className="score-label">Risk Score:</span>
              <span className="score-value">{riskAssessment.risk_score}/90</span>
            </div>
            <div className="risk-category">
              <span className={`category-badge ${riskAssessment.risk_category.toLowerCase().replace(' ', '-')}`}>
                {riskAssessment.risk_category}
              </span>
            </div>
          </div>
        </div>
      )}

      {recommendations && (
        <div className="recommendations-section">
          <h3 className="text-xl font-bold mb-4">Investment Recommendations</h3>
          
          <div className="ai-reasoning">
            <div className="reasoning-card">
              <h4 className="font-semibold mb-2">AI Analysis</h4>
              <p className="text-gray-700">{recommendations.reasoning}</p>
            </div>
          </div>

          <div className="allocation-chart">
            <h4 className="font-semibold mb-4">Asset Allocation</h4>
            <div className="allocation-bars">
              {Object.entries(recommendations.allocation).map(([asset, percentage]) => (
                <div key={asset} className="allocation-item">
                  <div className="allocation-label">
                    <span>{asset.replace('_', ' ').toUpperCase()}</span>
                    <span className="percentage">{percentage}%</span>
                  </div>
                  <div className="allocation-bar">
                    <div
                      className="allocation-fill"
                      style={{ width: `${percentage}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="recommendations-list">
            <h4 className="font-semibold mb-4">Specific Recommendations</h4>
            {recommendations.recommendations.map((rec, index) => (
              <div key={index} className="recommendation-card">
                <div className="rec-header">
                  <h5 className="rec-title">{rec.type}</h5>
                  <div className="rec-allocation">
                    <span className="allocation-percent">{rec.allocation_percent}%</span>
                    <span className="allocation-amount">{formatCurrency(rec.amount)}/month</span>
                  </div>
                </div>
                <p className="rec-rationale">{rec.rationale}</p>
                <div className="rec-instruments">
                  <strong>Suggested Instruments:</strong>
                  <ul>
                    {rec.instruments.map((instrument, idx) => (
                      <li key={idx}>{instrument}</li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="chat-section">
        <h3 className="text-xl font-bold mb-4">Ask Your AI Financial Advisor</h3>
        <div className="chat-container">
          <div className="chat-history">
            {chatHistory.map((msg, index) => (
              <div key={index} className={`chat-message ${msg.type}`}>
                <div className="message-content">
                  {msg.type === 'ai' && <span className="ai-icon">🤖</span>}
                  {msg.message}
                </div>
              </div>
            ))}
          </div>
          <div className="chat-input">
            <input
              type="text"
              value={chatMessage}
              onChange={(e) => setChatMessage(e.target.value)}
              placeholder="Ask about your investment plan..."
              onKeyPress={(e) => e.key === 'Enter' && sendChatMessage()}
            />
            <button onClick={sendChatMessage} className="send-btn">
              Send
            </button>
          </div>
        </div>
      </div>

      <button
        className="new-analysis-btn"
        onClick={() => {
          setCurrentStep('profile');
          setRiskAssessment(null);
          setRecommendations(null);
          setChatHistory([]);
          setUserProfile({
            name: '',
            age: '',
            monthly_income: '',
            monthly_expenses: '',
            current_savings: '',
            dependents: '',
            financial_goals: [],
            investment_experience: '',
            risk_preference: '',
            investment_horizon: '',
            emergency_fund: ''
          });
        }}
      >
        Start New Analysis
      </button>
    </div>
  );

  return (
    <div className="App">
      <div className="container">
        {currentStep === 'profile' && renderProfileForm()}
        {currentStep === 'results' && renderResults()}
      </div>
    </div>
  );
}

export default App;