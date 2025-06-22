import os
import pytsk3
import sys

from tqdm import tqdm  # For progress tracking

# Function to recover files from the NTFS image
def recover_files_from_ntfs(image_file, output_dir, recover_deleted=False, file_types=None, verbose=False):
    try:
        image = pytsk3.Img_Info(image_file)
    except Exception as e:
        print(f"Error reading image file: {str(e)}")
        return

    try:
        filesystem = pytsk3.FS_Info(image)
    except Exception as e:
        print(f"Error opening filesystem: {str(e)}")
        return

    recovered_files = 0
    skipped_files = 0
    errors = 0

    # Function to handle directory traversal and file recovery
    def recover_from_dir(directory, current_path):
        nonlocal recovered_files, skipped_files, errors
        for entry in directory:
            if entry.info.name.name in [b'.', b'..']:
                continue

            # Ensure the metadata exists before trying to access it
            if entry.info.meta is None:
                print(f"Skipping entry due to missing metadata: {entry.info.name.name}")
                skipped_files += 1
                continue

            try:
                entry_name = entry.info.name.name.decode('utf-8')
                entry_path = os.path.join(current_path, entry_name)

                # Filter file types if specified
                if file_types and not any(entry_name.endswith(ft) for ft in file_types):
                    if verbose:
                        print(f"Skipping {entry_name}: Does not match specified file types.")
                    skipped_files += 1
                    continue

                # Filter based on whether we are recovering deleted files or not
                is_deleted = entry.info.meta.flags & pytsk3.TSK_FS_META_FLAG_UNALLOC
                if recover_deleted and not is_deleted:
                    if verbose:
                        print(f"Skipping {entry_name}: Not a deleted file.")
                    skipped_files += 1
                    continue
                elif not recover_deleted and is_deleted:
                    if verbose:
                        print(f"Skipping {entry_name}: Is a deleted file.")
                    skipped_files += 1
                    continue

                # If it's a file, recover it
                if entry.info.meta.type == pytsk3.TSK_FS_META_TYPE_REG:
                    output_file_path = os.path.join(output_dir, entry_path)  # Use output_dir for recovery
                    if verbose:
                        print(f"Recovering file: {entry_path}")
                    recover_file(entry, output_file_path)

                # If it's a directory, recurse into it
                elif entry.info.meta.type == pytsk3.TSK_FS_META_TYPE_DIR:
                    if verbose:
                        print(f"Entering directory: {entry_path}")
                    new_output_dir = os.path.join(output_dir, entry_path)
                    if not os.path.exists(new_output_dir):
                        os.makedirs(new_output_dir)

                    sub_directory = entry.as_directory()
                    recover_from_dir(sub_directory, entry_path)

            except Exception as e:
                print(f"Error processing {entry.info.name.name}: {str(e)}")
                errors += 1

    # Function to recover a file
    def recover_file(file_entry, output_file_path):
        nonlocal recovered_files
        try:
            file_size = file_entry.info.meta.size

            # Handle filename conflicts
            base_name, ext = os.path.splitext(output_file_path)
            counter = 1
            while os.path.exists(output_file_path):
                output_file_path = f"{base_name}_{counter}{ext}"
                counter += 1

            # Read and write file in chunks (e.g., 1024 bytes)
            with open(output_file_path, 'wb') as output_file:
                offset = 0
                chunk_size = 1024
                while offset < file_size:
                    data = file_entry.read_random(offset, min(chunk_size, file_size - offset))
                    if not data:
                        break
                    output_file.write(data)
                    offset += len(data)

            recovered_files += 1
            if verbose:
                print(f"File saved: {output_file_path}")
        except Exception as e:
            print(f"Error recovering file {file_entry.info.name.name}: {str(e)}")

    # Progress tracking with tqdm
    def count_total_files(directory):
        total_files = 0
        for entry in directory:
            if entry.info.name.name in [b'.', b'..']:
                continue

            # Ensure the metadata exists before trying to access it
            if entry.info.meta is None:
                continue

            if entry.info.meta.type == pytsk3.TSK_FS_META_TYPE_REG or entry.info.meta.type == pytsk3.TSK_FS_META_TYPE_DIR:
                total_files += 1
        return total_files

    # Start from the root directory and track progress
    root_dir = filesystem.open_dir(path='/')
    total_files = count_total_files(root_dir)
    with tqdm(total=total_files, desc="Recovering files", unit="file") as progress_bar:
        recover_from_dir(root_dir, '')
        progress_bar.update(recovered_files)

    # Final report
    print(f"Total files recovered: {recovered_files}")
    print(f"Total files skipped: {skipped_files}")
    print(f"Total errors: {errors}")

    return {"total":recovered_files,"skip":skipped_files,"error":errors}


# Main code entry point
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python ntfs_recover.py <image_file> <output_directory> [--recover-deleted] [--file-types jpg,png,pdf] [--verbose]")
        sys.exit(1)

    image_file = sys.argv[1]
    output_directory = sys.argv[2]
    recover_deleted = '--recover-deleted' in sys.argv
    verbose = '--verbose' in sys.argv
    file_types = None

    # Parse file types argument
    for arg in sys.argv:
        if arg.startswith('--file-types'):
            file_types = arg.split('=')[1].split(',')

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    recover_files_from_ntfs(image_file, output_directory, recover_deleted=recover_deleted, file_types=file_types, verbose=verbose)
