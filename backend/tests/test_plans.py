def test_generate_plan_enriches_output(client, user, plan_factory):
    response = plan_factory(user["headers"])
    assert response.status_code == 200, response.text
    plan = response.json()
    assert plan["rooms"]
    assert plan["material_estimate"]["rate_per_sqft_pkr"] == 3200
    assert plan["material_estimate"]["estimated_cost_pkr"] > 0
    assert plan["bylaws_report"]
    assert plan["vastu_report"]
    assert plan["impact_summary"]

    me = client.get("/api/v1/auth/me", headers=user["headers"]).json()
    assert me["credits"] == 2


def test_generate_variants_and_credit_drain(client, user, plan_factory):
    variants = client.post(
        "/api/v1/plans/generate-variants",
        json={"base": {
            "prompt": "3 marla house",
            "plot_width": 20,
            "plot_length": 35,
            "building_type": "house",
            "floors": 1,
            "bedrooms": 2,
            "bathrooms": 2,
        }, "count": 3},
        headers=user["headers"],
    )
    assert variants.status_code == 200, variants.text
    body = variants.json()
    assert len(body["variants"]) == 3
    assert body["compare"]["rows"]
    assert body["compare"]["recommendation"]

    plan_factory(user["headers"])
    plan_factory(user["headers"])
    blocked = plan_factory(user["headers"])
    assert blocked.status_code == 403


def test_bylaws_packs_and_presets(client):
    packs = client.get("/api/v1/plans/bylaws-packs")
    assert packs.status_code == 200
    ids = {pack["id"] for pack in packs.json()["packs"]}
    assert {"pakistan_generic", "dha_lahore", "lda_lahore", "cda_islamabad", "sbca_karachi"} <= ids

    presets = client.get("/api/v1/plans/presets")
    assert presets.status_code == 200
    assert "5_marla" in presets.json()["presets"]


def test_export_pdf_and_dxf(client, user, plan_factory):
    plan = plan_factory(user["headers"]).json()

    pdf = client.post("/api/v1/plans/export-pdf", json=plan, headers=user["headers"])
    assert pdf.status_code == 200
    assert pdf.content.startswith(b"%PDF-")
    assert len(pdf.content) > 2000

    dxf = client.post("/api/v1/plans/export-dxf", json=plan, headers=user["headers"])
    assert dxf.status_code == 200
    assert b"SECTION" in dxf.content[:200]


def test_recalculate_and_validate(client, user, plan_factory):
    plan = plan_factory(user["headers"]).json()
    recalculated = client.post(
        "/api/v1/plans/recalculate",
        json={"plan": plan, "rate_per_sqft_pkr": 4100, "bylaws_pack": "dha_lahore"},
        headers=user["headers"],
    )
    assert recalculated.status_code == 200, recalculated.text
    assert recalculated.json()["material_estimate"]["rate_per_sqft_pkr"] == 4100

    validated = client.post("/api/v1/plans/validate-layout", json=plan, headers=user["headers"])
    assert validated.status_code == 200
    assert validated.json()["rooms"]
