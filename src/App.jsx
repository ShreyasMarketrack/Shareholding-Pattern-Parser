import { useState, useEffect } from 'react';
import './App.css';

const ChevronRight = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="9 18 15 12 9 6"></polyline>
  </svg>
);

const TaxonomyNode = ({ node, depth = 0 }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  const hasChildren = node.children && node.children.length > 0;
  const hasEntities = node.entities && node.entities.length > 0;
  const isExpandable = hasChildren || hasEntities;

  const toggleNode = () => {
    if (isExpandable) setIsExpanded(!isExpanded);
  };

  return (
    <>
      <tr 
        className={`taxonomy-row depth-${depth} ${isExpanded ? 'expanded' : ''} ${!isExpandable ? 'leaf' : ''}`}
        onClick={toggleNode}
      >
        <td style={{ paddingLeft: `${1.5 + depth * 2}rem` }}>
          <div className="category-cell">
            {isExpandable ? (
              <span className={`expand-icon ${isExpanded ? 'open' : ''}`}>
                <ChevronRight />
              </span>
            ) : (
              <span className="spacer-icon"></span>
            )}
            <span className="node-name">{node.name}</span>
          </div>
        </td>
        <td>
          <div className="percentage-bar-container">
            <div 
              className="percentage-bar" 
              style={{ width: `${Math.min(100, node.percentage || 0)}%` }}
            ></div>
          </div>
          {(node.percentage || 0).toFixed(2)}%
        </td>
      </tr>
      
      {isExpanded && hasChildren && node.children.map((child, idx) => (
        <TaxonomyNode key={idx} node={child} depth={depth + 1} />
      ))}

      {isExpanded && hasEntities && node.entities.map((entity, idx) => (
        <tr className={`entity-row depth-${depth + 1}`} key={`entity-${idx}`}>
          <td style={{ paddingLeft: `${1.5 + (depth + 1) * 2}rem` }}>
            <div className="entity-name">{entity.name}</div>
            <div className="entity-meta">({entity.member_type}) - {(entity.shares || 0).toLocaleString()} shares</div>
          </td>
          <td>{(entity.percentage || 0).toFixed(2)}%</td>
        </tr>
      ))}
    </>
  );
};

function App() {
  const [data, setData] = useState(null);
  const [selectedCompany, setSelectedCompany] = useState('');
  const [selectedQuarter, setSelectedQuarter] = useState('');

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

  if (!data) {
    return <div className="loading">Loading Shareholding Data...</div>;
  }

  const currentDataset = data.data[selectedCompany]?.[selectedQuarter];
  
  if (!currentDataset) {
    return <div className="error-message">No data available for this selection.</div>;
  }
  
  const currentCategories = currentDataset.categories;
  const genInfo = currentDataset.general_info;

  let totalPercentage = 0;
  if (currentCategories) {
    currentCategories.forEach(c => {
      totalPercentage += (c.percentage || 0);
    });
  }

  return (
    <div className="app-container">
      <header>
        <h1>Shareholding Pattern Viewer</h1>
        <p className="subtitle">Recursive Taxonomy Implementation</p>
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
            {currentCategories.map((cat, idx) => (
              <TaxonomyNode key={idx} node={cat} />
            ))}
            
            <tr className="total-row">
              <td style={{ paddingLeft: '1.5rem' }}>Total Validated Shareholding</td>
              <td>{totalPercentage.toFixed(2)}%</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default App;
