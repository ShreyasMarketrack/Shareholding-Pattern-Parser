# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: tests\shp.spec.js >> Shareholding Viewer displays nested taxonomy groups accurately
- Location: tests\shp.spec.js:3:1

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('text=Individuals/Hindu undivided Family').first()
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 5000ms
  - waiting for locator('text=Individuals/Hindu undivided Family').first()

```

```yaml
- banner:
  - heading "Shareholding Pattern Viewer" [level=1]
  - paragraph: Recursive Taxonomy Implementation
- text: Data Source
- button "Raw XBRL JSON"
- button "Processed JSON"
- text: Company
- combobox:
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
- text: Reporting Quarter
- combobox:
  - option "201238" [selected]
  - option "201950"
  - option "204693"
- text: Hide Zero Values
- checkbox "Hide Zero Values"
- text: "Company Name: ADANI PORTS AND SPECIAL ECONOMIC ZONE LIMITED Scrip Code / Symbol: 532921 / ADANIPORTS Date of Report: 2025-06-30"
- heading "Disclosures & Notes" [level=4]
- paragraph: In SBO, as there is option to mention PAN of only one SBO, hence we have mentioned dummy PAN ZZZZZ9999Z. Further, in case of nationality, we have mention Indian/ Cypriot as nationality of (i) Gautambhai Shantilal Adani and Rajeshbhai Shantilal Adani is Indian, and (ii) nationality of Vinodbhai Shantilal Adani is Cypriot.
- table:
  - rowgroup:
    - row "Category of Shareholder Shareholding %":
      - columnheader "Category of Shareholder"
      - columnheader "Shareholding %"
  - rowgroup:
    - row "Promoters 65.89%":
      - cell "Promoters":
        - img
        - text: Promoters
      - cell "65.89%"
    - row "Indian 42.65%":
      - cell "Indian":
        - img
        - text: Indian
      - cell "42.65%"
    - row "Foreign 23.24%":
      - cell "Foreign":
        - img
        - text: Foreign
      - cell "23.24%"
    - row "FII 13.53%":
      - cell "FII":
        - img
        - text: FII
      - cell "13.53%"
    - row "DII 15.15%":
      - cell "DII":
        - img
        - text: DII
      - cell "15.15%"
    - row "Govt 0.00%":
      - cell "Govt":
        - img
        - text: Govt
      - cell "0.00%"
    - row "Retail Public 4.38%":
      - cell "Retail Public":
        - img
        - text: Retail Public
      - cell "4.38%"
    - row "Others 1.06%":
      - cell "Others":
        - img
        - text: Others
      - cell "1.06%"
    - row "Total Validated Shareholding 100.01%":
      - cell "Total Validated Shareholding"
      - cell "100.01%"
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
  36 |   await page.evaluate(() => {
  37 |     const input = document.querySelector('label.switch-label input[type="checkbox"]');
  38 |     if (input) {
  39 |       input.checked = false;
  40 |       input.dispatchEvent(new Event('change', { bubbles: true }));
  41 |     }
  42 |   });
  43 | 
  44 |   // Now "Individuals/Hindu undivided Family" should be visible
> 45 |   await expect(page.locator('text=Individuals/Hindu undivided Family').first()).toBeVisible();
     |                                                                                 ^ Error: expect(locator).toBeVisible() failed
  46 | 
  47 |   // Click on it
  48 |   await page.click('text=Individuals/Hindu undivided Family');
  49 | 
  50 |   // Now we should see the deep rows
  51 |   let deepRowsCount = await page.locator('.entity-row.depth-3').count();
  52 |   console.log(`Found ${deepRowsCount} specific entities under Individuals/HUF with Hide Zero OFF`);
  53 |   expect(deepRowsCount).toBeGreaterThan(0);
  54 |   // Turn Hide Zero Values back on
  55 |   await page.evaluate(() => {
  56 |     const input = document.querySelector('label.switch-label input[type="checkbox"]');
  57 |     if (input) {
  58 |       input.checked = true;
  59 |       input.dispatchEvent(new Event('change', { bubbles: true }));
  60 |     }
  61 |   });
  62 |   
  63 |   // Let's check "Any Other (specify)" which has the 32.9% Adani Trust
  64 |   await page.click('text=Any Other (specify)');
  65 |   const otherRowsCount = await page.locator('.entity-row').filter({ hasText: 'Adani Family Trust' }).count();
  66 |   console.log(`Found Adani Family Trust: ${otherRowsCount}`);
  67 |   expect(otherRowsCount).toBeGreaterThan(0);
  68 | 
  69 |   // Switch to Processed JSON
  70 |   await page.click('button:has-text("Processed JSON")');
  71 |   await page.waitForTimeout(500); // wait for data fetch
  72 |   
  73 |   const companyNameProcessed = await page.textContent('.info-item:has-text("Company Name") .info-value');
  74 |   expect(companyNameProcessed).toBeTruthy();
  75 |   console.log(`Loaded processed company: ${companyNameProcessed}`);
  76 |   
  77 |   const totalShareholdingProcessed = await page.textContent('.total-row td:last-child');
  78 |   const totalValProc = parseFloat(totalShareholdingProcessed);
  79 |   expect(totalValProc).toBeLessThanOrEqual(100.01);
  80 |   expect(totalValProc).toBeGreaterThan(0);
  81 | 
  82 |   console.log("Playwright test completed successfully!");
  83 | });
  84 | 
```