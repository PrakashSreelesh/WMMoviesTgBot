# 2nd code starts her============================>>>>>>>>>>>>>


import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import os
import asyncio
import json
import time


# Timer to detect batch processing
batch_processing_timeout = 3  # Time in seconds to consider the end of a batch
last_file_processed_time = None  # To track the time of the last file processed
movie_counter = 326  # Initialize starting value

# ================================================================================================================================


def load_movie_counter():
    """Load the movie counter from the 'counter.json' file."""
    global movie_counter
    counter_file_path = os.path.join("telegram_bot", "media", "counter.json")
    if os.path.exists(counter_file_path):
        with open(counter_file_path, "r") as counter_file:
            data = json.load(counter_file)
            # Default to 325 if not found
            movie_counter = data.get("movie_counter")
    else:
        # Initialize counter if the file does not exist
        save_movie_counter()


def save_movie_counter():
    """Save the current movie counter to the 'counter.json' file."""
    counter_file_path = os.path.join("telegram_bot", "media", "counter.json")
    data = {"movie_counter": movie_counter}
    with open(counter_file_path, "w") as counter_file:
        json.dump(data, counter_file)


async def handle_forwarded_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global movie_counter, last_file_processed_time

    if update.message:
        try:
            movie_counter = load_movie_counter()
            processed_files = load_processed_files()
            if processed_files["batch_id"] is None or processed_files["batch_id"] != movie_counter:
                batch_id = movie_counter
            # if batch_id == 0 or batch_id is None:
            #     batch_id = int(time.time())

            print("start Batch", batch_id)

            file_info = {
                "file_id": None,
                "caption": None,
                "file_size": None,
                "processed_time": asyncio.get_event_loop().time()
            }

            # Check if it's an image
            if update.message.photo:
                file_name = update.message.caption or "Unknown File"
                movie_counter += 1
                transformed_caption = re.sub(
                    r'★ ροωєяє∂ ϐγ : @Team_KL', f"© Movie#: {movie_counter}", file_name)

                await update.message.reply_photo(
                    photo=update.message.photo[-1].file_id, caption=transformed_caption
                )

                # Add to processed files
                file_info["file_id"] = update.message.photo[-1].file_id
                file_info["caption"] = transformed_caption
                file_info["file_size"] = "N/A"
                add_processed_file(batch_id, file_info)

            elif update.message.document:
                document = update.message.document

                lan_pattern = r"Audio\s*[:\-\s]*([A-Za-z, ]+)"
                res_pattern = r"Quality\s*[:\-\s]*([\d]+p)"

                original_caption = update.message.caption or ""
                file_size = round(document.file_size /
                                  (1024 * 1024), 2)  # File size in MB
                file_name = document.file_name
                file_name = remove_bot_username(file_name)

                lan_match = re.search(lan_pattern, original_caption)
                languages = lan_match.group(1) if lan_match else ""
                res_match = re.search(res_pattern, original_caption)
                resolution = res_match.group(1) if res_match else ""

                transformed_caption = create_new_caption(
                    file_name, file_size, languages, resolution
                )

                await update.message.reply_document(
                    document=document.file_id, caption=transformed_caption, parse_mode="HTML"
                )

                # Add to processed files
                file_info["file_id"] = document.file_id
                file_info["caption"] = file_name
                file_info["file_size"] = f"{file_size} MB"
                add_processed_file(batch_id, file_info)

            # Record the time of the last processed file
            # last_file_processed_time = asyncio.get_event_loop().time()

            # asyncio.create_task(schedule_sticker_send(update, context))

            backup_processed_files()
            clear_processed_files()
            save_movie_counter()

            # Generate a unique URL for the batch
            processed_files_url = f"https://t.me/{
                context.bot.username}?start={batch_id}"

            await update.message.reply_text(
                f"Batch processing complete! View the list of processed files here: {
                    processed_files_url}"
            )

            # await update.message.delete()

        except Exception as e:
            print(f"Error processing message: {e}")


async def schedule_sticker_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_file_processed_time, movie_counter

    await asyncio.sleep(batch_processing_timeout)  # Wait for the timeout
    current_time = asyncio.get_event_loop().time()

    # Check if no new file was processed during the timeout
    if current_time - last_file_processed_time >= batch_processing_timeout:
        batch_id = load_last_batch_id()

        # Path to the end sticker
        sticker_path = os.path.join("telegram_bot/media", "end_sticker.webp")

        try:
            # Send the end sticker
            with open(sticker_path, "rb") as sticker_file:
                sticker_message = await context.bot.send_sticker(
                    chat_id=update.message.chat_id,
                    sticker=sticker_file
                )

            # Check if the sticker was successfully sent
            if sticker_message and sticker_message.sticker:
                sticker_info = {
                    "file_id": sticker_message.sticker.file_id,
                    "caption": "Batch end sticker",
                    "file_size": "N/A",
                    "processed_time": asyncio.get_event_loop().time()
                }
                add_processed_file(batch_id, sticker_info)

            backup_processed_files()

            clear_processed_files()

            # Generate a unique URL for the batch
            processed_files_url = f"https://t.me/{
                context.bot.username}?start={batch_id}"

            await update.message.reply_text(
                f"Batch processing complete! View the list of processed files here: {
                    processed_files_url}"
            )

            save_movie_counter()
            print("stkr end", batch_id)

        except Exception as e:
            print(f"Error sending sticker: {e}")


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Extract the batch ID from the message
    batch_id = update.message.text.split()[-1]
    print(batch_id)

    # Load the processed files for this batch
    processed_files = load_backup_batchid(batch_id)

    if processed_files:
        for file_info in processed_files:
            file_id = file_info['file_id']
            caption = file_info['caption']
            file_size = file_info['file_size']

            # Send the file along with the caption
            if file_info['file_size'] == "N/A":  # Photo
                await update.message.reply_photo(
                    photo=file_id, caption=caption
                )
            else:  # Document
                await update.message.reply_document(
                    document=file_id, caption=caption
                )

        # Send the end sticker after listing the files
        sticker_path = os.path.join("telegram_bot/media", "end_sticker.webp")
        with open(sticker_path, "rb") as sticker_file:
            await update.message.reply_sticker(sticker_file)

    else:
        # await update.message.reply_text("No files found for this batch.")
        await update.message.reply_text(
            "Welcome! Forward me a media file and I'll change its caption."
        )


def add_processed_file(batch_id, file_info):
    """Add the processed file to the list with a specific batch ID."""
    processed_files = load_processed_files()

    if processed_files["batch_id"] == 0:
        processed_files = {"batch_id": batch_id, "files": []}
        processed_files["files"].append(file_info)

    elif processed_files["batch_id"] == batch_id:
        processed_files["files"].append(file_info)

    else:
        print(f"Error: batch_id not same")

    save_processed_files(processed_files)


def load_processed_files():
    """Load the processed files from the 'processed_files.json' file."""
    processed_file_path = os.path.join(
        "telegram_bot", "media", "processed_files.json")
    processed_files = {}

    # If the processed_files.json exists and has data
    if os.path.exists(processed_file_path) and os.path.getsize(processed_file_path) > 0:
        try:
            # if processed_files["batch_id"] == batch_id:
            with open(processed_file_path, "r") as processed_file:
                processed_files = json.load(processed_file)
        except json.JSONDecodeError:
            print(f"Error decoding JSON in {
                  processed_file_path}. The file might be corrupt.")
            # Optionally reset the file or load defaults
            save_processed_files({"batch_id": 0, "files": []})
    else:
        print(
            f"{processed_file_path} is empty or does not exist. Initializing an empty json.")
        save_processed_files({"batch_id": 0, "files": []})

    return processed_files


def save_processed_files(processed_files):
    """Save the processed files to the 'processed_files.json' file."""
    processed_file_path = os.path.join(
        "telegram_bot", "media", "processed_files.json")

    # Ensure the directory exists
    os.makedirs(os.path.dirname(processed_file_path), exist_ok=True)

    with open(processed_file_path, "w") as processed_file:
        try:
            # Write the current batch of processed files to the file
            json.dump(processed_files, processed_file)
        except json.JSONDecodeError:
            print("Error encoding JSON. Please check the data format.")


def backup_processed_files():
    """Backup the current batch data to 'backup.json'."""
    processed_file_path = os.path.join(
        "telegram_bot", "media", "processed_files.json")
    backup_file_path = os.path.join("telegram_bot", "media", "backup.json")

    if os.path.exists(processed_file_path):
        # Read the current processed batch from processed_files.json
        with open(processed_file_path, "r") as processed_file:
            current_batch = json.load(processed_file)

        if current_batch and "batch_id" in current_batch:
            # Read the existing backup data
            backup_data = load_backup_data()

            # Check if the current batch_id already exists in the backup
            if any(batch.get("batch_id") == current_batch["batch_id"] for batch in backup_data):
                print(
                    f"Batch {current_batch['batch_id']} already exists in the backup. Skipping.")
            else:
                # Append the current batch to the backup
                backup_data.append(current_batch)

            # Save the backup data back to backup.json
            with open(backup_file_path, "w") as backup_file:
                json.dump(backup_data, backup_file)

            print(f"Batch {current_batch['batch_id']} has been backed up.")
        else:
            print("No valid batch to backup.")
    else:
        print("No processed files found to backup.")


def load_backup_data():
    """Load all backup batches from 'backup.json'."""
    backup_file_path = os.path.join("telegram_bot", "media", "backup.json")

    if os.path.exists(backup_file_path) and os.path.getsize(backup_file_path) > 0:
        try:
            with open(backup_file_path, "r") as backup_file:
                return json.load(backup_file)
        except json.JSONDecodeError:
            return []
    else:
        return []


def clear_processed_files():
    """Clear processed files and reset 'processed_files.json' to default format."""
    processed_file_path = os.path.join(
        "telegram_bot", "media", "processed_files.json")

    # Reset the processed files to default format
    default_data = {
        "batch_id": 0,
        "files": []
    }

    with open(processed_file_path, "w") as processed_file:
        json.dump(default_data, processed_file)

    print("Processed files have been cleared and reset.")


def load_backup_batchid(batch_id):
    backup_file_path = os.path.join(
        "telegram_bot", "media", "backup.json")
    if os.path.exists(backup_file_path) and os.path.getsize(backup_file_path) > 0:
        try:
            with open(backup_file_path, "r") as backup_file:
                backup_batch_data = json.load(backup_file)

            print(backup_batch_data)

            for batch in backup_batch_data:
                if batch["batch_id"] == batch_id:
                    print("files", batch["files"])
                    return batch["files"]

        except json.JSONDecodeError:
            return None


def load_all_batches():
    """Load all the batches stored in the processed files JSON."""
    processed_file_path = os.path.join(
        "telegram_bot", "media", "processed_files.json")
    if os.path.exists(processed_file_path) and os.path.getsize(processed_file_path) > 0:
        try:
            with open(processed_file_path, "r") as processed_file:
                return json.load(processed_file)
        except json.JSONDecodeError:
            return []
    else:
        return []


def load_last_batch_id():
    try:
        with open('processed_files.json', 'r') as file:
            data = json.load(file)
            if data:
                return data["batch_id"]
            return None  # In case there's no batch_id
    except FileNotFoundError:
        return None  # If file doesn't exist yet


# ================================================================================================================================

def remove_bot_username(file_name):
    # Remove any @username pattern from the file name
    cleaned_file_name = re.sub(r'@[\w_]+', '', file_name)

    # Clean up any leading or trailing spaces
    cleaned_file_name = cleaned_file_name.strip()

    return cleaned_file_name


def create_new_caption(file_name, file_size, languages, resolution):
    # Start with the [MM]-{file_name} format
    caption = f'<a href="https://t.me/WMBroadcastBot?start">[MM]</a>-{
        file_name}'

    if file_size >= 1024:
        caption += f"\n\n📼 FileSize: {file_size / 1024:.2f} GB"
    else:
        caption += f"\n\n📼 FileSize: {file_size} MB"

    caption += f"\n🔉 Audio: {languages}"
    caption += f"\n💿 Quality: {resolution}"
    caption += f"\n\n📯 Join: @WMBroadcastBot"

    return caption


def save_batch_files(batch_id):
    """Save the batch ID in a file to track the batch."""
    batch_file_path = os.path.join("telegram_bot", "media", "batches.json")
    if os.path.exists(batch_file_path):
        with open(batch_file_path, "r") as batch_file:
            batch = json.load(batch_file)
    else:
        batch = {"files": []}

    batch["batch_id"] = batch_id

    with open(batch_file_path, "w") as batch_file:
        json.dump(batch, batch_file)


def configure_bot():
    load_dotenv()  # Load environment variables from the .env file

    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        raise ValueError(
            "Telegram bot token not found. Please check the .env file.")

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", handle_start))
    application.add_handler(MessageHandler(
        filters.ALL, handle_forwarded_media))

    return application


def main():
    load_movie_counter()  # Load movie counter at the start
    app = configure_bot()
    app.run_polling()


if __name__ == "__main__":
    main()



##==========================Old Code========================
# import re
# from telegram import Update
# from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
# from dotenv import load_dotenv
# import os
# import asyncio
# import json
# import time


# # Timer to detect batch processing
# batch_processing_timeout = 3  # Time in seconds to consider the end of a batch
# last_file_processed_time = None  # To track the time of the last file processed
# movie_counter = 325  # Initialize starting value

# # ================================================================================================================================


# def load_movie_counter():
#     """Load the movie counter from the 'counter.json' file."""
#     global movie_counter
#     counter_file_path = os.path.join("telegram_bot", "media", "counter.json")
#     if os.path.exists(counter_file_path):
#         with open(counter_file_path, "r") as counter_file:
#             data = json.load(counter_file)
#             # Default to 325 if not found
#             movie_counter = data.get("movie_counter")
#     else:
#         # Initialize counter if the file does not exist
#         save_movie_counter()


# def save_movie_counter():
#     """Save the current movie counter to the 'counter.json' file."""
#     counter_file_path = os.path.join("telegram_bot", "media", "counter.json")
#     data = {"movie_counter": movie_counter}
#     with open(counter_file_path, "w") as counter_file:
#         json.dump(data, counter_file)


# async def handle_forwarded_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     global movie_counter, last_file_processed_time

#     if update.message:
#         try:
#             file_info = {
#                 "file_id": None,
#                 "caption": None,
#                 "file_size": None,
#                 "processed_time": asyncio.get_event_loop().time()
#             }

#             # Generate batch_id if it's not available (you can adjust as needed)
#             batch_id = int(time.time())

#             # Check if it's an image
#             if update.message.photo:
#                 file_name = update.message.caption or "Unknown File"
#                 movie_counter += 1
#                 transformed_caption = re.sub(
#                     r'★ ροωєяє∂ ϐγ : @Team_KL', f"© Movie#: {movie_counter}", file_name)

#                 await update.message.reply_photo(
#                     photo=update.message.photo[-1].file_id, caption=transformed_caption
#                 )

#                 # Add to processed files
#                 file_info["file_id"] = update.message.photo[-1].file_id
#                 file_info["caption"] = transformed_caption
#                 # Photo doesn't have a size in MB
#                 file_info["file_size"] = "N/A"
#                 add_processed_file(file_info, batch_id)

#             elif update.message.document:
#                 document = update.message.document

#                 lan_pattern = r"Audio\s*[:\-\s]*([A-Za-z, ]+)"
#                 res_pattern = r"Quality\s*[:\-\s]*([\d]+p)"

#                 original_caption = update.message.caption or ""
#                 file_size = round(document.file_size /
#                                   (1024 * 1024), 2)  # File size in MB
#                 file_name = document.file_name
#                 file_name = remove_bot_username(file_name)

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

#                 # Add to processed files
#                 file_info["file_id"] = document.file_id
#                 file_info["caption"] = transformed_caption
#                 file_info["file_size"] = f"{file_size} MB"
#                 add_processed_file(file_info, batch_id)

#             # Record the time of the last processed file
#             last_file_processed_time = asyncio.get_event_loop().time()

#             # Schedule sending the sticker after a timeout if no more files are processed
#             asyncio.create_task(schedule_sticker_send(update, context))

#             await update.message.delete()

#         except Exception as e:
#             print(f"Error processing message: {e}")


# async def schedule_sticker_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     global last_file_processed_time, movie_counter

#     await asyncio.sleep(batch_processing_timeout)  # Wait for the timeout
#     current_time = asyncio.get_event_loop().time()

#     # Check if no new file was processed during the timeout
#     if current_time - last_file_processed_time >= batch_processing_timeout:
#         # Generate a unique batch ID (e.g., timestamp or incremented batch number)
#         batch_id = load_last_batch_id()
#         if batch_id is None:
#             batch_id = int(time.time())

#         # Path to the end sticker
#         sticker_path = os.path.join("telegram_bot/media", "end_sticker.webp")

#         try:
#             # Send the end sticker
#             with open(sticker_path, "rb") as sticker_file:
#                 await context.bot.send_sticker(
#                     chat_id=update.message.chat_id,
#                     sticker=sticker_file
#                 )

#             sticker_info= load_processed_files(batch_id)

#             # Add sticker also
#             sticker_info["file_id"] = update.message.sticker.file_id
#             sticker_info["file_size"] = "N/A"
#             add_processed_file(sticker_info, batch_id)

#             # After sending the sticker, update and save the movie counter
#             save_movie_counter()

#             # Generate a unique URL for the batch
#             processed_files_url = f"https://t.me/{
#                 context.bot.username}?start={batch_id}"

#             # Store the batch and its files
#             save_batch_files(batch_id)

#             await update.message.reply_text(
#                 f"Batch processing complete! View the list of processed files here: {
#                     processed_files_url}"
#             )

#         except Exception as e:
#             print(f"Error sending sticker: {e}")


# def remove_bot_username(file_name):
#     # Remove any @username pattern from the file name
#     cleaned_file_name = re.sub(r'@[\w_]+', '', file_name)

#     # Clean up any leading or trailing spaces
#     cleaned_file_name = cleaned_file_name.strip()

#     return cleaned_file_name


# def parse_file_name(file_name):
#     # Extract movie name and year
#     movie_match = re.search(r'(.+?)\s*\((\d{4})\)', file_name)
#     movie_name = movie_match.group(1).strip() if movie_match else "Unknown"
#     year = movie_match.group(2) if movie_match else "Unknown"

#     # Extract languages
#     lang_match = re.search(
#         r'(Tamil|Hindi|Malayalam|Telugu|Kannada|Arabic)', file_name, re.IGNORECASE)
#     languages = ", ".join(re.findall(
#         r'(Tamil|Hindi|Malayalam|Telugu|Kannada|Arabic)', file_name, re.IGNORECASE))

#     # Extract quality
#     quality_match = re.search(
#         r'(\d{3,4}p|HDRip|DVDRip|BluRay|HD AVC)', file_name, re.IGNORECASE)
#     quality = quality_match.group(1) if quality_match else "Unknown"

#     # Extract rating (default to '--/10' if not available)
#     # rating = "8.6"

#     return movie_name, year, languages, quality


# def create_new_caption(file_name, file_size, languages, resolution):
#     # Start with the [MM]-{file_name} format
#     caption = f'<a href="https://t.me/WMBroadcastBot?start">[MM]</a>-{
#         file_name}'

#     if file_size >= 1024:
#         caption += f"\n\n📼 FileSize: {file_size / 1024:.2f} GB"
#     else:
#         caption += f"\n\n📼 FileSize: {file_size} MB"

#     caption += f"\n🔉 Audio: {languages}"
#     caption += f"\n💿 Quality: {resolution}"
#     caption += f"\n\n📯 Join: @WMBroadcastBot"

#     return caption


# async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     # Extract the batch ID from the message
#     batch_id = update.message.text.split()[-1]

#     # Load the processed files for this batch
#     processed_files = load_processed_files(batch_id)

#     if processed_files:
#         for file_info in processed_files:
#             file_id = file_info['file_id']
#             caption = file_info['caption']
#             file_size = file_info['file_size']

#             # Send the file along with the caption
#             if file_info['file_size'] == "N/A":  # Photo
#                 await update.message.reply_photo(
#                     photo=file_id, caption=caption
#                 )
#             else:  # Document
#                 await update.message.reply_document(
#                     document=file_id, caption=caption
#                 )

#         # Send the end sticker after listing the files
#         sticker_path = os.path.join("telegram_bot/media", "end_sticker.webp")
#         with open(sticker_path, "rb") as sticker_file:
#             await update.message.reply_sticker(sticker_file)

#     else:
#         # await update.message.reply_text("No files found for this batch.")
#         await update.message.reply_text(
#             "Welcome! Forward me a media file and I'll change its caption."
#         )


# # async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
# #     await update.message.reply_text(
# #         "Welcome! Forward me a media file and I'll change its caption."
# #     )


# # ================================================================================================================================
# def load_processed_files(batch_id):
#     """Load the processed files from the 'processed_files.json' file."""
#     processed_files = []
#     processed_file_path = os.path.join("telegram_bot", "media", "processed_files.json")

#     # Ensure the file exists and is not empty
#     if os.path.exists(processed_file_path) and os.path.getsize(processed_file_path) > 0:
#         try:
#             with open(processed_file_path, "r") as processed_file:
#                 all_files = json.load(processed_file)
#                 processed_files = [file for file in all_files if file['batch_id'] == batch_id]
#         except json.JSONDecodeError:
#             print(f"Error decoding JSON in {processed_file_path}. The file might be corrupt.")
#             # Optionally, reset the file or load defaults
#             save_processed_files([])
#     else:
#         print(f"{processed_file_path} is empty or does not exist. Initializing an empty list.")
#         save_processed_files(processed_files)

#     return processed_files


# def save_processed_files(processed_files):
#     """Save the processed files to the 'processed_files.json' file."""
#     processed_file_path = os.path.join("telegram_bot", "media", "processed_files.json")

#     # Ensure the directory exists
#     os.makedirs(os.path.dirname(processed_file_path), exist_ok=True)

#     with open(processed_file_path, "w") as processed_file:
#         try:
#             json.dump(processed_files, processed_file)
#         except json.JSONDecodeError:
#             print("Error encoding JSON. Please check the data format.")


# def load_last_batch_id():
#     try:
#         with open('processed_files.json', 'r') as file:
#             data = json.load(file)
#             if data and "last_batch_id" in data:
#                 return data["last_batch_id"]
#             return None  # In case there's no batch_id
#     except FileNotFoundError:
#         return None  # If file doesn't exist yet


# def add_processed_file(file_info, batch_id):
#     """Add the processed file to the list with a batch ID."""
#     processed_files = load_processed_files(batch_id)
#     file_info['batch_id'] = batch_id
#     processed_files.append(file_info)
#     save_processed_files(processed_files)


# def save_batch_files(batch_id):
#     """Save the batch ID in a file to track the batch."""
#     batch_file_path = os.path.join("telegram_bot", "media", "batches.json")
#     if os.path.exists(batch_file_path):
#         with open(batch_file_path, "r") as batch_file:
#             batches = json.load(batch_file)
#     else:
#         batches = []

#     batches.append(batch_id)

#     with open(batch_file_path, "w") as batch_file:
#         json.dump(batches, batch_file)


# # ================================================================================================================================

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
#         filters.FORWARDED & (filters.Document.ALL | filters.PHOTO), handle_forwarded_media))

#     return application
