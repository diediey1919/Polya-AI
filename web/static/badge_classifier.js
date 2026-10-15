/*
 * Polya UI — Case badge classification (pure function)
 * Source of truth: web/static/index.html case-status-badge rendering (Recovery-012)
 * Extracted to enable regression testing via Node.js (no browser/E2E required).
 * Returns the badge label and color class only — never renders DOM.
 */
(function (root, factory) {
  "use strict";
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.PolyaBadge = factory();
  }
}(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  // Color tokens referenced by index.html badge blocks
  var ROSE = "var(--rose)";
  var EMERALD = "var(--emerald)";

  function _badge(label, color, bg) {
    return {
      label: label,
      color: color,
      background: bg,
      verified: false,
      isDemo: false,
      isError: false,
      isUnverified: false
    };
  }

  function classifyCaseBadge(cf) {
    cf = cf || {};
    var isDemo = cf.is_demo === true;

    if (isDemo) {
      return Object.assign(_badge("DEMO / MOCK DATA", ROSE, "rgba(244, 63, 94, 0.15)"),
        { isDemo: true });
    }

    var synth = String(cf.synthesis_status || "").toUpperCase();
    var ret = String(cf.retrieval_status || "").toUpperCase();
    // hasEvidence: array non-empty AND each item passes structural plausibility
    // (rejects [{}, "string", null] that would otherwise pass a length-only check).
    var hasEvidence = Array.isArray(cf.evidence) && cf.evidence.length > 0 &&
      cf.evidence.every(function (e) {
        var s = e && typeof e === "object" ? e : {};
        var txt = s.source_text || s.original_text || s.passage_reference || "";
        return s.evidence_id || s.passage_reference || s.source_id || txt;
      });

    if (synth === "MODEL_ERROR") {
      return Object.assign(_badge("MODEL ERROR", "#f59e0b", "rgba(245, 158, 11, 0.15)"),
        { isError: true });
    }

    if (ret === "INSUFFICIENT_EVIDENCE" || !hasEvidence) {
      return Object.assign(_badge("BELUM TERVERIFIKASI", "#f59e0b", "rgba(245, 158, 11, 0.15)"),
        { isUnverified: true });
    }

    if (synth === "SUCCESS" && ret === "SUFFICIENT" && !cf.fallback_used) {
      return Object.assign(_badge("VERIFIED REAL INTEL", EMERALD, "rgba(16, 185, 129, 0.15)"),
        { verified: true });
    }

    // Fail-closed: any other case (unknown status, missing fields, fallback_used, PARTIAL)
    return Object.assign(_badge("BELUM TERVERIFIKASI", "#f59e0b", "rgba(245, 158, 11, 0.15)"),
      { isUnverified: true });
  }

  return { classifyCaseBadge: classifyCaseBadge };
}));
