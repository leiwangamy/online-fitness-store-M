# core/admin_actions.py
import csv
from django.http import HttpResponse

def export_selected_as_csv(modeladmin, request, queryset):
    """
    Generic CSV export for ANY model in Django admin.
    Exports model fields (basic columns).
    """
    model = modeladmin.model
    opts = model._meta

    field_names = [f.name for f in opts.fields]  # basic DB fields only

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{opts.model_name}.csv"'

    writer = csv.writer(response)
    writer.writerow(field_names)

    for obj in queryset:
        row = []
        for name in field_names:
            val = getattr(obj, name)
            row.append(str(val) if val is not None else "")
        writer.writerow(row)

    return response

export_selected_as_csv.short_description = "Export selected rows to CSV"
