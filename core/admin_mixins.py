# core/admin_mixins.py
from .admin_actions import export_csv_action

class ExportCsvMixin:
    csv_fields = []

    def get_actions(self, request):
        actions = super().get_actions(request)
        if self.csv_fields:
            action = export_csv_action(self.csv_fields)
            actions["export_csv"] = (
                action,
                "export_csv",
                action.short_description,
            )
        return actions
