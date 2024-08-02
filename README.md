# extract-text-app

This is a web app that allows users to upload PDF or image files and use the relative position of common anchor text present in the documents to extract other text in the document like the title, revision, or other metadata.

This is particularly useful for extracting data from engineering drawings whether it is printed or handwritten. Because it uses relative position to extract text, it can extract text from different sized documents reliably compared to Bluebeam's PDF extract tools for example. After extracting, you can then export the extracted text to a CSV.

## Tech stack
* Frontend: Svelte
* Web Server: SvelteKit
* API: Hasura
* Database: PostgreSQL
* Text extraction API: Azure AI OCR 

## Developing

1. Clone the repo
2. Download Docker Desktop
3. Open the repo in VSCode and get the Dev Containers extension and reopen the repo in a dev container.
4. Copy `sample.env` to `.env` and fill out your credentials for your Azure AI OCR endpoint.
5. Run `npm install`
6. Apply [migrations](https://hasura.io/docs/latest/migrations-metadata-seeds/manage-migrations/) and [metadata](https://hasura.io/docs/latest/migrations-metadata-seeds/manage-metadata/). `cd hasura && npx hasura migrate apply && npx hasura metadata apply; cd ..`
7. Run `npm run dev`

## Building

To create a production version of your app:

1. Set the `VITE_GRAPHQL_ENDPOINT_HOST` BEFORE building as it will be set to whatever the env var is at build time.

2. Build
```bash
npm run build
```