FROM {{ base_image }}

WORKDIR /{{ work_folder }}
COPY {{ source_code }} .
RUN apt update
RUN apt install -y wget vim gcc python3-dev
RUN pip install -r requirements.txt


EXPOSE {% for port in ports %} {{ port }} {{ "," if not loop.last else "" }} {% endfor %}
CMD {{ cmd }}
