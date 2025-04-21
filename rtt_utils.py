import shutil
import os
import subprocess

def remove_extraneous_process_items(items_to_remove):
    """
    Remove specified files or directories.

    Args:
        items_to_remove (list): List of file or directory paths to remove.
    """
    for item in items_to_remove:
        if os.path.exists(item):
            try:
                if os.path.isfile(item) or os.path.islink(item):
                    os.remove(item)  # Remove file or symbolic link
                    print(f"Removed file: {item}")
                elif os.path.isdir(item):
                    shutil.rmtree(item)
                    print(f"Removed directory: {item}")
            except Exception as e:
                print(f"Error removing {item}: {e}")
        else:
            # print(f"Item does not exist: {item}")
            pass

def remove_incomplete_process_directory(folder_to_remove):
    assert not os.path.isfile(os.path.join(folder_to_remove, "done.txt"))
    if os.path.exists(folder_to_remove):
        shutil.rmtree(folder_to_remove)

def get_video_fps(video_path):
    cmd = f'ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate -of default=noprint_wrappers=1 "{video_path}"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    fps_str = result.stdout.strip().split('=')[-1]
    numerator, denominator = map(int, fps_str.split('/'))
    fps = numerator / denominator

    return fps, numerator, denominator

def create_video_subset(video_path, output_path, start_frame, end_frame):
    fps, _, _ = get_video_fps(video_path)
    start_time = start_frame / fps
    end_time = end_frame / fps
    # duration = end_time - start_time

    start_time_str = f"{int(start_time // 3600):02}:{int((start_time % 3600) // 60):02}:{int(start_time % 60):02}.{int((start_time % 1) * 1000):03}"
    end_time_str = f"{int(end_time // 3600):02}:{int((end_time % 3600) // 60):02}:{int(end_time % 60):02}.{int((end_time % 1) * 1000):03}"

    cmd = [
        "ffmpeg", "-ss", start_time_str, "-to", end_time_str, "-i", video_path, "-c", "copy", output_path
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def detail_from_clip(clip):
    hash = clip[0:11]
    start = clip[12:].split("_")[0]
    score = "_".join(clip[12:].split("_")[1:])
    return hash, int(start), score