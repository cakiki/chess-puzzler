ALL_TAGS = []
ALL_TAG_KINDS = []


def register(*tag_names):
    def decorator(fn):
        fn.tags = list(tag_names)
        ALL_TAGS.append(fn)
        ALL_TAG_KINDS.extend(tag_names)
        return fn

    return decorator
