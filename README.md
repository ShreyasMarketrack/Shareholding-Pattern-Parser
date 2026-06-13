# Shareholding Pattern Parser & Viewer

A sophisticated, full-stack solution for ingesting, parsing, transforming, and visualizing deep, recursive XBRL Shareholding Pattern data submitted by Indian companies to regulatory authorities (NSE/BSE).

This application processes raw XBRL JSON extracts or pre-processed NSE/BSE domains, unifies them into a strict hierarchical taxonomy tree, and renders them in a highly interactive, beautifully designed React frontend.

---

## 🎯 Core Objectives & Goals

### Goals
- **Precise Taxonomic Recreation**: Perfectly mirror the exact N-ary tree relationships found in the official `SHP Taxonomy` definition linkbases (e.g., `Promoters` -> `Indian` -> `Individuals/Hindu undivided Family`).
- **Dual Data Source Support**: Seamlessly parse both Raw XBRL representations and flattened, pre-processed NSE/BSE domain JSON formats.
- **Flawless Mathematical Rollups**: Aggregate leaf-node entity shareholdings bottom-up to ensure totals never exceed `100.01%` while automatically rectifying fractional data (`1.0` vs `100.0`).
- **Interactive Visualization**: Provide an expandable, nested UI with advanced filtering (Zero-value hiding) and instant toggling between source mechanisms.

### Non-Goals
- Real-time fetching from live BSE servers (this operates on local data drops).
- Modifying or writing data back to the XBRL structures.

---

## 🧠 Architectural Overview

### 1. JSON Taxonomy Grouping (`shp_mapping.json`)
Instead of a flattened string array, the taxonomy is structured dynamically as a deeply nested N-ary tree. 
- Categories branch out recursively (`Promoters -> Indian -> Institutions -> Financial Institutions`).
- This file acts as the source of truth for the Python parser to map dynamic contexts to fixed tree locations.

### 2. Python Data Processor (`process_shp.py`)
A heavy-duty traversal and parsing engine responsible for:
- **Raw XBRL Mode**: Identifying dimensional contexts (including explicit string manipulations for edge cases like `D_` prefixes) and mapping them back to the XBRL taxonomy.
- **Processed JSON Mode (Taxonomy Drift Remediation)**: Resolving data leakage from legacy NSE/BSE taxonomy files. Through the internal `alias_map` engine, it remaps deeply deprecated keys (e.g., `DetailsOfSharesHeldByInstitutionsForeignPortfolioInvestorOneDomain` or `CentralGovernmentOrStateGovernmentsDomain`) into their correct modern node schemas without dropping data.
- **Mathematical Rollups**: Summing nested arrays into top-level percentages (`max(explicit_percentage, sum(children))`).
- **Fractional Normalization**: Automatically multiplying values by 100 if the root total evaluates to `< 1.02`.

### 3. React Frontend (`App.jsx`)
A responsive, modern UI built with Vite:
- **Recursive Rendering**: Utilizes `<TaxonomyNode />` to endlessly render indentations based on tree depth.
- **UI Filters**: Implements custom CSS toggle switches for "Hide Zero Values" (strictly stripping `0%` rows to reduce noise).
- **Dual Source Toggling**: Pill-shaped segmented controls to instantly hot-swap the UI between the parsed Raw XBRL output and parsed Pre-processed output.
- **Entity Sorting**: Organizes specific individual shareholders inside categories in strictly descending numerical order.
- **Disclosure Display**: Extracts `DisclosureOfNotesOnShareholdingPatternExplanatoryTextBlock` globally to display context-level explanatory notes.

### 4. Taxonomy Drift Diagnostics (`audit_shp.py`)
An exhaustive audit script designed to traverse thousands of files to prevent data leakage. It:
- Extracts all numerical contexts across historical files.
- Cross-references them against the modern `shp_mapping.json`.
- Automatically flags legacy tags and generates a `taxonomy_drift_report.md` detailing exact occurrences, allowing the parser to safely bridge old namespaces into the unified schema.

---

## 🚀 Getting Started

### Prerequisites
- **Node.js**: v18+ (for Vite/React)
- **Python**: 3.9+ (for the parser)
- **Playwright**: For UI automation testing

### Installation & Execution

1. **Install Frontend Dependencies**
   ```bash
   npm install
   ```
2. **Generate the Data**
   Run the Python script against your local data directories to generate `all_shp_data_raw.json` and `all_shp_data_processed.json`.
   ```bash
   python process_shp.py
   ```
3. **Start the Development Server**
   ```bash
   npm run dev
   ```
   Navigate to `http://localhost:5173/` in your browser.

---

## 🧪 Playwright Testing Suite

To guarantee visual and mathematical accuracy, we enforce Playwright E2E testing on Chromium browsers.

### Execution
Run the automated test suite locally via:
```bash
npx playwright test --browser=chromium
```

### What is Tested (`shp.spec.js`)
1. **Application Load**: Verifies the root application mounts and the initial JSON data populates.
2. **Metadata Presence**: Asserts that `Company Name` and `Total Shareholding` metrics render.
3. **Mathematical Safety Limits**: Ensures that the `Total Validated Shareholding` calculates strictly to `<= 100.01%` and `> 0%`.
4. **Interactive Expansions**: Simulates user clicks to traverse nested taxonomy elements (e.g., expanding `Promoters` -> `Indian`).
5. **Zero-Value Filtration Verification**: 
   - Dynamically clicks the custom CSS `.slider` switch to disable "Hide Zero Values".
   - Verifies deeply nested elements mathematically equal to `0.00%` become correctly visible.
   - Re-engages the switch to test DOM hiding.
6. **Taxonomy Drift Verification (Titan Edge Case)**: Explicitly tests the `Central Government/ State Government(s)` node for companies like TITAN, ensuring that legacy nested data correctly renders via the alias mapping system.
7. **Data Toggling Integrity**: Simulates switching from "Raw JSON" to "Processed JSON", waiting for network refetches, and asserting that total limits remain unviolated across datasets.
