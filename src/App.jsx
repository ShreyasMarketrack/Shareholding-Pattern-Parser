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
    // Fetch the processed data
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

  // Update quarter when company changes
  useEffect(() => {
    if (data && selectedCompany && data.data[selectedCompany]) {
      const quarters = Object.keys(data.data[selectedCompany]);
      if (quarters.length > 0 && !quarters.includes(selectedQuarter)) {
        setSelectedQuarter(quarters[0]);
      }
    }
  }, [selectedCompany, data]);

  const toggleCategory = (category) => {
    setExpandedCategories(prev => ({
      ...prev,
      [category]: !prev[category]
    }));
  };

  if (!data) {
    return <div className="loading">Loading Shareholding Data...</div>;
  }

  const currentData = data.data[selectedCompany]?.[selectedQuarter];
  
  // Define exact order of categories as per UI design
  const categoryOrder = [
    "Promoters",
    "Foreign Institutions",
    "Domestic Institutions",
    "Retail Individuals",
    "Others",
    "Government"
  ];

  let totalPercentage = 0;

  return (
    <div className="app-container">
      <header>
        <h1>Shareholding Pattern</h1>
        <p className="subtitle">Definitive Source of Truth Mapping</p>
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
            {data.data[selectedCompany] && Object.keys(data.data[selectedCompany]).map(q => (
              <option key={q} value={q}>{q}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="table-container">
        {currentData ? (
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
                          
                          {isExpanded && catData.children && catData.children.length > 0 && (
                            <tr className="child-rows-container">
                              <td colSpan="2" style={{ padding: 0 }}>
                                <div className="child-rows">
                                  <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                    <tbody>
                                      {catData.children.map((child, idx) => (
                                        <tr className="child-row" key={idx}>
                                          <td>{child.name}</td>
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
        ) : (
          <div className="error-message">No data available for this selection.</div>
        )}
      </div>
    </div>
  );
}

export default App;
