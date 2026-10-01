"""
Database Exceptions for Polya Philological Bible Engine (Phase 1, Task 1.2).
Strictly adheres to Architecture v2.0 FROZEN specification.
"""

import sqlite3


class BibleEngineDatabaseError(Exception):
    """Base exception for all Bible Engine database layer errors."""
    pass


class DatabaseConnectionError(BibleEngineDatabaseError):
    """Raised when an SQLite connection cannot be established or database file is inaccessible."""
    pass


class DatabaseConfigurationError(BibleEngineDatabaseError):
    """Raised when an invalid database configuration or illegal pragma modification is attempted."""
    pass


class DatabaseTransactionError(BibleEngineDatabaseError):
    """Raised on transaction lifecycle violations (e.g. invalid nesting, commit on closed connection)."""
    pass


class ReadOnlyViolationError(BibleEngineDatabaseError):
    """Raised when a write/mutation operation is attempted against a read-only connection."""
    pass


class SchemaInitializationError(BibleEngineDatabaseError):
    """Raised when schema bootstrap from 001_initial_schema.sql fails."""
    pass


class MigrationError(BibleEngineDatabaseError):
    """Base exception for all migration runner errors."""
    pass


class MigrationIntegrityError(MigrationError):
    """Raised on migration integrity violations (e.g. checksum mismatch, pragma tampering)."""
    pass


class MigrationChecksumMismatchError(MigrationIntegrityError):
    """Raised when an already-applied migration script differs from its recorded database checksum."""
    pass


class MissingMigrationFileError(MigrationError):
    """Raised when a recorded applied migration file is absent from the filesystem."""
    pass


class DuplicateMigrationError(MigrationError):
    """Raised when duplicate migration sequence numbers or IDs are discovered."""
    pass


class MalformedMigrationNameError(MigrationError):
    """Raised when a migration filename violates the strict NNN_name.sql naming convention."""
    pass


class AmbiguousMigrationOrderError(MigrationError):
    """Raised on ambiguous ordering, out-of-order pending migrations, or unexpected sequence gaps."""
    pass


class MigrationExecutionError(MigrationError):
    """Raised when executing a migration script fails, wrapping the underlying database error."""

    def __init__(self, migration_id: str, cause: Exception, statement: str = "") -> None:
        self.migration_id = migration_id
        self.cause = cause
        self.statement = statement
        msg = f"Failed to execute migration '{migration_id}': {cause}"
        if statement:
            stmt_snippet = statement.strip().replace("\n", " ")[:80]
            msg += f" (at statement: {stmt_snippet}...)"
        super().__init__(msg)


class ProvenanceError(BibleEngineDatabaseError):
    """Base exception for all provenance subsystem errors."""
    pass


class ProvenanceRecordNotFoundError(ProvenanceError):
    """Raised when a requested provenance record does not exist."""
    pass


class ProvenanceIntegrityError(ProvenanceError):
    """Raised when a provenance integrity check fails."""
    pass


class ProvenanceImmutabilityError(ProvenanceIntegrityError):
    """Raised when an illegal modification or deletion of provenance records is attempted."""
    pass


class ProvenanceHashMismatchError(ProvenanceIntegrityError):
    """Raised when content verification fails against the recorded SHA-256 provenance hash."""
    pass


class ProvenanceMissingParentError(ProvenanceIntegrityError):
    """Raised when a referenced parent provenance record is missing or unresolved."""
    pass


class ProvenanceChainBrokenError(ProvenanceIntegrityError):
    """Raised when an object's lineage chain is broken, disconnected, or unverified."""
    pass


class VersioningError(BibleEngineDatabaseError):
    """Base exception for all versioning subsystem errors."""
    pass


class VersionNotFoundError(VersioningError):
    """Raised when a requested object version does not exist."""
    pass


class VersionIntegrityError(VersioningError):
    """Raised when a version integrity check fails."""
    pass


class DuplicateVersionError(VersionIntegrityError):
    """Raised when attempting to create a duplicate version or version number for an object."""
    pass


class VersionInvalidParentError(VersionIntegrityError):
    """Raised when a referenced parent version does not exist or violates lineage rules."""
    pass


class VersionInvalidProvenanceError(VersionIntegrityError):
    """Raised when a referenced provenance record does not exist or fails validation."""
    pass


class VersionHashMismatchError(VersionIntegrityError):
    """Raised when content verification fails against the recorded content hash."""
    pass


class IllegalStateTransitionError(VersionIntegrityError):
    """Raised when an illegal version status transition is attempted."""
    pass


class VersionImmutabilityError(VersionIntegrityError):
    """Raised when an illegal modification or deletion of an immutable version is attempted."""
    pass


class VersionConcurrencyConflictError(VersioningError):
    """Raised when concurrent writers conflict during atomic version creation."""
    pass


# =============================================================================
# SOURCE REGISTRY ERRORS (Task 1.6)
# =============================================================================

class SourceRegistryError(BibleEngineDatabaseError):
    """Base exception for all source registry subsystem errors."""
    pass


class SourceNotFoundError(SourceRegistryError):
    """Raised when a requested registered source does not exist."""
    pass


class DuplicateSourceError(SourceRegistryError):
    """Raised when registering a source with a duplicate identifier or canonical name."""
    pass


class InvalidSourceTypeError(SourceRegistryError):
    """Raised when an invalid or unclassified source type is specified."""
    pass


class InvalidSourceLanguageError(SourceRegistryError):
    """Raised when an invalid or unclassified source language is specified."""
    pass


class InvalidSourceAuthorityError(SourceRegistryError):
    """Raised when an invalid functional authority level is specified."""
    pass


class InvalidVerificationStatusError(SourceRegistryError):
    """Raised when an invalid verification status is specified."""
    pass


class SourceTranslationFirewallError(SourceRegistryError):
    """Raised when translation firewall invariants are violated (e.g. translation marked as primary witness)."""
    pass


class SourceImmutabilityError(SourceRegistryError):
    """Raised when an illegal modification or deletion of source registry records is attempted."""
    pass


class SourceInvalidProvenanceError(SourceRegistryError):
    """Raised when a referenced provenance record does not exist or fails validation."""
    pass


class SourceInvalidVersionError(SourceRegistryError):
    """Raised when a referenced object version does not exist or fails validation."""
    pass


class SourceHashMismatchError(SourceRegistryError):
    """Raised when content hash validation fails against source artifact."""
    pass


class IllegalSourceStateTransitionError(SourceRegistryError):
    """Raised when an illegal verification status transition is attempted."""
    pass


# =============================================================================
# SOURCE TEXT SUBSYSTEM EXCEPTIONS (Task 2.1)
# =============================================================================

class SourceTextError(BibleEngineDatabaseError):
    """Base exception for all Source Text subsystem errors."""
    pass


class SourceTextNotFoundError(SourceTextError):
    """Raised when a requested source text record does not exist."""
    pass


class DuplicateSourceTextError(SourceTextError):
    """Raised when registering a source text with a duplicate identifier or conflicting unique key."""
    pass


class SourceTextImmutabilityError(SourceTextError):
    """Raised when an illegal modification, update of raw content/hash, or deletion of source text is attempted."""
    pass


class SourceTextTranslationFirewallError(SourceTextError):
    """Raised when translation firewall invariants are violated in source text operations."""
    pass


class SourceTextHashMismatchError(SourceTextError):
    """Raised when content hash validation fails against source text artifact."""
    pass


class MalformedContentHashError(SourceTextError):
    """Raised when a provided content hash violates the required 64-character lowercase hexadecimal format."""
    pass


class InvalidSourceTextLanguageError(SourceTextError):
    """Raised when an invalid or unclassified source text language is specified."""
    pass


class InvalidRepresentationTypeError(SourceTextError):
    """Raised when an invalid or unclassified representation type is specified."""
    pass


class SourceTextInvalidProvenanceError(SourceTextError):
    """Raised when a referenced provenance record does not exist or fails validation."""
    pass


class SourceTextInvalidVersionError(SourceTextError):
    """Raised when a referenced object version does not exist or fails validation."""
    pass


class SourceTextOrphanError(SourceTextError):
    """Raised when attempting to register or persist a source text without a valid registered source."""
    pass


# =============================================================================
# TOKENIZATION SUBSYSTEM EXCEPTIONS (Task 2.2)
# =============================================================================

class TokenError(BibleEngineDatabaseError):
    """Base exception for all Tokenization subsystem errors."""
    pass


class TokenNotFoundError(TokenError):
    """Raised when a requested token or tokenization run does not exist."""
    pass


class DuplicateTokenError(TokenError):
    """Raised when registering a token with a duplicate identifier or colliding position."""
    pass


class TokenImmutabilityError(TokenError):
    """Raised when an illegal modification or deletion of a token or tokenization run is attempted."""
    pass


class TokenSourceNotFoundError(TokenError):
    """Raised when a referenced source text for tokenization does not exist."""
    pass


class TokenOffsetError(TokenError):
    """Raised when token character/byte offsets are invalid, negative, out of bounds, or inverted."""
    pass


class TokenReconstructionError(TokenError):
    """Raised when token surface form does not match the source text slice at the specified offsets."""
    pass


class TokenLanguageMismatchError(TokenError):
    """Raised when tokenization language conflicts with source text language."""
    pass


class InvalidTokenTypeError(TokenError):
    """Raised when an invalid or unclassified token type is specified."""
    pass


class TokenNormalizationFirewallError(TokenError):
    """Raised when normalization firewall rules are violated during tokenization."""
    pass


class TokenInvalidProvenanceError(TokenError):
    """Raised when a referenced provenance record does not exist or fails validation."""
    pass


class TokenInvalidVersionError(TokenError):
    """Raised when a referenced object version does not exist or fails validation."""
    pass


# =============================================================================
# MORPHOLOGY SUBSYSTEM EXCEPTIONS (Task 2.3)
# =============================================================================

class MorphologyError(BibleEngineDatabaseError):
    """Base exception for all Morphology subsystem errors."""
    pass


class MorphologyNotFoundError(MorphologyError):
    """Raised when a requested morphology observation or run does not exist."""
    pass


class DuplicateMorphologyError(MorphologyError):
    """Raised when registering a duplicate morphology annotation or conflicting parse index."""
    pass


class MorphologyImmutabilityError(MorphologyError):
    """Raised when an illegal modification or deletion of a morphology observation or run is attempted."""
    pass


class MorphologyTokenNotFoundError(MorphologyError):
    """Raised when a referenced token for morphology analysis does not exist."""
    pass


class MorphologyLanguageMismatchError(MorphologyError):
    """Raised when morphological features or analysis language conflict with source text/token language."""
    pass


class MorphologyFeatureValidationError(MorphologyError):
    """Raised when an invalid, cross-language, or contradictory morphological feature is supplied."""
    pass


class MorphologyConfidenceError(MorphologyError):
    """Raised when confidence scores are out of bounds or confidence is erroneously treated as evidence."""
    pass


class MorphologyNormalizationFirewallError(MorphologyError):
    """Raised when normalization firewall rules are violated during morphological analysis."""
    pass


class MorphologyInvalidProvenanceError(MorphologyError):
    """Raised when a referenced provenance record does not exist or fails validation."""
    pass


class MorphologyInvalidVersionError(MorphologyError):
    """Raised when a referenced object version does not exist or fails validation."""
    pass


class MorphologyOrphanError(MorphologyError):
    """Raised when attempting to record morphology without an authoritative token linkage."""
    pass


class LemmaNotFoundError(MorphologyError):
    """Raised when a referenced lemma does not exist in the lemma registry."""
    pass


class DuplicateLemmaError(MorphologyError):
    """Raised when attempting to register an identical lemma string in the same language."""
    pass


# =============================================================================
# SYNTAX SUBSYSTEM EXCEPTIONS (Task 2.4)
# =============================================================================

class SyntaxSubsystemError(BibleEngineDatabaseError):
    """Base exception for all Syntax subsystem errors."""
    pass


class SyntaxNotFoundError(SyntaxSubsystemError):
    """Raised when a requested syntax run, clause, constituent, or dependency relation is not found."""
    pass


class DuplicateSyntaxError(SyntaxSubsystemError):
    """Raised when registering duplicate syntax structures or conflicting parse index."""
    pass


class SyntaxImmutabilityError(SyntaxSubsystemError):
    """Raised when an illegal modification or deletion of a syntax run, clause, constituent, or dependency is attempted."""
    pass


class SyntaxTokenNotFoundError(SyntaxSubsystemError):
    """Raised when a referenced token for syntax analysis does not exist."""
    pass


class SyntaxClauseNotFoundError(SyntaxSubsystemError):
    """Raised when a referenced clause does not exist."""
    pass


class SyntaxConstituentNotFoundError(SyntaxSubsystemError):
    """Raised when a referenced syntactic constituent does not exist."""
    pass


class SyntaxCycleError(SyntaxSubsystemError):
    """Raised when an illegal directed cycle is detected in a syntax dependency graph."""
    pass


class SyntaxSpanValidationError(SyntaxSubsystemError):
    """Raised when constituent or clause token span boundaries are inverted or out of order."""
    pass


class SyntaxLanguageMismatchError(SyntaxSubsystemError):
    """Raised when syntactic structures or tags conflict with source text/token language."""
    pass


class SyntaxFeatureValidationError(SyntaxSubsystemError):
    """Raised when an invalid, illegal, or contradictory syntactic relation is supplied."""
    pass


class SyntaxConfidenceError(SyntaxSubsystemError):
    """Raised when confidence scores are out of bounds or confidence is erroneously substituted for evidence."""
    pass


class SyntaxInvalidProvenanceError(SyntaxSubsystemError):
    """Raised when a referenced provenance record does not exist or fails validation."""
    pass


class SyntaxInvalidVersionError(SyntaxSubsystemError):
    """Raised when a referenced object version does not exist or fails validation."""
    pass


class SyntaxOrphanError(SyntaxSubsystemError):
    """Raised when attempting to record syntax without an authoritative token or constituent linkage."""
    pass


class SyntaxSemanticsFirewallError(SyntaxSubsystemError):
    """Raised when an illegal attempt is made to automatically collapse syntactic structure into semantic roles."""
    pass


class SyntaxTheologyFirewallError(SyntaxSubsystemError):
    """Raised when an illegal attempt is made to generate theological or doctrinal claims from syntax."""
    pass


class SyntaxIdentityFirewallError(SyntaxSubsystemError):
    """Raised when an illegal attempt is made to automatically infer strict referential identity from syntax."""
    pass


class SyntaxMorphologyFirewallError(SyntaxSubsystemError):
    """Raised when syntax attempts to illegally overwrite or mutate morphology observations."""
    pass


# =============================================================================
# SEMANTICS SUBSYSTEM EXCEPTIONS (Task 2.5)
# =============================================================================

class SemanticSubsystemError(BibleEngineDatabaseError):
    """Base exception for all Semantics subsystem errors."""
    pass


class SemanticNotFoundError(SemanticSubsystemError):
    """Raised when a requested semantic entity, sense, lexeme, or run does not exist."""
    pass


class DuplicateSemanticError(SemanticSubsystemError):
    """Raised when attempting to insert a duplicate lexeme, sense, relation, or candidate."""
    pass


class SemanticImmutabilityError(SemanticSubsystemError):
    """Raised when attempting to update or delete immutable semantic records."""
    pass


class LexemeNotFoundError(SemanticSubsystemError):
    """Raised when a referenced lexeme does not exist."""
    pass


class SemanticSenseNotFoundError(SemanticSubsystemError):
    """Raised when a referenced semantic sense does not exist."""
    pass


class SemanticDomainNotFoundError(SemanticSubsystemError):
    """Raised when a referenced semantic domain does not exist."""
    pass


class SemanticTokenNotFoundError(SemanticSubsystemError):
    """Raised when contextual semantic analysis references a nonexistent token."""
    pass


class SemanticLanguageMismatchError(SemanticSubsystemError):
    """Raised when lexemes, senses, or contextual candidates conflict with source text language."""
    pass


class SemanticRelationError(SemanticSubsystemError):
    """Raised when an invalid semantic relation (e.g. self-relation) is attempted."""
    pass


class SemanticConfidenceError(SemanticSubsystemError):
    """Raised when confidence score or level is invalid or confidence is substituted for evidence."""
    pass


class SemanticInvalidProvenanceError(SemanticSubsystemError):
    """Raised when a referenced provenance record does not exist or fails validation."""
    pass


class SemanticInvalidVersionError(SemanticSubsystemError):
    """Raised when a referenced object version does not exist or fails validation."""
    pass


class SemanticOrphanError(SemanticSubsystemError):
    """Raised when contextual sense analysis has no token or source text linkage."""
    pass


class SemanticTranslationFirewallError(SemanticSubsystemError):
    """Raised when translation glosses or target-language idioms are substituted for source-language lexical senses."""
    pass


class SemanticMorphologyFirewallError(SemanticSubsystemError):
    """Raised when semantics attempts to modify or dictate morphological parses."""
    pass


class SemanticSyntaxFirewallError(SemanticSubsystemError):
    """Raised when semantics attempts to equate syntactic relations with semantic roles without justification."""
    pass


class SemanticTheologyFirewallError(SemanticSubsystemError):
    """Raised when an illegal attempt is made to generate theological or dogmatic claims from semantic analysis."""
    pass


class SemanticIdentityFirewallError(SemanticSubsystemError):
    """Raised when an illegal attempt is made to infer strict ontological or referential identity directly from semantic senses."""
    pass


# =============================================================================
# REFERENTIAL & ENTITY SUBSYSTEM (Task 2.6)
# =============================================================================

class ReferentialSubsystemError(BibleEngineDatabaseError):
    """Base class for referential and entity foundation subsystem violations."""
    pass


class ReferentialNotFoundError(ReferentialSubsystemError):
    """Raised when a referential run or relation cannot be located."""
    pass


class DuplicateReferentialError(ReferentialSubsystemError):
    """Raised when a referential artifact violates uniqueness constraints."""
    pass


class ReferentialImmutabilityError(ReferentialSubsystemError):
    """Raised when an attempt is made to mutate an immutable referential record."""
    pass


class EntityNotFoundError(ReferentialSubsystemError):
    """Raised when a referenced entity does not exist."""
    pass


class DuplicateEntityError(ReferentialSubsystemError):
    """Raised when an entity ID or standard name is already registered."""
    pass


class EntityMentionNotFoundError(ReferentialSubsystemError):
    """Raised when an entity mention cannot be located."""
    pass


class ReferentialRelationNotFoundError(ReferentialSubsystemError):
    """Raised when a referential relation cannot be located."""
    pass


class ReferentialTokenNotFoundError(ReferentialSubsystemError):
    """Raised when an entity mention anchors to a nonexistent token."""
    pass


class ReferentialLanguageMismatchError(ReferentialSubsystemError):
    """Raised when entity or mention language conflicts with the source text language."""
    pass


class ReferentialConfidenceError(ReferentialSubsystemError):
    """Raised when a referential confidence score or level is malformed or unsupported."""
    pass


class ReferentialInvalidProvenanceError(ReferentialSubsystemError):
    """Raised when referential provenance linkage is absent or invalid."""
    pass


class ReferentialInvalidVersionError(ReferentialSubsystemError):
    """Raised when referential version linkage is absent or invalid."""
    pass


class ReferentialOrphanError(ReferentialSubsystemError):
    """Raised when a referential record references a nonexistent parent artifact."""
    pass


class ReferentialEvidenceNotFoundError(ReferentialSubsystemError):
    """Raised when a relation cites an evidence_id absent from the evidence ledger."""
    pass


class ReferentialTranslationFirewallError(ReferentialSubsystemError):
    """Raised when translation-layer glosses or target-language idioms are substituted for referential analysis."""
    pass


class ReferentialMorphologyFirewallError(ReferentialSubsystemError):
    """Raised when the referential engine attempts to alter or dictate morphological parses."""
    pass


class ReferentialSyntaxFirewallError(ReferentialSubsystemError):
    """Raised when a referential relation cites a syntactic clause belonging to another text."""
    pass


class ReferentialTheologyFirewallError(ReferentialSubsystemError):
    """Raised when a referential relation or entity is used to assert theological or dogmatic claims."""
    pass


class ReferentialIdentityFirewallError(ReferentialSubsystemError):
    """Raised when associative symbolism is collapsed into ontological identity without explicit, traceable evidence and grammatical justification."""
    pass


# =============================================================================
# DISCOURSE & CONTEXT SUBSYSTEM (Task 2.7)
# =============================================================================

class DiscourseSubsystemError(BibleEngineDatabaseError):
    """Base class for discourse and context foundation subsystem violations."""
    pass


class DiscourseNotFoundError(DiscourseSubsystemError):
    """Raised when a discourse run or discourse artifact cannot be located."""
    pass


class DuplicateDiscourseError(DiscourseSubsystemError):
    """Raised when a discourse artifact violates a uniqueness constraint."""
    pass


class DiscourseImmutabilityError(DiscourseSubsystemError):
    """Raised when an attempt is made to mutate an immutable discourse record."""
    pass


class DiscourseConfidenceError(DiscourseSubsystemError):
    """Raised when a discourse confidence score or level is malformed or unsupported."""
    pass


class DiscourseInvalidProvenanceError(DiscourseSubsystemError):
    """Raised when discourse provenance linkage is absent or invalid."""
    pass


class DiscourseInvalidVersionError(DiscourseSubsystemError):
    """Raised when discourse version linkage is absent or invalid."""
    pass


class DiscourseOrphanError(DiscourseSubsystemError):
    """Raised when a discourse record references a nonexistent parent artifact."""
    pass


class DiscourseTokenNotFoundError(DiscourseSubsystemError):
    """Raised when a discourse anchor cites a token absent from the source text."""
    pass


class DiscourseSpanValidationError(DiscourseSubsystemError):
    """Raised when a discourse unit or segment span is reversed or otherwise invalid."""
    pass


class DiscourseRelationAnchorError(DiscourseSubsystemError):
    """Raised when a discourse relation declares an unsupported unit/segment anchor kind."""
    pass


class DiscourseRelationNotFoundError(DiscourseSubsystemError):
    """Raised when a discourse relation cannot be located."""
    pass


class DiscourseAmbiguityFirewallError(DiscourseSubsystemError):
    """Raised when unresolved ambiguity is collapsed, or resolution is claimed without evidence."""
    pass


class DiscourseContextFirewallError(DiscourseSubsystemError):
    """Raised when a context-layer observation is promoted into evidence. CONTEXT IS NOT AUTOMATICALLY EVIDENCE."""
    pass


class DiscourseLanguageMismatchError(DiscourseSubsystemError):
    """Raised when discourse language conflicts with the source text language."""
    pass


class DiscourseNoMorphologyAloneFirewallError(DiscourseSubsystemError):
    """Raised when a discourse relation is derived from morphology alone without a cited connector token."""
    pass


class DiscourseMorphologyFirewallError(DiscourseNoMorphologyAloneFirewallError):
    """Raised when a discourse observation is asserted on a morphological basis alone."""
    pass


class DiscourseTranslationFirewallError(DiscourseSubsystemError):
    """Raised when discourse meaning is derived from a modern translation rather than the source text."""
    pass


class DiscourseSyntaxFirewallError(DiscourseSubsystemError):
    """Raised when a discourse anchor cites a syntactic artifact belonging to another source text."""
    pass


class DiscourseTheologyFirewallError(DiscourseSubsystemError):
    """Raised when a discourse observation is used to assert a theological or doctrinal claim."""
    pass


class DiscourseIdentityFirewallError(DiscourseSubsystemError):
    """Raised when a discourse participant or antecedent candidate asserts ontological or strict identity."""
    pass


class DiscourseFrequencyFirewallError(DiscourseSubsystemError):
    """Raised when discourse meaning or truth is derived from contextual frequency or statistical majority."""
    pass


# =============================================================================
# EVIDENCE & CLAIM SUBSYSTEM (Task 2.8)
# =============================================================================

class EvidenceClaimSubsystemError(BibleEngineDatabaseError):
    """Base class for evidence and claim foundation subsystem violations."""
    pass


class EvidenceNotFoundError(EvidenceClaimSubsystemError):
    """Raised when an evidence item or evidence run cannot be located."""
    pass


class ClaimNotFoundError(EvidenceClaimSubsystemError):
    """Raised when a claim record cannot be located."""
    pass


class ClaimEvidenceLinkNotFoundError(EvidenceClaimSubsystemError):
    """Raised when a claim-evidence link cannot be located."""
    pass


class DuplicateEvidenceError(EvidenceClaimSubsystemError):
    """Raised when an evidence ID violates a uniqueness constraint."""
    pass


class DuplicateClaimError(EvidenceClaimSubsystemError):
    """Raised when a claim ID violates a uniqueness constraint."""
    pass


class DuplicateClaimEvidenceLinkError(EvidenceClaimSubsystemError):
    """Raised when a claim-evidence link violates uniqueness constraints."""
    pass


class EvidenceClaimImmutabilityError(EvidenceClaimSubsystemError):
    """Raised when an attempt is made to mutate an immutable evidence or claim record."""
    pass


class InvalidEvidenceClassError(EvidenceClaimSubsystemError):
    """Raised when an evidence record specifies an invalid or unapproved evidence class."""
    pass


class InvalidClaimTierError(EvidenceClaimSubsystemError):
    """Raised when a claim record specifies an invalid or unapproved claim tier."""
    pass


class InvalidEpistemicTypeError(EvidenceClaimSubsystemError):
    """Raised when an evidence or claim record specifies an invalid epistemic type."""
    pass


class InvalidEvidenceRelationshipError(EvidenceClaimSubsystemError):
    """Raised when an evidence-to-claim link specifies an invalid relationship."""
    pass


class EvidenceConfidenceError(EvidenceClaimSubsystemError):
    """Raised when a confidence score or level is malformed, out of bounds, or substituted for evidence."""
    pass


class EvidenceClaimInvalidProvenanceError(EvidenceClaimSubsystemError):
    """Raised when evidence or claim provenance linkage is absent or invalid."""
    pass


class EvidenceClaimInvalidVersionError(EvidenceClaimSubsystemError):
    """Raised when evidence or claim version linkage is absent or invalid."""
    pass


class EvidenceClaimOrphanError(EvidenceClaimSubsystemError):
    """Raised when an evidence or claim record references a nonexistent parent artifact."""
    pass


class TranslationToE0FirewallError(EvidenceClaimSubsystemError):
    """Raised when translation output is illicitly classified as E0 DIRECT_TEXT."""
    pass


class AIPrimaryEvidenceFirewallError(EvidenceClaimSubsystemError):
    """Raised when AI model output is illicitly asserted as primary evidence (E0-E12)."""
    pass


class ConfidenceUpgradeFirewallError(EvidenceClaimSubsystemError):
    """Raised when model confidence is used to upgrade E-level, upgrade claim tier, or establish theology/identity/fact."""
    pass


class MorphologyTheologyFirewallError(EvidenceClaimSubsystemError):
    """Raised when morphology alone is used to directly create a T3 or T4 interpretive/theological claim."""
    pass


class SyntaxTheologyFirewallError(SyntaxSubsystemError, EvidenceClaimSubsystemError):
    """Raised when syntax alone is used to directly create a T3 or T4 interpretive/theological claim."""
    pass


class SemanticTheologyFirewallError(SemanticSubsystemError, EvidenceClaimSubsystemError):
    """Raised when semantic sense alone is used to directly create a T3 or T4 interpretive/theological claim."""
    pass


class DiscourseTheologyFirewallError(DiscourseSubsystemError, EvidenceClaimSubsystemError):
    """Raised when discourse relation alone is used to directly create a T3 or T4 interpretive/theological claim."""
    pass


class IdentityFirewallError(EvidenceClaimSubsystemError):
    """Raised when entity association is illicitly promoted to STRICT_IDENTITY without explicit justification and evidence."""
    pass


class UnsupportedClaimError(EvidenceClaimSubsystemError):
    """Raised when a claim has zero supporting evidence or is unsupported by primary evidence."""
    pass


class MissingProvenanceError(EvidenceClaimSubsystemError):
    """Raised when evidence or claim records lack mandatory provenance metadata."""
    pass


class UnresolvedContradictionFirewallError(EvidenceClaimSubsystemError):
    """Raised when a claim with unresolved contradiction is marked established or verified fact."""
    pass


# =============================================================================
# EXEGESIS FOUNDATION SUBSYSTEM (Task 2.9)
# =============================================================================

class ExegesisSubsystemError(BibleEngineDatabaseError):
    """Base exception for all exegesis foundation subsystem violations."""
    pass


class ExegesisRunNotFoundError(ExegesisSubsystemError):
    """Raised when an exegesis run record cannot be located."""
    pass


class ObservationNotFoundError(ExegesisSubsystemError):
    """Raised when an exegesis observation cannot be located."""
    pass


class HypothesisNotFoundError(ExegesisSubsystemError):
    """Raised when an interpretive hypothesis cannot be located."""
    pass


class CompetingInterpretationNotFoundError(ExegesisSubsystemError):
    """Raised when a competing interpretation record cannot be located."""
    pass


class EvidenceAuditNotFoundError(ExegesisSubsystemError):
    """Raised when an evidence audit record cannot be located."""
    pass


class CalibratedConclusionNotFoundError(ExegesisSubsystemError):
    """Raised when a calibrated conclusion record cannot be located."""
    pass


class UnresolvedIssueNotFoundError(ExegesisSubsystemError):
    """Raised when an unresolved issue record cannot be located."""
    pass


class DuplicateExegesisError(ExegesisSubsystemError):
    """Raised when an exegesis artifact violates uniqueness constraints."""
    pass


class ExegesisImmutabilityError(ExegesisSubsystemError):
    """Raised when an attempt is made to mutate an immutable exegesis record."""
    pass


class ExegesisInvalidProvenanceError(ExegesisSubsystemError):
    """Raised when exegesis provenance linkage is absent or invalid."""
    pass


class ExegesisInvalidVersionError(ExegesisSubsystemError):
    """Raised when exegesis version linkage is absent or invalid."""
    pass


class ExegesisOrphanError(ExegesisSubsystemError):
    """Raised when an exegesis record references a nonexistent parent artifact."""
    pass


class PericopePrimaryUnitFirewallError(ExegesisSubsystemError):
    """Raised when pericope is bypassed or verse is substituted for pericope as primary unit."""
    pass


class UnsupportedConclusionFirewallError(ExegesisSubsystemError):
    """Raised when a conclusion lacks supporting evidence or is unsupported by primary evidence."""
    pass


class InterpretationWithoutEvidenceFirewallError(ExegesisSubsystemError):
    """Raised when an interpretation or hypothesis is asserted without supporting evidence."""
    pass


class SuppressionOfCompetingInterpretationFirewallError(ExegesisSubsystemError):
    """Raised when competing interpretations or alternative readings are suppressed."""
    pass


class SuppressionOfCounterEvidenceFirewallError(ExegesisSubsystemError):
    """Raised when counter-evidence is silently omitted or suppressed."""
    pass


class SilentAmbiguityResolutionFirewallError(ExegesisSubsystemError):
    """Raised when textual, syntactic, semantic, or referential ambiguity is silently resolved."""
    pass


class ModelMajorityTruthFirewallError(ExegesisSubsystemError):
    """Raised when model agreement or majority consensus is asserted as truth without evidence."""
    pass


class ConfidenceAsEvidenceFirewallError(ExegesisSubsystemError):
    """Raised when model confidence is substituted for evidence or used to upgrade epistemic certainty."""
    pass


class TranslationAsSourceFirewallError(ExegesisSubsystemError):
    """Raised when translation output is illicitly treated as source evidence."""
    pass


class StrictIdentityEvidenceFirewallError(ExegesisSubsystemError):
    """Raised when entity association is promoted to STRICT_IDENTITY without independent evidence."""
    pass


MorphologySubsystemError = MorphologyError


class ExegesisMorphologyTheologyFirewallError(MorphologyError, ExegesisSubsystemError):
    """Raised when morphology alone is used to directly establish theological conclusions."""
    pass


class ExegesisSyntaxTheologyFirewallError(SyntaxSubsystemError, ExegesisSubsystemError):
    """Raised when syntax alone is used to directly establish theological conclusions."""
    pass


class ExegesisSemanticTheologyFirewallError(SemanticSubsystemError, ExegesisSubsystemError):
    """Raised when semantic sense alone is used to directly establish theological conclusions."""
    pass


class ExegesisDiscourseTheologyFirewallError(DiscourseSubsystemError, ExegesisSubsystemError):
    """Raised when discourse relation alone is used to directly establish theological conclusions."""
    pass


class ExegesisEntityIdentityFirewallError(ReferentialSubsystemError, ExegesisSubsystemError):
    """Raised when entity association alone is used to directly establish theological identity."""
    pass


# =============================================================================
# TEXTUAL CRITICISM SUBSYSTEM ERRORS (Task 3.1)
# =============================================================================

class TextualCriticismSubsystemError(BibleEngineDatabaseError):
    """Base exception for all textual criticism subsystem and apparatus errors."""
    pass


class VariantUnitNotFoundError(TextualCriticismSubsystemError):
    """Raised when a requested variant unit cannot be found."""
    pass


class VariantReadingNotFoundError(TextualCriticismSubsystemError):
    """Raised when a requested variant reading cannot be found."""
    pass


class WitnessNotFoundError(TextualCriticismSubsystemError):
    """Raised when a cited manuscript or version witness is unknown or unregistered."""
    pass


class TranslationAsWitnessFirewallError(TextualCriticismSubsystemError):
    """Raised when a secondary translation is illicitly cited as direct manuscript evidence."""
    pass


class ModernTranslationAsAttestationFirewallError(TextualCriticismSubsystemError):
    """Raised when a modern translation is illicitly submitted as ancient witness attestation."""
    pass


class AITextualEvidenceFirewallError(TextualCriticismSubsystemError):
    """Raised when AI-generated text is illicitly submitted as primary manuscript evidence."""
    pass


class ConfidenceTextualUpgradeFirewallError(TextualCriticismSubsystemError):
    """Raised when statistical/model confidence is illicitly used to upgrade textual evidence class."""
    pass


class AutomaticPriorityCriterionFirewallError(TextualCriticismSubsystemError):
    """Raised when an isolated textual-critical criterion is asserted as an automatic selection formula."""
    pass


class WitnessAgePriorityFirewallError(AutomaticPriorityCriterionFirewallError):
    """Raised when witness age alone is asserted to determine textual priority."""
    pass


class WitnessCountPriorityFirewallError(AutomaticPriorityCriterionFirewallError):
    """Raised when number of witnesses alone is asserted to determine textual priority."""
    pass


class TextualFamilyPriorityFirewallError(AutomaticPriorityCriterionFirewallError):
    """Raised when textual family alone is asserted to determine textual priority."""
    pass


class LectioDifficiliorPriorityFirewallError(AutomaticPriorityCriterionFirewallError):
    """Raised when lectio difficilior is asserted as an automatic truth formula without contextual balance."""
    pass


class LectioBreviorPriorityFirewallError(AutomaticPriorityCriterionFirewallError):
    """Raised when lectio brevior is asserted as an automatic truth formula without contextual balance."""
    pass


class SuppressionOfAlternativeReadingsFirewallError(TextualCriticismSubsystemError):
    """Raised when alternative or competing textual readings are suppressed or omitted."""
    pass


class PreferredAsCertainOriginalFirewallError(TextualCriticismSubsystemError):
    """Raised when a preferred reading is dogmatically asserted as certain original without epistemic warrant."""
    pass


class TextualCriticismImmutabilityError(TextualCriticismSubsystemError):
    """Raised when an immutable textual criticism run or decision record is modified."""
    pass


class TextualCriticismInvalidProvenanceError(TextualCriticismSubsystemError):
    """Raised when textual criticism provenance metadata is missing, broken, or hash-mismatched."""
    pass


class TextualCriticismInvalidVersionError(TextualCriticismSubsystemError):
    """Raised when textual criticism versioning constraints or relations are violated."""
    pass


class TextualCriticismConcurrencyError(TextualCriticismSubsystemError):
    """Raised when concurrent operations collide on a textual criticism run or variant unit."""
    pass


# =============================================================================
# HISTORICAL-LINGUISTIC & DIACHRONIC SUBSYSTEM ERRORS (Task 3.2)
# =============================================================================

class HistoricalLinguisticSubsystemError(BibleEngineDatabaseError):
    """Base exception for all historical-linguistic and diachronic engine errors."""
    pass


class LexicalSimilarityNotBorrowingFirewallError(HistoricalLinguisticSubsystemError):
    """Raised when lexical similarity is illicitly asserted as borrowing without evidence."""
    pass


class LexicalSimilarityNotCausationFirewallError(HistoricalLinguisticSubsystemError):
    """Raised when lexical similarity is illicitly asserted as historical causation."""
    pass


class ChronologicalProximityNotCausationFirewallError(HistoricalLinguisticSubsystemError):
    """Raised when chronological proximity is illicitly asserted as causal influence."""
    pass


class SharedRootNotSameSourceFirewallError(HistoricalLinguisticSubsystemError):
    """Raised when shared root is illicitly asserted to demonstrate identical historical source."""
    pass


class LaterFormEarlierReadingFirewallError(HistoricalLinguisticSubsystemError):
    """Raised when a later linguistic form is illicitly treated as an automatic earlier reading."""
    pass


class ModernTerminologyAuthorialIntentFirewallError(HistoricalLinguisticSubsystemError):
    """Raised when modern linguistic/theological terminology is illicitly retrofitted to ancient authorial intent."""
    pass


class AIHistoricalEvidenceFirewallError(HistoricalLinguisticSubsystemError):
    """Raised when AI-generated etymology or historical parallel is illicitly submitted as primary evidence."""
    pass


class TranslationHistoricalSourceFirewallError(HistoricalLinguisticSubsystemError):
    """Raised when a translation is illicitly submitted as historical-linguistic source evidence."""
    pass


class ParallelNotIntertextualFirewallError(HistoricalLinguisticSubsystemError):
    """Raised when an epigraphic/papyrological parallel is automatically upgraded to E10 intertextuality."""
    pass


class BorrowingEvidenceRequiredFirewallError(HistoricalLinguisticSubsystemError):
    """Raised when loanword borrowing is registered without supporting evidence."""
    pass


class HistoricalLinguisticImmutabilityError(HistoricalLinguisticSubsystemError):
    """Raised when an immutable historical-linguistic record is updated or deleted."""
    pass


class HistoricalLinguisticInvalidProvenanceError(HistoricalLinguisticSubsystemError):
    """Raised when historical-linguistic provenance metadata is missing, broken, or hash-mismatched."""
    pass


class HistoricalLinguisticInvalidVersionError(HistoricalLinguisticSubsystemError):
    """Raised when historical-linguistic versioning constraints or relations are violated."""
    pass


class HistoricalLinguisticConcurrencyError(HistoricalLinguisticSubsystemError):
    """Raised when concurrent operations collide on a historical-linguistic run or entity."""
    pass


class StratumNotFoundError(HistoricalLinguisticSubsystemError):
    """Raised when a referenced diachronic stratum is not found."""
    pass


class HistoricalObservationNotFoundError(HistoricalLinguisticSubsystemError):
    """Raised when a referenced historical-linguistic observation is not found."""
    pass


# =============================================================================
# INTERTEXTUAL SUBSYSTEM ERRORS (Task 3.3 - E10)
# =============================================================================

class IntertextualSubsystemError(BibleEngineDatabaseError):
    """Base exception for all intertextual analysis subsystem errors."""
    pass


class LexicalSimilarityNotIntertextualityFirewallError(IntertextualSubsystemError):
    """Raised when lexical similarity or shared vocabulary is illicitly asserted as intertextual dependence."""
    pass


class ThematicSimilarityNotIntertextualityFirewallError(IntertextualSubsystemError):
    """Raised when thematic similarity or shared motif is illicitly asserted as direct intertextual dependence."""
    pass


class ChronologyNotDependenceFirewallError(IntertextualSubsystemError):
    """Raised when chronological proximity or precedence is illicitly asserted as textual dependence."""
    pass


class SameWordingNotAutomaticQuotationFirewallError(IntertextualSubsystemError):
    """Raised when same wording or lexical overlap is asserted as direct quotation without supporting evidence."""
    pass


class SharedTraditionNotDirectQuotationFirewallError(IntertextualSubsystemError):
    """Raised when traditional parallel or common motif is illicitly asserted as direct quotation."""
    pass


class E9ParallelNotE10IntertextFirewallError(IntertextualSubsystemError):
    """Raised when an E9 historical-linguistic parallel is automatically upgraded to E10 intertextual evidence."""
    pass


class TranslationNotOriginalSourceFirewallError(IntertextualSubsystemError):
    """Raised when a translation is treated as original source text or translation mediation is suppressed."""
    pass


class ReceptionSourceNotAuthorialSourceFirewallError(IntertextualSubsystemError):
    """Raised when a later commentary/reception source is illicitly asserted as authorial source of an earlier text."""
    pass


class EntityIdentityNotTextualDependenceFirewallError(IntertextualSubsystemError):
    """Raised when shared entity, person, title, or divine name is illicitly asserted as textual dependence."""
    pass


class UnknownDirectionPreservationFirewallError(IntertextualSubsystemError):
    """Raised when unknown direction is illicitly forced into source->target or target->source without evidence."""
    pass


class AIIntertextualEvidenceFirewallError(IntertextualSubsystemError):
    """Raised when AI-generated proposal is illicitly submitted as primary E10 intertextual evidence."""
    pass


class ModernCommentaryNotAncientSourceFirewallError(IntertextualSubsystemError):
    """Raised when modern commentary is illicitly submitted as ancient intertextual source."""
    pass


class ConfidenceNotEvidenceUpgradeFirewallError(IntertextualSubsystemError):
    """Raised when confidence score or level is illicitly used to manufacture or upgrade evidence tier."""
    pass


class RetrievalRankingNotTruthFirewallError(IntertextualSubsystemError):
    """Raised when retrieval score or ranking is illicitly treated as truth or used to force a single winner."""
    pass


class CounterEvidencePreservationFirewallError(IntertextualSubsystemError):
    """Raised when counter-evidence is suppressed or discarded."""
    pass


class QuotationEvidenceRequiredFirewallError(IntertextualSubsystemError):
    """Raised when direct quotation is asserted without explicit quotation formula or high-confidence evidence."""
    pass


class ChronologyOnlyRelationFirewallError(IntertextualSubsystemError):
    """Raised when an intertextual relationship is established solely on chronological grounds."""
    pass


class IntertextualNotTheologicalClaimFirewallError(IntertextualSubsystemError):
    """Raised when an intertextual claim or observation is illicitly escalated directly into a T4 theological claim."""
    pass


class UnverifiedIdentifierPreservationFirewallError(IntertextualSubsystemError):
    """Raised when an unverified external identifier is illicitly marked or treated as verified."""
    pass


class IntertextualImmutabilityError(IntertextualSubsystemError):
    """Raised when an immutable intertextual record is updated or deleted."""
    pass


class IntertextualInvalidProvenanceError(IntertextualSubsystemError):
    """Raised when intertextual provenance metadata is missing, broken, or hash-mismatched."""
    pass


class IntertextualInvalidVersionError(IntertextualSubsystemError):
    """Raised when intertextual versioning constraints or relations are violated."""
    pass


class IntertextualConcurrencyError(IntertextualSubsystemError):
    """Raised when concurrent operations collide on an intertextual run or entity."""
    pass


class IntertextualSourceNotFoundError(IntertextualSubsystemError):
    """Raised when a referenced intertextual source metadata record is not found."""
    pass


class IntertextualRelationshipNotFoundError(IntertextualSubsystemError):
    """Raised when a referenced intertextual relationship is not found."""
    pass


# =============================================================================
# RECEPTION HISTORY ERRORS (Task 3.4)
# Evidence Classes: E11_EARLY_RECEPTION, E12_LATER_INTERPRETATION
# =============================================================================

class ReceptionHistorySubsystemError(BibleEngineDatabaseError):
    """Base exception for all reception history engine errors."""
    pass


class ReceptionActorNotFoundError(ReceptionHistorySubsystemError):
    """Raised when a referenced reception actor is not found."""
    pass


class ReceptionSourceNotFoundError(ReceptionHistorySubsystemError):
    """Raised when a referenced reception source is not found."""
    pass


class ReceptionRecordNotFoundError(ReceptionHistorySubsystemError):
    """Raised when a referenced reception record is not found."""
    pass


class ReceptionClaimNotFoundError(ReceptionHistorySubsystemError):
    """Raised when a referenced reception claim is not found."""
    pass


class ReceptionRelationNotFoundError(ReceptionHistorySubsystemError):
    """Raised when a referenced reception relation is not found."""
    pass


class ReceptionAuthorialIntentFirewallError(ReceptionHistorySubsystemError):
    """Raised when later reception or interpretation is illicitly equated to original authorial intent."""
    pass


class ReceptionTheologicalTruthFirewallError(ReceptionHistorySubsystemError):
    """Raised when reception history is illicitly equated to absolute theological truth or T4 dogma."""
    pass


class ReceptionEarlyNotApostolicFirewallError(ReceptionHistorySubsystemError):
    """Raised when early or patristic reception is automatically equated to apostolic/authorial meaning."""
    pass


class ReceptionRabbinicNotSecondTempleFirewallError(ReceptionHistorySubsystemError):
    """Raised when rabbinic interpretation is automatically equated to Second Temple intent."""
    pass


class ReceptionMedievalNotBiblicalFirewallError(ReceptionHistorySubsystemError):
    """Raised when medieval interpretation is automatically equated to ancient biblical meaning."""
    pass


class ReceptionScholarlyNotTextualFirewallError(ReceptionHistorySubsystemError):
    """Raised when modern scholarly consensus is treated as primary textual evidence."""
    pass


class ReceptionDenominationalNotAuthorialFirewallError(ReceptionHistorySubsystemError):
    """Raised when denominational doctrine is treated as ancient authorial intent."""
    pass


class ReceptionChronologyNotInfluenceFirewallError(ReceptionHistorySubsystemError):
    """Raised when temporal proximity alone is asserted as causal influence or dependence."""
    pass


class ReceptionCitationNotInterpretationFirewallError(ReceptionHistorySubsystemError):
    """Raised when mere quotation/citation is treated as full interpretive consensus or agreement."""
    pass


class ReceptionAllusionNotQuotationFirewallError(ReceptionHistorySubsystemError):
    """Raised when an allusion is illicitly classified as direct quotation without textual quotation formula."""
    pass


class ReceptionTranslationNotOriginalFirewallError(ReceptionHistorySubsystemError):
    """Raised when translation mediation is ignored or translation text is asserted as original source."""
    pass


class ReceptionLexicalNotReceptionFirewallError(ReceptionHistorySubsystemError):
    """Raised when lexical similarity alone is asserted as reception history connection."""
    pass


class ReceptionThematicNotReceptionFirewallError(ReceptionHistorySubsystemError):
    """Raised when thematic parallel alone is asserted as reception history connection."""
    pass


class ReceptionDoctrinalNotTextualReadingFirewallError(ReceptionHistorySubsystemError):
    """Raised when doctrinal formulation is treated as an explicit textual reading of the passage."""
    pass


class ReceptionSourceNotAuthorialSourceFirewallError(ReceptionHistorySubsystemError):
    """Raised when later reception source is asserted as authorial source of the ancient text."""
    pass


class ReceptionNotCanonicalAuthorityFirewallError(ReceptionHistorySubsystemError):
    """Raised when reception history is illicitly endowed with canonical authority."""
    pass


class ReceptionMajorityNotFactFirewallError(ReceptionHistorySubsystemError):
    """Raised when majority or consensus reception is asserted as verified textual fact."""
    pass


class ReceptionAISummaryNotPrimarySourceFirewallError(ReceptionHistorySubsystemError):
    """Raised when AI-generated summary is submitted as primary E11/E12 reception evidence."""
    pass


class ReceptionModernCommentaryNotWitnessFirewallError(ReceptionHistorySubsystemError):
    """Raised when modern commentary is submitted as ancient historical witness."""
    pass


class ReceptionUnverifiedIdentifierFirewallError(ReceptionHistorySubsystemError):
    """Raised when an unverified external identifier is illicitly treated as verified."""
    pass


class ReceptionConfidenceNotUpgradeFirewallError(ReceptionHistorySubsystemError):
    """Raised when confidence score is used to manufacture or upgrade evidence class or tier."""
    pass


class ReceptionTemporalDirectionFirewallError(ReceptionHistorySubsystemError):
    """Raised when temporal direction is reversed or asserted without chronological verification."""
    pass


class ReceptionCounterEvidencePreservationFirewallError(ReceptionHistorySubsystemError):
    """Raised when counter-evidence or competing interpretations are suppressed or omitted."""
    pass


class ReceptionImmutabilityError(ReceptionHistorySubsystemError):
    """Raised when an immutable reception record is updated or deleted."""
    pass


class ReceptionInvalidProvenanceError(ReceptionHistorySubsystemError):
    """Raised when reception provenance metadata is missing, broken, or hash-mismatched."""
    pass


class ReceptionInvalidVersionError(ReceptionHistorySubsystemError):
    """Raised when reception versioning constraints or relations are violated."""
    pass


class ReceptionConcurrencyError(ReceptionHistorySubsystemError):
    """Raised when concurrent operations collide on a reception run or entity."""
    pass


class ReceptionValidationError(ReceptionHistorySubsystemError):
    """Raised when a reception history definition or relation fails structural validation."""
    pass


# =============================================================================
# TASK 3.5: EVIDENCE ADJUDICATION SUBSYSTEM ERRORS (E0-E12 Adjudication & Fallacies)
# =============================================================================

class EvidenceAdjudicationSubsystemError(BibleEngineDatabaseError):
    """Base error for all Evidence Adjudication subsystem failures."""
    pass



class FallacyDetectedError(EvidenceAdjudicationSubsystemError):
    """Base error raised when a hermeneutical or dialectical fallacy is detected."""
    pass


class IllegitimateTotalityTransferError(FallacyDetectedError):
    """Raised when all potential meanings of a lexeme are illicitly transferred into a single passage."""
    pass


class RootFallacyError(FallacyDetectedError):
    """Raised when an etymological root is asserted as the determinative meaning in context."""
    pass


class AnachronisticSemanticInjectionError(FallacyDetectedError):
    """Raised when later theological development or semantics are injected back into ancient text."""
    pass


class UnwarrantedGeneralizationError(FallacyDetectedError):
    """Raised when a specific contextual finding is illegitimately generalized across all contexts."""
    pass


class SuppressedCounterEvidenceError(EvidenceAdjudicationSubsystemError):
    """Raised when relevant counter-evidence is suppressed, ignored, or omitted in adjudication."""
    pass


class MajorityVoteEpistemologyError(EvidenceAdjudicationSubsystemError):
    """Raised when majority vote or source popularity is illicitly asserted as truth."""
    pass


class ConsensusAsTruthError(EvidenceAdjudicationSubsystemError):
    """Raised when scholarly or ecclesial consensus is illicitly equated to textual truth."""
    pass


class ConfidenceEscalationError(EvidenceAdjudicationSubsystemError):
    """Raised when confidence score escalates beyond the weakest critical evidence dependency."""
    pass


class UnresolvedConflictSuppressionError(EvidenceAdjudicationSubsystemError):
    """Raised when an unresolved dialectical conflict is suppressed or prematurely decided."""
    pass


class AdjudicationNotFoundError(EvidenceAdjudicationSubsystemError):
    """Raised when an adjudication run, hypothesis, conflict, or verdict cannot be found."""
    pass


class AdjudicationValidationError(EvidenceAdjudicationSubsystemError):
    """Raised when an adjudication definition fails structural or semantic validation."""
    pass


class AdjudicationImmutabilityError(EvidenceAdjudicationSubsystemError):
    """Raised when an immutable adjudication record is illicitly modified or deleted."""
    pass


class AdjudicationInvalidProvenanceError(EvidenceAdjudicationSubsystemError):
    """Raised when adjudication provenance metadata is missing, broken, or hash-mismatched."""
    pass


class AdjudicationInvalidVersionError(EvidenceAdjudicationSubsystemError):
    """Raised when adjudication versioning constraints or relations are violated."""
    pass


class AdjudicationConcurrencyError(EvidenceAdjudicationSubsystemError):
    """Raised when concurrent operations collide on an adjudication run or entity."""
    pass


# =============================================================================
# TASK 3.6: CROSS-PERICOPE EVIDENCE KNOWLEDGE GRAPH ERRORS
# =============================================================================

class GraphSubsystemError(BibleEngineDatabaseError):
    """Base error for all Knowledge Graph subsystem failures."""
    pass


class GraphCycleDetectedError(GraphSubsystemError):
    """Raised when an edge creation would introduce a cycle in dependency paths (violating DAG)."""
    pass


class GraphValidationError(GraphSubsystemError):
    """Raised when a graph node, edge, or configuration fails validation."""
    pass


class GraphNodeNotFoundError(GraphSubsystemError):
    """Raised when a specified graph node does not exist."""
    pass


class GraphEdgeNotFoundError(GraphSubsystemError):
    """Raised when a specified graph edge does not exist."""
    pass


class GraphConfidenceViolationError(GraphSubsystemError):
    """Raised when path confidence exceeds the weakest critical edge confidence."""
    pass


class GraphEvidenceTierViolationError(GraphSubsystemError):
    """Raised when an edge or node attempts to illicitly upgrade evidence class or claim tier."""
    pass


class GraphIdentityFirewallError(GraphSubsystemError):
    """Raised when EQUATED_WITH edge is asserted without explicit justification or provenance."""
    pass


class GraphReceptionAuthorialFirewallError(GraphSubsystemError):
    """Raised when E11/E12 reception is illicitly converted into E0-E5 authorial intent."""
    pass


class GraphCounterEvidenceSuppressionError(GraphSubsystemError):
    """Raised when contrary or competing edges are omitted or filtered out."""
    pass


class GraphImmutabilityError(GraphSubsystemError):
    """Raised when an immutable graph record is illicitly modified or deleted."""
    pass


class GraphInvalidProvenanceError(GraphSubsystemError):
    """Raised when graph provenance metadata is missing, broken, or hash-mismatched."""
    pass


class GraphInvalidVersionError(GraphSubsystemError):
    """Raised when graph versioning constraints or relations are violated."""
    pass


class GraphConcurrencyError(GraphSubsystemError):
    """Raised when concurrent operations collide on a graph run, node, or edge."""
    pass


# =============================================================================
# TASK 3.7: HIERARCHICAL SYNTHESIS SUBSYSTEM ERRORS
# =============================================================================

class SynthesisSubsystemError(BibleEngineDatabaseError):
    """Base error for all Hierarchical Synthesis subsystem failures."""
    pass


class SynthesisScopeJumpError(SynthesisSubsystemError):
    """Raised when synthesis jumps scope levels improperly or skips hierarchical progression."""
    pass


class SynthesisReverseScopeError(SynthesisSubsystemError):
    """Raised when higher scope is used as constituent/proof for lower scope (violating directionality)."""
    pass


class SynthesisCircularDependencyError(SynthesisSubsystemError):
    """Raised when a synthesis run attempts to feed itself or introduces circular dependencies."""
    pass


class SynthesisConfidenceInflationError(SynthesisSubsystemError):
    """Raised when synthesis confidence exceeds the weakest critical constituent dependency."""
    pass


class SynthesisHarmonizationError(SynthesisSubsystemError):
    """Raised when divergent authors or conflicting evidence are illicitly harmonized without tension."""
    pass


class SynthesisAuthorialDistinctiveViolationError(SynthesisSubsystemError):
    """Raised when distinct authorial theology/tradition is collapsed without explicit dependency."""
    pass


class SynthesisReceptionAuthorialFirewallError(SynthesisSubsystemError):
    """Raised when E11/E12 reception history is converted into authorial corpus theology."""
    pass


class SynthesisEvidenceTierViolationError(SynthesisSubsystemError):
    """Raised when synthesis attempts to escalate evidence class or claim tier."""
    pass


class SynthesisMissingConstituentError(SynthesisSubsystemError):
    """Raised when synthesis claim lacks required constituent evidence or adjudication linkages."""
    pass


class SynthesisNotFoundError(SynthesisSubsystemError):
    """Raised when a referenced synthesis run, claim, tension, or constituent is not found."""
    pass


class SynthesisValidationError(SynthesisSubsystemError):
    """Raised when synthesis inputs fail structural, schema, or invariant validation."""
    pass


class SynthesisImmutabilityError(SynthesisSubsystemError):
    """Raised when an immutable synthesis record is illicitly modified or deleted."""
    pass


class SynthesisInvalidProvenanceError(SynthesisSubsystemError):
    """Raised when synthesis provenance metadata is missing, broken, or hash-mismatched."""
    pass


class SynthesisInvalidVersionError(SynthesisSubsystemError):
    """Raised when synthesis versioning constraints or relations are violated."""
    pass


class SynthesisConcurrencyError(SynthesisSubsystemError):
    """Raised when concurrent synthesis operations collide or fail serialization."""
    pass


# =============================================================================
# TASK 3.8: THEOLOGICAL COMPARISON & ILZAM AL-KHASM SUBSYSTEM ERRORS
# =============================================================================

class TheologicalComparisonSubsystemError(BibleEngineDatabaseError):
    """Base error for all Theological Comparison and Ilzam al-Khasm subsystem failures."""
    pass


class TheologyFirewallError(TheologicalComparisonSubsystemError):
    """Base error for violations of the directional boundary between T4 dogma and T0-T3 evidence."""
    pass


class DogmaticEvidenceContaminationError(TheologyFirewallError):
    """Raised when a T4 dogmatic claim attempts to modify, rewrite, upgrade, or define T0-T3 evidence."""
    pass


class CircularProofStructureError(TheologicalComparisonSubsystemError):
    """Raised when a theological proposition serves as evidence for its own underlying premises (petitio principii)."""
    pass


class IlzamCritiqueDetectedError(TheologicalComparisonSubsystemError):
    """Raised or used when an internal critique demonstrates a fatal contradiction within opponent's premises."""
    pass


class AnachronisticRetrojectionError(TheologicalComparisonSubsystemError):
    """Raised when later theological terminology is retrojected into ancient texts without contemporary warrant."""
    pass


class IdentityCollapseError(TheologicalComparisonSubsystemError):
    """Raised when metaphorical agency or divine representation is illicitly equated to ontological identity."""
    pass


class TheologicalConfidenceInflationError(TheologicalComparisonSubsystemError):
    """Raised when comparison confidence exceeds the weakest critical dependency or uses popularity/consensus."""
    pass


class AsymmetricalFrameworkEvaluationError(TheologicalComparisonSubsystemError):
    """Raised when theological frameworks are evaluated under non-symmetrical criteria or majority voting."""
    pass


class TheologicalHarmonizationError(TheologicalComparisonSubsystemError):
    """Raised when genuine tensions between dogma and biblical text are illicitly harmonized without warrant."""
    pass


class FrameworkNotFoundError(TheologicalComparisonSubsystemError):
    """Raised when a referenced theological framework is not found."""
    pass


class PropositionNotFoundError(TheologicalComparisonSubsystemError):
    """Raised when a referenced dogmatic proposition is not found."""
    pass


class ComparisonRunNotFoundError(TheologicalComparisonSubsystemError):
    """Raised when a referenced comparison run is not found."""
    pass


class TheologicalValidationError(TheologicalComparisonSubsystemError):
    """Raised when comparison inputs fail structural, schema, or invariant validation."""
    pass


class TheologicalImmutabilityError(TheologicalComparisonSubsystemError):
    """Raised when an immutable comparison record is updated or deleted."""
    pass


class TheologicalInvalidProvenanceError(TheologicalComparisonSubsystemError):
    """Raised when theological comparison provenance metadata is missing, broken, or hash-mismatched."""
    pass


class TheologicalInvalidVersionError(TheologicalComparisonSubsystemError):
    """Raised when theological comparison versioning constraints or relations are violated."""
    pass


class TheologicalConcurrencyError(TheologicalComparisonSubsystemError):
    """Raised when concurrent operations collide on a comparison run or proposition."""
    pass


# =============================================================================
# HYBRID SYMMETRICAL RETRIEVAL SUBSYSTEM ERRORS (Task 3.9)
# =============================================================================

class RetrievalSubsystemError(BibleEngineDatabaseError):
    """Base exception for all Retrieval Subsystem errors."""
    pass


class CounterSearchSuppressionError(RetrievalSubsystemError):
    """Raised when an attempt is made to disable, suppress, or bypass counter-search."""
    pass


class AsymmetricalRetrievalError(RetrievalSubsystemError):
    """Raised when search symmetry obligations between primary and counter branches are violated."""
    pass


class EpistemicTierConfusionError(RetrievalSubsystemError):
    """Raised when E-tier and T-tier are conflated or standalone T-tier is directly assigned to retrieval items."""
    pass


class DogmaticContaminationError(RetrievalSubsystemError):
    """Raised when a T4 dogmatic claim is illicitly retrojected or used as evidence for T0–T3 claims."""
    pass


class GraphEpistemicLeakageError(RetrievalSubsystemError):
    """Raised when graph connectivity, node degree, or path length is illicitly treated as truth or confidence."""
    pass


class AbsenceOfEvidenceConflationError(RetrievalSubsystemError):
    """Raised when NOT_FOUND is illicitly converted or interpreted as NO_COUNTER_EVIDENCE_EXISTS."""
    pass


class RetrievalConfidenceInflationError(RetrievalSubsystemError):
    """Raised when retrieval ranking, BM25 score, or frequency inflates epistemic confidence."""
    pass


class FTS5HostileInputError(RetrievalSubsystemError):
    """Raised when FTS5 input contains malicious or unparsable syntax that cannot be sanitized."""
    pass


class RetrievalImmutabilityError(RetrievalSubsystemError):
    """Raised when an immutable retrieval query, run, coverage, pack, or item is modified or deleted."""
    pass


class RetrievalQueryNotFoundError(RetrievalSubsystemError):
    """Raised when a requested retrieval query record does not exist."""
    pass


class RetrievalRunNotFoundError(RetrievalSubsystemError):
    """Raised when a requested retrieval run record does not exist."""
    pass


class RetrievalContextPackNotFoundError(RetrievalSubsystemError):
    """Raised when a requested retrieval context pack does not exist."""
    pass


class RetrievalValidationError(RetrievalSubsystemError):
    """Raised when retrieval parameters or pack structures fail validation."""
    pass


class RetrievalInvalidProvenanceError(RetrievalSubsystemError):
    """Raised when retrieval provenance records are missing or invalid."""
    pass


class RetrievalInvalidVersionError(RetrievalSubsystemError):
    """Raised when retrieval version records are missing or invalid."""
    pass


class RetrievalConcurrencyError(RetrievalSubsystemError):
    """Raised when concurrent operations collide on a retrieval run or pack."""
    pass


class DeterministicHashMismatchError(RetrievalSubsystemError):
    """Raised when a computed pack hash does not match canonical deterministic serialization."""
    pass





