This is the Project's Architech on Django Apps Documentation.

For all the Project's Architech Documentation, please go to the [Architect Doc Index](index.md).

For all the documentation, please go to the [All Doc Index](../index.md).

For the App Documentation, please go to the [Apps Doc Index](../apps/index.md).

WARNING: If you write a code, you MUST write arch in the specific doc file in the [docs folder](..), and doc string on the function!!!

## Apps
The project has the apps following:
- [api](../../apps/api) \([doc](../apps/api/index.md)\): For API related functions. (REST API, MediaWiki API compatibility layer)
- [core](../../apps/core) \([doc](../apps/core/index.md)\): Page storage, revisions, slots, titles, redirects, structured protection, permissions and routing services.
- [extension](../../apps/extension) \([doc](../apps/extension/index.md)\): For Extension related functions. (Extension, Hooks)
- [file](../../apps/file) \([doc](../apps/file/index.md)\): For File metadata, storage and upload. Currently only the metadata model and permissions exist.
- [parser](../../apps/parser) \([doc](../apps/parser/index.md)\): For Djanki Parser
- [property](../../apps/property) \([doc](../apps/property/index.md)\): Category binding projection derived from the core properties slot, plus rebuild services.
- [search](../../apps/search) \([doc](../apps/search/index.md)\): For Search related functions.
- [special](../../apps/special) \([doc](../apps/special/index.md)\): For Special Page related functions. Like managing the wiki(Special Pages)
- [user](../../apps/user) \([doc](../apps/user/index.md)\): Users, groups, permissions, block history, login/logout.
- [webui](../../apps/webui) \([doc](../apps/webui/index.md)\): For Web UI related functions. Presenting the page to users visiting via web browsers.

## Architecture decisions

See the [ADR index](decisions/index.md) for the unified revision model, global revid,
title bindings, normalization, permission ownership, DRF API and migration reset.
