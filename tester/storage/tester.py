from cloud.services.storage import MinioStorage

conf = {
    "minio_server": "...",
    "minio_access": "...",
    "minio_secret": "..."
  }

st = MinioStorage(conf)
print(st.get("660536385258d2797e390397"))