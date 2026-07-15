# -*- coding: utf-8 -*-

from flask import Blueprint, Response, jsonify, request
import requests


MCP_SERVICE_BASE_URL = "http://127.0.0.1:5010"
MCP_PROXY_TIMEOUT_SECONDS = 95
PROXY_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")
FORWARDED_REQUEST_HEADERS = (
    "Accept",
    "Authorization",
    "Content-Type",
    "Cookie",
)
FORWARDED_RESPONSE_HEADERS = (
    "Cache-Control",
    "Content-Disposition",
    "Content-Type",
)


def _send_upstream_request(*, method, url, query_string, body, headers):
    if query_string:
        url = f"{url}?{query_string.decode('latin-1')}"
    return requests.request(
        method=method,
        url=url,
        data=body,
        headers=headers,
        timeout=MCP_PROXY_TIMEOUT_SECONDS,
        allow_redirects=False,
    )


def _request_headers():
    return {
        name: request.headers[name]
        for name in FORWARDED_REQUEST_HEADERS
        if name in request.headers
    }


def _upstream_response(response):
    headers = {
        name: response.headers[name]
        for name in FORWARDED_RESPONSE_HEADERS
        if name in response.headers
    }
    return Response(response.content, status=response.status_code, headers=headers)


def register_mcp_proxy(
    app,
    *,
    target=MCP_SERVICE_BASE_URL,
    request_sender=_send_upstream_request,
):
    blueprint = Blueprint("mcp_management_proxy", __name__)

    @blueprint.route(
        "/api/mcp",
        defaults={"subpath": ""},
        methods=PROXY_METHODS,
    )
    @blueprint.route("/api/mcp/<path:subpath>", methods=PROXY_METHODS)
    def proxy_mcp_request(subpath):
        suffix = f"/{subpath}" if subpath else ""
        try:
            response = request_sender(
                method=request.method,
                url=f"{target}/api/mcp{suffix}",
                query_string=request.query_string,
                body=request.get_data(),
                headers=_request_headers(),
            )
        except (requests.RequestException, ConnectionError):
            return jsonify({"error": "MCP 管理服务不可用"}), 502
        return _upstream_response(response)

    app.register_blueprint(blueprint)

