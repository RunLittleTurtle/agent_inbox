#!/usr/bin/env node

/**
 * Google OAuth Configuration Checker
 *
 * Verifies that all required environment variables are set
 * for Google OAuth integration to work properly.
 *
 * Usage:
 *   node check-google-oauth.js
 */

const fs = require('fs');
const path = require('path');

console.log('\n🔍 Checking Google OAuth Configuration...\n');

// Load .env.local
const envPath = path.join(__dirname, '.env.local');
if (!fs.existsSync(envPath)) {
  console.error('❌ .env.local file not found!');
  console.log('   Create it by copying .env.google-oauth-example\n');
  process.exit(1);
}

const envContent = fs.readFileSync(envPath, 'utf-8');
const envLines = envContent.split('\n');
const envVars = {};

// Parse .env file
envLines.forEach(line => {
  const match = line.match(/^([^#=]+)=(.*)$/);
  if (match) {
    const key = match[1].trim();
    const value = match[2].trim();
    envVars[key] = value;
  }
});

// Check required variables
const checks = [
  {
    name: 'GOOGLE_CLIENT_ID',
    required: true,
    validator: (val) => val && val.includes('.apps.googleusercontent.com'),
    errorMsg: 'Should end with .apps.googleusercontent.com'
  },
  {
    name: 'GOOGLE_CLIENT_SECRET',
    required: true,
    validator: (val) => val && val.startsWith('GOCSPX-'),
    errorMsg: 'Should start with GOCSPX-'
  },
  {
    name: 'NEXT_PUBLIC_APP_URL',
    required: true,
    validator: (val) => val && (val.startsWith('http://') || val.startsWith('https://')),
    errorMsg: 'Should start with http:// or https://'
  },
  {
    name: 'NEXT_PUBLIC_SUPABASE_URL',
    required: true,
    validator: (val) => val && val.includes('supabase.co'),
    errorMsg: 'Should contain supabase.co'
  },
  {
    name: 'SUPABASE_SECRET_KEY',
    required: true,
    validator: (val) => val && val.length > 20,
    errorMsg: 'Should be a long secret key'
  },
  {
    name: 'NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY',
    required: true,
    validator: (val) => val && val.startsWith('pk_'),
    errorMsg: 'Should start with pk_'
  },
  {
    name: 'CLERK_SECRET_KEY',
    required: true,
    validator: (val) => val && val.startsWith('sk_'),
    errorMsg: 'Should start with sk_'
  }
];

let allPassed = true;
let googleOAuthConfigured = true;

checks.forEach(check => {
  const value = envVars[check.name];
  const exists = value !== undefined && value !== '';
  const isValid = exists && check.validator(value);

  let status = '✅';
  let message = '';

  if (!exists) {
    status = check.required ? '❌' : '⚠️';
    message = check.required ? 'MISSING (required)' : 'Not set (optional)';
    allPassed = false;
    if (check.name.includes('GOOGLE')) googleOAuthConfigured = false;
  } else if (!isValid) {
    status = '⚠️';
    message = `Invalid format: ${check.errorMsg}`;
    if (check.required) allPassed = false;
    if (check.name.includes('GOOGLE')) googleOAuthConfigured = false;
  } else {
    // Mask sensitive values
    if (check.name.includes('SECRET') || check.name.includes('KEY')) {
      message = `${value.substring(0, 10)}...${value.substring(value.length - 4)}`;
    } else {
      message = value.length > 50 ? `${value.substring(0, 47)}...` : value;
    }
  }

  console.log(`${status} ${check.name.padEnd(40)} ${message}`);
});

console.log('\n' + '='.repeat(80));

if (allPassed) {
  console.log('✅ All required environment variables are set!\n');
} else {
  console.log('❌ Some required environment variables are missing or invalid.\n');
  console.log('📝 To fix:');
  console.log('   1. Get credentials from Google Cloud Console');
  console.log('   2. Add missing variables to .env.local');
  console.log('   3. Run this check again\n');
  process.exit(1);
}

// Additional checks
console.log('\n🔧 Additional Checks:\n');

// Check if config-app is in correct directory
const packageJsonPath = path.join(__dirname, 'package.json');
if (fs.existsSync(packageJsonPath)) {
  const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf-8'));
  console.log(`✅ Project name: ${packageJson.name}`);
} else {
  console.log('⚠️  package.json not found');
}

// Check if OAuth routes exist
const initiateRoute = path.join(__dirname, 'src/app/api/oauth/google/initiate/route.ts');
const callbackRoute = path.join(__dirname, 'src/app/api/oauth/google/callback/route.ts');
const successPage = path.join(__dirname, 'src/app/oauth/google/success/page.tsx');
const errorPage = path.join(__dirname, 'src/app/oauth/google/error/page.tsx');

console.log(`${fs.existsSync(initiateRoute) ? '✅' : '❌'} OAuth initiate route exists`);
console.log(`${fs.existsSync(callbackRoute) ? '✅' : '❌'} OAuth callback route exists`);
console.log(`${fs.existsSync(successPage) ? '✅' : '❌'} OAuth success page exists`);
console.log(`${fs.existsSync(errorPage) ? '✅' : '❌'} OAuth error page exists`);

// Check if GoogleWorkspaceCard exists
const googleCardPath = path.join(__dirname, 'src/components/config/cards/GoogleWorkspaceCard.tsx');
console.log(`${fs.existsSync(googleCardPath) ? '✅' : '❌'} GoogleWorkspaceCard component exists`);

console.log('\n' + '='.repeat(80));

if (googleOAuthConfigured) {
  console.log('\n✅ Google OAuth is properly configured!\n');
  console.log('📝 Next steps:');
  console.log('   1. Start dev server: npm run dev');
  console.log('   2. Open: http://localhost:3004');
  console.log('   3. Navigate to Google Workspace Integration');
  console.log('   4. Click "Connect Google Account"\n');
} else {
  console.log('\n⚠️  Google OAuth credentials not configured.\n');
  console.log('📝 Setup instructions:');
  console.log('   1. See: GOOGLE_OAUTH_SETUP.md');
  console.log('   2. Get credentials from Google Cloud Console');
  console.log('   3. Add to .env.local file');
  console.log('   4. Run this check again\n');
}
