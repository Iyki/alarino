# alarino

## Backend setup [alarino-backend](./alarino-backend/)
```
cd alarino-backend
conda env create alarino
conda activate alarino

# python -m pip list --format=freeze > pip-requirements.txt  --to save python libraries used in conda
# conda list -e > conda-requirements.txt -- save conda libraries

conda create --name alarino --file conda-requirements.txt

# or 
# python -m venv .venv
# source .venv/bin/activate
# pip install -r pip-requirements.txt if using python virtual environments
```

### Run backend app
```
python app.py
```

## Frontend setup [alarino-frontend](./alarino-frontend/)
```
cd alarino-frontend
brew install npm
npm install  // setting up from package lock
npm run dev  

# npm run build // npm run build (Vite) to generate static files in a /build or /dist folder for production.
```

## Notes
```

/*
//npm create vite@latest alarino-frontend -- --template react-ts

npm install axios
npm i @chakra-ui/react@2 @emotion/react @emotion/styled framer-motion  // use v2 for chakra, v3 is too new
npm install typescript@latest --save-dev

npm i @chakra-ui/react @emotion/react
npx @chakra-ui/cli snippet add

npm install --save-dev rollup-plugin-visualizer

*/

```



