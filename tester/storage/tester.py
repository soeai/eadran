from cloud.services.storage import MinioStorage

conf = {
    "minio_server": "192.168.10.235:9000",
    "minio_access": "rofavfHE2cXiAmpnYRVm",
    "minio_secret": "Foj8xObF2k1OQHDQ2qkB6tqEjQFJJyFqYgA8kMv9"
  }

st = MinioStorage(conf)
print(st.get("660536385258d2797e390397"))