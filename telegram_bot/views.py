from django.shortcuts import render, get_object_or_404
from .models import ProcessedBatch


def view_batch(request, batch_id):
    # Get the batch by ID
    processed_batch = get_object_or_404(ProcessedBatch, batch_id=batch_id)

    # Get the associated files
    batch_details = processed_batch.batch_details.all()

    # Render the batch details to a template
    return render(request, 'batch_detail.html', {'batch': processed_batch, 'batch_details': batch_details})
