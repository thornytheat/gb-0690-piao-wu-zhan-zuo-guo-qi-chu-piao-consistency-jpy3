import pytest
from app.pipeline import run
from app.config import SAMPLES
from app.modules.m1_receive.rules import receive

SHOWS = (SAMPLES / "shows.csv").read_bytes()
HEADER = ("id,show,channel,seat,order,time,type,expires,version,amount,ticket\n")

def test_show_sample_conservation():
    r = run(SHOWS, persist=False)
    assert r["input_count"] == len(r["records"]) + len(r["quarantine"]) == 15

def test_missing_show_rows_are_quarantined_with_line_numbers():
    r = run(SHOWS, persist=False)
    no_show = [q for q in r["quarantine"] if q["code"] == "NO_SHOW"]
    assert len(no_show) == 3
    assert {q["line"] for q in no_show} == {14, 15, 16}
    # 证据保留原始内容可追查
    assert all(q["raw"]["order"] for q in no_show)

def test_missing_show_never_touches_inventory_or_revenue():
    r = run(SHOWS, persist=False)
    assert not any(p["order"] == "OX1" for p in r["payments"])
    assert not any(t["order"] in ("OX1", "OX2") for t in r["tickets"])
    assert not any(l["order"] in ("OX1", "OX2") for l in r["leases"])

def test_same_seat_sells_independently_per_show():
    r = run(SHOWS, persist=False)
    a01 = [t for t in r["tickets"] if t["seat"] == "A-01"]
    assert {t["show"] for t in a01} == {"1117-A", "1118-E"}
    assert len(a01) == 2

def test_reconcile_is_partitioned_by_show():
    r = run(SHOWS, persist=False)
    totals = {b["show"]: b for b in r["show_balances"]}
    assert int(totals["1117-A"]["paid"]) == 200 and int(totals["1117-A"]["ticketed"]) == 200
    assert int(totals["1118-E"]["paid"]) == 240 and int(totals["1118-E"]["delta"]) == 120
    assert all("show" in row for row in r["channel_balances"])

def test_legacy_file_without_show_column_backfilled():
    out = receive((SAMPLES / "legacy.csv").read_bytes(), "1117-A")
    assert all(x["show"] == "1117-A" for x in out["records"])
    assert not any(q["code"] == "NO_SHOW" for q in out["quarantine"])

def test_custom_default_show_parameter():
    r = run((SAMPLES / "dirty.csv").read_bytes(), params={"default_show": "MATINEE"}, persist=False)
    assert {x["show"] for x in r["records"]} == {"MATINEE"}

def test_blank_show_among_filled_rows_isolated_not_backfilled():
    csv_text = HEADER + (
        "H1,1117-A,官方,A01,O1,2026-11-17T10:00:00+08:00,hold,2026-11-17T10:15:00+08:00,1,0,\n"
        "U1,,官方,A01,OU,2026-11-17T11:00:00+08:00,hold,2026-11-17T11:15:00+08:00,1,0,\n"
    )
    r = run(csv_text, persist=False)
    assert [q["code"] for q in r["quarantine"]] == ["NO_SHOW"]
    assert len(r["leases"]) == 1 and r["leases"][0]["show"] == "1117-A"

def test_unknown_show_row_does_not_block_same_seat_sale():
    csv_text = HEADER + (
        "U1,,官方,A01,OU,2026-11-17T11:00:00+08:00,hold,2026-11-17T11:15:00+08:00,1,0,\n"
        "H1,1117-A,官方,A01,O1,2026-11-17T10:00:00+08:00,hold,2026-11-17T10:15:00+08:00,1,0,\n"
        "P1,1117-A,官方,A01,O1,2026-11-17T10:05:00+08:00,pay,,1,100,\n"
        "T1,1117-A,官方,A01,O1,2026-11-17T10:06:00+08:00,issue,,1,100,TK1\n"
    )
    r = run(csv_text, persist=False)
    assert len(r["tickets"]) == 1 and r["tickets"][0]["ticket"] == "TK1"

def test_rerun_same_batch_creates_no_new_record(raw, isolate):
    a = run(SHOWS)
    b = run(SHOWS)
    assert a["manifest"]["run_id"] == b["manifest"]["run_id"]
    import sqlite3, os
    db = sqlite3.connect(os.path.join(os.environ["DATA_DIR"], "runs.sqlite"))
    assert db.execute("SELECT COUNT(*) FROM runs").fetchone()[0] == 1
    db.close()

def test_ticket_number_still_globally_unique_across_shows():
    csv_text = HEADER + (
        "H1,1117-A,官方,A01,O1,2026-11-17T10:00:00+08:00,hold,2026-11-17T10:15:00+08:00,1,0,\n"
        "P1,1117-A,官方,A01,O1,2026-11-17T10:05:00+08:00,pay,,1,100,\n"
        "T1,1117-A,官方,A01,O1,2026-11-17T10:06:00+08:00,issue,,1,100,SAME\n"
        "H2,1118-E,官方,A02,O2,2026-11-17T14:00:00+08:00,hold,2026-11-17T14:15:00+08:00,1,0,\n"
        "P2,1118-E,官方,A02,O2,2026-11-17T14:05:00+08:00,pay,,1,100,\n"
        "T2,1118-E,官方,A02,O2,2026-11-17T14:06:00+08:00,issue,,1,100,SAME\n"
    )
    r = run(csv_text, persist=False)
    assert len(r["tickets"]) == 1
    assert any(q["code"] == "CONFLICT" for q in r["quarantine"])

def test_watermark_is_tracked_per_show():
    r = run(SHOWS, persist=False)
    assert set(r["audit"]["watermark"]) == {"1117-A", "1118-E"}
    assert r["audit"]["shows"] == ["1117-A", "1118-E"]

def test_pages_render_per_show_and_expose_unknown_rows(client):
    saved = client.post("/api/runs", json={"text": SHOWS.decode("utf-8-sig")}).json
    rid = saved["manifest"]["run_id"]
    for stage in range(1, 8):
        page = client.get(f"/m/{stage}?run={rid}&show=1118-E")
        assert page.status_code == 200
        assert "1118-E".encode() in page.data
    m1 = client.get(f"/m/1?run={rid}").text
    assert "场次缺失" in m1 and "NX1" in m1
    m6 = client.get(f"/m/6?run={rid}").text
    assert "1117-A" in m6 and "1118-E" in m6

def test_evidence_csv_contains_no_show_reason(client):
    saved = client.post("/api/runs", json={"text": SHOWS.decode("utf-8-sig")}).json
    text = client.get("/api/evidence.csv?run=" + saved["manifest"]["run_id"]).text
    assert "NO_SHOW" in text and "NX3" in text
