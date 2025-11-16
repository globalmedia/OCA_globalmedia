{
    "name": "Plan Monitoring",
    "summary": "Dashboard de uso por instância (usuários, storage, transações).",
    "version": "18.0.1.0.0",
    "author": "GlobalMedia",
    "license": "Other OSI approved licence",
    "depends": ["plan_limits", "account"],
    "data": [
        "views/monitoring_views.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
}