from accounts.models import User
from django.core.management.base import BaseCommand

# https://qiita.com/ekzemplaro/items/e97bf9aa778bfddd4cec


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        for user in User.objects.all():
            print(user.id, "\t", end="")
            print(user.username, "\t", end="")
            print(user.email)
