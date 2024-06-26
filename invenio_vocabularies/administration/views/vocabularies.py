# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2021 CERN.
# Copyright (C) 2024 Uni Münster.
#
# Invenio-Vocabularies is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Vocabularies admin interface."""
from flask import current_app
from invenio_administration.views.base import (
    AdminResourceEditView,
    AdminResourceListView,
)
from invenio_i18n import lazy_gettext as _
from flask import current_app


class VocabulariesListView(AdminResourceListView):
    """Configuration for overview list view for vocabularies."""

    api_endpoint = "/vocabularies/"
    name = "vocabulary-types"
    menu_label = "Vocabulary Types"
    resource_config = "vocabulary_admin_resource"
    search_request_headers = {"Accept": "application/json"}
    title = "Vocabulary Types"
    category = "Site management"

    pid_path = "id"
    icon = "exchange"
    template = "invenio_administration/search.html"

    display_search = True
    display_delete = False
    display_edit = False
    display_create = False

    item_field_list = {
        "id": {"text": "Name", "order": 1},
        "count": {"text": "Number of entries", "order": 2},
    }

    search_config_name = "VOCABULARIES_TYPES_SEARCH"
    search_facets_config_name = "VOCABULARIES_TYPES_FACETS"
    search_sort_config_name = "VOCABULARIES_TYPES_SORT_OPTIONS"


class VocabularyDetailsListView(AdminResourceListView):
    """Configuration for list view for specific vocabulary types."""

    def get_api_endpoint(self, pid_value=None):
        """overwrite get_api_endpoint to accept pid_value"""

        if pid_value in current_app.config.get(
            "VOCABULARIES_CUSTOM_VOCABULARY_TYPES", []
        ):
            return f"/api/{pid_value}"
        else:
            return f"/api/vocabularies/{pid_value}"

    def get_context(self, **kwargs):
        """Create details view context."""
        search_conf = self.init_search_config(**kwargs)
        schema = self.get_service_schema()
        serialized_schema = self._schema_to_json(schema)
        pid_value = kwargs.get("pid_value", "")
        return {
            "search_config": search_conf,
            "title": f"{pid_value} vocabulary items",
            "name": self.name,
            "resource_schema": serialized_schema,
            "fields": self.item_field_list,
            "display_search": self.display_search,
            "display_create": self.display_create,
            "display_edit": self.display_edit,
            "display_delete": self.display_delete,
            "display_read": self.display_read,
            "actions": self.serialize_actions(),
            "pid_path": self.pid_path,
            "pid_value": pid_value,
            "create_ui_endpoint": self.get_create_view_endpoint(),
            "list_ui_endpoint": self.get_list_view_endpoint(),
            "resource_name": (
                self.resource_name if self.resource_name else self.pid_path
            ),
        }

    name = "vocabulary-type-items"
    url = "/vocabulary-types/<pid_value>"

    # INFO name of the resource's list view name, enables navigation between items view and types view.
    list_view_name = "vocabulary-types"

    resource_config = "vocabulary_admin_resource"
    search_request_headers = {"Accept": "application/json"}

    pid_path = "id"

    # INFO only if disabled() (as a function) it's not in the sidebar, see https://github.com/inveniosoftware/invenio-administration/blob/main/invenio_administration/menu/menu.py#L54
    disabled = lambda _: True

    template = "invenio_administration/search.html"

    display_delete = False
    display_create = False
    display_edit = True
    display_search = False

    item_field_list = {
        "id": {"text": "ID", "order": 0},
        "created": {"text": "Created", "order": 1},
    }

    search_config_name = "VOCABULARIES_TYPES_ITEMS_SEARCH"
    search_facets_config_name = "VOCABULARIES_TYPES_ITEMS_FACETS"
    search_sort_config_name = "VOCABULARIES_TYPES_ITEMS_SORT_OPTIONS"


class VocabularyTypesDetailsEditView(AdminResourceEditView):
    """WIP Configuration for vocabulary item edit view."""

    # Edit view for vocabulary items from a specific vocabulary type
    # def get_api_endpoint(vocab_type=None, pid=None):
    #     """overwrite get_api_endpoint to accept pid_value"""
    #     if vocab_type in current_app.config.get(
    #         "VOCABULARIES_CUSTOM_VOCABULARY_TYPES", []
    #     ):
    #         return f"/api/{vocab_type}"
    #     else:
    #         return f"/api/{vocab_type}/{pid}"

    def get(self, **kwargs):
        """GET view method."""
        schema = self.get_service_schema()
        serialized_schema = self._schema_to_json(schema)
        form_fields = self.form_fields
        return self.render(
            **{
                "resource_schema": serialized_schema,
                "form_fields": form_fields,
                "pid": kwargs.get("pid_value"),
                "api_endpoint": self.get_api_endpoint(),
                "title": self.title,
                "list_endpoint": self.get_list_view_endpoint(),
                "ui_config": self.form_fields,
            }
        )

    def _get_view_url(self, url):
        """Generate URL for the view. Override to change default behavior."""
        new_url = url
        if new_url is None:
            if isinstance(self, self.administration.dashboard_view_class):
                new_url = "/"
            else:
                new_url = "/%s" % self.name.lower()
        else:
            if not url.startswith("/"):
                new_url = "/%s" % (url)
        # Sanitize url
        new_url = new_url.replace(" ", "_")

        return new_url

    name = "vocabularies_details_edit"
    url = "/vocabulary-types/names/<pid_value>/edit"
    resource_config = "vocabulary_admin_resource"
    pid_path = "id"
    title = "Edit vocabulary item"
    api_endpoint = "/vocabulary-types/<vocab_type>/<pid_value>"
    list_view_name = "vocabulary-type-items"

    # form_fields = {
    #     "ID": {
    #         "order": 1,
    #         "text": "Set ID",
    #         "description": _("Some ID."),
    #     },
    #     "created": {"order": 2},
    #     "updated": {"order": 3},
    # }
