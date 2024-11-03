#!/usr/bin/env bash
source /opt/$VENV_NAME/bin/activate 

rm -rf ./pipeline/data_refresh_files
rm ./pipeline/data_refresh.html
quarto render ./pipeline/data_refresh.qmd --to html

rm -rf docs/data_refresh/
mkdir docs/data_refresh
cp ./pipeline/data_refresh.html ./docs/data_refresh/
cp -R ./pipeline/data_refresh_files ./docs/data_refresh/

echo "Finish"
p=$(pwd)
git config --global --add safe.directory $p


# Render the Quarto dashboard
if [[ "$(git status --porcelain)" != "" ]]; then
    # quarto render pipeline/index.qmd
    # cp pipeline/index.html docs/index.html
    # rm -rf docs/index_files
    # cp -R pipeline/index_files/ docs/
    # rm pipeline/index.html
    # rm -rf pipeline/index_files
    git config --global user.name $USER_NAME
    git config --global user.email $USER_EMAIL
    git add data/*
    git add docs/*
    git commit -m "Auto update of the data"
    git push origin main
else
echo "Nothing to commit..."
fi