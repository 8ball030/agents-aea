FROM ubuntu:18.04

RUN apt-get update &&                                                        \
    apt-get install -y dialog &&                                             \
    apt-get install -y apt-utils &&                                          \
    apt-get upgrade -y &&                                                    \
    apt-get install -y sudo

# This adds the 'default' user to sudoers with full privileges:
RUN HOME=/home/default &&                                                    \
    mkdir -p ${HOME} &&                                                      \
    GROUP_ID=1000 &&                                                         \
    USER_ID=1000 &&                                                          \
    groupadd -r default -f -g "$GROUP_ID" &&                                 \
    useradd -u "$USER_ID" -r -g default -d "$HOME" -s /sbin/nologin          \
    -c "Default Application User" default &&                                 \
    chown -R "$USER_ID:$GROUP_ID" ${HOME} &&                                 \
    usermod -a -G sudo default &&                                            \
    echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers


RUN apt-get install -y                                                       \
       build-essential                                                       \
       software-properties-common                                            \
       vim                                                                   \
       make                                                                  \
       git                                                                   \
       less                                                                  \
       curl                                                                  \
       wget                                                                  \
       zlib1g-dev                                                            \
       libssl-dev                                                            \
       libffi-dev                                                            \
       python3-venv                                                          \
       python3-pip                                                           \
       python3-dev                                                           \
       python3.7                                                             \
       python3.7-dev                                                         \
       python3.7-venv


# needed by Pipenv
ENV DEBIAN_FRONTEND noninteractive
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

RUN apt-get install -y tox
RUN python3.7 -m pip install -U pipenv

# install Python 3.8 interpreter
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update
RUN apt-get install -y      \
    python3.8               \
    python3.8-dev           \
    python3.8-distutils
RUN python3.8 -m pip install Cython
RUN python3.8 -m pip install git+https://github.com/pytoolz/cytoolz.git#egg=cytoolz==0.10.1.dev0


ENV PATH="/usr/local/bin:${PATH}"
USER default

RUN sudo mkdir /build
WORKDIR /build
COPY . /build

RUN sudo make clean

RUN pipenv --python python3.7
RUN pipenv install --dev
RUN pipenv run pip3 install .

CMD ["/bin/bash"]
