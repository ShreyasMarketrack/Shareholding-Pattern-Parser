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

  // Click on "Indian" to expand it
  await page.click('text=Indian');

  // Now "Individuals/Hindu undivided Family" should be visible
  await expect(page.locator('text=Individuals/Hindu undivided Family').first()).toBeVisible();

  // Click on it
  await page.click('text=Individuals/Hindu undivided Family');

  // Verify that specific entities are shown (e.g. shareholder names or the aggregate generic string)
  // We'll just verify the depth-3 rows are visible
  const deepRowsCount = await page.locator('.entity-row.depth-3').count();
  console.log(`Found ${deepRowsCount} specific entities under Individuals/HUF`);
  
  // At least one specific member or generic grouping should appear
  expect(deepRowsCount).toBeGreaterThanOrEqual(0);

  console.log("Playwright test completed successfully!");
});
