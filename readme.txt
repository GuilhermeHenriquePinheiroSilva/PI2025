### = Comentários

-----Comandos do Git--------
git init 
git remote add origin https://github.com/GuilhermeHenriquePinheiroSilva/PI2025.git
git pull origin ###Front ou Back
git checkout ###Front ou Back

### Salvar mudanças
git add *
git commit -m "###Dê um nome para suas alterações"
git push -u origin ###Front ou Back

-----Comandos do Back-------
python -m venv venv
.\venv\scripts\activate
pip install -r requirements.txt
python -m app.database.init_db
uvicorn app.main:app --reload

-----Comandos do Front------
npm i
ng serve