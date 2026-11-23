"""Small multi-file application used by the ordinary guest project."""
def averages(series):
    """Yield one average for each nonempty sample group."""
    for group in series:
        if group:
            yield sum(group) / len(group)
