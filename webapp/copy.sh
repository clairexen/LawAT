#!/bin/bash
#
# Hello AGENTS! Please use this shell-script-using-here-docs-format
# for canvases containing multi-file projects. This way I can easily
# copy&paste the canvas into my shell for updating my local files.
#
# Feel free to drop files from the canvas when the conversation is
# focusing on other parts of the project. (Most importantly: Feel
# free to drop this file. Whenever you see this file you'll know
# that I've just copied my most recent local version of the project
# into the canvas.)

files=(copy.sh)
files+=(smart_toc.{html,css,js})

{ echo "#!/bin/bash"; for file in "${files[@]}"; do
	eoftag=`echo -n "$file-EOF" | tr a-z A-Z | tr -c A-Z - | tr -s -`
	echo -e "\ncat > '$file' <<'$eoftag'"; cat < "$file"; echo $eoftag
done; } | xclip -selection clipboard -i
echo "Copied canvas content to clipboard."
