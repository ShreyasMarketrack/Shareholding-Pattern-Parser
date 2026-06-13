# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: tests\shp.spec.js >> Shareholding Viewer displays nested taxonomy groups accurately
- Location: tests\shp.spec.js:3:1

# Error details

```
Error: locator.uncheck: Element is outside of the viewport
Call log:
  - waiting for locator('label.switch-label input[type="checkbox"]')
    - locator resolved to <input checked type="checkbox"/>
  - attempting click action
    - scrolling into view if needed
    - done scrolling

```

# Page snapshot

```yaml
- generic [ref=e3]:
  - banner [ref=e4]:
    - heading "Shareholding Pattern Viewer" [level=1] [ref=e5]
    - paragraph [ref=e6]: Recursive Taxonomy Implementation
  - generic [ref=e7]:
    - generic [ref=e8]:
      - generic [ref=e9]: Data Source
      - generic [ref=e10]:
        - button "Raw XBRL JSON" [ref=e11] [cursor=pointer]
        - button "Processed JSON" [ref=e12] [cursor=pointer]
    - generic [ref=e13]:
      - generic [ref=e14]: Company
      - combobox [ref=e15] [cursor=pointer]:
        - option "ADANIPORTS" [selected]
        - option "ADANIPOWER"
        - option "AXISBANK"
        - option "BAJAJFINSV"
        - option "BAJFINANCE"
        - option "BEL"
        - option "BHARTIARTL"
        - option "COALINDIA"
        - option "HCLTECH"
        - option "HDFCBANK"
        - option "HINDUNILVR"
        - option "ICICIBANK"
        - option "INFY"
        - option "ITC"
        - option "JSWSTEEL"
        - option "KOTAKBANK"
        - option "LICI"
        - option "LT"
        - option "M&M"
        - option "MARUTI"
        - option "NTPC"
        - option "ONGC"
        - option "POWERGRID"
        - option "RELIANCE"
        - option "SBIN"
        - option "SUNPHARMA"
        - option "TCS"
        - option "TITAN"
        - option "ULTRACEMCO"
        - option "VEDL"
    - generic [ref=e16]:
      - generic [ref=e17]: Reporting Quarter
      - combobox [ref=e18] [cursor=pointer]:
        - option "201238" [selected]
        - option "201950"
        - option "204693"
    - generic [ref=e20] [cursor=pointer]:
      - generic [ref=e21]: Hide Zero Values
      - checkbox "Hide Zero Values" [checked]
  - generic [ref=e23]:
    - generic [ref=e24]:
      - generic [ref=e25]:
        - generic [ref=e26]: "Company Name:"
        - generic [ref=e27]: ADANI PORTS AND SPECIAL ECONOMIC ZONE LIMITED
      - generic [ref=e28]:
        - generic [ref=e29]: "Scrip Code / Symbol:"
        - generic [ref=e30]: 532921 / ADANIPORTS
      - generic [ref=e31]:
        - generic [ref=e32]: "Date of Report:"
        - generic [ref=e33]: 2025-06-30
    - generic [ref=e34]:
      - heading "Disclosures & Notes" [level=4] [ref=e35]
      - paragraph [ref=e36]: In SBO, as there is option to mention PAN of only one SBO, hence we have mentioned dummy PAN ZZZZZ9999Z. Further, in case of nationality, we have mention Indian/ Cypriot as nationality of (i) Gautambhai Shantilal Adani and Rajeshbhai Shantilal Adani is Indian, and (ii) nationality of Vinodbhai Shantilal Adani is Cypriot.
  - table [ref=e38]:
    - rowgroup [ref=e39]:
      - row "Category of Shareholder Shareholding %" [ref=e40]:
        - columnheader "Category of Shareholder" [ref=e41]
        - columnheader "Shareholding %" [ref=e42]
    - rowgroup [ref=e43]:
      - row "Promoters 65.89%" [ref=e44] [cursor=pointer]:
        - cell "Promoters" [ref=e45]:
          - generic [ref=e46]:
            - img [ref=e48]
            - generic [ref=e50]: Promoters
        - cell "65.89%" [ref=e51]: 65.89%
      - row "Indian 42.65%" [ref=e54] [cursor=pointer]:
        - cell "Indian" [ref=e55]:
          - generic [ref=e56]:
            - img [ref=e58]
            - generic [ref=e60]: Indian
        - cell "42.65%" [ref=e61]: 42.65%
      - row "Foreign 23.24%" [ref=e64] [cursor=pointer]:
        - cell "Foreign" [ref=e65]:
          - generic [ref=e66]:
            - img [ref=e68]
            - generic [ref=e70]: Foreign
        - cell "23.24%" [ref=e71]: 23.24%
      - row "FII 13.53%" [ref=e74] [cursor=pointer]:
        - cell "FII" [ref=e75]:
          - generic [ref=e76]:
            - img [ref=e78]
            - generic [ref=e80]: FII
        - cell "13.53%" [ref=e81]: 13.53%
      - row "DII 15.15%" [ref=e84] [cursor=pointer]:
        - cell "DII" [ref=e85]:
          - generic [ref=e86]:
            - img [ref=e88]
            - generic [ref=e90]: DII
        - cell "15.15%" [ref=e91]: 15.15%
      - row "Govt 0.00%" [ref=e94] [cursor=pointer]:
        - cell "Govt" [ref=e95]:
          - generic [ref=e96]:
            - img [ref=e98]
            - generic [ref=e100]: Govt
        - cell "0.00%" [ref=e101]: 0.00%
      - row "Retail Public 4.38%" [ref=e103] [cursor=pointer]:
        - cell "Retail Public" [ref=e104]:
          - generic [ref=e105]:
            - img [ref=e107]
            - generic [ref=e109]: Retail Public
        - cell "4.38%" [ref=e110]: 4.38%
      - row "Others 1.06%" [ref=e113] [cursor=pointer]:
        - cell "Others" [ref=e114]:
          - generic [ref=e115]:
            - img [ref=e117]
            - generic [ref=e119]: Others
        - cell "1.06%" [ref=e120]: 1.06%
      - row "Total Validated Shareholding 100.01%" [ref=e123]:
        - cell "Total Validated Shareholding" [ref=e124]
        - cell "100.01%" [ref=e125]
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | test('Shareholding Viewer displays nested taxonomy groups accurately', async ({ page }) => {
  4  |   // Go to the locally running app
  5  |   await page.goto('http://localhost:5173/');
  6  | 
  7  |   // Wait for data to load
  8  |   await page.waitForSelector('.shp-table');
  9  | 
  10 |   // Verify the general information panel
  11 |   const companyName = await page.textContent('.info-item:has-text("Company Name") .info-value');
  12 |   expect(companyName).toBeTruthy();
  13 |   console.log(`Loaded company: ${companyName}`);
  14 | 
  15 |   // Get total validation string
  16 |   const totalShareholding = await page.textContent('.total-row td:last-child');
  17 |   console.log(`Total Shareholding: ${totalShareholding}`);
  18 |   
  19 |   // Total shareholding should ideally be around 100% (or strictly <= 100% since rollups fix overflow)
  20 |   const totalVal = parseFloat(totalShareholding);
  21 |   expect(totalVal).toBeLessThanOrEqual(100.01);
  22 |   expect(totalVal).toBeGreaterThan(0);
  23 | 
  24 |   // Click on "Promoters" to expand it
  25 |   await page.click('text=Promoters');
  26 |   
  27 |   // Now "Indian" and "Foreign" should be visible
  28 |   await expect(page.locator('text=Indian').first()).toBeVisible();
  29 |   await expect(page.locator('text=Foreign').first()).toBeVisible();
  30 | 
  31 |   // Click on "Indian" to expand it
  32 |   await page.click('text=Indian');
  33 | 
  34 |   // Since we default to Hide Zero Values = true, Individuals/HUF is hidden (it's 0%).
  35 |   // Let's toggle off "Hide Zero Values" to see it
  36 |   const hideZeroCheckbox = page.locator('label.switch-label input[type="checkbox"]');
> 37 |   await hideZeroCheckbox.uncheck({ force: true });
     |                          ^ Error: locator.uncheck: Element is outside of the viewport
  38 | 
  39 |   // Now "Individuals/Hindu undivided Family" should be visible
  40 |   await expect(page.locator('text=Individuals/Hindu undivided Family').first()).toBeVisible();
  41 | 
  42 |   // Click on it
  43 |   await page.click('text=Individuals/Hindu undivided Family');
  44 | 
  45 |   // Now we should see the deep rows
  46 |   let deepRowsCount = await page.locator('.entity-row.depth-3').count();
  47 |   console.log(`Found ${deepRowsCount} specific entities under Individuals/HUF with Hide Zero OFF`);
  48 |   expect(deepRowsCount).toBeGreaterThan(0);
  49 |   
  50 |   // Turn Hide Zero Values back on
  51 |   await hideZeroCheckbox.check({ force: true });
  52 |   
  53 |   // Let's check "Any Other (specify)" which has the 32.9% Adani Trust
  54 |   await page.click('text=Any Other (specify)');
  55 |   const otherRowsCount = await page.locator('.entity-row').filter({ hasText: 'Adani Family Trust' }).count();
  56 |   console.log(`Found Adani Family Trust: ${otherRowsCount}`);
  57 |   expect(otherRowsCount).toBeGreaterThan(0);
  58 | 
  59 |   // Switch to Processed JSON
  60 |   await page.click('button:has-text("Processed JSON")');
  61 |   await page.waitForTimeout(500); // wait for data fetch
  62 |   
  63 |   const companyNameProcessed = await page.textContent('.info-item:has-text("Company Name") .info-value');
  64 |   expect(companyNameProcessed).toBeTruthy();
  65 |   console.log(`Loaded processed company: ${companyNameProcessed}`);
  66 |   
  67 |   const totalShareholdingProcessed = await page.textContent('.total-row td:last-child');
  68 |   const totalValProc = parseFloat(totalShareholdingProcessed);
  69 |   expect(totalValProc).toBeLessThanOrEqual(100.01);
  70 |   expect(totalValProc).toBeGreaterThan(0);
  71 | 
  72 |   console.log("Playwright test completed successfully!");
  73 | });
  74 | 
```