# Init aerich in docker on first start only!

docker-compose exec -T web sh -c 'aerich init -t axegaoshop.db.config.TORTOISE_CONFIG --location axegaoshop/db/migrations &&  aerich init-db'
