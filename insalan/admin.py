# Covering django.contrib.admin.AdminSite.get_app_list
from django.contrib import admin

ADMIN_ORDERING = []

# Creating a sort function
def get_app_list(self, request, app_label=None):
    app_dict = self._build_app_dict(request, app_label)

    ordering = []
    # For each app in the app list
    for app_name, app_data in app_dict.items():
        # If app_name is not in ADMIN_ORDERING
        if app_name not in [x[0] for x in ADMIN_ORDERING]:
            # Add basic ordering
            ordering.append((app_name, [x['object_name'] for x in app_data['models']]))
    ordering += ADMIN_ORDERING

    app_list = []
    # For each app in the Ordering list
    for app_name, object_list in ordering:
        if app_name not in app_dict:
            continue
        app = app_dict[app_name]
        # Sort the models
        app['models'].sort(key=lambda x, object_list=object_list: object_list.index(x['object_name']))
        app_list.append(app)

    return app_list

admin.AdminSite.get_app_list = get_app_list
