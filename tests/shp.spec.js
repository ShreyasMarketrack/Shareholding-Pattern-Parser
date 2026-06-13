import { test, expect } from '@playwright/test';

test('Shareholding Viewer displays nested taxonomy groups accurately', async ({ page }) => {
  // Go to the locally running app
  await page.goto('http://localhost:5173/');

  // Wait for data to load
  await page.waitForSelector('.shp-table');

  // Verify the general information panel
  const companyName = await page.textContent('.info-item:has-text("Company Name") .info-value');
  expect(companyName).toBeTruthy();
  console.log(`Loaded company: ${companyName}`);

  // Get total validation string
  const totalShareholding = await page.textContent('.total-row td:last-child');
  console.log(`Total Shareholding: ${totalShareholding}`);
  
  // Total shareholding should ideally be around 100% (or strictly <= 100% since rollups fix overflow)
  const totalVal = parseFloat(totalShareholding);
  expect(totalVal).toBeLessThanOrEqual(100.01);
  expect(totalVal).toBeGreaterThan(0);

  // Click on "Promoters" to expand it
  await page.click('text=Promoters');
  
  // Now "Indian" and "Foreign" should be visible
  await expect(page.locator('text=Indian').first()).toBeVisible();
  await expect(page.locator('text=Foreign').first()).toBeVisible();

  // Switch to Processed JSON
  await page.click('button:has-text("Processed JSON")');
  await page.waitForTimeout(500); // wait for data fetch
  
  const companyNameProcessed = await page.textContent('.info-item:has-text("Company Name") .info-value');
  expect(companyNameProcessed).toBeTruthy();
  console.log(`Loaded processed company: ${companyNameProcessed}`);
  
  const totalShareholdingProcessed = await page.textContent('.total-row td:last-child');
  const totalValProc = parseFloat(totalShareholdingProcessed);
  expect(totalValProc).toBeLessThanOrEqual(100.01);
  expect(totalValProc).toBeGreaterThan(0);
  
  // Test Taxonomy Drift Remediation (TITAN Edge Case)
  await page.reload();
  await page.waitForSelector('.shp-table');
  await page.click('button:has-text("Processed JSON")');
  await page.waitForTimeout(500);
  
  // Select TITAN from the company dropdown
  const companySelect = page.locator('.control-group select').nth(0);
  await companySelect.selectOption({ label: 'TITAN' });
  await page.waitForTimeout(500);
  
  // Verify TITAN Loaded
  const titanName = await page.textContent('.info-item:has-text("Company Name") .info-value');
  expect(titanName).toContain('TITAN');
  
  // Expand Promoters -> Indian -> Central Government/ State Government(s)
  await page.click('text=Promoters');
  await page.click('text=Indian');
  await page.click('text=Central Government/ State Government(s)');
  
  // Assert Tamilnadu Industrial Development Corporation Ltd is visible
  const titanGovtRow = page.locator('.entity-row').filter({ hasText: 'Tamilnadu Industrial Development Corporation Ltd' });
  await expect(titanGovtRow).toBeVisible();
  
  const titanGovtPct = await titanGovtRow.locator('td:last-child').textContent();
  console.log(`Found TITAN Govt shareholding: ${titanGovtPct}`);
  expect(parseFloat(titanGovtPct)).toBeGreaterThan(27.0);

  console.log("Playwright test completed successfully!");
});
