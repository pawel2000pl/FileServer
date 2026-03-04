# Simple file server

## Preparing the environment

First you need to add certificates to the `deploy/cert` directory.<br/>
Then you need to create a `storage` directory.
To avoid sharing the whole filesystem, you can only create a single directory and create binds in filesystem.<br/>
Example of `fstab` entry for binding a single directory:
~~~
/media/external_storage/source /opt/this_app_storage/name   none   defaults,auto,bind,rw,nofail     0       0
~~~


## Running

Debugging without docker
~~~
cd server
gunicorn main:application
~~~

Production without docker
~~~
cd server
gunicorn main:application
~~~

Production with docker (modify ports or storage path)
~~~
docker build -t file_server .
docker run --rm -d -p 443:443 -p 80:80 --mount type=bind,src=storage_on_host,dst=/app/storage --name file_server file_server

# or:
# docker run --rm -d -p 43443:443 -p 8080:80 --mount type=bind,src=storage_on_host,dst=/app/storage --name file_server file_server
~~~