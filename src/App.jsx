import { useState, useEffect } from 'react';
import './App.css';

// SVG Icon for expand/collapse
const ChevronRight = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="9 18 15 12 9 6"></polyline>
  </svg>
);

function App() {
  const [data, setData] = useState(null);
  const [selectedCompany, setSelectedCompany] = useState('');
  const [selectedQuarter, setSelectedQuarter] = useState('');
  const [expandedCategories, setExpandedCategories] = useState({});

  useEffect(() => {
    fetch('/data/all_shp_data.json')
      .then(res => res.json())
      .then(json => {
        setData(json);
        if (json.companies && json.companies.length > 0) {
          const firstCompany = json.companies[0];
          setSelectedCompany(firstCompany);
          
          const quarters = Object.keys(json.data[firstCompany]);
          if (quarters.length > 0) {
            setSelectedQuarter(quarters[0]);
          }
        }
      })
      .catch(err => console.error("Failed to load data", err));
  }, []);

  useEffect(() => {
    if (data && selectedCompany && data.data[selectedCompany]) {
      const quarters = Object.keys(data.data[selectedCompany]);
      if (quarters.length > 0 && !quarters.includes(selectedQuarter)) {
        setSelectedQuarter(quarters[0]);
      }
    }
  }, [selectedCompany, data, selectedQuarter]);

  const toggleCategory = (category) => {
    setExpandedCategories(prev => ({
      ...prev,
      [category]: !prev[category]
    }));
  };

  if (!data) {
    return <div className="loading">Loading Shareholding Data...</div>;
  }

  const currentDataset = data.data[selectedCompany]?.[selectedQuarter];
  
  if (!currentDataset) {
    return <div className="error-message">No data available for this selection.</div>;
  }
  
  const currentData = currentDataset.categories;
  const genInfo = currentDataset.general_info;
  
  const categoryOrder = [
    "Promoters",
    "FII",
    "DII",
    "Govt",
    "Retail Public",
    "Others"
  ];

  let totalPercentage = 0;

  return (
    <div className="app-container">
      <header>
        <h1>Shareholding Pattern Viewer</h1>
        <p className="subtitle">Official XBRL Taxonomy Representation</p>
      </header>

      <div className="controls">
        <div className="control-group">
          <label>Company</label>
          <select 
            value={selectedCompany} 
            onChange={e => setSelectedCompany(e.target.value)}
          >
            {data.companies.map(c => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label>Reporting Quarter</label>
          <select 
            value={selectedQuarter} 
            onChange={e => setSelectedQuarter(e.target.value)}
          >
            {Object.keys(data.data[selectedCompany] || {}).map(q => (
              <option key={q} value={q}>{q}</option>
            ))}
          </select>
        </div>
      </div>
      
      {genInfo && (
        <div className="general-info-panel">
          <div className="info-item">
            <span className="info-label">Company Name:</span>
            <span className="info-value">{genInfo.NameOfTheCompany || 'N/A'}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Scrip Code / Symbol:</span>
            <span className="info-value">{genInfo.ScripCode || 'N/A'} / {genInfo.Symbol || 'N/A'}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Date of Report:</span>
            <span className="info-value">{genInfo.DateOfReport || 'N/A'}</span>
          </div>
        </div>
      )}

      <div className="table-container">
        <table className="shp-table">
          <thead>
            <tr>
              <th>Category of Shareholder</th>
              <th>Shareholding %</th>
            </tr>
          </thead>
          <tbody>
            {categoryOrder.map(category => {
              const catData = currentData[category];
              if (!catData) return null;
              
              totalPercentage += catData.percentage;
              const isExpanded = expandedCategories[category];
              
              // Filter to show specific shareholder entities in the expanded view
              const subEntities = catData.entities.filter(e => e.is_specific);

              return (
                <tr className="row-group" key={category}>
                  <td colSpan="2" style={{ padding: 0 }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                      <tbody>
                        <tr 
                          className={`parent-row ${isExpanded ? 'expanded' : ''}`}
                          onClick={() => toggleCategory(category)}
                        >
                          <td>
                            <div className="category-cell">
                              <span className={`expand-icon ${isExpanded ? 'open' : ''}`}>
                                <ChevronRight />
                              </span>
                              {category}
                            </div>
                          </td>
                          <td>
                            <div className="percentage-bar-container">
                              <div 
                                className="percentage-bar" 
                                style={{ width: `${Math.min(100, catData.percentage)}%` }}
                              ></div>
                            </div>
                            {catData.percentage.toFixed(2)}%
                          </td>
                        </tr>
                        
                        {isExpanded && subEntities.length > 0 && (
                          <tr className="child-rows-container">
                            <td colSpan="2" style={{ padding: 0 }}>
                              <div className="child-rows">
                                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                  <tbody>
                                    {subEntities.map((child, idx) => (
                                      <tr className="child-row" key={idx}>
                                        <td>
                                          <div className="child-name">{child.name}</div>
                                          <div className="child-meta">({child.member_type}) - {child.shares.toLocaleString()} shares</div>
                                        </td>
                                        <td>{child.percentage.toFixed(2)}%</td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              </div>
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </td>
                </tr>
              );
            })}
            
            <tr className="total-row">
              <td>Total Validated Shareholding</td>
              <td>{totalPercentage.toFixed(2)}%</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default App;
