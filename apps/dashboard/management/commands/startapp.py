import os
from django.core.management.commands.startapp import Command as BaseCommand


class Command(BaseCommand):
    help = 'Creates a Django app directory inside apps/ with the correct dotted name.'

    def handle(self, **options):
        app_name = options['name']

        if options.get('directory') is None:
            target = os.path.join(os.getcwd(), 'apps', app_name)
            os.makedirs(target, exist_ok=True)
            options['directory'] = target

        super().handle(**options)

        apps_py = os.path.join(options['directory'], 'apps.py')
        if os.path.exists(apps_py):
            with open(apps_py, 'r') as f:
                content = f.read()
            content = content.replace(
                f"name = '{app_name}'",
                f"name = 'apps.{app_name}'",
            )
            with open(apps_py, 'w') as f:
                f.write(content)
