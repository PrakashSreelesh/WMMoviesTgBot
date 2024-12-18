from rest_framework import serializers
from .models import ProcessedBatch, BatchDetail


class BatchDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = BatchDetail
        fields = ['id', 'batch', 'file_id', 'file_type',
                  'file_size', 'audio', 'file_quality']


class ProcessedBatchSerializer(serializers.ModelSerializer):
    batch_details = BatchDetailSerializer(many=True, read_only=True)

    class Meta:
        model = ProcessedBatch
        fields = ['id', 'batch_id', 'movie_counter', 'movie_name', 'year',
                  'languages', 'quality', 'rating', 'batch_url', 'batch_details']

    def create(self, validated_data):
        """Create ProcessedBatch and associated BatchDetails"""
        batch_details_data = validated_data.pop('batch_details', [])
        processed_batch = ProcessedBatch.objects.create(**validated_data)
        for detail_data in batch_details_data:
            BatchDetail.objects.create(batch=processed_batch, **detail_data)
        return processed_batch

    def update(self, instance, validated_data):
        """Update ProcessedBatch and associated BatchDetails"""
        batch_details_data = validated_data.pop('batch_details', [])
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update BatchDetails
        for detail_data in batch_details_data:
            detail_id = detail_data.get('id')
            if detail_id:
                # Update existing details
                detail_instance = BatchDetail.objects.get(id=detail_id)
                for attr, value in detail_data.items():
                    setattr(detail_instance, attr, value)
                detail_instance.save()
            else:
                # Create new details
                BatchDetail.objects.create(batch=instance, **detail_data)
        return instance
