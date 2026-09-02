SEED_WORKSPACE = {
    "project": {
        "name": "Retail demand forecast",
        "brief": "Plan the next 12 weeks of demand forecasting",
        "goal": "Reduce stock-outs while keeping recommendations explainable to the merchandising team.",
    },
    "readiness": {
        "status": "PLANNED",
        "dataset": "retail_orders.parquet",
        "score": 0,
        "note": "No dataset is connected; this is a readiness plan, not a measured profile.",
        "boundary": "planning-only · no model artifact",
    },
    "tasks": [
        {"id": 1, "title": "Capture business constraints", "area": "Business understanding", "priority": "high", "done": True},
        {"id": 2, "title": "Document the feature plan", "area": "Data preparation", "priority": "medium", "done": True},
        {"id": 3, "title": "Validate promotion and holiday flags", "area": "Data preparation", "priority": "high", "done": False},
        {"id": 4, "title": "Compare seasonal naive baseline", "area": "Modeling", "priority": "medium", "done": False},
        {"id": 5, "title": "Write stakeholder readout", "area": "Evaluation", "priority": "low", "done": False},
    ],
    "workflow": {
        "current": "Modeling phase",
        "stages": [
            {"name": "Business understanding", "status": "complete", "evidence": "Goal and constraints captured", "detail": "Define the stock-out objective, forecast horizon, and explainability needs."},
            {"name": "Data understanding", "status": "complete", "evidence": "Schema and quality review planned", "detail": "Profile dates, missingness, duplicate orders, and coverage before fitting anything."},
            {"name": "Data preparation", "status": "complete", "evidence": "Feature plan documented", "detail": "Specify calendar, promotion, and lag features without leaking future demand."},
            {"name": "Modeling", "status": "planned", "evidence": "Baseline comparison planned", "detail": "Start with a seasonal-naive baseline before evaluating a learned model."},
            {"name": "Evaluation", "status": "planned", "evidence": "Waiting on model artifacts", "detail": "Use a chronological holdout and report error by store, horizon, and season."},
            {"name": "Deployment", "status": "planned", "evidence": "Planned after sign-off", "detail": "Define monitoring and rollback criteria only after evidence exists."},
        ],
    },
    "activity": [{"message": "Workspace initialized", "detail": "Planning boundary is explicit; no model run was claimed."}],
}
