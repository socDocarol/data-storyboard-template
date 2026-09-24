"""Public ArcGIS Hub, FeatureServer and MapServer table/layer downloads."""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urlsplit

from .common import SourceError, row_limit
from .http import JsonClient, validate_url


def _get(client, url, **params):
    # Query is read-only. Form POST avoids URL length limits on object ID batches.
    result = client.get(url, {"f": "json", **params}, post=url.endswith("/query"))
    if not isinstance(result, dict) or "error" in result:
        raise SourceError(
            "ArcGIS could not serve this request. Check the public layer, fields, and where clause."
        )
    return result


def resolve_layer(url: str, client: JsonClient, layer_id: int | None = None) -> str:
    parts = validate_url(url)
    if re.search(r"/(FeatureServer|MapServer)/\d+/?$", parts.path, re.I):
        return url.split("?")[0].rstrip("/")
    if re.search(r"/(FeatureServer|MapServer)/?$", parts.path, re.I):
        service = url.split("?")[0].rstrip("/")
    else:
        match = re.search(r"/datasets/([a-f0-9]{32})(?:_(\d+))?", parts.path, re.I)
        item_id = match[1] if match else parse_qs(parts.query).get("id", [""])[0]
        if not re.fullmatch(r"[a-f0-9]{32}", item_id, re.I):
            raise SourceError(
                "Use an ArcGIS Hub dataset URL, ArcGIS item URL, or a FeatureServer/MapServer layer URL."
            )
        if match and match[2] is not None and layer_id is None:
            layer_id = int(match[2])
        item = _get(
            client, f"https://www.arcgis.com/sharing/rest/content/items/{item_id}"
        )
        service = item.get("url", "")
        validate_url(service)
        if re.search(
            r"/(FeatureServer|MapServer)/\d+/?$", urlsplit(service).path, re.I
        ):
            return service.rstrip("/")
        if not re.search(
            r"/(FeatureServer|MapServer)/?$", urlsplit(service).path, re.I
        ):
            raise SourceError(
                "This ArcGIS item is not a queryable feature/table service. Choose its published data layer or a CSV/XLSX download."
            )
        service = service.rstrip("/")
    if layer_id is not None:
        if type(layer_id) is not int or layer_id < 0:
            raise SourceError("layer_id must be a nonnegative layer number.")
        return f"{service}/{layer_id}"
    info = _get(client, service)
    layers = info.get("layers", []) + info.get("tables", [])
    if len(layers) != 1:
        raise SourceError(
            "This service has multiple layers or tables. Inspect it and choose layer_id."
        )
    return f"{service}/{layers[0]['id']}"


def inspect_layer(config: dict) -> dict:
    client = JsonClient()
    layer = resolve_layer(config.get("url", ""), client, config.get("layer_id"))
    info = _get(client, layer)
    return {
        "url": layer,
        "name": info.get("name"),
        "description": info.get("description"),
        "fields": info.get("fields", []),
        "maxRecordCount": info.get("maxRecordCount"),
        "dateFieldsTimeReference": info.get("dateFieldsTimeReference"),
        "editingInfo": info.get("editingInfo"),
    }


def read_rows(config: dict) -> list[dict]:
    client = JsonClient()
    layer = resolve_layer(config.get("url", ""), client, config.get("layer_id"))
    info = _get(client, layer)
    fields = {field["name"]: field for field in info.get("fields", [])}
    columns = {column for column in config["columns"].values() if column is not None}
    if not columns <= fields.keys():
        raise SourceError(
            "The ArcGIS layer is missing a mapped field. Inspect the layer and update columns."
        )
    oid = info.get("objectIdField") or next(
        (name for name, field in fields.items() if field["type"] == "esriFieldTypeOID"),
        None,
    )
    if not oid:
        raise SourceError("This layer has no object ID field for complete downloads.")
    if info.get("datesInUnknownTimezone"):
        raise SourceError(
            "This layer's date timezone is unknown. Confirm its date meaning before connecting."
        )
    where = config.get("where", "1=1")
    if not isinstance(where, str) or not where.strip():
        raise SourceError("where must be a nonempty ArcGIS filter.")
    query = layer + "/query"
    count = _get(client, query, where=where, returnCountOnly="true").get("count")
    if type(count) is not int or count < 0:
        raise SourceError("ArcGIS did not return a valid row count.")
    if count > row_limit(config):
        raise SourceError(
            "The ArcGIS query exceeds max_rows. Narrow its date range or where clause."
        )
    response = _get(client, query, where=where, returnIdsOnly="true")
    ids = response.get("objectIds") or []
    if (
        not isinstance(ids, list)
        or any(type(item) is not int for item in ids)
        or len(set(ids)) != len(ids)
        or response.get("exceededTransferLimit")
    ):
        raise SourceError("ArcGIS did not return a complete unique ID list.")
    if len(ids) != count:
        raise SourceError(
            "The source changed during the download. Retry to obtain a consistent snapshot."
        )
    size = min(500, info.get("maxRecordCount", 500))
    if type(size) is not int or size < 1:
        raise SourceError("ArcGIS reported an invalid transfer limit.")
    rows = []
    for offset in range(0, len(ids), size):
        wanted = set(ids[offset : offset + size])
        page = _get(
            client,
            query,
            objectIds=",".join(map(str, sorted(wanted))),
            outFields=",".join(sorted(columns | {oid})),
            returnGeometry="false",
        )
        features = page.get("features")
        if page.get("exceededTransferLimit") or not isinstance(features, list):
            raise SourceError(
                "ArcGIS returned an incomplete page. No partial totals were loaded."
            )
        attributes = [feature.get("attributes", {}) for feature in features]
        if (
            len(attributes) != len(wanted)
            or {row.get(oid) for row in attributes} != wanted
        ):
            raise SourceError(
                "ArcGIS omitted or repeated requested records. Retry the download."
            )
        # Decode coded-value domains for grouping labels; numeric measures stay numeric.
        for row in attributes:
            for dimension in ("category", "area", "status"):
                column = config["columns"][dimension]
                domain = fields.get(column, {}).get("domain") or {}
                codes = {
                    entry["code"]: entry["name"]
                    for entry in domain.get("codedValues", [])
                }
                if column and row.get(column) in codes:
                    row[column] = codes[row[column]]
        rows.extend(attributes)
    return rows
