import { GraphQLClient } from "graphql-request";

// TODO change so it can be used in production
const endpoint = "http://localhost:3080/";

const client = new GraphQLClient(endpoint, { headers: {} });

const hexToRGB = (hex, alpha) => {
  const r = parseInt(hex.slice(1, 3), 16),
    g = parseInt(hex.slice(3, 5), 16),
    b = parseInt(hex.slice(5, 7), 16);

  if (alpha) {
    return "rgba(" + r + ", " + g + ", " + b + ", " + alpha + ")";
  } else {
    return "rgb(" + r + ", " + g + ", " + b + ")";
  }
};

export { client, hexToRGB };
