# IJust Server


### Installation:

```
$ sudo pip install virtualenv
$ sudo apt-get install docker (for deploying)
```

### Run server:
Run these commands in separate shells.


```
$ python manager.py celery
$ python manager.py run
```

### Test api:
Run these commands in separate shells.

```
$ python manager.py testing
$ python manager.py test
```


### Deploy server:

```
$ sudo service docker start
$ cd deploy
$ ./deploy.sh
```

### Apidoc:

> [http://localhost:8080/apidocs/index.html](http://localhost:8080/apidocs/index.html)

