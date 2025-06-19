FROM ubuntu:22.04

# プロキシ設定
ENV http_proxy=http://10.0.16.210:8080
ENV https_proxy=http://10.0.16.210:8080
ENV HTTP_PROXY=http://10.0.16.210:8080
ENV HTTPS_PROXY=http://10.0.16.210:8080

# 必要パッケージのインストール
RUN apt-get update
RUN apt-get install -y wget cmake g++ m4 xz-utils libgmp-dev unzip \
    zlib1g-dev libboost-program-options-dev libboost-serialization-dev \
    libboost-regex-dev libboost-iostreams-dev libtbb-dev libreadline-dev \
    pkg-config git liblapack-dev libgsl-dev flex bison libcliquer-dev \
    gfortran file dpkg-dev libopenblas-dev rpm

# SCIPインストール（SCIP: v8.0.3）
WORKDIR /opt
ADD ../scipoptsuite-8.0.3.tgz /opt/
RUN cd scipoptsuite-8.0.3\
    mkdir build && cd build && \
    cmake .. -DPAPILO=OFF -DIPOPT=OFF && \
    make -j$(nproc) &&\
    make install

# アプリコード配置
WORKDIR /app
COPY . /app

# Pythonライブラリのインストール
RUN pip3 install -r requirements.txt

# アプリ起動（Streamlitなどを想定）
EXPOSE 8501
CMD ["streamlit", "run", "./src/allocation_sim_app.py"]
