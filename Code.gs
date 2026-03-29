/**
 * Google Apps Script for Rural India AI Session Logging
 * 
 * This script runs in Google Sheets and receives session data from FastAPI backend.
 * Automatically appends login/logout events and calculates session duration.
 * 
 * SETUP INSTRUCTIONS:
 * 1. Create a new Google Sheet (or use existing)
 * 2. Set up columns: A=Serial, B=Name, C=Email, D=Login Time, E=Logout Time, F=Total Minutes
 * 3. Go to Extensions → Apps Script
 * 4. Paste this entire script into Code.gs
 * 5. Deploy as Web App (see instructions in comments below)
 * 6. Copy the deployment URL to your FastAPI .env file
 */

// ===== CONFIGURATION =====

// Sheet name where session logs will be stored
const SHEET_NAME = 'Session Logs';

// Column indices (1-based)
const COLUMN_SERIAL = 1;      // A
const COLUMN_NAME = 2;         // B
const COLUMN_EMAIL = 3;        // C
const COLUMN_LOGIN = 4;        // D
const COLUMN_LOGOUT = 5;       // E
const COLUMN_DURATION = 6;     // F

// ===== INITIALIZATION =====

/**
 * Initialize the Google Sheet with headers if not already present
 * Run this function manually once after deployment:
 * 1. Click "Run" → "initializeSheet"
 * 2. Authorize the script
 * Once complete, you can delete this line from the file
 */
function initializeSheet() {
  const sheet = getOrCreateSheet(SHEET_NAME);
  
  // Check if headers already exist
  const headers = sheet.getRange(1, 1, 1, 6).getValues()[0];
  if (headers[0] === 'Serial') {
    Logger.log('✅ Sheet already initialized with headers');
    return;
  }
  
  // Add headers
  const headerRow = [
    'Serial',
    'Name',
    'Email',
    'Login Time',
    'Logout Time',
    'Total Minutes'
  ];
  sheet.getRange(1, 1, 1, 6).setValues([headerRow]);
  
  // Format header row
  const headerRange = sheet.getRange(1, 1, 1, 6);
  headerRange.setBackground('#4285F4');
  headerRange.setFontColor('#FFFFFF');
  headerRange.setFontWeight('bold');
  
  // Set column widths
  sheet.setColumnWidth(COLUMN_SERIAL, 80);      // Serial
  sheet.setColumnWidth(COLUMN_NAME, 150);       // Name
  sheet.setColumnWidth(COLUMN_EMAIL, 200);      // Email
  sheet.setColumnWidth(COLUMN_LOGIN, 200);      // Login Time
  sheet.setColumnWidth(COLUMN_LOGOUT, 200);     // Logout Time
  sheet.setColumnWidth(COLUMN_DURATION, 130);   // Total Minutes
  
  Logger.log('✅ Sheet initialized with headers');
}

// ===== MAIN: doPost HANDLER =====

/**
 * Main handler for POST requests from FastAPI backend
 * 
 * Receives JSON payload with structure:
 * {
 *   "action": "LOGIN" | "LOGOUT",
 *   "email": "user@example.com",
 *   "name": "User Name",           // Only for LOGIN
 *   "timestamp": "2026-03-29T10:32:45.123456"
 * }
 * 
 * Returns 200 OK on success
 */
function doPost(e) {
  try {
    // Parse incoming JSON
    let payload;
    try {
      payload = JSON.parse(e.postData.contents);
    } catch (parseError) {
      Logger.error('❌ JSON parse error: ' + parseError);
      return ContentService
        .createTextOutput(JSON.stringify({error: 'Invalid JSON'}))
        .setMimeType(ContentService.MimeType.JSON);
    }
    
    // Validate payload
    if (!payload.action || !payload.email) {
      Logger.error('❌ Missing action or email in payload');
      return ContentService
        .createTextOutput(JSON.stringify({error: 'Missing action or email'}))
        .setMimeType(ContentService.MimeType.JSON);
    }
    
    const action = payload.action.toUpperCase();
    const email = payload.email;
    const name = payload.name || email.split('@')[0];
    const timestamp = payload.timestamp || new Date().toISOString();
    
    Logger.log(`📩 Received ${action} request for ${email}`);
    
    // Route to appropriate handler
    if (action === 'LOGIN') {
      logLogin(email, name, timestamp);
    } else if (action === 'LOGOUT') {
      logLogout(email, timestamp);
    } else {
      Logger.warn(`⚠️  Unknown action: ${action}`);
    }
    
    // Return success
    return ContentService
      .createTextOutput(JSON.stringify({status: 'success', action: action}))
      .setMimeType(ContentService.MimeType.JSON);
    
  } catch (error) {
    Logger.error('❌ Error in doPost: ' + error);
    return ContentService
      .createTextOutput(JSON.stringify({error: error.toString()}))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

// ===== HANDLERS =====

/**
 * Handle LOGIN action
 * Appends new row with serial number, user info, and login timestamp
 */
function logLogin(email, name, timestamp) {
  const sheet = getOrCreateSheet(SHEET_NAME);
  
  // Get next serial number
  const lastRow = sheet.getLastRow();
  const serialNumber = lastRow; // Serial starts at 2 (row 1 is header)
  
  // Parse timestamp to readable format
  const loginTime = formatTimestamp(timestamp);
  
  // Append new row
  const newRow = [
    serialNumber,           // Serial
    name,                   // Name
    email,                  // Email
    loginTime,              // Login Time
    '',                     // Logout Time (empty initially)
    ''                      // Total Minutes (calculated on logout)
  ];
  
  sheet.appendRow(newRow);
  
  Logger.log(`✅ Login logged: ${email} (Serial: ${serialNumber})`);
}

/**
 * Handle LOGOUT action
 * Finds user's active login row, adds logout time, and calculates duration
 */
function logLogout(email, timestamp) {
  const sheet = getOrCreateSheet(SHEET_NAME);
  
  // Find active login row for this user (no logout time yet)
  const data = sheet.getDataRange().getValues();
  let activeRowIndex = -1;
  
  for (let i = 1; i < data.length; i++) { // Skip header (row 0)
    const rowEmail = data[i][COLUMN_EMAIL - 1]; // -1 because array is 0-indexed
    const logoutTime = data[i][COLUMN_LOGOUT - 1];
    
    if (rowEmail === email && logoutTime === '') {
      activeRowIndex = i + 1; // +1 because sheet rows are 1-indexed
      break;
    }
  }
  
  if (activeRowIndex === -1) {
    Logger.warn(`⚠️  No active login found for ${email}`);
    return;
  }
  
  // Format logout timestamp
  const logoutTimeStr = formatTimestamp(timestamp);
  
  // Get login time to calculate duration
  const loginTimeStr = sheet.getRange(activeRowIndex, COLUMN_LOGIN).getValue();
  
  // Set logout time
  sheet.getRange(activeRowIndex, COLUMN_LOGOUT).setValue(logoutTimeStr);
  
  // Calculate duration in minutes
  const durationMinutes = calculateDurationMinutes(loginTimeStr, logoutTimeStr);
  sheet.getRange(activeRowIndex, COLUMN_DURATION).setValue(durationMinutes);
  
  Logger.log(
    `✅ Logout logged: ${email} (Row: ${activeRowIndex}, Duration: ${durationMinutes} min)`
  );
}

// ===== HELPER FUNCTIONS =====

/**
 * Get or create a sheet with the given name
 */
function getOrCreateSheet(sheetName) {
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = spreadsheet.getSheetByName(sheetName);
  
  if (!sheet) {
    sheet = spreadsheet.insertSheet(sheetName);
    Logger.log(`📄 Created new sheet: ${sheetName}`);
  }
  
  return sheet;
}

/**
 * Format ISO timestamp to readable format
 * Input: "2026-03-29T10:32:45.123456"
 * Output: "29 Mar 2026, 10:32:45"
 */
function formatTimestamp(isoTimestamp) {
  try {
    // Parse ISO format
    const date = new Date(isoTimestamp);
    
    // Format: "29 Mar 2026, 10:32:45"
    const options = {
      year: 'numeric',
      month: 'short',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    };
    
    return date.toLocaleString('en-US', options);
  } catch (error) {
    Logger.warn(`⚠️  Error formatting timestamp: ${error}`);
    return new Date().toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
  }
}

/**
 * Calculate duration in minutes between two time strings
 * Handles Google Sheets date format
 */
function calculateDurationMinutes(loginTimeStr, logoutTimeStr) {
  try {
    // Parse time strings
    const loginDate = new Date(loginTimeStr);
    const logoutDate = new Date(logoutTimeStr);
    
    // Calculate difference in ms, convert to minutes
    const durationMs = logoutDate - loginDate;
    const durationMinutes = Math.round(durationMs / (1000 * 60));
    
    return Math.max(0, durationMinutes); // Ensure non-negative
  } catch (error) {
    Logger.warn(`⚠️  Error calculating duration: ${error}`);
    return 0;
  }
}

// ===== TESTING & DEBUGGING =====

/**
 * Test function to verify the script setup
 * Run this to see if everything is configured correctly:
 * 1. Click "Run" → "testWebhook"
 * 2. Check logs for results
 */
function testWebhook() {
  Logger.log('🧪 Testing Google Apps Script setup...\n');
  
  // Test 1: Check if sheet exists
  const sheet = getOrCreateSheet(SHEET_NAME);
  if (sheet) {
    Logger.log('✅ Sheet "' + SHEET_NAME + '" exists');
  } else {
    Logger.log('❌ Could not access or create sheet');
    return;
  }
  
  // Test 2: Check if headers exist
  const headers = sheet.getRange(1, 1, 1, 6).getValues()[0];
  if (headers[0] === 'Serial') {
    Logger.log('✅ Headers found in row 1');
  } else {
    Logger.log('⚠️  Headers not found. Run initializeSheet() first.');
    return;
  }
  
  // Test 3: Simulate a login
  Logger.log('\n📝 Simulating LOGIN event...');
  logLogin('test@example.com', 'Test User', new Date().toISOString());
  Logger.log('✅ Login row appended');
  
  // Test 4: Get the newly added row and simulate logout
  Logger.log('\n📝 Simulating LOGOUT event...');
  logLogout('test@example.com', new Date().toISOString());
  Logger.log('✅ Logout time and duration calculated');
  
  // Test 5: Show final rows
  const allData = sheet.getDataRange().getValues();
  Logger.log('\n📊 Sheet data after test:');
  for (let i = Math.max(0, allData.length - 3); i < allData.length; i++) {
    Logger.log(`Row ${i + 1}: ${JSON.stringify(allData[i])}`);
  }
  
  Logger.log('\n✅ Test completed successfully!');
}

/**
 * Delete test rows (clean up after testing)
 * Run this to remove the test data:
 * 1. Click "Run" → "cleanupTestData"
 */
function cleanupTestData() {
  const sheet = getOrCreateSheet(SHEET_NAME);
  const data = sheet.getDataRange().getValues();
  
  // Find and delete rows with test@example.com
  for (let i = data.length - 1; i >= 1; i--) { // Skip header
    if (data[i][COLUMN_EMAIL - 1] === 'test@example.com') {
      sheet.deleteRow(i + 1); // +1 because sheet is 1-indexed
      Logger.log(`🗑️  Deleted test row: ${i + 1}`);
    }
  }
}

// ===== DEPLOYMENT INSTRUCTIONS =====

/**
 * HOW TO DEPLOY THIS SCRIPT:
 * 
 * 1. CREATE A GOOGLE SHEET
 *    - Go to https://sheets.google.com
 *    - Click "Create new spreadsheet"
 *    - Name it "Rural India AI - Session Logs"
 * 
 * 2. ADD THIS SCRIPT
 *    - Go to Extensions → Apps Script
 *    - Delete any default code
 *    - Paste this entire script
 * 
 * 3. INITIALIZE THE SHEET
 *    - In the Apps Script editor:
 *    - Select "initializeSheet" from dropdown
 *    - Click "Run"
 *    - Authorize when prompted
 *    - Check logs (Ctrl+Enter) for "✅ Sheet initialized"
 * 
 * 4. DEPLOY AS WEB APP
 *    - In Apps Script editor, click "Deploy" → "New Deployment"
 *    - Select type: "Web app"
 *    - Execute as: (your Google account)
 *    - Who has access: "Anyone"
 *    - Click "Deploy"
 *    - You'll see: https://script.google.com/macros/d/{SCRIPT_ID}/userweb?state=done
 *    - Copy this URL
 * 
 * 5. UPDATE YOUR FASTAPI .env
 *    - Add: GOOGLE_SHEET_WEBHOOK_URL=https://script.google.com/macros/d/{SCRIPT_ID}/userweb?state=done
 *    - Replace {SCRIPT_ID} with actual script ID from step 4
 * 
 * 6. TEST IT
 *    - In Apps Script editor:
 *    - Select "testWebhook" from dropdown
 *    - Click "Run"
 *    - Check logs to see test data added to sheet
 * 
 * 7. VERIFY IN GOOGLE SHEET
 *    - Open your sheet in browser
 *    - Should see "Session Logs" tab
 *    - Should see test rows with login/logout times and duration
 * 
 * 8. CLEANUP (Optional)
 *    - Run "cleanupTestData" to delete test rows before going live
 * 
 * 9. INTEGRATE WITH FASTAPI
 *    - Add import: from google_sheets_logger import log_user_login_to_sheet, log_user_logout_to_sheet
 *    - Call in auth endpoints (see auth.py or FASTAPI_GOOGLE_SHEETS_INTEGRATION.md)
 * 
 * DONE! Your backend will now log all sessions to Google Sheets automatically.
 */
