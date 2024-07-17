# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2021 CERN.
# Copyright (C) 2024 Uni Münster.
#
# Invenio-Vocabularies is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Vocabularies admin interface."""
from functools import partial

from flask import current_app, url_for
from invenio_administration.views.base import AdminResourceListView, AdminResourceEditView
from invenio_search_ui.searchconfig import FacetsConfig, SortConfig, search_app_config
from invenio_i18n import lazy_gettext as _


class VocabulariesListView(AdminResourceListView):
    """Configuration for vocabularies list view."""

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
    """Configuration for vocabularies list view."""

    def get_api_endpoint(self, pid_value=None):
        """Overwrite get_api_endpoint to accept pid_value."""
        if pid_value in current_app.config.get(
            "VOCABULARIES_CUSTOM_VOCABULARY_TYPES", []
        ):
            return f"/api/{pid_value}"
        else:
            return f"/api/vocabularies/{pid_value}"

    def init_search_config(self, **kwargs):
        """Build search view config."""
        pid_value = kwargs.get("pid_value", "")
        custom_search_config = current_app.config[self.search_config_name].get(
            pid_value
        )

        if custom_search_config:
            available_sort_options = current_app.config[self.search_sort_config_name]
            available_facets = current_app.config.get(self.search_facets_config_name)

            return partial(
                search_app_config,
                config_name=self.get_search_app_name(**kwargs),
                available_facets=available_facets,
                sort_options=available_sort_options,
                endpoint=self.get_api_endpoint(**kwargs),
                headers=self.get_search_request_headers(**kwargs),
                sort=SortConfig(
                    available_sort_options,
                    custom_search_config["sort"],
                    custom_search_config["sort_default"],
                    custom_search_config["sort_default_no_query"],
                ),
                facets=FacetsConfig(available_facets, custom_search_config["facets"]),
            )
        else:
            return super().init_search_config(**kwargs)

    def get(self, **kwargs):
        """GET view method."""
        parent_context = super().get_context(**kwargs)

        pid_value = kwargs.get("pid_value", "")
        vocab_admin_cfg = current_app.config["VOCABULARIES_ADMINISTRATION_CONFIG"]

        custom_config = vocab_admin_cfg.get(pid_value)

        if custom_config:
            parent_context.update(custom_config)
        else:
            parent_context.update(
                {"title": f"{pid_value.capitalize()} vocabulary items"}
            )

        return self.render(**parent_context)

    name = "vocabulary-type-items"
    url = "/vocabulary-types/<pid_value>"

    # INFO name of the resource's list view name, enables navigation between items view and types view.
    list_view_name = "vocabulary-types"

    resource_config = "vocabulary_admin_resource"
    search_request_headers = {"Accept": "application/json"}

    pid_path = "id"
    resource_name = "title['en']"

    # INFO only if disabled() (as a function) it's not in the sidebar, see https://github.com/inveniosoftware/invenio-administration/blob/main/invenio_administration/menu/menu.py#L54
    disabled = lambda _: True

    template = "invenio_administration/search.html"

    display_delete = False
    display_create = False
    display_edit = True
    display_search = True

    # TODO: It would ne nicer to use the title's translation in the currently selected language and fall back to English if this doesn't exist
    item_field_list = {
        "title['en']": {"text": "Title [en]", "order": 0},
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

    # def get(self, **kwargs):
    #     """GET view method."""
    #     schema = self.get_service_schema()
    #     serialized_schema = self._schema_to_json(schema)
    #     form_fields = self.form_fields
    #     return self.render(
    #         **{
    #             "resource_schema": serialized_schema,
    #             "form_fields": form_fields,
    #             "pid": kwargs.get("pid_value"),
    #             "api_endpoint": self.get_api_endpoint(),
    #             "title": self.title,
    #             "list_endpoint": self.get_list_view_endpoint(),
    #             "ui_config": self.form_fields,
    #         }
    #     )

    def get_list_view_endpoint(self, **kwargs):
        """Returns administration UI list view endpoint."""
        # if self.list_view_name:
        #     return url_for(f"administration.{self.list_view_name}")
        # if isinstance(self, AdminResourceListView):
        #     return url_for(f"administration.{self.name}")
        pid_value = kwargs.get("pid_value", "")
        vocab_type = kwargs.get("vocab_type", "")

        return f"/vocabularies/{vocab_type}/"

    # def _get_view_url(self, url):
    #     """Generate URL for the view. Override to change default behavior."""
    #     new_url = url
    #     if new_url is None:
    #         if isinstance(self, self.administration.dashboard_view_class):
    #             new_url = "/"
    #         else:
    #             new_url = "/%s" % self.name.lower()
    #     else:
    #         if not url.startswith("/"):
    #             new_url = "/%s" % (url)
    #     # Sanitize url
    #     new_url = new_url.replace(" ", "_")
    #
    #     return new_url

    name = "vocabularies_details_edit"
    url = "/vocabulary-types/names/<pid_value>/edit"
    resource_config = "vocabulary_admin_resource"
    pid_path = "id"
    title = "Edit vocabulary item"
    api_endpoint = "/vocabulary-types/<vocab_type>/<pid_value>"
    list_view_name = "vocabulary-type-items"

    form_fields = {
        "ID": {
            "order": 1,
            "text": "Set ID",
            "description": _("Some ID."),
        },
        "created": {"order": 2},
        "updated": {"order": 3},
    }
