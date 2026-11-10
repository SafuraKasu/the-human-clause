"""Local app: serves the workspace and records review decisions (record-only) over HTTP."""
import json
import shutil
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from backend import config
from backend.app.__main__ import make_server
from backend.review import records

RUN = config.ROOT / "data" / "runs" / "20261108-005651-live"
ITEM = "E5:escalation:ED_btg_B_meds"


@pytest.fixture
def server(tmp_path):
    run = tmp_path / "run"
    shutil.copytree(RUN, run, ignore=shutil.ignore_patterns("reviews.jsonl"))
    srv = make_server(run, 0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}", run
    srv.shutdown()


def call(url, method="GET", body=None, headers=None):
    h = {"Content-Type": "application/json", **(headers or {})}
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None, method=method, headers=h)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


GOOD = {"item": ITEM, "decision": "uphold", "reviewer": "Dr Test", "role": "clinician",
        "reason": "Agree the block stands pending a senior decision."}


def test_page_is_served_in_server_mode(server):
    url, _ = server
    code, body = call(url + "/")
    assert code == 200 and b"Fatima Hassan" in body and b'"server": true' in body


def test_valid_review_is_recorded_and_chained(server):
    url, run = server
    code, body = call(url + "/api/review", "POST", GOOD)
    j = json.loads(body)
    assert code == 200 and j["review_status"][ITEM]["decision"] == "uphold" and j["review_integrity"]["status"] == "ok"
    assert records.check(run)["status"] == "ok"


@pytest.mark.parametrize("patch,needle", [({"reason": "too short"}, "reason"), ({"item": "E9:nope"}, "unknown item"),
                                          ({"decision": "approve"}, "decision"), ({"reviewer": " "}, "required")])
def test_invalid_reviews_are_refused(server, patch, needle):
    url, run = server
    code, body = call(url + "/api/review", "POST", {**GOOD, **patch})
    assert code == 400 and needle in json.loads(body)["error"]
    assert not (run / "reviews.jsonl").exists()


def test_cross_origin_and_non_json_posts_are_refused(server):
    url, _ = server
    assert call(url + "/api/review", "POST", GOOD, {"Origin": "http://evil.example"})[0] == 403
    assert call(url + "/api/review", "POST", GOOD, {"Content-Type": "text/plain"})[0] == 415


def test_tampered_audit_blocks_reviews(server):
    url, run = server
    lines = (run / "audit.jsonl").read_text(encoding="utf-8").splitlines()
    (run / "audit.jsonl").write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")  # cut the end off
    code, body = call(url + "/api/review", "POST", GOOD)
    assert code == 400 and "audit" in json.loads(body)["error"]


def test_wrong_host_header_and_bad_content_length_are_refused(server):
    import http.client
    url, _ = server
    port = int(url.rsplit(":", 1)[1])
    c = http.client.HTTPConnection("127.0.0.1", port)
    c.request("POST", "/api/review", json.dumps(GOOD), {"Content-Type": "application/json", "Host": "evil.example"})
    assert c.getresponse().status == 403
    c = http.client.HTTPConnection("127.0.0.1", port)
    c.putrequest("POST", "/api/review"); c.putheader("Content-Type", "application/json"); c.putheader("Content-Length", "abc"); c.endheaders()
    assert c.getresponse().status == 400


def test_control_characters_in_review_fields_are_refused(server):
    url, run = server
    code, body = call(url + "/api/review", "POST", {**GOOD, "reviewer": "QA\nFAKE (clinician): forged"})
    assert code == 400 and "plain text" in json.loads(body)["error"]
    assert not (run / "reviews.jsonl").exists()
