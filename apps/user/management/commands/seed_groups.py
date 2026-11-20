"""Management command for seeding standard groups."""

from django.core.management.base import BaseCommand

from apps.user.groups import seed_groups


class Command(BaseCommand):
    """Create or update the standard wiki groups."""

    help = "Create or update the standard wiki groups and their permissions."

    def handle(self, *args, **options):
        """Run the idempotent group seeder."""
        result = seed_groups(verbosity=options.get("verbosity", 0))
        for name, count in sorted(result.items()):
            self.stdout.write(f"{name}: {count} permissions")
