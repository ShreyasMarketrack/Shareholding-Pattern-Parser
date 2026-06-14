import { useState, useEffect, useMemo } from 'react';
import './App.css';
import MAPPING_TREE from './shp_mapping.json';
import { findBestMatch } from './utils/fuzzy.js';

const ChevronRight = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="9 18 15 12 9 6"></polyline>
  </svg>
);

const TaxonomyNode = ({ node, depth = 0, hideZeroValues }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  if (hideZeroValues && (node.percentage || 0) === 0) {
    return null;
  }

  const validChildren = hideZeroValues 
    ? (node.children || []).filter(c => (c.percentage || 0) > 0)
    : (node.children || []);
    
  const validEntities = hideZeroValues
    ? (node.entities || []).filter(e => (e.percentage || 0) > 0)
    : (node.entities || []);

  const hasChildren = validChildren.length > 0;
  const hasEntities = validEntities.length > 0;
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
      
      {isExpanded && hasChildren && validChildren.map((child, idx) => (
        <TaxonomyNode key={idx} node={child} depth={depth + 1} hideZeroValues={hideZeroValues} />
      ))}

      {isExpanded && hasEntities && validEntities.map((entity, idx) => (
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
  const [dataSource, setDataSource] = useState('raw');
  const [hideZeroValues, setHideZeroValues] = useState(true);

  useEffect(() => {
    setData(null);
    fetch(`/data/all_shp_data_${dataSource}.json`)
      .then(res => res.json())
      .then(json => {
        setData(json);
        if (json.companies && json.companies.length > 0) {
          // Only reset if the current selection is invalid
          let newComp = selectedCompany;
          if (!newComp || !json.companies.includes(newComp)) {
            newComp = json.companies[0];
            setSelectedCompany(newComp);
          }
          
          if (json.data[newComp]) {
            const quarters = Object.keys(json.data[newComp]);
            if (quarters.length > 0 && (!selectedQuarter || !quarters.includes(selectedQuarter))) {
              setSelectedQuarter(quarters[0]);
            }
          }
        }
      })
      .catch(err => console.error(`Failed to load ${dataSource} data`, err));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dataSource]);

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
    return (
      <div className="app-container">
        <header>
          <h1>Shareholding Pattern Viewer</h1>
          <p className="subtitle">Data source mismatch</p>
        </header>
        <div className="controls">
          <div className="control-group">
            <label>Data Source</label>
            <div className="toggle-buttons">
              <button className={dataSource === 'raw' ? 'active' : ''} onClick={() => setDataSource('raw')}>Raw XBRL JSON</button>
              <button className={dataSource === 'processed' ? 'active' : ''} onClick={() => setDataSource('processed')}>Processed JSON</button>
            </div>
          </div>
        </div>
        <div className="error-message">No data available for this selection in the current source. Please select another company or switch data source.</div>
      </div>
    );
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
          <label>Data Source</label>
          <div className="toggle-buttons">
            <button className={dataSource === 'raw' ? 'active' : ''} onClick={() => setDataSource('raw')}>Raw XBRL JSON</button>
            <button className={dataSource === 'processed' ? 'active' : ''} onClick={() => setDataSource('processed')}>Processed JSON</button>
          </div>
        </div>

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
        
        <div className="control-group filter-group">
          <label className="switch-label">
            <span>Hide Zero Values</span>
            <input 
              type="checkbox" 
              checked={hideZeroValues} 
              onChange={e => setHideZeroValues(e.target.checked)} 
            />
            <span className="slider"></span>
          </label>
        </div>
      </div>
      
      {genInfo && (
        <div className="general-info-panel">
          <div className="info-grid">
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
          {genInfo.Disclosure && (
            <div className="disclosure-box">
              <h4>Disclosures & Notes</h4>
              <p>{genInfo.Disclosure}</p>
            </div>
          )}
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
              <TaxonomyNode key={idx} node={cat} hideZeroValues={hideZeroValues} />
            ))}
            
            <tr className="total-row">
              <td style={{ paddingLeft: '1.5rem' }}>Total Validated Shareholding</td>
              <td>{totalPercentage.toFixed(2)}%</td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Floating Action Button utilizing declarative popover control */}
      <button 
        className="dev-tools-fab" 
        popovertarget="heuristic-dev-tools"
        title="Taxonomy Drift Dev Tools"
      >
        🛠️
      </button>

      {/* Modern Native Popover API with @starting-style animations */}
      <div id="heuristic-dev-tools" popover="auto" className="dev-tools-popover">
        <h3>
          Taxonomy Drift Dev Tools
          <button className="close-popover" popovertarget="heuristic-dev-tools" popovertargetaction="hide">×</button>
        </h3>
        <div className="dev-tools-content">
          <p style={{marginTop: 0, fontSize: '0.9rem', color: '#ccc'}}>
            Test the fuzzy string matching heuristic against live taxonomy data.
          </p>
          <div className="dev-tools-input">
            <input 
              type="text" 
              placeholder="Enter legacy taxonomy tag..."
              id="dev-fuzzy-input"
            />
            <button onClick={() => {
              const input = document.getElementById('dev-fuzzy-input').value;
              if (!input) return;
              
              const validDomains = new Set();
              const extractDomains = (n) => {
                if (n.member) validDomains.add(n.member.replace('Member', 'Domain'));
                (n.children || []).forEach(extractDomains);
              };
              (MAPPING_TREE.children || []).forEach(extractDomains);
              
              const result = findBestMatch(input, Array.from(validDomains));
              document.getElementById('dev-fuzzy-result').innerHTML = `
                <div style="margin-bottom:0.5rem"><strong>Original:</strong> <span style="word-break:break-all">${result.original}</span></div>
                <div style="margin-bottom:0.5rem"><strong>Stripped:</strong> <span style="word-break:break-all">${result.stripped}</span></div>
                <div style="margin-bottom:0.5rem"><strong>Best Match:</strong> <span style="color: #a777e3; font-weight: bold; word-break:break-all">${result.bestMatch}</span></div>
                <div><strong>Sorensen-Dice Score:</strong> <span style="color: #4CAF50">${result.score}</span></div>
              `;
            }}>Test Heuristic</button>
          </div>
          <div id="dev-fuzzy-result" className="dev-tools-result" style={{fontSize: '0.85rem'}}></div>
        </div>
      </div>

    </div>
  );
}

export default App;
