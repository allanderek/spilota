. venv/bin/activate.fish
set dir (dirname (status -f))
set -gx PATH "$dir/node_modules/.bin/" $PATH
