# coding: utf-8
from hapic.type import TYPE_SCHEMA


class SchemaUsage(object):
    def __init__(
        self,
        schema: TYPE_SCHEMA,
        plugin_helper_kwargs: dict = None,
        plugin_name_resolver_kwargs: dict = None,
    ) -> None:
        self.schema = schema
        self.plugin_helper_kwargs = plugin_helper_kwargs or {}
        self.plugin_name_resolver_kwargs = plugin_name_resolver_kwargs or {}

    def __hash__(self):
        return hash(
            (
                self.schema,
                frozenset(self.plugin_helper_kwargs),
                frozenset(self.plugin_name_resolver_kwargs),
            )
        )
