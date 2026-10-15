/*
 * POLYA-PIPELINE-RECOVERY-015C: Badge classifier provenance regression tests.
 *
 * Tests web/static/badge_classifier.js directly via require() — no copy.
 * Verifies that green badge (VERIFIED REAL INTEL) only appears when ALL
 * conditions are met: provenance === "verified_success", provider is a
 * live provider (starts with "live:"), synthesis SUCCESS, retrieval
 * SUFFICIENT, evidence present, no fallback.
 *
 * FAIL-CLOSED: any missing/insufficient provenance → amber badge.
 */
"use strict";

const path = require("path");
const assert = require("assert");

// Import the real production badge classifier — no copy
const { classifyCaseBadge } = require(
  path.join(__dirname, "..", "web", "static", "badge_classifier.js")
);

// Shared constants matching the module
const EMERALD_GREEN = "rgba(16, 185, 129, 0.15)";
const ROSE_BG = "rgba(244, 63, 94, 0.15)";
const AMBER_BG = "rgba(245, 158, 11, 0.15)";

function _goodCase(overrides) {
  return Object.assign({
    case_id: "case_test_01",
    claim: "Test claim",
    is_demo: false,
    notice: "",
    synthesis_status: "SUCCESS",
    retrieval_status: "SUFFICIENT",
    fallback_used: false,
    provider: "live:claude-code",
    provenance: "verified_success",
    evidence: [
      {
        evidence_id: "ev_001",
        source_text: "νόμον οὖν καταργοῦμεν διὰ τῆς πίστεως (Roma 3:31)",
        passage_reference: "Roma 3:31",
        source_locale: "el"
      }
    ],
    sources: [{ citation: "BDAG", type: "Lexicon" }],
    argument: "Test argument",
    counterargument: "Test counter",
    rebuttal: "Test rebuttal",
    weakness: "Test weakness",
    open_questions: [],
    debate_preparation: {},
  }, overrides || {});
}

// ─── TEST RUNNER ───────────────────────────────────────────────
let passed = 0;
let failed = 0;
const failures = [];

function test(name, fn) {
  try {
    fn();
    passed++;
    console.log("  ✓ " + name);
  } catch (err) {
    failed++;
    failures.push({ name, err });
    console.log("  ✗ " + name + " — " + err.message);
  }
}

// ─── TESTS ─────────────────────────────────────────────────────

test("DEMO case gets Rose badge, isDemo=true, verified=false", () => {
  const cf = _goodCase({ is_demo: true });
  const badge = classifyCaseBadge(cf);
  assert.strictEqual(badge.isDemo, true);
  assert.strictEqual(badge.verified, false);
  assert.strictEqual(badge.label, "DEMO / MOCK DATA");
  assert.strictEqual(badge.background, ROSE_BG || badge.background);
});

test("MODEL_ERROR gets amber badge, isError=true", () => {
  const cf = _goodCase({ synthesis_status: "MODEL_ERROR" });
  const badge = classifyCaseBadge(cf);
  assert.strictEqual(badge.isError, true);
  assert.strictEqual(badge.verified, false);
});

test("INSUFFICIENT_EVIDENCE gets amber badge, isUnverified=true", () => {
  const cf = _goodCase({ retrieval_status: "INSUFFICIENT_EVIDENCE" });
  const badge = classifyCaseBadge(cf);
  assert.strictEqual(badge.isUnverified, true);
  assert.strictEqual(badge.verified, false);
});

test("Empty evidence array gets amber badge, isUnverified=true", () => {
  const cf = _goodCase({ evidence: [] });
  const badge = classifyCaseBadge(cf);
  assert.strictEqual(badge.isUnverified, true);
  assert.strictEqual(badge.verified, false);
});

test("template provider with SUCCESS/SUFFICIENT is NOT green (fail-closed)", () => {
  const cf = _goodCase({ provider: "template" });
  const badge = classifyCaseBadge(cf);
  assert.strictEqual(badge.verified, false);
  assert.strictEqual(badge.isUnverified, true);
});

test("unknown provider with SUCCESS/SUFFICIENT is NOT green", () => {
  const cf = _goodCase({ provider: "unknown" });
  const badge = classifyCaseBadge(cf);
  assert.strictEqual(badge.verified, false);
  assert.strictEqual(badge.isUnverified, true);
});

test("fallback_used blocks green badge even with live provider", () => {
  const cf = _goodCase({ fallback_used: true });
  const badge = classifyCaseBadge(cf);
  assert.strictEqual(badge.verified, false);
  assert.strictEqual(badge.isUnverified, true);
});

test("verified_success with non-live provider (live: without suffix) is NOT green", () => {
  const cf = _goodCase({ provider: "live:" });
  const badge = classifyCaseBadge(cf);
  assert.strictEqual(badge.verified, false);
  assert.strictEqual(badge.isUnverified, true);
});

test("SUCCESS + SUFFICIENT + no fallback + provenance=unknown is NOT green", () => {
  const cf = _goodCase({ provenance: "unknown" });
  const badge = classifyCaseBadge(cf);
  assert.strictEqual(badge.verified, false);
  assert.strictEqual(badge.isUnverified, true);
});

test("SUCCESS + SUFFICIENT + no fallback + provenance=fallback is NOT green", () => {
  const cf = _goodCase({ provenance: "fallback" });
  const badge = classifyCaseBadge(cf);
  assert.strictEqual(badge.verified, false);
  assert.strictEqual(badge.isUnverified, true);
});

test("Green badge ONLY for fully verified: SUCCESS+SUFFICIENT+no fallback+verified_success+live provider", () => {
  const cf = _goodCase({});
  const badge = classifyCaseBadge(cf);
  assert.strictEqual(badge.verified, true);
  assert.strictEqual(badge.isDemo, false);
  assert.strictEqual(badge.isError, false);
  assert.strictEqual(badge.isUnverified, false);
  assert.strictEqual(badge.label, "VERIFIED REAL INTEL");
});

test("Missing provenance field defaults to unknown — NOT green", () => {
  const cf = _goodCase({ provider: "live:claude-code" });
  delete cf.provenance;
  const badge = classifyCaseBadge(cf);
  assert.strictEqual(badge.verified, false);
  assert.strictEqual(badge.isUnverified, true);
});

test("Missing provider field defaults to unknown — NOT green", () => {
  const cf = _goodCase({ provenance: "verified_success" });
  delete cf.provider;
  const badge = classifyCaseBadge(cf);
  assert.strictEqual(badge.verified, false);
  assert.strictEqual(badge.isUnverified, true);
});

test("Partial synthesis with live provider is NOT green", () => {
  const cf = _goodCase({ synthesis_status: "PARTIAL" });
  const badge = classifyCaseBadge(cf);
  assert.strictEqual(badge.verified, false);
  assert.strictEqual(badge.isUnverified, true);
});

test("Live provider with empty output is NOT green (provenance=unknown)", () => {
  const cf = _goodCase({
    provider: "live:claude-code",
    provenance: "unknown",
    evidence: [{ passage_reference: "Test" }],
  });
  const badge = classifyCaseBadge(cf);
  assert.strictEqual(badge.verified, false);
});

test("PROVENANCE: template output never gets green even if synthesis says SUCCESS", () => {
  // This is the core Recovery-015C invariant
  const cf = _goodCase({
    provider: "template",
    provenance: "template",
  });
  const badge = classifyCaseBadge(cf);
  assert.strictEqual(badge.verified, false,
    "Template output must NEVER get green badge despite SUCCESS synthesis status");
});

// ─── SUMMARY ───────────────────────────────────────────────────
console.log("\n═══════════════════════════════════════════");
console.log("Badge classifier provenance tests: " + passed + " passed, " + failed + " failed");
console.log("═══════════════════════════════════════════");

if (failed > 0) {
  console.log("\nFailing tests:");
  failures.forEach(function (f) {
    console.log("  ✗ " + f.name + ": " + f.err.message);
  });
  process.exit(1);
}

process.exit(0);
