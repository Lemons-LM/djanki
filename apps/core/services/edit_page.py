from apps.core.models.page import Page


def edit_page(*, type, target_page: Page, author: 'User', content_data: str, edit_comment: str = ''):
    #TODO: Add permission check
    #TODO: Add yes/no result
    if type == 'page':
        return target_page.new_rev(
            content_data=content_data,
            author=author,
            edit_comment=edit_comment
        )
    elif type == 'property':
        return target_page.new_prop_rev(
            content_data=content_data,
            author=author,
            edit_comment=edit_comment
        )