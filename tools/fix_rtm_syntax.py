#!/usr/bin/env python3
"""
Fix specific syntax errors in rtm.py caused by automated reformatting.
"""

import re
from pathlib import Path


def fix_rtm_syntax():
    """Fix specific syntax errors in rtm.py."""
    file_path = Path(__file__).parent.parent / "src" / "be" / "api" / "rtm.py"

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Fix major syntax issues
    fixes = [
        # Fix docstring placement issues
        (') -> List[dict]: """Apply basic filtering logic', ') -> List[dict]:\n    """Apply basic filtering logic'),
        ('# Dashboard and Web Interface @router.get', '# Dashboard and Web Interface\n@router.get'),
        ('def multipersona_dashboard(request: Request): """Serve the Multi-Persona Dashboard', 'def multipersona_dashboard(request: Request):\n    """Serve the Multi-Persona Dashboard'),
        ('def multipersona_dashboard_demo(request: Request): """Serve the Multi-Persona Dashboard', 'def multipersona_dashboard_demo(request: Request):\n    """Serve the Multi-Persona Dashboard'),

        # Fix missing newlines and indentation issues
        (' @router.get("/epics/', '\n\n@router.get("/epics/'),
        (' @router.get("/user-stories/', '\n\n@router.get("/user-stories/'),
        (' @router.put("/tests/', '\n\n@router.put("/tests/'),
        (' @router.get("/reports/', '\n\n@router.get("/reports/'),
        (' @router.post("/epics/', '\n\n@router.post("/epics/'),
        (' @router.get("/epics/{epic_id}/metrics")', '\n\n@router.get("/epics/{epic_id}/metrics")'),
        (' @router.post("/epics/{epic_id}/metrics/update")', '\n\n@router.post("/epics/{epic_id}/metrics/update")'),
        (' @router.get("/epics/{epic_id}/metrics/timeline")', '\n\n@router.get("/epics/{epic_id}/metrics/timeline")'),
        (' @router.get("/dashboard/metrics/demo")', '\n\n@router.get("/dashboard/metrics/demo")'),
        (' @router.get("/dependencies/analysis/critical-path")', '\n\n@router.get("/dependencies/analysis/critical-path")'),

        # Fix component filtering sections
        ('if component: components = [c.strip() for c in component.split(",")]', 'if component:\n        components = [c.strip() for c in component.split(",")]'),
        ('if exclude_component: exclude_components = [c.strip() for c in exclude_component.split(",")]', 'if exclude_component:\n        exclude_components = [c.strip() for c in exclude_component.split(",")]'),

        # Fix condition checking
        ('if not epic: raise HTTPException', 'if not epic:\n        raise HTTPException'),
        ('if not test: raise HTTPException', 'if not test:\n        raise HTTPException'),

        # Fix specific broken lines
        ('db.query(Test) .filter(Test.component == component, Test.last_execution_status =="passed")',
         'db.query(Test)\n            .filter(\n                Test.component == component,\n                Test.last_execution_status == "passed"\n            )'),

        # Fix missing line breaks in result assignments
        (') result["user_stories"]', ')\n        result["user_stories"]'),
        (') result["tests"]', ')\n        result["tests"]'),
        (') result["defects"]', ')\n        result["defects"]'),

        # Fix elif/else statements
        ('return HTMLResponse(content=content) elif format =="markdown":', 'return HTMLResponse(content=content)\n    elif format == "markdown":'),
        ('content = generator.generate_markdown_matrix(filters) return Response', 'content = generator.generate_markdown_matrix(filters)\n        return Response'),
        ('content, media_type, filename = generator.export_full_matrix(format) elif report_type =="epic-progress":',
         'content, media_type, filename = generator.export_full_matrix(format)\n    elif report_type == "epic-progress":'),
        ('content, media_type, filename = generator.export_epic_progress(format) elif report_type =="test-summary":',
         'content, media_type, filename = generator.export_epic_progress(format)\n    elif report_type == "test-summary":'),

        # Fix function definition issues
        ('def calculate_dashboard_summary(epic_metrics: List[dict], persona: str) -> dict: """Calculate aggregated',
         'def calculate_dashboard_summary(epic_metrics: List[dict], persona: str) -> dict:\n    """Calculate aggregated'),
        ('if persona_key =="pm":', 'if persona_key == "pm":'),

        # Fix broken dictionary formatting
        ('{ "epic_id": epic_id,', '{\n        "epic_id": epic_id,'),
        ('{ "severity": severity_filter, "days_back": days_back,', '{\n        "severity": severity_filter,\n        "days_back": days_back,'),
        ('{ "epic_id": epic_filter, "status": status_filter, "priority": priority_filter, "us_status_filter": us_status_filter, "test_type_filter": test_type_filter, "defect_priority_filter": defect_priority_filter, "defect_status_filter": defect_status_filter, "include_tests": include_tests,',
         '{\n        "epic_id": epic_filter,\n        "status": status_filter,\n        "priority": priority_filter,\n        "us_status_filter": us_status_filter,\n        "test_type_filter": test_type_filter,\n        "defect_priority_filter": defect_priority_filter,\n        "defect_status_filter": defect_status_filter,\n        "include_tests": include_tests,'),

        # Fix broken return statements
        ('"timestamp": datetime.now(datetime.UTC).isoformat(), "epic_status": epic_status,',
         '"timestamp": datetime.now(datetime.UTC).isoformat(),\n        "epic_status": epic_status,'),
        ('"epic_id": epic_id,\n            "persona": persona.upper(), "metrics": metrics,',
         '"epic_id": epic_id,\n            "persona": persona.upper(),\n            "metrics": metrics,'),
        ('"epic_id": epic_id,\n            "metrics": metrics,',
         '"epic_id": epic_id,\n            "metrics": metrics,'),

        # Fix missing spaces in component filters
        ('supports comma-separated values )', 'supports comma-separated values)'),
    ]

    for old, new in fixes:
        content = content.replace(old, new)

    # Write fixed content back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("Fixed syntax errors in rtm.py")


if __name__ == "__main__":
    fix_rtm_syntax()