ssh sam@192.168.0.5 "rm -r '/Users/sam/Library/Application Support/Anki2/addons21/contanki' | exit"
scp -r ~/Developer/anki-contanki/contanki sam@192.168.0.5:"'/Users/sam/Library/Application Support/Anki2/addons21/'"

