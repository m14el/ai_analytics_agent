"""Verification script for AI Analytics Agent."""
import httpx
import sys

BASE = "http://localhost:8000"

def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {name}" + (f" -- {detail}" if detail else ""))
    return condition

def main():
    ok = True

    # 1. API Summary
    print("=== API /api/summary ===")
    try:
        r = httpx.get(f"{BASE}/api/summary", timeout=10)
        d = r.json()
        ok &= check("Status 200", r.status_code == 200, str(r.status_code))
        ok &= check("Revenue > 0", d["total_revenue"] > 0, f"${d['total_revenue']:,.0f}")
        ok &= check("Costs > 0", d["total_costs"] > 0, f"${d['total_costs']:,.0f}")
        ok &= check("Projects = 18", d["project_count"] == 18, str(d["project_count"]))
        ok &= check("Developers = 30", d["developer_count"] == 30, str(d["developer_count"]))
        ok &= check("Tasks = 73", d["task_count"] == 73, str(d["task_count"]))
        ok &= check("Loss projects > 0", d["loss_projects_count"] > 0, str(d["loss_projects_count"]))
        ok &= check("Projects list", len(d["projects"]) == 18)
        ok &= check("Stacks list", len(d["stacks"]) == 6)
        ok &= check("Task types", len(d["task_types"]) > 0)

        # AI Analysis
        ai = d.get("ai_analysis", {})
        ok &= check("AI summary", bool(ai.get("summary")))
        ok &= check("AI hypotheses", len(ai.get("hypotheses", [])) > 0, str(len(ai.get("hypotheses", []))))
        ok &= check("AI recommendations", len(ai.get("recommendations", [])) > 0, str(len(ai.get("recommendations", []))))
        ok &= check("AI anomalies", len(ai.get("anomalies", [])) > 0, str(len(ai.get("anomalies", []))))
    except Exception as e:
        print(f"  [FAIL] API unreachable: {e}")
        ok = False

    # 2. HTML Pages
    print("\n=== HTML Pages ===")
    pages = ["/", "/projects", "/stacks", "/tasks", "/developers"]
    for page in pages:
        try:
            r = httpx.get(f"{BASE}{page}", timeout=10)
            has_content = len(r.text) > 500
            ok &= check(f"GET {page}", r.status_code == 200 and has_content, f"status={r.status_code}, len={len(r.text)}")
        except Exception as e:
            print(f"  [FAIL] {page}: {e}")
            ok = False

    # 3. API Endpoints
    print("\n=== API Endpoints ===")
    for ep in ["/api/summary", "/api/anomalies", "/api/ai-analysis"]:
        try:
            r = httpx.get(f"{BASE}{ep}", timeout=10)
            ok &= check(f"GET {ep}", r.status_code == 200, f"status={r.status_code}")
        except Exception as e:
            print(f"  [FAIL] {ep}: {e}")
            ok = False

    # 4. Dashboard content checks
    print("\n=== Dashboard Content ===")
    try:
        r = httpx.get(f"{BASE}/", timeout=10)
        html = r.text
        ok &= check("Has Plotly.js", "plotly" in html.lower())
        ok &= check("Has chart containers", "chart-container" in html)
        ok &= check("Has KPI cards", "kpi-card" in html)
        ok &= check("Has AI panel", "ai-panel" in html)
        ok &= check("Has sidebar", "sidebar" in html)
    except Exception as e:
        print(f"  [FAIL] Dashboard check: {e}")
        ok = False

    print("\n" + "=" * 40)
    print(f"RESULT: {'ALL CHECKS PASSED' if ok else 'SOME CHECKS FAILED'}")
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
