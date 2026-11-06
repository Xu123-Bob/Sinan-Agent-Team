# 用 Python 3.12（最稳的版本）
FROM python:3.12-slim

WORKDIR /app

# 系统依赖（python-docx / python-pptx / pyreadstat 编译所需）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 先装依赖（利用层缓存）
COPY pyproject.toml README.md ./
COPY agent ./agent
RUN pip install --no-cache-dir -e .

# 再拷配置和目录
COPY .env.example ./.env.example
RUN mkdir -p knowledge outputs data

# 友好提示
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["sinan"]
CMD []