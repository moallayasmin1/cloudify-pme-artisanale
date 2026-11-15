# cloudify-pme-artisanale
Mini-projet Cloud Computing - Cloudification d'une PME e-business avec microservices Docker
## Partie 3 : Application Flask conteneurisée
```bash
cd partie3-app
docker build -t mon-app .
docker run -p 8000:8000 mon-app
```
Accès: http://localhost:8000