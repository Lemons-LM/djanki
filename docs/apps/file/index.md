# File App

The file app currently provides a minimal metadata model so file permissions have the
correct owner. Upload, storage and download endpoints are not implemented yet.

## Model

`file.File` stores:

- `title`, `namespace` (default 6), `storage_key`, `original_name`, `mime_type`
- `size`, `sha1`, `uploaded_by`, `is_deleted`, `created_at`

`Meta.permissions` adds `upload_file` and `move_file`; Django provides the built-in
`delete_file` and `view_file` permissions.

## Scope

- Upload/storage backends: future work.
- Moving a file between titles: future work; `move_file` permission already exists.
- The model is intentionally independent of the core revision model for now. A later
  design can add file revisions or slots if required.
