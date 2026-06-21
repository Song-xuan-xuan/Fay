# -*- coding: utf-8 -*-
import os

FRONTEND_PUBLIC_ROUTE_PREFIX = "/frontend-static"
FRONTEND_PUBLIC_DIR_NAME = "frontend-static"


def resolve_vue_public_asset(project_root, filename):
    if not filename or os.path.isabs(filename):
        return None

    public_root = os.path.abspath(
        os.path.join(project_root, "fay-frontend", "dist", FRONTEND_PUBLIC_DIR_NAME)
    )
    target_path = os.path.abspath(os.path.join(public_root, filename))

    try:
        if os.path.commonpath([public_root, target_path]) != public_root:
            return None
    except ValueError:
        return None

    if not os.path.isfile(target_path):
        return None

    return target_path
