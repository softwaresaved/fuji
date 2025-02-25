# Docker services for server and web client

For convenience, all services required for running the F-UJI server and a simple web client have been bundled up in [`compose.yml`](./compose.yml):
- `fuji-server` runs the API server
- `nginx` and `php` provide the web interface

To start, make sure you have Docker installed on your system (refer to the [official documentation](https://docs.docker.com/engine/install/) for details).

## Configuration

Open [`fuji/fuji_server/config/users.py`](../../fuji_server/config/users.py) and set a username and password.
Set the same username and password in [`index.php`](./index.php#L51) in the variables `$fuji_username` and `$fuji_password`.

Optionally, follow the instructions in the [root README](../../README.md#github-api) to set up authorisation with GitHub.

## Build

Next, build the API server image.
Navigate to the root of this repository and run `docker build -t fuji-ext .`.
This should use the [`Dockerfile`](../../Dockerfile) at the root of the repository.

With that done, navigate back to this directory (`fuji/simpleclient/docker`) and run `docker compose up -d`.
The web client will be available on `localhost:80`.
