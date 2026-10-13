import os
import subprocess
import imageio_ffmpeg

ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
base_dir = r"E:\coad\hrx website 2\images\catagories videos"
out_dir = r"E:\coad\hrx website 2\images"

for f in os.listdir(base_dir):
    out_f = None
    if "crash" in f.lower(): out_f = "cat_vid_crash.mp4"
    elif "fog" in f.lower(): out_f = "cat_vid_fog.mp4"
    elif "luggage" in f.lower(): out_f = "cat_vid_luggage.mp4"
    elif "helmet" in f.lower(): out_f = "cat_vid_helmet.mp4"
    
    if out_f:
        in_path = os.path.join(base_dir, f)
        out_path = os.path.join(out_dir, out_f)
        cmd = [
            ffmpeg_exe, "-y", "-i", in_path, 
            "-vcodec", "libx264", "-crf", "28", "-preset", "fast", "-an", "-movflags", "+faststart", out_path
        ]
        print(f"Compressing {f}...")
        subprocess.run(cmd)
print("Compression done!")
