#!/bin/bash

# Ensure environment variables are substituted and run the GRANT command
echo "GRANT ALL PRIVILEGES ON ${MYSQL_DATABASE}.* TO '${MYSQL_USER}'@'%'; FLUSH PRIVILEGES;" | mysql -u root -p${MYSQL_ROOT_PASSWORD}
