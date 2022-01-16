from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200, verbose_name='Имя группы')
    slug = models.SlugField(max_length=200, unique=True, verbose_name='URL')
    description = models.TextField(verbose_name='О сообществе')

    class Meta:
        verbose_name_plural = 'Группы'
        verbose_name = 'Группа'

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(verbose_name='Пост')
    pub_date = models.DateTimeField(auto_now_add=True,
                                    verbose_name='Дата публикации')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )
    group = models.ForeignKey(Group,
                              on_delete=models.SET_NULL,
                              blank=True,
                              null=True,
                              related_name='posts',
                              verbose_name='Группа')
    image = models.ImageField(
        upload_to='posts/',
        blank=True,
        verbose_name='Картинка'
    )

    class Meta:
        verbose_name_plural = 'Посты'
        verbose_name = 'Пост'
        ordering = ['-pub_date']

    def __str__(self):
        return self.text[:15]


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Пост')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор')
    text = models.TextField(verbose_name='Комментарий')
    created = models.DateTimeField(auto_now_add=True,
                                   verbose_name='Время комментария')

    class Meta:
        verbose_name_plural = 'Комментарии'
        verbose_name = 'Комментарий'
        ordering = ['created']

    def __str__(self):
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор на которого подписывается'
    )

    class Meta:
        verbose_name_plural = 'Подписки'
        verbose_name = 'Подписка'
