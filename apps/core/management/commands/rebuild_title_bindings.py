"""Rebuild the title binding projection from current revisions."""

from django.core.management.base import BaseCommand

from apps.core.services.titles import rebuild_title_bindings


class Command(BaseCommand):
    """Reconcile TitleBinding rows with current page properties."""

    help = "Rebuild the title binding projection from current revisions."

    def add_arguments(self, parser):
        """Add a dry-run flag."""
        parser.add_argument(
            "--check",
            action="store_true",
            dest="check_only",
            help="Report differences without writing.",
        )

    def handle(self, *args, **options):
        """Run the rebuild and print the report."""
        report = rebuild_title_bindings(check_only=options["check_only"])
        self.stdout.write(
            "pages={pages_scanned} released={released} created={created} conflicts={conflicts}".format(
                **report.__dict__
            )
        )
