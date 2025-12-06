from django.db import models


class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='product_images/')
    alt_text = models.CharField(max_length=255, blank=True)
    display_order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.product.name} - Image {self.id}"


class ProductVideo(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='videos'
    )
    title = models.CharField(max_length=200, blank=True)

    # Option 1: upload your own video file
    video_file = models.FileField(
        upload_to='product_videos/',
        blank=True,
        null=True
    )

    # Option 2: external video link (YouTube, etc.)
    video_url = models.URLField(
        blank=True,
        null=True
    )

    display_order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.product.name} - Video {self.title or self.id}"


class ProductAudio(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='audios'
    )
    title = models.CharField(max_length=200, blank=True)

    # Option 1: upload audio file
    audio_file = models.FileField(
        upload_to='product_audio/',
        blank=True,
        null=True
    )

    # Option 2: external audio link
    audio_url = models.URLField(
        blank=True,
        null=True
    )

    display_order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.product.name} - Audio {self.title or self.id}"
