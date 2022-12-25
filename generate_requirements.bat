@ECHO OFF
@ECHO Running...
py -m pip install -U -q pipreqs
pipreqs .\BlackBoxr --force --savepath .\requirements.txt
PAUSE