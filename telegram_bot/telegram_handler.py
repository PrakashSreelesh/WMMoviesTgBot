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
batch_processing_timeout = 3  # Time in seconds to consider the end of a batch
last_file_processed_time = None  # To track the time of the last file processed
movie_counter = 395  # Initialize starting value
current_batch_id = None  # To store the batch ID for the current batch

# ================================================================================================================================


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
    # save_movie_counter()

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
                # print("Seconddddddddddddddd")
                # print(f"\nStartImagesProcessed: {num_images_processed}")

            # Generate batch_id only for the first image in the batch
            if current_batch_id is None and update.message.photo:
                # current_batch_id = str(int(time.time()))
                processed_files = load_processed_files()
                # print("\nprocessed_files: ", processed_files)

                processed_files = {"batch_id": 0, "files": []}
                current_batch_id = str(int(time.time()))

                # print("Firsttttttttttttttt")

            # print("Processed files:", processed_files)
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

                save_movie_counter()

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
                lan_pattern = r"🔉 Audio\s*[:\-\s]*([A-Za-z, \+]+(?:\s[A-Za-z, \+]+)*)"
                res_pattern = r"Quality\s*[:\-\s]*([\d]+p)"
                lan_match = re.search(lan_pattern, original_caption)
                languages = lan_match.group(1) if lan_match else ""
                res_match = re.search(res_pattern, original_caption)
                resolution = res_match.group(1) if res_match else ""

                # Transform the caption for the document
                file_name.lstrip('- _.').strip()
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
                    document=document.file_id, caption=transformed_caption, thumbnail=thumbnail_path, parse_mode="HTML"
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
            # Update the last processed time
            last_file_processed_time = asyncio.get_event_loop().time()
            asyncio.create_task(schedule_batch_completion(update, context))
            # await send_sticker(update)

        except Exception as e:
            print(f"Error processing message: {e}")


async def schedule_batch_completion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_file_processed_time, current_batch_id

    await asyncio.sleep(batch_processing_timeout)  # Wait for the timeout
    current_time = asyncio.get_event_loop().time()

    if last_file_processed_time is None:
        last_file_processed_time = current_time

    # Check if no new file was processed during the timeout
    if current_time - last_file_processed_time >= batch_processing_timeout and current_batch_id:
        # Process the batch and save it to the database

        await process_caption(current_batch_id)

        # processed_files_url = f"https://t.me/{
        #     context.bot.username}?start={current_batch_id}"
        # # Send the batch completion message with the URL
        # await update.message.reply_text(
        #     f"Batch processing complete! View the list of processed files here: {
        #         processed_files_url}"
        # )

        if is_last_file_in_batch():
            await send_sticker(update)

        current_batch_id = None  # Reset the batch_id for the next batch


def load_movie_counter():
    global movie_counter
    counter_file_path = os.path.join("telegram_bot", "media", "counter.json")
    if os.path.exists(counter_file_path):
        with open(counter_file_path, "r") as counter_file:
            data = json.load(counter_file)
            movie_counter = data.get("movie_counter", 395)
    else:
        save_movie_counter()


def save_movie_counter():
    global movie_counter
    counter_file_path = os.path.join("telegram_bot", "media", "counter.json")
    data = {"movie_counter": movie_counter}
    with open(counter_file_path, "w") as counter_file:
        json.dump(data, counter_file)


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
    global current_batch_id
    # caption = f'📯 ᴍovɪᴇ:  [ᴍwᴍ]{file_name}'
    # # caption = f'[MM]{file_name}'
    # if file_size >= 1024:
    #     caption += f"\n\n🎟️ Fɪʟᴇ Sɪᴢᴇ: {file_size / 1024:.2f} GB"
    # else:
    #     caption += f"\n\n🎟️ Fɪʟᴇ Sɪᴢᴇ: {file_size} MB"

    # caption += f"\n\n🔊 Aᴜᴅɪᴏ: {languages}\n🎥 Quality: {resolution}"
    # caption == f"\n🍿 Qᴜᴀʟɪᴛʏ: {resolution}"
    # caption += f"\n\n<spoiler>📯 JᴏoOɪɴ: @WMBroadcastBot</spoiler>"

    languages_per_line = 3
    # Find the year in the movie name using regex (assuming the year is 4 digits)
    year_match = re.search(r'(\d{4})', file_name)

    if year_match:
        year = year_match.group(1)
        year_index = file_name.index(year)

        before_year = file_name[:year_index]
        after_year = file_name[year_index:]

        # Replace unwanted characters before the year with space and after the year with underscore
        cleaned_before_year = before_year.replace(
            '-', '-').replace(' ', '-').replace('_', '-').replace('.', '-')
        cleaned_after_year = after_year.replace(
            '-', '_').replace(' ', '_').replace('_', '_').replace('.', '_')

        # Remove leading characters from the specified list
        cleaned_before_year = cleaned_before_year.lstrip('- _.').strip()

        file_name = cleaned_before_year + cleaned_after_year.strip()

    else:
        file_name.strip()

    # formatted_languages = languages
    language_list = languages.split(", ")

    formatted_languages = ""
    for i in range(0, len(language_list), languages_per_line):
        print(current_batch_id)
        if formatted_languages:
            formatted_languages += ",\n" + "    "*5 + "   "  # Add indentation to next line
        formatted_languages += ", ".join(
            language_list[i:i + languages_per_line])

    if file_size >= 1024:
        file_size_str = f"{file_size / 1024:.2f} GB"
    else:
        file_size_str = f"{file_size} MB"

    caption = f"""
    🍿<b><a href="https://t.me/WMBroadcastBot?start">[ᴍwᴍ]</a></b><code>{file_name}</code>

    🎟️ <b>FɪʟᴇSɪᴢᴇ:</b>  {file_size_str}
    💿 <b>Qᴜᴀʟɪᴛʏ:</b>  {resolution}
    🔊 <b>Aᴜᴅɪᴏ:</b> {formatted_languages}

<i><a href="https://t.me/WMBroadcastBot?start">✨ᴜᴘʟᴏᴀᴅᴇᴅ ᴡɪᴛʜ 💖 ғᴏʀ ʏᴏᴜ.!✨</a></i>
📯 JᴏoOɪɴ ᴜs: @WMBroadcastBot 📯
    """.strip()

    return caption


def configure_bot():
    load_dotenv()
    # movie_counter = load_movie_counter()

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


# # Register handlers
# bot = configure_bot()

# bot.run_polling()


async def main():
    bot = configure_bot()
    await bot.run_polling()  # Properly await run_polling in the asyncio loop


if __name__ == "__main__":
    asyncio.run(main())  # Explicitly run the bot inside the asyncio event loop
