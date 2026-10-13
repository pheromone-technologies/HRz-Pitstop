import os
import subprocess
import imageio_ffmpeg

ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
base_dir = r"E:\coad\hrx website 2\images\catagories videos"
out_dir = r"E:\coad\hrx website 2\images"

files = [
    ("crash_guard._20261008231556.mp4", "cat_vid_crash.mp4"),
    ("fog light_1080p_20261008230845.mp4", "cat_vid_fog.mp4"),
    ("luggage_20261008230611.mp4", "cat_vid_luggage.mp4"),
    ("Motorcycle_helmet_transforming_i._1080p_20261008230856.mp4", "cat_vid_helmet.mp4")
]

for in_f, out_f in files:
    in_path = os.path.join(base_dir, in_f)
    out_path = os.path.join(out_dir, out_f)
    cmd = [
        ffmpeg_exe, "-y", "-i", in_path, 
        "-vcodec", "libx264", "-crf", "28", "-preset", "fast", "-an", "-movflags", "+faststart", out_path
    ]
    print(f"Compressing {in_f}...")
    subprocess.run(cmd)
print("Compression done!")
