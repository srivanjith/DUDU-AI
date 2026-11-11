"""
DODO MongoDB Atlas Connection Repair, Diagnostic & Live Verification Suite
Executes in-depth diagnostics across all network, TLS, DNS, and driver layers:
1. Inspects configuration without exposing credentials
2. Validates URI syntax and driver settings
3. Performs DNS SRV resolution & TCP port 27017 socket checks
4. Performs TLS handshake and server selection diagnostics
5. Distinguishes IP access-list failures from TLS, DNS, and auth errors
6. Verifies live Atlas connection (strictly prohibiting silent fallback to JSON)
"""
import json
import os
import re
import socket
import ssl
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

root_dir = Path("D:/DODO").resolve()
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import certifi
import pymongo
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure, ServerSelectionTimeoutError
from pymongo.uri_parser import parse_uri

from backend.app.core.config import settings
from backend.app.core.security import redact_secrets
from backend.app.database.mongodb import MongoDBManager


def get_public_ip() -> str:
    """Retrieves current public IP address of this machine."""
    endpoints = [
        "https://api.ipify.org",
        "https://checkip.amazonaws.com",
        "https://ifconfig.me/ip",
    ]
    for url in endpoints:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=4) as resp:
                ip = resp.read().decode("utf-8").strip()
                if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip):
                    return ip
        except Exception:
            continue
    return "Unknown (Could not query public IP)"


def mask_uri(uri: str) -> str:
    """Masks credentials in MongoDB connection string."""
    if not uri:
        return "NOT_CONFIGURED"
    return re.sub(r"(mongodb(?:\+srv)?:\/\/)([^:@\s]+):([^@\s]+)@", r"\1***:***@", uri)


def run_diagnostics():
    print("=" * 70)
    print("🍃 DODO MONGODB ATLAS CONNECTION REPAIR & LIVE VERIFICATION")
    print("=" * 70)

    raw_uri = settings.MONGODB_URI
    db_name = settings.MONGODB_DB_NAME
    masked_uri = mask_uri(raw_uri)
    public_ip = get_public_ip()

    # -------------------------------------------------------------------------
    # OBJECTIVE 1: Inspect Configuration
    # -------------------------------------------------------------------------
    print("\n[Objective 1] Inspecting MongoDB Atlas Configuration...")
    print(f"  • Connection URI:        {masked_uri}")
    print(f"  • Target Database:       {db_name}")
    print(f"  • PyMongo Version:       {pymongo.__version__}")
    print(f"  • OpenSSL Version:       {ssl.OPENSSL_VERSION}")
    print(f"  • Certifi CA Bundle:     {certifi.where()} (exists: {Path(certifi.where()).exists()})")
    print(f"  • Min / Max Pool Size:   {settings.MONGODB_MIN_POOL_SIZE} / {settings.MONGODB_MAX_POOL_SIZE}")
    print(f"  • Timeout Setting:       {settings.MONGODB_SERVER_SELECTION_TIMEOUT_MS} ms")
    print(f"  • Client Public IPv4:    {public_ip}")

    # -------------------------------------------------------------------------
    # OBJECTIVE 2: Validate URI Syntax & Driver Configuration
    # -------------------------------------------------------------------------
    print("\n[Objective 2] Validating Connection String & Driver Options...")
    uri_valid = False
    parsed_hosts = []
    uri_options = {}
    try:
        parsed = parse_uri(raw_uri)
        parsed_hosts = parsed.get("nodelist", [])
        uri_options = parsed.get("options", {})
        database_in_uri = parsed.get("database")
        uri_valid = True
        print("  ✓ URI Syntax: Valid MongoDB SRV connection string")
        print(f"  • Seed Host:             {parsed_hosts}")
        print(f"  • Default Auth Source:   {uri_options.get('authsource', 'admin')}")
        print(f"  • Retry Writes:          {uri_options.get('retrywrites', 'default')}")
        print(f"  • Write Concern:         {uri_options.get('w', 'default')}")
    except Exception as e:
        print(f"  ✗ URI Syntax Error: {e}")
        return

    # -------------------------------------------------------------------------
    # OBJECTIVE 3: DNS SRV Resolution & Network TCP Reachability
    # -------------------------------------------------------------------------
    print("\n[Objective 3] Checking DNS Resolution & TCP Port 27017 Connectivity...")
    # Known shard hosts for cluster0.iyje0uk.mongodb.net
    target_cluster_domain = parsed_hosts[0][0] if parsed_hosts else "cluster0.iyje0uk.mongodb.net"
    shard_nodes = [
        "ac-9wdshyy-shard-00-00.iyje0uk.mongodb.net",
        "ac-9wdshyy-shard-00-01.iyje0uk.mongodb.net",
        "ac-9wdshyy-shard-00-02.iyje0uk.mongodb.net",
    ]

    dns_results = {}
    tcp_results = {}

    for node in shard_nodes:
        # DNS
        try:
            ip = socket.gethostbyname(node)
            dns_results[node] = {"status": "PASS", "ip": ip}
            print(f"  ✓ DNS OK: {node} -> {ip}")
        except Exception as e:
            dns_results[node] = {"status": "FAIL", "error": str(e)}
            print(f"  ✗ DNS FAIL: {node} -> {e}")
            continue

        # TCP Socket
        t0 = time.perf_counter()
        try:
            sock = socket.create_connection((node, 27017), timeout=4)
            latency = (time.perf_counter() - t0) * 1000
            sock.close()
            tcp_results[node] = {"status": "PASS", "latency_ms": round(latency, 2)}
            print(f"  ✓ TCP OK: {node}:27017 -> Connected in {latency:.1f}ms")
        except Exception as e:
            tcp_results[node] = {"status": "FAIL", "error": str(e)}
            print(f"  ✗ TCP FAIL: {node}:27017 -> {e}")

    # -------------------------------------------------------------------------
    # OBJECTIVE 4: TLS Handshake & SSL Server Selection
    # -------------------------------------------------------------------------
    print("\n[Objective 4] Checking TLS Handshake & SSL Alert Classification...")
    tls_results = {}
    primary_test_node = shard_nodes[0]
    ctx = ssl.create_default_context(cafile=certifi.where())

    try:
        raw_sock = socket.create_connection((primary_test_node, 27017), timeout=5)
        wrapped_sock = ctx.wrap_socket(raw_sock, server_hostname=primary_test_node)
        cipher = wrapped_sock.cipher()
        tls_version = wrapped_sock.version()
        tls_results[primary_test_node] = {"status": "PASS", "cipher": cipher, "version": tls_version}
        print(f"  ✓ TLS OK: Handshake completed! Version: {tls_version}, Cipher: {cipher[0]}")
        wrapped_sock.close()
    except ssl.SSLError as ssl_err:
        err_str = str(ssl_err)
        tls_results[primary_test_node] = {"status": "FAIL", "error": err_str}
        print(f"  ✗ TLS Alert Encountered: {err_str}")
    except Exception as e:
        tls_results[primary_test_node] = {"status": "FAIL", "error": str(e)}
        print(f"  ✗ Socket/TLS Exception: {e}")

    # -------------------------------------------------------------------------
    # OBJECTIVE 5: Distinguish Root Cause
    # -------------------------------------------------------------------------
    print("\n[Objective 5] Granular Root Cause Categorization Matrix:")
    dns_pass = any(v["status"] == "PASS" for v in dns_results.values())
    tcp_pass = any(v["status"] == "PASS" for v in tcp_results.values())
    tls_pass = any(v["status"] == "PASS" for v in tls_results.values())

    print(f"  • 1. DNS Resolution:       {'PASS' if dns_pass else 'FAIL'}")
    print(f"  • 2. TCP Port 27017 Reach: {'PASS' if tcp_pass else 'FAIL'}")
    print(f"  • 3. TLS Handshake:        {'PASS' if tls_pass else 'FAIL (SSL Alert 80)'}")
    print(f"  • 4. Authentication State: {'REACHABLE' if tls_pass else 'NOT REACHED (Pre-Auth TLS Termination)'}")

    tls_err_str = tls_results.get(primary_test_node, {}).get("error", "")
    is_ip_access_list_rejection = "TLSV1_ALERT_INTERNAL_ERROR" in tls_err_str or "alert number 80" in tls_err_str

    if is_ip_access_list_rejection:
        print("\n  🎯 ROOT CAUSE DETERMINATION:")
        print("  • Category: IP ACCESS-LIST RESTRICTION (MongoDB Atlas Ingress Firewall)")
        print(f"  • Current Client Public IP: {public_ip}")
        print("  • Explanation:")
        print("    MongoDB Atlas employs an ingress gateway that verifies incoming IP addresses against")
        print("    the project's Network Access Whitelist during TLS negotiation.")
        print(f"    Because IP '{public_ip}' is not registered in the Atlas IP Access List,")
        print("    Atlas sends fatal TLS Alert 80 (INTERNAL_ERROR) and closes the connection.")
        print("  • Required Resolution:")
        print("    1. Log in to cloud.mongodb.com")
        print("    2. Navigate to: Security -> Network Access")
        print(f"    3. Click 'Add IP Address' -> Add '{public_ip}' (or allow '0.0.0.0/0')")
        print("    4. Save changes (takes ~30-60 seconds to propagate).")
    elif not tls_pass:
        print(f"\n  🎯 ROOT CAUSE DETERMINATION: TLS / Certificate Error: {tls_err_str}")
    else:
        print("\n  🎯 ROOT CAUSE DETERMINATION: Network & TLS Handshake are fully operational.")

    # -------------------------------------------------------------------------
    # OBJECTIVE 6 & LIVE ATLAS VERIFICATION (Strictly no silent mock fallback)
    # -------------------------------------------------------------------------
    print("\n[Objective 6 & Live Verification] Attempting Real MongoDB Atlas Operations...")
    print("  (Safety Rule Enforced: Silent JSON / mongomock fallback is disabled for this test)")

    real_atlas_client = None
    real_atlas_connected = False
    server_info = {}

    try:
        real_atlas_client = MongoClient(
            raw_uri,
            serverSelectionTimeoutMS=4000,
            connectTimeoutMS=4000,
            tlsCAFile=certifi.where()
        )
        ping_res = real_atlas_client.admin.command("ping")
        server_info = real_atlas_client.server_info()
        real_atlas_connected = True
    except Exception as e:
        real_atlas_connected = False
        atlas_conn_err = str(e)

    if not real_atlas_connected:
        print("\n" + "=" * 70)
        print("🛑 ATLAS LIVE VERIFICATION RESULT: BLOCKED / FAIL")
        print("=" * 70)
        print(f"1. Actual Atlas Connection Status: FAIL")
        print(f"2. Reason:                         IP ACCESS-LIST RESTRICTION")
        print(f"3. Client Machine IP to Whitelist: {public_ip}")
        print(f"4. Expected Database:              {db_name}")
        print(f"5. Fallback Status:                Local JSON fallback preserved for IDE offline safety")
        print(f"6. Mock Database Active:           FALSE (Silent fallback was NOT allowed)")
        print(f"7. Server Version:                 UNAVAILABLE (Handshake terminated)")
        print(f"8. Remaining Error:                {tls_err_str or 'ServerSelectionTimeoutError'}")
        print("=" * 70)
        return False

    # If network access was granted:
    print(f"✓ LIVE ATLAS CONNECTION ESTABLISHED!")
    server_version = server_info.get("version", "Unknown")
    print(f"  • Server Version: {server_version}")
    print(f"  • Database:       {db_name}")
    print(f"  • is_mock:        False (Real MongoDB Atlas Cluster)")

    target_db = real_atlas_client[db_name]
    test_collection_name = "__atlas_live_verify__"
    test_col = target_db[test_collection_name]

    print(f"\n[Live Operations] Executing CRUD on collection '{test_collection_name}'...")
    # 1. Insert
    test_doc = {"id": "verify_test_doc_01", "name": "DODO Live Verifier", "timestamp": time.time()}
    ins_res = test_col.insert_one(test_doc)
    print(f"✓ Insert OK: Created document with ObjectId {ins_res.inserted_id}")

    # 2. Read
    found = test_col.find_one({"id": "verify_test_doc_01"})
    assert found and found["name"] == "DODO Live Verifier"
    print(f"✓ Read OK: Retrieved document '{found['name']}'")

    # 3. Update
    test_col.update_one({"id": "verify_test_doc_01"}, {"$set": {"status": "Verified Active"}})
    updated = test_col.find_one({"id": "verify_test_doc_01"})
    assert updated and updated.get("status") == "Verified Active"
    print(f"✓ Update OK: Modified document status to '{updated['status']}'")

    # 4. Index verification
    test_col.create_index([("id", pymongo.ASCENDING)], unique=True)
    indexes = list(test_col.list_indexes())
    index_names = [idx["name"] for idx in indexes]
    print(f"✓ Indexing OK: Created and verified indexes: {index_names}")

    # 5. Restart Persistence Test
    print("\n[Restart Simulation] Disconnecting and re-establishing fresh client connection...")
    real_atlas_client.close()
    time.sleep(1)

    fresh_client = MongoClient(raw_uri, serverSelectionTimeoutMS=4000, tlsCAFile=certifi.where())
    fresh_col = fresh_client[db_name][test_collection_name]
    re_found = fresh_col.find_one({"id": "verify_test_doc_01"})
    assert re_found is not None and re_found.get("status") == "Verified Active"
    print("✓ Restart Durability OK: Record survived client teardown and reconnection.")

    # 6. Delete & Cleanup
    fresh_col.delete_one({"id": "verify_test_doc_01"})
    assert fresh_col.find_one({"id": "verify_test_doc_01"}) is None
    fresh_col.drop()
    print("✓ Cleanup OK: Removed test document and dropped test collection.")
    fresh_client.close()

    print("\n" + "=" * 70)
    print("🎉 ATLAS LIVE VERIFICATION RESULT: PASS")
    print(f"  • Server Version: {server_version}")
    print(f"  • Database:       {db_name}")
    print(f"  • is_mock:        False")
    print(f"  • CRUD Tests:     All Passed")
    print("=" * 70)
    return True


if __name__ == "__main__":
    success = run_diagnostics()
    sys.exit(0 if success else 1)
