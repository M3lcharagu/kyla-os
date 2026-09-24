"""KYLA integrations package."""

# Auto-install extra wrappers (ruflo / agent-reach / cyber_skills)
def _kyla_install_extra_wrappers():
    try:
        from integrations import runtime as _rt
        from integrations.wrappers_extra import install as _install
        _install(_rt.WRAPPERS, _rt.print_header)
    except Exception:
        pass
_kyla_install_extra_wrappers()
