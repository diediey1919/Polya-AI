const fs = require('fs');
const path = require('path');
const vm = require('vm');

const REPO_ROOT = path.resolve(__dirname, '..');
const INDEX_HTML_PATH = path.join(REPO_ROOT, 'web', 'static', 'index.html');
const I18N_DICT_PATH = path.join(REPO_ROOT, 'web', 'static', 'i18n_dict.js');

const CANONICAL_LANGS = [
  'id', 'en', 'ar', 'es', 'pt', 'ur', 'hi', 'fr', 'de', 'ru', 'tr', 'fa', 'bn', 'zh', 'ja', 'ko', 'it'
];

console.log('--- Loading i18n_dict.js and index.html ---');
const indexHtmlContent = fs.readFileSync(INDEX_HTML_PATH, 'utf8');
const i18nDictContent = fs.readFileSync(I18N_DICT_PATH, 'utf8');

// Set up VM context
const sandbox = {
  window: {},
  document: {
    documentElement: {},
    body: { classList: { toggle: () => {} } },
    querySelectorAll: () => [],
    getElementById: () => null
  },
  console: console
};
vm.createContext(sandbox);

// 1. Execute i18n_dict.js
// In i18n_dict.js, it might define const EXTENDED_I18N_MODULES. We attach it to window.EXTENDED_I18N_MODULES
const wrappedDictCode = i18nDictContent + '\nwindow.EXTENDED_I18N_MODULES = typeof EXTENDED_I18N_MODULES !== "undefined" ? EXTENDED_I18N_MODULES : (typeof window !== "undefined" && window.EXTENDED_I18N_MODULES);';
vm.runInContext(wrappedDictCode, sandbox);

// 2. Extract I18N_DICTIONARY from index.html
const dictStartMatch = indexHtmlContent.indexOf('const I18N_DICTIONARY = {');
if (dictStartMatch === -1) {
  throw new Error('Could not find "const I18N_DICTIONARY = {" in index.html');
}
const dictEndMatch = indexHtmlContent.indexOf('(function mergeExtendedModules()', dictStartMatch);
if (dictEndMatch === -1) {
  throw new Error('Could not find "function mergeExtendedModules" in index.html');
}

const rawDictCode = indexHtmlContent.substring(dictStartMatch, dictEndMatch);

// Find the end of mergeExtendedModules function
const mergeEndMatch = indexHtmlContent.indexOf('})();', dictEndMatch);
if (mergeEndMatch === -1) {
  throw new Error('Could not find "})();" in index.html after mergeExtendedModules');
}
const rawMergeCode = indexHtmlContent.substring(dictEndMatch, mergeEndMatch + '})();'.length);

vm.runInContext(rawDictCode + '\n' + rawMergeCode, sandbox);

const I18N = sandbox.window.i18n || sandbox.I18N_DICTIONARY;
if (!I18N) {
  throw new Error('Failed to extract I18N dictionary!');
}

console.log(`Loaded I18N dictionary with ${Object.keys(I18N).length} languages.`);

// Verify all 17 canonical languages exist in I18N
const missingLangs = CANONICAL_LANGS.filter(l => !I18N[l]);
if (missingLangs.length > 0) {
  console.error(`FATAL: Missing canonical languages in dictionary: ${missingLangs.join(', ')}`);
  process.exit(1);
}

// 3. Extract all data-i18n* attributes from index.html
const dataI18nRegex = /data-i18n(?:-title|-placeholder|-html)?=["']([^"']+)["']/g;
const htmlKeys = new Set();
let match;
while ((match = dataI18nRegex.exec(indexHtmlContent)) !== null) {
  htmlKeys.add(match[1]);
}
console.log(`Found ${htmlKeys.size} distinct data-i18n* keys in index.html.`);

// 4. Extract ID_I18N_MAP from index.html
const idMapStartMatch = indexHtmlContent.indexOf('const ID_I18N_MAP = {');
if (idMapStartMatch === -1) {
  throw new Error('Could not find "const ID_I18N_MAP = {" in index.html');
}
const idMapEndMatch = indexHtmlContent.indexOf('};', idMapStartMatch);
const rawIdMapCode = indexHtmlContent.substring(idMapStartMatch, idMapEndMatch + 2);
vm.runInContext(rawIdMapCode + '\nsandbox_ID_I18N_MAP = ID_I18N_MAP;', sandbox);
const ID_I18N_MAP = sandbox.sandbox_ID_I18N_MAP;
console.log(`Found ${Object.keys(ID_I18N_MAP).length} elements in ID_I18N_MAP.`);

const idMapKeys = new Set(Object.values(ID_I18N_MAP));

// 5. Add critical dynamic UI keys that must be localized across all 17 languages
const dynamicKeys = [
  'btnSidebarMenu',
  'btnSidebarToggleTitle',
  'quotaPillFree',
  'quotaFreeAnalyses',
  'heroCtaFree',
  'heroCtaPremium',
  'heroCtaSubscribe',
  'canonicalLoading',
  'canonicalLoadingMore',
  'canonicalConnectionError',
  'navApologeticsMachine',
  'navSearchMotions',
  'navWorkspace',
  'navAncientCourse',
  'navBilling',
  'navPricing',
  'themesCounterSummary',
  'themeCatAll',
  'themeCatDialectic',
  'themeCatChristology',
  'themeCatPhilology',
  'themeCatTheology',
  'themeCatTrinity',
  'themeCatPauline',
  'themeCatProphecy',
  'unitMotions',
  'unitVideos',
  'badgeRecommended',
  'statusVideoQueue',
  'statusVerifiedCluster',
  'btnExploreMotions',
  'btnBackToAllClusters',
  'filterActive',
  'filterCluster',
  'btnTestInCalculator',
  'btnDossierDetail',
  'showingCategoryMotions',
  'allMotionsVerifiedTranscript',
  'loadNextMotions',
  'allClusterMotionsDisplayed',
  'knowledgeTabGraph',
  'knowledgeShuffleBtn',
  'knowledgeShuffleTitle',
  'knowledgeDirToggleDefault',
  'knowledgeDirToggleOpen',
  'knowledgeDirToggleTitle',
  'knowledgeQueryPlaceholder',
  'knowledgeDirSearchPlaceholder',
  'knowledgeStatsNodes',
  'knowledgeStatsEdges',
  'knowledgeSectionRelations',
  'knowledgeSectionEdges',
  'nodeTypeClaim',
  'nodeTypeProposition',
  'nodeTypeEvidence',
  'evidenceAccuracy',
  'inspectEvidenceAction',
  'inspectEvidenceTooltip',
  'transComparisonTitle',
  'transLiteralTitle',
  'transLaiTitle',
  'transKjvTitle',
  'transEsvTitle',
  'manuscriptWitnessesTitle',
  'confidenceLabel',
  'badgeOriginalText',
  'badgePrimaryCorpus',
  'knowledgeBtnExploreCard',
  'knowledgeBtnExploreTooltip',
  'thSource',
  'thDialecticalRelation',
  'thTarget',
  'thWeight',
  'knowledgeNodeDetailTitle',
  'knowledgeClaimsHeading',
  'knowledgeClaimsSub',
  'knowledgeEvidenceHeading',
  'knowledgeEvidenceSub',
  'knowledgeGraphLoading',
  'claimsLoading',
  'claimsEmpty',
  'evidenceLoading',
  'evidenceEmpty',
  'badgeStatusActive',
  'badgeStatusSupported',
  'badgeStatusInferred',
  'badgeStatusPrimarySource',
  'badgeStatusVerified',
  'badgeStatusDisputed',
  'badgeStatusUnsupported',
  'btnInspectDrawer',
  'btnShowSource',
  'selectedZero',
  'btnClearSearch'
];

// Helper to resolve dot-notation path like in index.html
function resolvePath(obj, pathStr) {
  if (!obj || !pathStr) return undefined;
  const parts = pathStr.split('.');
  let curr = obj;
  for (const p of parts) {
    if (curr && curr[p] !== undefined) {
      curr = curr[p];
    } else {
      curr = undefined;
      break;
    }
  }
  return curr !== undefined ? curr : obj[pathStr];
}

// Combine all required keys
const allRequiredKeys = new Set([...htmlKeys, ...idMapKeys, ...dynamicKeys]);
console.log(`Total unique i18n keys to verify per language: ${allRequiredKeys.size}`);

// Check each language
let totalFailures = 0;
const report = {};

for (const lang of CANONICAL_LANGS) {
  const langDict = I18N[lang];
  const missing = [];
  for (const key of allRequiredKeys) {
    const val = resolvePath(langDict, key);
    if (val === undefined || val === null || val === '') {
      missing.push(key);
    }
  }
  report[lang] = {
    totalKeys: allRequiredKeys.size,
    missingCount: missing.length,
    missingKeys: missing
  };
  if (missing.length > 0) {
    totalFailures += missing.length;
    console.error(`Language '${lang}' missing ${missing.length} keys: ${missing.slice(0, 10).join(', ')}${missing.length > 10 ? '...' : ''}`);
  } else {
    console.log(`Language '${lang}': 0 missing keys (OK)`);
  }
}

// Specifically check 'id' values requested in prompt
console.log('\n--- Checking specific Indonesian (id) translations ---');
const idExpected = {
  navApologeticsMachine: 'Mesin Apologetika',
  navWorkspace: 'Ruang Kerja',
  headingWorkspace: 'Ruang Kerja Riset'
};

for (const [k, expectedVal] of Object.entries(idExpected)) {
  const actualVal = resolvePath(I18N['id'], k);
  if (actualVal !== expectedVal) {
    console.error(`ID mismatch for '${k}': expected '${expectedVal}', got '${actualVal}'`);
    totalFailures++;
  } else {
    console.log(`ID check '${k}': '${actualVal}' (OK)`);
  }
}

console.log('\n=============================================');
if (totalFailures === 0) {
  console.log('SUCCESS: All 17 languages have 0 missing keys!');
  process.exit(0);
} else {
  console.error(`FAILURE: Found ${totalFailures} total missing or invalid keys across languages!`);
  process.exit(1);
}
