import { GraphQLClient } from "graphql-request";

// TODO change so it can be used in production
const endpoint = "http://localhost:3080/"

const client = new GraphQLClient(endpoint, { headers: {} })

export {
    client
}
