# Notification system: BuildingDamageProtection
To start the application locally with docker:
```
docker build -t building-damage-protection .
docker run building-damage-protection
```

To start the application locally without docker:
```
pip install -r requiremets.txt
gunicorn -w 3 --pythonpath src/main/python/ --log-level debug gateway:application 
```
To run the unittests:
```
python src/main/python/bdp_unittest.py
```

To run the unittests with docker:
```
docker ps
docker exec -it {{ container id }} /bin/sh
python src/main/python/bdp_unittest.py
```
Documentations: docs/build/index.html