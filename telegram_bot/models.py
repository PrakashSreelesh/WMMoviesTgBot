from django.db import models


class ForwardedMediaLog(models.Model):
    chat_id = models.CharField(max_length=100)
    media_file_id = models.CharField(max_length=255)
    new_caption = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

#===============================================================================

class ProcessedBatch(models.Model):
    # BatchId is now an integer and it will be used as a foreign key reference
    batch_id = models.IntegerField(unique=True, null=False)
    movie_counter = models.IntegerField(null=False)
    movie_name = models.CharField(max_length=255, null=False)
    year = models.IntegerField(null=False)
    languages = models.CharField(max_length=255, null=False)
    quality = models.CharField(max_length=50, null=False)
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=False)
    batch_url = models.URLField(null=False)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Batch {self.batch_id}: {self.movie_name} ({self.year})"


class BatchDetail(models.Model):
    # Foreign Key reference to ProcessedBatch
    batch = models.ForeignKey(ProcessedBatch, related_name="batch_details", on_delete=models.CASCADE)
    file_id = models.CharField(max_length=255, null=False)
    file_type = models.CharField(max_length=50, choices=[('image', 'Image'), ('document', 'Document')], null=False)
    file_size = models.CharField(max_length=50, null=True)
    audio = models.CharField(max_length=255, null=True)
    file_quality = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return f"File {self.file_id} for Batch {self.batch.batch_id}"