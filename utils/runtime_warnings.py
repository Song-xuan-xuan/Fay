import warnings


def suppress_pygame_pkg_resources_warning():
    warnings.filterwarnings(
        "ignore",
        message=r"pkg_resources is deprecated as an API\..*",
        category=UserWarning,
        module=r"pygame\.pkgdata",
    )
