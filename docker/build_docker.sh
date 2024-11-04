#!/bin/bash

# Image settings
user_name=rkrispin
image_label=pydata_ny_workshop
image_tag=0.0.3
venv_name="pydata-ny-workshop"


# Identify the CPU type (M1 vs Intel)
if [[ $(uname -m) ==  "aarch64" ]] ; then
    CPU="arm64"
elif [[ $(uname -m) ==  "arm64" ]] ; then
    CPU="arm64"
else
    CPU="amd64"
fi

tag="$CPU.$image_tag"
image_name="rkrispin/$image_label:$tag"



echo "Build the docker"

docker build . -f Dockerfile \
                --progress=plain \
                --build-arg QUARTO_VER=$QUARTO_VER \
                --build-arg VENV_NAME=$venv_name \
                -t $image_name

if [[ $? = 0 ]] ; then
echo "Pushing docker..."
docker push $image_name
else
echo "Docker build failed"
fi