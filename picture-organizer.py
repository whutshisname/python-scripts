import os
import shutil
from PIL import Image
from PIL.ExifTags import TAGS
from datetime import datetime
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata

def get_image_date_taken(path):
    try:
        image = Image.open(path)
        exif_data = image._getexif()
        if exif_data:
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == 'DateTimeOriginal':
                    return datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
    except Exception as e:
        print(f"Could not read EXIF from {path}: {e}")
    return None

def get_video_date_taken(path):
    try:
        parser = createParser(path)
        if not parser:
            return None
        with parser:
            metadata = extractMetadata(parser)
        if metadata and metadata.has("creation_date"):
            return metadata.get("creation_date")
    except Exception as e:
        print(f"Could not read video metadata from {path}: {e}")
    return None

def generate_unique_filename(dest_folder, filename):
    base, ext = os.path.splitext(filename)
    counter = 1
    new_filename = filename
    while os.path.exists(os.path.join(dest_folder, new_filename)):
        new_filename = f"{base}_{counter}{ext}"
        counter += 1
    return new_filename

def organize_media_by_date(source_dir, dest_dir):
    skipped_base_dir = os.path.join(dest_dir, 'SKIPPED')

    for root, _, files in os.walk(source_dir):
        for file in files:
            file_path = os.path.join(root, file)
            file_lower = file.lower()
            rel_dir = os.path.relpath(root, source_dir)

            is_image = file_lower.endswith(('.jpg', '.jpeg', '.png'))
            is_video = file_lower.endswith(('.mov', '.mp4', '.avi', '.mkv'))

            date_taken = None
            if is_image:
                date_taken = get_image_date_taken(file_path)
            elif is_video:
                date_taken = get_video_date_taken(file_path)

            if date_taken:
                folder_name = date_taken.strftime('%Y%m')
                target_folder = os.path.join(dest_dir, folder_name)
            else:
                target_folder = os.path.join(skipped_base_dir, rel_dir)

            os.makedirs(target_folder, exist_ok=True)
            unique_filename = generate_unique_filename(target_folder, file)
            target_path = os.path.join(target_folder, unique_filename)

            shutil.copy2(file_path, target_path)
            print(f"Copied {file_path} to {target_path}")

source_directory = 'Z:\\'
destination_directory = 'D:\\dev\\organized-pics'

organize_media_by_date(source_directory, destination_directory)
