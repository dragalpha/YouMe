import os
result = os.system(r'"c:\Users\SANTAM\Desktop\Youme\ffmpeg.exe" -y -i "c:\Users\SANTAM\Desktop\Youme\mitjul-vtuber.3840x2160.mp4" -ss 00:00:01 -vframes 1 "c:\Users\SANTAM\Desktop\Youme\static\themes\hello-kitty-wallpaper.jpg" > c:\Users\SANTAM\Desktop\Youme\ffmpeg_log.txt 2>&1')
print(f"Return code: {result}")
