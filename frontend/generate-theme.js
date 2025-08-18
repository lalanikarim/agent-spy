#!/usr/bin/env node

// This script should be run on the frontend server where npm is available
// Usage: node generate-theme.js

const fs = require('fs');
const path = require('path');

// Read theme tokens from JSON file
const tokensPath = path.join(__dirname, 'theme-tokens.json');
const tokens = JSON.parse(fs.readFileSync(tokensPath, 'utf8'));

function generateCSSVariables(themeTokens) {
  const cssVars = [];

  for (const [category, values] of Object.entries(themeTokens)) {
    if (typeof values === 'object' && values !== null) {
      for (const [key, value] of Object.entries(values)) {
        if (typeof value === 'object' && value !== null) {
          // Handle nested objects like fontSize, fontWeight, etc.
          for (const [subKey, subValue] of Object.entries(value)) {
            const cssVarName = `--${category}-${key}-${subKey}`;
            cssVars.push(`  ${cssVarName}: ${subValue};`);
          }
        } else {
          // Handle simple key-value pairs
          const cssVarName = category !== "colors" ? `--${category}-${key}` : `--color-${key}`;
          cssVars.push(`  ${cssVarName}: ${value};`);
        }
      }
    }
  }

  return cssVars.join('\n');
}

function generateOptimizedCSS() {
  const lightVars = generateCSSVariables(tokens.light);
  const darkVars = generateCSSVariables(tokens.dark);

  return `/* Theme System - Generated from centralized tokens */

/* Light Theme Variables */
:root {
${lightVars}
}

/* Dark Theme Variables */
[data-theme="dark"] {
${darkVars}
}

/* Utility Classes */
.bg-theme-surface { background-color: var(--color-surface); }
.bg-theme-surface-hover { background-color: var(--color-surface-hover); }
.bg-theme-surface-active { background-color: var(--color-surface-active); }

.text-theme-text { color: var(--color-text); }
.text-theme-text-secondary { color: var(--color-text-secondary); }
.text-theme-text-muted { color: var(--color-text-muted); }
.text-theme-text-inverse { color: var(--color-text-inverse); }

.border-theme-border { border-color: var(--color-border); }
.border-theme-border-hover { border-color: var(--color-border-hover); }
.border-theme-border-focus { border-color: var(--color-border-focus); }

/* Dedicated hover utility classes */
.bg-theme-hover-light { background-color: var(--color-hover-light); }
.bg-theme-hover-dark { background-color: var(--color-hover-dark); }
.text-theme-hover-text { color: var(--color-hover-text); }
.border-theme-hover-border { border-color: var(--color-hover-border); }

/* Dedicated selection utility classes */
.bg-theme-selection-light { background-color: var(--color-selection-light); }
.bg-theme-selection-dark { background-color: var(--color-selection-dark); }
.text-theme-selection-text-light { color: var(--color-selection-text-light); }
.text-theme-selection-text-dark { color: var(--color-selection-text-dark); }

.shadow-theme-sm { box-shadow: var(--shadows-sm); }
.shadow-theme-md { box-shadow: var(--shadows-md); }
.shadow-theme-lg { box-shadow: var(--shadows-lg); }
.shadow-theme-xl { box-shadow: var(--shadows-xl); }

.rounded-theme-sm { border-radius: var(--borderRadius-sm); }
.rounded-theme-md { border-radius: var(--borderRadius-md); }
.rounded-theme-lg { border-radius: var(--borderRadius-lg); }
.rounded-theme-xl { border-radius: var(--borderRadius-xl); }

.transition-theme-fast { transition-duration: var(--transitions-fast); }
.transition-theme-normal { transition-duration: var(--transitions-normal); }
.transition-theme-slow { transition-duration: var(--transitions-slow); }

/* Ant Design Overrides */
.ant-btn {
  border-radius: var(--borderRadius-md);
  transition: all var(--transitions-normal);
}

.ant-card {
  border-radius: var(--borderRadius-lg);
  box-shadow: var(--shadows-md);
}

.ant-input {
  border-radius: var(--borderRadius-md);
  transition: all var(--transitions-normal);
}

.ant-select {
  border-radius: var(--borderRadius-md);
}

.ant-modal {
  border-radius: var(--borderRadius-lg);
}

/* Animation Keyframes */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideIn {
  from { transform: translateY(-10px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}`;
}

try {
  // Generate the CSS
  const css = generateOptimizedCSS();

  // Write to theme.css
  const outputPath = path.join(__dirname, 'src/styles/theme.css');
  fs.writeFileSync(outputPath, css);

  console.log('✅ Theme CSS generated successfully!');
  console.log('📁 Output:', outputPath);
  console.log('📊 Tokens source:', tokensPath);

} catch (error) {
  console.error('❌ Error generating theme CSS:', error.message);
  process.exit(1);
}
