from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        max_length=200, unique=True, null=False, blank=False
    )
    slug = models.SlugField(unique=True, null=False, blank=False)
    description = models.TextField()

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(verbose_name='Текст')
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации', auto_now_add=True,
        db_index=True
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='posts',
        verbose_name='Автор'
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True, null=True,
        related_name='posts',
        verbose_name='Группа'
    )
    image = models.ImageField(upload_to='posts/', blank=True, null=True, verbose_name='Изображение')

    def __str__(self):
        return f'{self.author}:{self.text[:10]}:{self.pub_date.strftime("%d/%m/%Y")}'

    class Meta():
        ordering = ['-pub_date']


class Comment(models.Model):
    post = models.ForeignKey(Post, null=True, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created = models.DateTimeField(auto_now_add=True)


class Follow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='follower')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')

    class Meta():
        unique_together = ('user', 'author')
