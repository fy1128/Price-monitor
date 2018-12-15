#!/bin/sh
set -e

if [ -n "$TYPE" ] && [ "$TYPE" = "js" ]; then
	main=monitor_main_js.py
else
	main=monitor_main.py
	pip install selenium
fi

cd /usr/src/app/

if [ ! -f "db_demo.db" ]; then
	python PriceMonitor/create_db.py
fi

cd PriceMonitor
ln -s $main main.py
cd ../

exec python PriceMonitor/main.py

