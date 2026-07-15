# -*- coding: utf-8 -*-
"""Vue history-mode route registration for the Flask web app."""

from collections.abc import Callable
from typing import Any

from flask import Flask


def register_vue_spa_routes(app: Flask, vue_entry: Callable[[], Any]) -> None:
    """Serve the Vue entry document for the authenticated `/app` route family."""

    @app.route("/app", defaults={"subpath": ""}, methods=["GET"])
    @app.route("/app/<path:subpath>", methods=["GET"])
    def vue_spa_entry(subpath: str):
        return vue_entry()
