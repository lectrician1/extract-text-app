/// <references types="houdini-svelte">

/** @type {import('houdini').ConfigFile} */
const config = {
    "watchSchema": {
        "url": "http://graphql-engine:8080/v1/graphql"
    },
    "plugins": {
        "houdini-svelte": {}
    },
    "scalars": {
        /* in your case, something like */
        uuid: {                  // <- The GraphQL Scalar
            type: "string"  // <-  The TypeScript type
        },
		timestamptz: {                  // <- The GraphQL Scalar
			type: "string"  // <-  The TypeScript type
		}
    }
}

export default config
