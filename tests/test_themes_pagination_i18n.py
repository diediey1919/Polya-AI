import pytest
from fastapi.testclient import TestClient
from web.app import app

client = TestClient(app)

def test_themes_pagination_and_localization_zh():
    """Verify offset=0, 20, 40 all return localized Chinese titles and passages."""
    for offset in [0, 20, 40]:
        response = client.get(f"/api/v1/themes?offset={offset}&limit=20&locale=zh-CN", headers={"Accept-Language": "zh-CN"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total"] == 2625
        assert len(data["themes"]) == 20
        assert data["locale"] == "zh-CN"

        for item in data["themes"]:
            # Title should exist
            assert item.get("title"), "Theme item missing title"
            # Passages should not contain untranslated Indonesian books
            for p in item.get("passages", []):
                assert not p.startswith("YOHANES "), f"Untranslated passage found: {p}"
                assert not p.startswith("KISAH PARA RASUL "), f"Untranslated passage found: {p}"
                assert not p.startswith("ULANGAN "), f"Untranslated passage found: {p}"
                assert not p.startswith("MATIUS "), f"Untranslated passage found: {p}"
                assert not p.startswith("MARKUS "), f"Untranslated passage found: {p}"

def test_themes_pagination_and_localization_en():
    """Verify offset=0, 20, 40 all return localized English titles and passages."""
    for offset in [0, 20, 40]:
        response = client.get(f"/api/v1/themes?offset={offset}&limit=20&locale=en", headers={"Accept-Language": "en"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total"] == 2625
        assert len(data["themes"]) == 20
        assert data["locale"] == "en"

        for item in data["themes"]:
            assert item.get("title"), "Theme item missing title"
            for p in item.get("passages", []):
                assert not p.startswith("YOHANES "), f"Untranslated passage found: {p}"
                assert not p.startswith("KISAH PARA RASUL "), f"Untranslated passage found: {p}"
                assert not p.startswith("ULANGAN "), f"Untranslated passage found: {p}"
                assert not p.startswith("MATIUS "), f"Untranslated passage found: {p}"
                assert not p.startswith("MARKUS "), f"Untranslated passage found: {p}"

def test_themes_monoteisme_and_kenabian_clusters_zh():
    """Verify specific clusters: Monoteisme (475 motions) and Kenabian (72 motions)."""
    # Monoteisme
    resp_mono = client.get("/api/v1/themes?category=Monoteisme%20%26%20Kritik%20Doktrin%20Trinitas&limit=25&offset=20&locale=zh-CN")
    assert resp_mono.status_code == 200
    data_mono = resp_mono.json()
    assert data_mono["total"] == 475
    assert len(data_mono["themes"]) == 25
    for item in data_mono["themes"]:
        # Verify title has Chinese characters
        assert any('\u4e00' <= char <= '\u9fff' for char in item["title"]), f"Title not in Chinese: {item['title']}"

    # Kenabian
    resp_kenabian = client.get("/api/v1/themes?category=Apologetika%20Islam%20%26%20Pembelaan%20Kenabian&limit=25&offset=20&locale=zh-CN")
    assert resp_kenabian.status_code == 200
    data_kenabian = resp_kenabian.json()
    assert data_kenabian["total"] == 72
    assert len(data_kenabian["themes"]) == 25
    for item in data_kenabian["themes"]:
        assert any('\u4e00' <= char <= '\u9fff' for char in item["title"]), f"Title not in Chinese: {item['title']}"
