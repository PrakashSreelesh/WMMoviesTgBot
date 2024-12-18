# import re
# from telegram import Update
# from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
# from dotenv import load_dotenv
# import os
# import asyncio
# import json
# import time

# # Timer for detecting batch processing
# batch_processing_timeout = 3  # Time in seconds to consider the end of a batch
# last_file_processed_time = None  # To track the time of the last file processed
# movie_counter = 326  # Initialize starting value
# current_batch_id = None  # To store the batch ID for the current batch

# # ================================================================================================================================


# def load_movie_counter():
#     global movie_counter
#     counter_file_path = os.path.join("telegram_bot", "media", "counter.json")
#     if os.path.exists(counter_file_path):
#         with open(counter_file_path, "r") as counter_file:
#             data = json.load(counter_file)
#             movie_counter = data.get("movie_counter", 326)
#     else:
#         save_movie_counter()


# def save_movie_counter():
#     counter_file_path = os.path.join("telegram_bot", "media", "counter.json")
#     data = {"movie_counter": movie_counter}
#     with open(counter_file_path, "w") as counter_file:
#         json.dump(data, counter_file)


# async def handle_forwarded_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     global movie_counter, last_file_processed_time, current_batch_id

#     if update.message:
#         try:
#             load_movie_counter()
#             processed_files = load_processed_files()

#             # Generate batch_id only for the first file in the batch
#             if current_batch_id is None and update.message.photo:
#                 # Use timestamp as batch_id
#                 current_batch_id = str(int(time.time()))

#             file_info = {
#                 "file_id": None,
#                 "caption": None,
#                 "file_size": None,
#                 "processed_time": asyncio.get_event_loop().time()
#             }

#             if update.message.photo:
#                 file_name = update.message.caption or "Unknown File"
#                 movie_counter += 1
#                 transformed_caption = re.sub(
#                     r'★ ροωєяє∂ ϐγ : @Team_KL', f"© Movie#: {
#                         movie_counter}", file_name
#                 )

#                 await update.message.reply_photo(
#                     photo=update.message.photo[-1].file_id, caption=transformed_caption
#                 )

#                 file_info["file_id"] = update.message.photo[-1].file_id
#                 file_info["caption"] = transformed_caption
#                 file_info["file_size"] = "N/A"
#                 add_processed_file(current_batch_id, file_info)

#             elif update.message.document:
#                 document = update.message.document
#                 lan_pattern = r"Audio\s*[:\-\s]*([A-Za-z, ]+)"
#                 res_pattern = r"Quality\s*[:\-\s]*([\d]+p)"
#                 original_caption = update.message.caption or ""
#                 file_size = round(document.file_size / (1024 * 1024), 2)
#                 file_name = remove_bot_username(document.file_name)

#                 lan_match = re.search(lan_pattern, original_caption)
#                 languages = lan_match.group(1) if lan_match else ""
#                 res_match = re.search(res_pattern, original_caption)
#                 resolution = res_match.group(1) if res_match else ""

#                 transformed_caption = create_new_caption(
#                     file_name, file_size, languages, resolution
#                 )

#                 await update.message.reply_document(
#                     document=document.file_id, caption=transformed_caption, parse_mode="HTML"
#                 )

#                 file_info["file_id"] = document.file_id
#                 file_info["caption"] = file_name
#                 file_info["file_size"] = f"{file_size} MB"
#                 add_processed_file(current_batch_id, file_info)

#             backup_processed_files()
#             save_movie_counter()

#             # Update the last processed time
#             last_file_processed_time = asyncio.get_event_loop().time()
#             asyncio.create_task(schedule_batch_completion(update, context))

#         except Exception as e:
#             print(f"Error processing message: {e}")


# async def schedule_batch_completion(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     global last_file_processed_time, current_batch_id

#     await asyncio.sleep(batch_processing_timeout)  # Wait for the timeout
#     current_time = asyncio.get_event_loop().time()

#     # Check if no new file was processed during the timeout
#     if current_time - last_file_processed_time >= batch_processing_timeout and current_batch_id:
#         processed_files_url = f"https://t.me/{
#             context.bot.username}?start={current_batch_id}"

#         # Send the batch completion message with the URL
#         await update.message.reply_text(
#             f"Batch processing complete! View the list of processed files here: {
#                 processed_files_url}"
#         )

#         current_batch_id = None  # Reset the batch_id for the next batch


# async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     batch_id = update.message.text.split()[-1]
#     processed_files = load_backup_batchid(batch_id)

#     if processed_files:
#         for file_info in processed_files:
#             file_id = file_info['file_id']
#             caption = file_info['caption']
#             file_size = file_info['file_size']

#             if file_size == "N/A":
#                 await update.message.reply_photo(photo=file_id, caption=caption)
#             else:
#                 await update.message.reply_document(document=file_id, caption=caption)

#         sticker_path = os.path.join("telegram_bot/media", "end_sticker.webp")
#         with open(sticker_path, "rb") as sticker_file:
#             await update.message.reply_sticker(sticker_file)
#     else:
#         await update.message.reply_text(
#             "Welcome! Forward me a media file and I'll change its caption."
#         )


# def add_processed_file(batch_id, file_info):
#     processed_files = load_processed_files()
#     if processed_files["batch_id"] == 0:
#         processed_files = {"batch_id": batch_id, "files": []}
#     processed_files["files"].append(file_info)
#     save_processed_files(processed_files)


# def load_processed_files():
#     processed_file_path = os.path.join(
#         "telegram_bot", "media", "processed_files.json")
#     if os.path.exists(processed_file_path) and os.path.getsize(processed_file_path) > 0:
#         try:
#             with open(processed_file_path, "r") as processed_file:
#                 return json.load(processed_file)
#         except json.JSONDecodeError:
#             save_processed_files({"batch_id": 0, "files": []})
#     return {"batch_id": 0, "files": []}


# def save_processed_files(processed_files):
#     processed_file_path = os.path.join(
#         "telegram_bot", "media", "processed_files.json")
#     os.makedirs(os.path.dirname(processed_file_path), exist_ok=True)
#     with open(processed_file_path, "w") as processed_file:
#         json.dump(processed_files, processed_file)


# def backup_processed_files():
#     processed_file_path = os.path.join(
#         "telegram_bot", "media", "processed_files.json")
#     backup_file_path = os.path.join("telegram_bot", "media", "backup.json")
#     if os.path.exists(processed_file_path):
#         with open(processed_file_path, "r") as processed_file:
#             current_batch = json.load(processed_file)
#         if current_batch and "batch_id" in current_batch:
#             backup_data = load_backup_data()
#             if not any(batch.get("batch_id") == current_batch["batch_id"] for batch in backup_data):
#                 backup_data.append(current_batch)
#             with open(backup_file_path, "w") as backup_file:
#                 json.dump(backup_data, backup_file)


# def load_backup_data():
#     backup_file_path = os.path.join("telegram_bot", "media", "backup.json")
#     if os.path.exists(backup_file_path) and os.path.getsize(backup_file_path) > 0:
#         with open(backup_file_path, "r") as backup_file:
#             return json.load(backup_file)
#     return []


# def load_backup_batchid(batch_id):
#     backup_file_path = os.path.join("telegram_bot", "media", "backup.json")
#     if os.path.exists(backup_file_path) and os.path.getsize(backup_file_path) > 0:
#         with open(backup_file_path, "r") as backup_file:
#             backup_batch_data = json.load(backup_file)
#         for batch in backup_batch_data:
#             if batch["batch_id"] == batch_id:
#                 return batch["files"]


# def remove_bot_username(file_name):
#     return re.sub(r'@[\w_]+', '', file_name).strip()


# def create_new_caption(file_name, file_size, languages, resolution):
#     caption = f'<a href="https://t.me/WMBroadcastBot?start">[MM]</a>-{
#         file_name}'
#     if file_size >= 1024:
#         caption += f"\n\n📼 FileSize: {file_size / 1024:.2f} GB"
#     else:
#         caption += f"\n\n📼 FileSize: {file_size} MB"
#     caption += f"\n\n🔊 Audio: {languages}\n🎥 Quality: {resolution}"
#     return caption


# def configure_bot():
#     # Load environment variables
#     load_dotenv()

#     TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
#     if not TOKEN:
#         raise ValueError(
#             "Bot token not found. Please set TELEGRAM_BOT_TOKEN in the environment variables."
#         )

#     # Create the Application instance
#     application = Application.builder().token(TOKEN).build()

#     # Add command and message handlers
#     application.add_handler(CommandHandler("start", handle_start))
#     application.add_handler(MessageHandler(
#         (filters.Document.ALL | filters.PHOTO), handle_forwarded_media))
#     # application.add_handler(MessageHandler(
#     #     filters.FORWARDED & (filters.Document.ALL | filters.PHOTO), handle_forwarded_media))

#     return application


# # Register handlers
# bot = configure_bot()

# bot.run_polling()


# telegram_handler.py
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import os
import asyncio
import json
import time
from django.db.transaction import atomic
from django.db import transaction
from .models import ProcessedBatch, BatchDetail
from asgiref.sync import sync_to_async
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist

# Timer for detecting batch processing
batch_processing_timeout = 5  # Time in seconds to consider the end of a batch
last_file_processed_time = None  # To track the time of the last file processed
movie_counter = 326  # Initialize starting value
current_batch_id = None  # To store the batch ID for the current batch

# ================================================================================================================================


def load_movie_counter():
    global movie_counter
    counter_file_path = os.path.join("telegram_bot", "media", "counter.json")
    if os.path.exists(counter_file_path):
        with open(counter_file_path, "r") as counter_file:
            data = json.load(counter_file)
            movie_counter = data.get("movie_counter", 326)
    else:
        save_movie_counter()


def save_movie_counter():
    counter_file_path = os.path.join("telegram_bot", "media", "counter.json")
    data = {"movie_counter": movie_counter}
    with open(counter_file_path, "w") as counter_file:
        json.dump(data, counter_file)


# async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Handle the /start command."""
#     # Check if a batch ID is passed
#     args = context.args
#     if args:
#         batch_id = args[0]  # Extract batch ID from /start <batch_id>
#         # processed_files = load_processed_files()
#         processed_files = ProcessedBatch.objects.filter(batch_id=batch_id)

#         print("processed_files: ", processed_files)

#         if processed_files["batch_id"] == batch_id:
#             files = processed_files.get("files", [])
#             if files:
#                 # await update.message.reply_text(f"Listing files for Batch ID: {batch_id}")

#                 for file_info in files:
#                     file_id = file_info["file_id"]
#                     caption = file_info["caption"]
#                     file_size = file_info["file_size"]

#                     # Send each file
#                     if file_size == "N/A":  # Photo
#                         await update.message.reply_photo(photo=file_id, caption=caption)
#                     else:  # Document
#                         await update.message.reply_document(document=file_id, caption=caption)

#                 # Optionally, send a summary message
#                 await update.message.reply_text("All files for the batch have been listed.")
#             else:
#                 await update.message.reply_text("No files found for this batch.")
#         else:
#             await update.message.reply_text("Invalid Batch ID or Batch not found.")
#     else:
#         # Default welcome message
#         await update.message.reply_text(
#             "Welcome to the bot! Forward me a media file, and I'll process it for you."
#         )


# async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Handle the /start command."""
#     # Check if a batch ID is passed
#     args = context.args
#     if args:
#         batch_id = args[0]  # Extract batch ID from /start <batch_id>

#         try:
#             # Fetch the batch and related details asynchronously
#             processed_batch = await sync_to_async(ProcessedBatch.objects.get)(batch_id=batch_id)
#             batch_details = await sync_to_async(list)(processed_batch.batch_details.all())

#             if batch_details:
#                 await update.message.reply_text(f"Listing files for Batch ID: {batch_id}")

#                 # Loop through the BatchDetail entries and send each file
#                 for detail in batch_details:
#                     file_id = detail.file_id
#                     file_type = detail.file_type
#                     caption = f"Batch {batch_id} | {
#                         processed_batch.movie_name} ({processed_batch.year})"
#                     file_size = detail.file_size or "N/A"
#                     audio_info = f"Audio: {
#                         detail.audio}" if detail.audio else ""

#                     # Construct caption with optional details
#                     caption = f"{caption}\n{audio_info}\nQuality: {
#                         detail.file_quality or 'Unknown'}"

#                     # Send the appropriate file type
#                     if file_type == "image":
#                         await update.message.reply_photo(photo=file_id, caption=caption)
#                     elif file_type == "document":
#                         await update.message.reply_document(document=file_id, caption=caption)

#                 # Optionally, send a summary message
#                 await update.message.reply_text("All files for the batch have been listed.")
#             else:
#                 await update.message.reply_text("No files found for this batch.")
#         except ObjectDoesNotExist:
#             await update.message.reply_text("Invalid Batch ID or Batch not found.")
#     else:
#         # Default welcome message
#         await update.message.reply_text(
#             "Welcome to the bot! Forward me a media file, and I'll process it for you."
#         )


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command."""
    # Check if a batch ID is passed
    args = context.args
    if args:
        batch_id = args[0]  # Extract batch ID from /start <batch_id>

        try:
            # Fetch the batch and related details asynchronously
            processed_batch = await sync_to_async(ProcessedBatch.objects.get)(batch_id=batch_id)
            batch_details = await sync_to_async(list)(processed_batch.batch_details.all())

            if batch_details:
                # Separate the first image file from the rest
                image_file = None
                other_files = []

                for detail in batch_details:
                    if detail.file_type == "image" and image_file is None:
                        image_file = detail  # Assign the first image file
                    else:
                        other_files.append(detail)  # Collect all other files

                if image_file:
                    # Process the image file with caption first
                    caption = (
                        f"Batch {batch_id} | {
                            processed_batch.movie_name} ({processed_batch.year})\n"
                        f"Audio: {image_file.audio or 'N/A'}\n"
                        f"Quality: {image_file.file_quality or 'Unknown'}"
                    )
                    try:
                        await update.message.reply_photo(
                            photo=image_file.file_id, caption=caption
                        )
                    except Exception as e:
                        await update.message.reply_text(
                            f"Failed to send the image file: {e}"
                        )
                        return  # Stop processing further if the first image fails

                # Process the remaining files
                for detail in other_files:
                    file_id = detail.file_id
                    file_type = detail.file_type
                    caption = (
                        f"Batch {batch_id} | {
                            processed_batch.movie_name} ({processed_batch.year})\n"
                        f"Audio: {detail.audio or 'N/A'}\n"
                        f"Quality: {detail.file_quality or 'Unknown'}"
                    )

                    try:
                        if file_type == "image":
                            await update.message.reply_photo(photo=file_id, caption=caption)
                        elif file_type == "document":
                            await update.message.reply_document(document=file_id, caption=caption)
                    except Exception as e:
                        await update.message.reply_text(
                            f"Failed to send a file ({file_id}): {e}"
                        )
                        return  # Stop processing further if any file fails

                # Optionally, send a summary message
                await update.message.reply_text("All files for the batch have been listed successfully.")
            else:
                await update.message.reply_text("No files found for this batch.")
        except ObjectDoesNotExist:
            await update.message.reply_text("Invalid Batch ID or Batch not found.")
    else:
        # Default welcome message
        await update.message.reply_text(
            "Welcome to the bot! Forward me a media file, and I'll process it for you."
        )


# async def handle_forwarded_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     global movie_counter, last_file_processed_time, current_batch_id

#     if update.message:
#         try:
#             load_movie_counter()
#             processed_files = load_processed_files()

#             # Generate batch_id only for the first file in the batch
#             if current_batch_id is None and update.message.photo:
#                 # Use timestamp as batch_id
#                 current_batch_id = str(int(time.time()))

#             file_info = {
#                 "file_id": None,
#                 "caption": None,
#                 "file_size": None,
#                 "audio": None,  # This will be populated later
#                 "file_quality": None,  # This will be populated later
#                 "movie_name": None,  # Movie details extracted from caption
#                 "year": None,
#                 "languages": None,
#                 "rating": None,
#                 "quality": None,
#                 "batch_url": None  # This can be populated dynamically
#             }

#             if update.message.photo:
#                 file_name = update.message.caption or "No Caption Provided"

#                 # Replace the user tag with the movie counter
#                 transformed_caption = re.sub(
#                     r'★ ροωєяє∂ ϐγ : @Team_KL',
#                     f"© Movie#: {movie_counter}",
#                     file_name
#                 )
#                 # If no match, append the default caption
#                 if transformed_caption == file_name:
#                     transformed_caption += f" | © Movie#: {movie_counter}"

#                 movie_counter += 1

#                 # Process the photo
#                 await update.message.reply_photo(
#                     photo=update.message.photo[-1].file_id, caption=transformed_caption
#                 )

#                 file_info["file_id"] = update.message.photo[-1].file_id
#                 file_info["caption"] = transformed_caption
#                 file_info["file_size"] = "N/A"  # Placeholder
#                 add_processed_file(current_batch_id, file_info)

#             elif update.message.document:
#                 document = update.message.document
#                 original_caption = update.message.caption or ""
#                 file_size = round(document.file_size / (1024 * 1024), 2)
#                 file_name = remove_bot_username(document.file_name)

#                 # Extract data using regex
#                 lan_pattern = r"Audio\s*[:\-\s]*([A-Za-z, ]+)"
#                 res_pattern = r"Quality\s*[:\-\s]*([\d]+p)"
#                 lan_match = re.search(lan_pattern, original_caption)
#                 languages = lan_match.group(1) if lan_match else ""
#                 res_match = re.search(res_pattern, original_caption)
#                 resolution = res_match.group(1) if res_match else ""

#                 # Transform the caption for the document
#                 transformed_caption = create_new_caption(
#                     file_name, file_size, languages, resolution
#                 )

#                 # Process the document
#                 await update.message.reply_document(
#                     document=document.file_id, caption=transformed_caption, parse_mode="HTML"
#                 )

#                 file_info["file_id"] = document.file_id
#                 file_info["caption"] = transformed_caption
#                 file_info["file_size"] = f"{file_size} MB"
#                 add_processed_file(current_batch_id, file_info)

#             backup_processed_files()
#             save_movie_counter()

#             # Update the last processed time
#             # last_file_processed_time = asyncio.get_event_loop().time()
#             # asyncio.create_task(schedule_batch_completion(update, context))

#         except Exception as e:
#             print(f"Error processing message: {e}")

async def send_sticker(update: Update):
    sticker_path = os.path.join("telegram_bot/media", "end_sticker.webp")

    with open(sticker_path, "rb") as sticker_file:
        await update.message.reply_sticker(sticker_file)

    backup_processed_files()
    save_movie_counter()

    processed_file_path = os.path.join(
        "telegram_bot", "media", "processed_files.json")
    os.makedirs(os.path.dirname(processed_file_path), exist_ok=True)

    renew_json = {"batch_id": 0, "files": []}

    try:
        with open(processed_file_path, "w") as processed_file:
            json.dump(renew_json, processed_file, indent=4)
    except IOError as e:
        print(f"Error saving processed files: {e}")


async def handle_forwarded_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global movie_counter, last_file_processed_time, current_batch_id

    if update.message:
        try:
            load_movie_counter()
            processed_files = load_processed_files()

            # Generate batch_id except first image in the batch
            if update.message.photo and current_batch_id is not None:
                processed_files = {"batch_id": 0, "files": []}

                files = processed_files.get("files", [])
                num_images_processed = len(
                    [file for file in files if file.get("file_id") and file["file_size"] == "N/A"])
                num_docs_processed = len([file for file in files if file.get(
                    "file_id") and file["file_size"] != "N/A"])

                if num_images_processed == 0:
                    await send_sticker(update)

                current_batch_id = str(int(time.time()))
                print("Seconddddddddddddddd")
                print(f"\nStartImagesProcessed: {num_images_processed}")

            # Generate batch_id only for the first image in the batch
            if current_batch_id is None and update.message.photo:
                # current_batch_id = str(int(time.time()))
                processed_files = load_processed_files()
                print("\nprocessed_files: ", processed_files)

                processed_files = {"batch_id": 0, "files": []}
                current_batch_id = str(int(time.time()))

                print("Firsttttttttttttttt")

            print("Processed files:", processed_files)
            # print(f"\nImagesProcessed: {num_images_processed}")
            print("Batch_id: ", current_batch_id)

            file_info = {
                "file_id": None,
                "caption": None,
                "file_size": None,
                "audio": None,  # This will be populated later
                "file_quality": None,  # This will be populated later
                "movie_name": None,  # Movie details extracted from caption
                "year": None,
                "languages": None,
                "rating": None,
                "quality": None,
                "batch_url": None  # This can be populated dynamically
            }

            if update.message.photo:
                file_name = update.message.caption or "No Caption Provided"

                # Replace the user tag with the movie counter
                transformed_caption = re.sub(
                    r'★ ροωєяє∂ ϐγ : @Team_KL',
                    f"\u00a9 Movie#: {movie_counter}",
                    file_name
                )

                # If no match, append the default caption
                if transformed_caption == file_name:
                    transformed_caption += f" |\n \u00a9 Movie#: {
                        movie_counter}"

                movie_counter += 1

                # Process the photo
                await update.message.reply_photo(
                    photo=update.message.photo[-1].file_id, caption=transformed_caption
                )

                file_info["file_id"] = update.message.photo[-1].file_id
                file_info["caption"] = transformed_caption
                file_info["file_size"] = "N/A"  # Placeholder for images

                add_processed_file(current_batch_id, file_info)

            elif update.message.document:
                document = update.message.document
                original_caption = update.message.caption or ""
                file_size = round(document.file_size / (1024 * 1024), 2)

                file_name = remove_bot_username(document.file_name)

                # Extract data using regex
                lan_pattern = r"Audio\s*[:\-\s]*([A-Za-z, ]+)"
                res_pattern = r"Quality\s*[:\-\s]*([\d]+p)"
                lan_match = re.search(lan_pattern, original_caption)
                languages = lan_match.group(1) if lan_match else ""
                res_match = re.search(res_pattern, original_caption)
                resolution = res_match.group(1) if res_match else ""

                # Transform the caption for the document
                transformed_caption = create_new_caption(
                    file_name, file_size, languages, resolution
                )

                # Process the document
                # await update.message.reply_document(
                #     document=document.file_id, caption=transformed_caption, parse_mode="HTML"
                # )

                # You can replace this with any file or icon you prefer
                thumbnail_path = os.path.join(
                    "telegram_bot/media", "thumb.jpg")

                # Process the document with custom thumbnail
                # with open(thumbnail_path, 'rb') as thumbnail_file:
                #     # Process the document with a custom thumbnail

                await update.message.reply_document(
                    document=document.file_id, caption=transformed_caption, thumbnail=thumbnail_path
                )

                file_info["file_id"] = document.file_id
                file_info["caption"] = transformed_caption
                file_info["file_size"] = f"{file_size} MB"

                add_processed_file(current_batch_id, file_info)

            # backup_processed_files()
            # save_movie_counter()

            # Send sticker after the last file in the entire batch (after all files are processed)
            # if is_last_file_in_batch():
            #     await send_sticker(update)

        except Exception as e:
            print(f"Error processing message: {e}")


async def schedule_batch_completion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_file_processed_time, current_batch_id

    await asyncio.sleep(batch_processing_timeout)  # Wait for the timeout
    current_time = asyncio.get_event_loop().time()

    # Check if no new file was processed during the timeout
    if current_time - last_file_processed_time >= batch_processing_timeout and current_batch_id:
        # Process the batch and save it to the database

        await process_caption(current_batch_id)

        # from .views import view_batch

        # batch_url = reverse('view_batch', kwargs={
        #                     'batch_id': current_batch_id})

        # print("URLBatch: ", batch_url)

        processed_files_url = f"https://t.me/{
            context.bot.username}?start={current_batch_id}"

        # Send the batch completion message with the URL
        await update.message.reply_text(
            f"Batch processing complete! View the list of processed files here: {
                processed_files_url}"
        )

        current_batch_id = None  # Reset the batch_id for the next batch


@sync_to_async
def process_caption(batch_id):
    try:
        processed_files = load_processed_files()

        # Extract movie details from the first file's caption (or any logic you prefer)
        if processed_files['files']:
            first_file = processed_files['files'][0]
            caption = first_file['caption']

            MOVIE_DETAILS_REGEX = re.compile(
                r"⍞ TɪᴛLᴇ : (?P<movie_name>.+?)\n"
                r"⌬ YᴇAʀ : (?P<year>\d+)\n"
                r"✇ LᴀNɢUᴀGᴇ : (?P<languages>.+?)\n"
                r"⛦ RᴀTɪNɢ : (?P<rating>[\d.]+) / 10.0\n"
                r"〄 QᴜAʟIᴛY : (?P<quality>.+?)\n"
            )

            match = MOVIE_DETAILS_REGEX.search(caption)
            if match:
                movie_details = match.groupdict()

                # Using transaction to ensure database consistency
                with transaction.atomic():
                    # Create a new batch entry
                    processed_batch = ProcessedBatch.objects.create(
                        batch_id=batch_id,
                        movie_counter=1,  # Example counter, could be dynamic
                        movie_name=movie_details['movie_name'],
                        year=movie_details['year'],
                        languages=movie_details['languages'],
                        quality=movie_details['quality'],
                        rating=float(movie_details['rating']),
                        batch_url="example.com"  # Example URL, can be dynamic
                    )

                    # Add the file details for each file in the batch
                    for file_info in processed_files['files']:
                        BatchDetail.objects.create(
                            batch=processed_batch,
                            # File ID from the media
                            file_id=file_info["file_id"],
                            file_type="image" if file_info["file_size"] == "N/A" else "document",
                            file_size=file_info["file_size"],
                            audio="Tamil",  # Example, should be extracted from caption
                            file_quality="HDRip"  # Example quality, should be dynamically fetched if possible
                        )

    except Exception as e:
        print(f"Error processing caption: {e}")


def add_processed_file(batch_id, file_info):
    processed_files = load_processed_files()
    if processed_files["batch_id"] == 0:
        processed_files = {"batch_id": batch_id, "files": []}
    processed_files["files"].append(file_info)
    save_processed_files(processed_files)


def is_last_file_in_batch():
    processed_files = load_processed_files()
    current_batch_files = [file for file in processed_files.get("files", [])
                           if file.get("batch_id") == current_batch_id]

    # Assuming a function or global value to determine total files in a batch
    total_files_in_batch = get_expected_files_in_batch(current_batch_id)

    return len(current_batch_files) == total_files_in_batch


def load_processed_files():
    processed_file_path = os.path.join(
        "telegram_bot", "media", "processed_files.json")
    if os.path.exists(processed_file_path) and os.path.getsize(processed_file_path) > 0:
        try:
            with open(processed_file_path, "r") as processed_file:
                return json.load(processed_file)
        except json.JSONDecodeError as e:
            print(f"Error loading processed files: {e}")
            # Log error and reset file content if corrupted
            save_processed_files({"batch_id": 0, "files": []})
    return {"batch_id": 0, "files": []}


def get_expected_files_in_batch(batch_id):
    # Path to the JSON file storing batch metadata
    batch_metadata_path = os.path.join(
        "telegram_bot", "media", "batch_metadata.json")

    if os.path.exists(batch_metadata_path) and os.path.getsize(batch_metadata_path) > 0:
        try:
            # Load batch metadata
            with open(batch_metadata_path, "r") as metadata_file:
                batch_metadata = json.load(metadata_file)

            # Find the entry for the current batch ID
            batch_info = batch_metadata.get(batch_id)
            if batch_info:
                # Default to 0 if key is missing
                return batch_info.get("total_files", 0)

        except json.JSONDecodeError as e:
            print(f"Error loading batch metadata: {e}")
            # Return 0 if metadata is corrupted
            return 0

    # Default if no metadata exists or batch_id is not found
    return 0


def save_processed_files(processed_files):
    processed_file_path = os.path.join(
        "telegram_bot", "media", "processed_files.json")
    os.makedirs(os.path.dirname(processed_file_path), exist_ok=True)
    try:
        with open(processed_file_path, "w") as processed_file:
            json.dump(processed_files, processed_file, indent=4)
    except IOError as e:
        print(f"Error saving processed files: {e}")


def backup_processed_files():
    processed_file_path = os.path.join(
        "telegram_bot", "media", "processed_files.json")
    backup_file_path = os.path.join("telegram_bot", "media", "backup.json")
    if os.path.exists(processed_file_path):
        with open(processed_file_path, "r") as processed_file:
            processed_data = json.load(processed_file)
        with open(backup_file_path, "w") as backup_file:
            json.dump(processed_data, backup_file, indent=4)


def load_backup_data():
    backup_file_path = os.path.join("telegram_bot", "media", "backup.json")
    if os.path.exists(backup_file_path):
        with open(backup_file_path, "r") as backup_file:
            return json.load(backup_file)
    return []


def remove_bot_username(file_name):
    return re.sub(r'@[\w_]+', '', file_name).strip()


def create_new_caption(file_name, file_size, languages, resolution):
    caption = f'<a href="https://t.me/WMBroadcastBot?start">[MM]</a>-{
        file_name}'
    caption = f'[MM]{file_name}'
    if file_size >= 1024:
        caption += f"\n\n📼 FileSize: {file_size / 1024:.2f} GB"
    else:
        caption += f"\n\n📼 FileSize: {file_size} MB"
    caption += f"\n\n🔊 Audio: {languages}\n🎥 Quality: {resolution}"

    return caption


def configure_bot():
    load_dotenv()

    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        raise ValueError(
            "Bot token not found. Please set TELEGRAM_BOT_TOKEN in the environment variables."
        )

    # Create the Application instance
    application = Application.builder().token(TOKEN).build()

    # Add command and message handlers
    # application.add_handler(CommandHandler("start", start))

    application.add_handler(CommandHandler("start", handle_start))
    application.add_handler(MessageHandler(
        (filters.Document.ALL | filters.PHOTO), handle_forwarded_media))

    return application


# Register handlers
bot = configure_bot()

bot.run_polling()
