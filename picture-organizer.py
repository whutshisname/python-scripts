import os
import shutil
import hashlib
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

def compute_file_hash(file_path, chunk_size=65536):
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b''):
            hasher.update(chunk)
    return hasher.hexdigest()

def generate_non_duplicate_filename(dest_folder, filename, src_file_hash):
    base, ext = os.path.splitext(filename)
    candidate_path = os.path.join(dest_folder, filename)

    if not os.path.exists(candidate_path):
        return filename

    existing_hash = compute_file_hash(candidate_path)
    if existing_hash == src_file_hash:
        return None

    counter = 1
    while True:
        new_filename = f"{base}_{counter}{ext}"
        new_path = os.path.join(dest_folder, new_filename)
        if not os.path.exists(new_path):
            return new_filename
        if compute_file_hash(new_path) == src_file_hash:
            return None
        counter += 1

def save_resume_state(dest_dir, rel_dir):
    resume_path = os.path.join(dest_dir, '.resume_state.txt')
    with open(resume_path, 'w') as f:
        f.write(rel_dir)

def load_resume_state(dest_dir):
    resume_path = os.path.join(dest_dir, '.resume_state.txt')
    if os.path.exists(resume_path):
        with open(resume_path, 'r') as f:
            return f.read().strip()
    return None

def organize_media_by_date(source_dir, dest_dir):
    skipped_base_dir = os.path.join(dest_dir, 'SKIPPED')
    os.makedirs(skipped_base_dir, exist_ok=True)

    last_processed = load_resume_state(dest_dir)
    skip_until_found = bool(last_processed)

    for root, _, files in os.walk(source_dir):
        rel_dir = os.path.relpath(root, source_dir)

        # Resume logic: skip folders until we reach the last processed one
        if skip_until_found:
            if rel_dir == last_processed:
                skip_until_found = False
            else:
                print(f"Skipping {rel_dir} (already processed)")
                continue

        for file in files:
            file_path = os.path.join(root, file)
            file_lower = file.lower()

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
            src_hash = compute_file_hash(file_path)
            target_filename = generate_non_duplicate_filename(target_folder, file, src_hash)
            if target_filename is None:
                print(f"Skipped duplicate: {file_path}")
                continue

            target_path = os.path.join(target_folder, target_filename)
            shutil.copy2(file_path, target_path)
            print(f"Copied {file_path} → {target_path}")

        # Save progress after each folder is completed
        save_resume_state(dest_dir, rel_dir)

source_directory = 'Z:\\'
destination_directory = 'D:\\dev\\organized-pics'

organize_media_by_date(source_directory, destination_directory)
