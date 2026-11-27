1. ffmpeg -i <hook.mp4> -q:v 1 w/src/%05d.png ; ffmpeg -i <hook.mp4> -ar 16000 -ac 1 w/a.wav
2. python3 align.py w/a.wav words.json
3. python3 ../project/matte1.py w u2net_human_seg matte 146 ; python3 matte2.py 48 95 0 1
4. python3 track.py ; python3 camera.py
5. LAYER=front node render.js w/front 30 146 ; LAYER=back node render.js w/back 30 146 $(seq -s, 45 95)
6. python3 composite.py | ffmpeg -f rawvideo -pix_fmt bgr24 -s 1080x1920 -r 30 -i - ... w/video.mp4 ; bash mix.sh ; mux
