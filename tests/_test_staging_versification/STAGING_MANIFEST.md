# STAGING VERSIFICATION ARTIFACTS AUDIT MANIFEST
Task 5F-B: Source Acquisition & Versification Data Validation

Directory: `tests/_test_staging_versification/` (Isolated Staging — Non-Production)

## 1. CrossWire SWORD KJV Canonical Versification Definition
- File: `canon_kjv.h`
- Source URL: `https://crosswire.org/svn/sword-tools/trunk/versification/basicv11ns/canon_kjv.h`
- Repository: CrossWire SWORD Tools (SVN trunk)
- Pinned SVN Revision: Revision 568 (ETag: `"455//trunk/versification/basicv11ns/canon_kjv.h"`)
- Actual SHA-256: `cf2f2844f0f8c8c1c66988c90dffff7708aada634b89d31e5e1ab1bcbb5fd88e`
- Size: 9,867 bytes
- License: GNU General Public License version 2 (GPL-2.0)
- Copyright: (c) 2009 CrossWire Bible Society (http://www.crosswire.org)
- Scope & Coverage:
  * Old Testament: 39 books (`otbooks_kjv`), 929 chapters
  * New Testament: 27 books (`ntbooks_kjv`), 260 chapters
  * Total Books: 66
  * Total Chapters: 1,189
  * Total Verses: 31,102 (verified against `vm_kjv[]` array)
  * Chapter counts match 100% against `/home/ubuntu/.polya/bible_engine.db` `books` table.

## 2. STEPBible TVTMS (Translators Versification Traditions with Methodology for Standardisation)
- File: `TVTMS_versification.txt` (raw filename: `TVTMS - Translators Versification Traditions with Methodology for Standardisation for Eng+Heb+Lat+Grk+Others - STEPBible.org CC BY.txt`)
- Source URL: `https://raw.githubusercontent.com/STEPBible/STEPBible-Data/master/Versification/TVTMS%20-%20Translators%20Versification%20Traditions%20with%20Methodology%20for%20Standardisation%20for%20Eng%2BHeb%2BLat%2BGrk%2BOthers%20-%20STEPBible.org%20CC%20BY.txt`
- Repository: `https://github.com/STEPBible/STEPBible-Data` (branch: master)
- Git Blob SHA-1: `4fdcb4fd761ba8a680a3f0cc95ad65f591e18d4b`
- Actual SHA-256: `63058e0f20201af4bdaa7d830da5be8f493455d947c5f147d84840b33db9ddf8`
- Size: 5,790,928 bytes
- License: Creative Commons Attribution 4.0 International (CC BY 4.0)
- Copyright & Attribution:
  * "Data created by www.STEPBible.org based on work at Tyndale House Cambridge (CC BY 4.0)"
  * Obligation: Retain attribution to STEPBible.org and Tyndale House Cambridge in distributions, derived datasets, and documentation.
- Scope & Coverage:
  * Full multidirectional versification alignment between KJV/English, Hebrew Masoretic Text (BHS/WLC), Greek Septuagint (LXX), Latin Vulgate, and modern versions.
  * Formatted rules for reversification and translation shift detection (e.g., Psalm title verse shifts, Malachi 3/4 differences, New Testament variants).
