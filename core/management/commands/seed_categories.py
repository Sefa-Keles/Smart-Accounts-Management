from django.core.management.base import BaseCommand

from core.models import Category


class Command(BaseCommand):
    help = "Seed default system categories"

    DEFAULT_CATEGORIES = [
        "Food",
        "Transportation",
        "Office Supplies",
        "Travel",
        "Utilities",
        "Rent",
        "Salary",
        "Freelance",
        "Health",
        "Education",
        "Entertainment",
        "Other",
    ]

    def handle(self, *args, **options):
        created_count = 0

        for category_name in self.DEFAULT_CATEGORIES:
            _, created = Category.objects.get_or_create(
                name=category_name,
                defaults={"is_system": True, "user": None},
            )
            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"System categories ready. Created {created_count} new category(ies)."
            )
        )
