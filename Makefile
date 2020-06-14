run:
	@pipenv run python main.py

docker-run:
	@docker-compose up -d

docker-stop:
	@docker-compose down

install-dependencies:
	@pipenv install
