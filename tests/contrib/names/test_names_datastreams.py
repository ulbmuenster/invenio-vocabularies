# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2024 CERN.
#
# Invenio-Vocabularies is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Names data streams tests."""

from copy import deepcopy
from unittest.mock import patch

import pytest
from invenio_access.permissions import system_identity
from invenio_records_resources.proxies import current_service_registry

from invenio_vocabularies.contrib.names.api import Name
from invenio_vocabularies.contrib.names.datastreams import (
    NamesServiceWriter,
    OrcidHTTPReader,
    OrcidTransformer,
)
from invenio_vocabularies.datastreams import StreamEntry
from invenio_vocabularies.datastreams.errors import TransformerError, WriterError


@pytest.fixture(scope="function")
def name_full_data():
    """Full name data."""
    return {
        "id": "0000-0001-8135-3489",
        "given_name": "Lars Holm",
        "family_name": "Nielsen",
        "name": "Nielsen, Lars Holm",
        "identifiers": [
            {
                "scheme": "orcid",
                "identifier": "0000-0001-8135-3489",  # normalized after create
            }
        ],
        "affiliations": [{"name": "CERN"}],
    }


@pytest.fixture(scope="module")
def expected_from_xml():
    return {
        "id": "0000-0001-8135-3489",
        "given_name": "Lars Holm",
        "family_name": "Nielsen",
        "identifiers": [{"scheme": "orcid", "identifier": "0000-0001-8135-3489"}],
        "affiliations": [{"name": "CERN"}],
    }


XML_ENTRY_DATA = bytes(
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<record:record path="/0000-0001-8135-3489">\n'
    "    <common:orcid-identifier>\n"
    "        <common:uri>https://orcid.org/0000-0001-8135-3489</common:uri>\n"  # noqa
    "        <common:path>0000-0001-8135-3489</common:path>\n"
    "        <common:host>orcid.org</common:host>\n"
    "    </common:orcid-identifier>\n"
    '    <person:person path="/0000-0001-8135-3489/person">\n'
    '        <person:name visibility="public" path="0000-0001-8135-3489">\n'  # noqa
    "            <personal-details:given-names>Lars Holm</personal-details:given-names>"  # noqa
    "            <personal-details:family-name>Nielsen</personal-details:family-name>\n"  # noqa
    "        </person:name>\n"
    '        <external-identifier:external-identifiers path="/0000-0001-8135-3489/external-identifiers"/>\n'  # noqa
    "    </person:person>\n"
    '    <activities:activities-summary path="/0000-0001-8135-3489/activities">\n'  # noqa
    '       <activities:employments path="/0000-0001-8135-3489/employments">\n'  # noqa
    "           <employments:affiliation-group>\n"
    "               <employments:employment-summary>\n"
    "                   <employment-summary:organization>\n"
    "                       <organization:name>CERN</organization:name>\n"
    "                   </employment-summary:organization>\n"
    "               </employments:employment-summary>\n"
    "           </employments:affiliation-group>\n"
    "       </activities:employments>\n"
    "    </activities:activities-summary>\n"
    "</record:record>\n",
    encoding="raw_unicode_escape",
)


@pytest.fixture(scope="function")
def bytes_xml_data():
    # simplified version of an XML file of the ORCiD dump
    return XML_ENTRY_DATA


NAMES_TEST = {
    "Lars Holm, Nielsen": True,
    "Lars Nielsen:)": False,
    "Lars Nielsen-H": True,
    "Lars Nielsen 👍": False,
    "Lars Nielsen (CERN)": True,
}


@pytest.fixture(scope="function")
def dict_xml_entry():
    return StreamEntry(
        {
            "orcid-identifier": {
                "uri": "https://orcid.org/0000-0001-8135-3489",
                "path": "0000-0001-8135-3489",
                "host": "orcid.org",
            },
            "person": {
                "name": {
                    "given-names": "Lars Holm",
                    "family-name": "Nielsen",
                    "@visibility": "public",
                    "@path": "0000-0001-8135-3489",
                },
                "external-identifiers": {
                    "@path": "/0000-0001-8135-3489/external-identifiers"
                },
                "@path": "/0000-0001-8135-3489/person",
            },
            "activities-summary": {
                "employments": {
                    "affiliation-group": {
                        "employment-summary": {"organization": {"name": "CERN"}}
                    },
                    "@path": "/0000-0001-8135-3489/employments",
                },
                "@path": "/0000-0001-8135-3489/activities",
            },
            "@path": "/0000-0001-8135-3489",
        }
    )


def test_orcid_transformer(dict_xml_entry, expected_from_xml):
    transformer = OrcidTransformer()
    assert expected_from_xml == transformer.apply(dict_xml_entry).entry


@pytest.mark.parametrize("name,is_valid_name", NAMES_TEST.items())
def test_orcid_transformer_different_names(dict_xml_entry, name, is_valid_name):
    transformer = OrcidTransformer()
    val = deepcopy(dict_xml_entry)
    if is_valid_name:
        assert transformer.apply(val).entry
    else:
        with pytest.raises(TransformerError):
            val.entry["person"]["name"]["given-names"] = name
            val.entry["person"]["name"]["family-name"] = ""
            transformer.apply(val)
        with pytest.raises(TransformerError):
            val.entry["person"]["name"]["given-names"] = ""
            val.entry["person"]["name"]["family-name"] = name
            transformer.apply(val)


@pytest.mark.parametrize("name", NAMES_TEST.keys())
def test_orcid_transformer_different_names_no_regex(dict_xml_entry, name):
    transformer = OrcidTransformer(names_exclude_regex=None)
    val = deepcopy(dict_xml_entry)
    val.entry["person"]["name"]["given-names"] = name
    val.entry["person"]["name"]["family-name"] = ""
    assert transformer.apply(val).entry


class MockResponse:
    content = XML_ENTRY_DATA
    status_code = 200


@patch("requests.get", side_effect=lambda url, headers: MockResponse())
def test_orcid_http_reader(_, bytes_xml_data):
    reader = OrcidHTTPReader(id="0000-0001-8135-3489")
    results = []
    for entry in reader.read():
        results.append(entry)

    assert len(results) == 1
    assert bytes_xml_data == results[0]


def test_names_service_writer_create(app, db, search_clear, name_full_data):
    writer = NamesServiceWriter()
    record = writer.write(StreamEntry(name_full_data))
    record = record.entry.to_dict()

    assert dict(record, **name_full_data) == record


def test_names_service_writer_duplicate(app, db, search_clear, name_full_data):
    writer = NamesServiceWriter()
    _ = writer.write(stream_entry=StreamEntry(name_full_data))
    Name.index.refresh()  # refresh index to make changes live
    with pytest.raises(WriterError) as err:
        writer.write(stream_entry=StreamEntry(name_full_data))

    expected_error = [f"Vocabulary entry already exists: {name_full_data}"]
    assert expected_error in err.value.args


def test_names_service_writer_update_existing(app, db, search_clear, name_full_data):
    # create vocabulary
    writer = NamesServiceWriter(update=True)
    name = writer.write(stream_entry=StreamEntry(name_full_data))
    Name.index.refresh()  # refresh index to make changes live
    # update vocabulary
    updated_name = deepcopy(name_full_data)
    updated_name["given_name"] = "Pablo"
    updated_name["family_name"] = "Panero"
    updated_name["name"] = "Panero, Pablo"
    # check changes vocabulary
    _ = writer.write(stream_entry=StreamEntry(updated_name))
    service = current_service_registry.get("names")
    record = service.read(system_identity, name.entry.id)
    record = record.to_dict()

    # needed while the writer resolves from ES
    assert _.entry.id == name.entry.id
    assert dict(record, **updated_name) == record


def test_names_service_writer_update_non_existing(
    app, db, search_clear, name_full_data
):
    # vocabulary item not created, call update directly
    updated_name = deepcopy(name_full_data)
    updated_name
    updated_name["given_name"] = "Pablo"
    updated_name["family_name"] = "Panero"
    updated_name["name"] = "Panero, Pablo"
    # check changes vocabulary
    writer = NamesServiceWriter(update=True)
    name = writer.write(stream_entry=StreamEntry(updated_name))
    service = current_service_registry.get("names")
    record = service.read(system_identity, name.entry.id)
    record = record.to_dict()

    assert dict(record, **updated_name) == record
