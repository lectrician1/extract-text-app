import { HoudiniClient, subscription } from "$houdini";
import { createClient } from "graphql-ws";

const graphqlEndpointHost = import.meta.env.VITE_GRAPHQL_ENDPOINT_HOST;
const httpSchema = import.meta.env.PROD ? "https" : "http";
const webSocketSchema = import.meta.env.PROD ? "wss" : "ws";

export default new HoudiniClient({
  url: `${httpSchema}://${graphqlEndpointHost}/v1/graphql`,
  plugins: [
    subscription(() =>
      createClient({
        url: `${webSocketSchema}://${graphqlEndpointHost}/v1/graphql`,
      })
    ),
  ],

  // uncomment this to configure the network call (for things like authentication)
  // for more information, please visit here: https://www.houdinigraphql.com/guides/authentication
  // fetchParams({ session }) {
  //     return {
  //         headers: {
  //             Authentication: `Bearer ${session.token}`,
  //         }
  //     }
  // }
});
