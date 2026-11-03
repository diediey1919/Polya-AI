"""
Test Suite: 2,456+ Verified Motion Directory & Search Engine Integration
Validates:
1. GET /api/v1/claims/directory returns all 2,456+ motions properly categorized with pagination.
2. Category filtering by 'perjanjian_lama', 'perjanjian_baru', and 'lainnya'.
3. Real-time keyword search filtering.
4. DOM structures in index.html for Motion Directory, tabs, search box, pagination, and click-to-fill handlers.
5. GET /api/v1/themes pagination with limit and offset.
"""
import json
import os
import sys
import pytest
from pathlib import Path

REPO_ROOT = str(Path(__file__).resolve().parent.parent)
WEB_DIR = os.path.join(REPO_ROOT, "web")
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
if WEB_DIR not in sys.path:
    sys.path.insert(0, WEB_DIR)

from tests.test_calculator_dom_null_regression import dispatch_asgi, read_index_html


@pytest.mark.anyio
async def test_claims_directory_endpoint_returns_catalog():
    """Validates /api/v1/claims/directory returns catalog with all 3 categories and 2,456 items."""
    status, data, _ = await dispatch_asgi("/api/v1/claims/directory")
    assert status == 200
    assert data.get("success") is True
    assert data.get("total") >= 2456
    assert "categories" in data
    cats = data["categories"]
    assert "perjanjian_lama" in cats
    assert "perjanjian_baru" in cats
    assert "lainnya" in cats
    assert cats["perjanjian_lama"] == 802
    assert cats["perjanjian_baru"] == 1654
    assert cats.get("lainnya", 0) == 0


@pytest.mark.anyio
async def test_claims_directory_pagination():
    """Validates limit and offset slicing on /api/v1/claims/directory."""
    # First page
    st1, p1, _ = await dispatch_asgi("/api/v1/claims/directory?limit=15&offset=0")
    assert st1 == 200
    assert p1.get("offset") == 0
    assert len(p1.get("items", [])) == 15

    # Second page
    st2, p2, _ = await dispatch_asgi("/api/v1/claims/directory?limit=15&offset=15")
    assert st2 == 200
    assert p2.get("offset") == 15
    assert len(p2.get("items", [])) == 15

    # Distinct items between pages
    ids_p1 = {it["id"] for it in p1.get("items", [])}
    ids_p2 = {it["id"] for it in p2.get("items", [])}
    assert ids_p1.isdisjoint(ids_p2)


@pytest.mark.anyio
async def test_themes_endpoint_pagination():
    """Validates limit and offset pagination on /api/v1/themes."""
    st1, p1, _ = await dispatch_asgi("/api/v1/themes?limit=20&offset=0")
    assert st1 == 200
    assert p1.get("offset") == 0
    assert p1.get("limit") == 20
    assert p1.get("total") >= 2000
    themes1 = p1.get("themes", [])
    assert len(themes1) == 20

    st2, p2, _ = await dispatch_asgi("/api/v1/themes?limit=20&offset=20")
    assert st2 == 200
    assert p2.get("offset") == 20
    assert p2.get("limit") == 20
    themes2 = p2.get("themes", [])
    assert len(themes2) == 20

    # Ensure different themes across pages
    ids1 = {t.get("id") for t in themes1}
    ids2 = {t.get("id") for t in themes2}
    assert ids1.isdisjoint(ids2)


@pytest.mark.anyio
async def test_claims_directory_category_and_search_filters():
    """Validates category and keyword search filtering on /api/v1/claims/directory."""
    # Filter Perjanjian Lama
    st_pl, data_pl, _ = await dispatch_asgi("/api/v1/claims/directory?category=perjanjian_lama&limit=10")
    assert st_pl == 200
    for it in data_pl.get("items", []):
        assert it.get("category") == "perjanjian_lama"

    # Filter Perjanjian Baru
    st_pb, data_pb, _ = await dispatch_asgi("/api/v1/claims/directory?category=perjanjian_baru&limit=10")
    assert st_pb == 200
    for it in data_pb.get("items", []):
        assert it.get("category") == "perjanjian_baru"

    # Keyword search
    st_q, data_q, _ = await dispatch_asgi("/api/v1/claims/directory?q=Yohanes%2010:30")
    assert st_q == 200
    assert data_q.get("total") >= 1
    found = any("10:30" in it.get("label", "") or "10:30" in it.get("claim", "") for it in data_q.get("items", []))
    assert found is True


def test_index_html_motion_directory_dom_elements():
    """Validates existence of Motion Directory DOM elements and scripts in index.html."""
    html = read_index_html()

    # Containers & Inputs
    assert 'id="motion-directory-panel"' in html
    assert 'id="motion-directory-search"' in html
    assert 'id="motion-directory-list"' in html
    assert 'id="btn-toggle-motion-dir"' in html
    assert 'id="quick-chips-featured"' in html

    # Category Tabs & Standardized Counts
    assert 'data-cat="all"' in html
    assert 'data-cat="perjanjian_lama"' in html
    assert 'data-cat="perjanjian_baru"' in html
    assert 'data-cat="lainnya"' in html
    assert 'id="count-tab-all">2.456<' in html
    assert 'id="count-tab-pl">802<' in html
    assert 'id="count-tab-pb">1.654<' in html
    assert 'id="count-tab-lainnya">0<' in html

    # Script Controllers & Optimization Constants
    assert 'function loadMotionDirectoryData()' in html
    assert 'function toggleMotionDirectory(' in html
    assert 'function filterMotionCategory(' in html
    assert 'function onMotionDirectorySearch(' in html
    assert 'function shuffleRandomMotion()' in html
    assert 'function renderMotionChunk()' in html
    assert 'const MOTION_RENDER_CHUNK = 100;' in html
    assert 'const CANONICAL_PAGE_SIZE = 20;' in html
    assert '/api/v1/themes?limit=${CANONICAL_PAGE_SIZE}&offset=' in html

    # Unified Canonical Card & Button Styling
    assert 'canonical-subcard motion-canonical-subcard' in html
    assert 'canonical-submotion-box' in html
    assert 'background: rgba(14, 165, 233, 0.08)' in html
    assert '⚡ Uji di Kalkulator' in html

    # Click-to-Fill Enhancement with smooth scroll & highlight
    assert 'claim-highlight-pulse' in html
    assert 'scrollIntoView({ behavior: "smooth"' in html


@pytest.mark.anyio
async def test_claims_directory_catalog_quality_and_uniqueness():
    """Validates that all catalog items have valid passages and no repetitive generic templates."""
    status, data, _ = await dispatch_asgi("/api/v1/claims/directory?limit=3000")
    assert status == 200
    items = data.get("items", [])
    assert len(items) >= 2456

    generic_template_1 = "Cross-Examination Sokratik ZUMA: Pembuktian Beban Pembuktian Doktrinal Interlocutor Berdasarkan Teks Kanon"
    generic_template_2 = "Cross-Examination Dialektika ZUMA: Pengujian Premis Doktrin Lawan Menggunakan Teks"

    for it in items:
        # Must have non-empty passage
        assert it.get("passage"), f"Item {it.get('id')} lacks passage"
        # Must not have exact generic repetitive template
        claim = it.get("claim", "")
        assert claim != generic_template_1, f"Item {it.get('id')} still has generic template 1"
        assert not claim.startswith(generic_template_2), f"Item {it.get('id')} still has generic template 2: {claim}"
        # Category must be valid kanon
        assert it.get("category") in {"perjanjian_lama", "perjanjian_baru"}
        # Must not contain raw youtube noise
        assert "kwkw" not in claim.lower()
        assert "addduuuhhhaaiii" not in claim.lower()
        assert "fooollll" not in claim.lower()

