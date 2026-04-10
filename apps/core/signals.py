from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.core.models.page_title import PageTitleIndex
from apps.core.models.prop_revision import PropRevision


@receiver(post_save, sender=PropRevision)
def sync_global_unique_title_index(sender, instance, created, **kwargs):
    if not created:
        return

    page = instance.page
    new_titles_set = {t for t in (instance.titles or []) if t}

    with transaction.atomic():
        current_owned_titles = PageTitleIndex.objects.filter(page=page).values_list('title', flat=True)
        titles_to_release = set(current_owned_titles) - new_titles_set

        if titles_to_release:
            PageTitleIndex.objects.filter(page=page, title__in=titles_to_release).delete()

        for title in new_titles_set:
            try:
                if PageTitleIndex.objects.filter(page=page, title=title).exists():
                    existing_index = PageTitleIndex.objects.get(page=page, title=title)
                    old_page = existing_index.page

                    if old_page != page:
                        current_prop_rev = old_page.current_property_revision
                        if current_prop_rev:
                            old_titles = set(current_prop_rev.titles or [])
                            old_titles.discard(title)

                            old_page.new_prop_rev(
                                content=current_prop_rev.content,
                                titles=list(old_titles),
                                author=instance.author,
                                edit_comment=instance.comment
                            )
                        else:
                            old_page.new_prop_rev(
                                content=None,
                                titles=None,
                                author=instance.author,
                                edit_comment=instance.comment
                            )
                        existing_index.page = page
                        existing_index.save(update_fields=['page'])
                    continue
                PageTitleIndex.objects.create(page=page, title=title)
            except PageTitleIndex.DoesNotExist:
                PageTitleIndex.objects.create(page=page, title=title)