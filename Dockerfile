FROM ubuntu:24.04

# プロキシ設定
ENV http_proxy=http://10.0.16.210:8080
ENV https_proxy=http://10.0.16.210:8080
ENV HTTP_PROXY=http://10.0.16.210:8080
ENV HTTPS_PROXY=http://10.0.16.210:8080

# 必要パッケージのインストール

#RUN apt-get update
#RUN apt-get install -y wget python3 python3-pip cmake g++ m4 xz-utils libgmp-dev unzip \
#    zlib1g-dev libboost-program-options-dev libboost-serialization-dev \
#    libboost-regex-dev libboost-iostreams-dev libtbb-dev libreadline-dev \
#    pkg-config git liblapack-dev libgsl-dev flex bison libcliquer-dev \
#    gfortran file dpkg-dev libopenblas-dev rpm

RUN apt update
RUN apt install -y wget python3 python3-pip python3-venv\
    build-essential cmake git zlib1g-dev libgmp-dev \
    libreadline-dev libncurses-dev libboost-all-dev libtbb-dev


# SCIPインストール（SCIP: v8.0.3）
#WORKDIR /opt
#RUN wget https://scip.zib.de/download/release/scipoptsuite-8.0.3.tgz
#RUN tar -xvzf scipoptsuite-8.0.3.tgz
#WORKDIR /opt/scipoptsuite-8.0.3/build
#RUN cmake .. -DPAPILO=OFF -DIPOPT=OFF
#RUN make -j$(nproc)
#RUN make install


# SCIPインストール（SCIP: v9.2.2）
WORKDIR /opt
RUN wget https://scip.zib.de/download/release/scipoptsuite-9.2.2.tgz
RUN tar -xvzf scipoptsuite-9.2.2.tgz
WORKDIR /opt/scipoptsuite-9.2.2/build
RUN cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DAUTOBUILD=ON \
    -DSHARED=ON \
    -DGMP=ON \
    -DREADLINE=ON \
    -DZLIB=ON
RUN make -j$(nproc)
RUN make install


# アプリコード配置
WORKDIR /app
COPY . /app

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"


# Pythonライブラリのインストール
RUN pip install --upgrade pip && pip install -r requirements.txt

# アプリ起動（Streamlitなどを想定）
#EXPOSE 8501
#CMD ["streamlit", "run", "./src/allocation_sim_app.py"]


# Streamlitアプリを起動（外部アクセス可能に）
CMD ["streamlit", "run", "./src/allocation_sim_app.py", "--server.address=0.0.0.0", "--server.port=8501"]
