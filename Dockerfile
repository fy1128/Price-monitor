FROM python:3.6.7-alpine
WORKDIR /usr/src/app
COPY . .

ENV TZ Asia/Shanghai

RUN set -ex; \
	\
	runDeps=' \
		libxml2-dev \
		libxslt-dev \
	'; \
	apk add --no-cache --virtual .build-deps \
		$runDeps \
		build-base \
	; \
	\
	pip install --no-cache-dir -r requirements.txt \
	; \
	apk add --no-cache --virtual .run-deps $runDeps; \
	apk del .build-deps

COPY entrypoint.sh /usr/local/bin/
RUN chmod a+x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["entrypoint.sh"]
#WORKDIR /usr/src/app/
#CMD [ "python", "PriceMonitor/monitor_main_js.py" ]
