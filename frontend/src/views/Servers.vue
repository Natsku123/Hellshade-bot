<template>
  <div class="Servers">
    <h1>Servers</h1>
    <router-link v-for="server in servers" :key="server.node.uuid" :to="'/servers/' + server.node.uuid">{{server.node.name}}</router-link>
  </div>
</template>

<script>
import { client } from '@/utils';
import { gql } from 'graphql-request';
export default {
  name: 'Servers',
  components: {

  },
  data: () => ({
    servers: [],
  }),
  mounted() {
    const query = gql`
        {
            allServers {
                edges {
                    node {
                        uuid
                        name
                    }
                }
            }
        }
    `
    client.request(query).then(
        (data) => {
          data['allServers']['edges'].forEach((n) => {
            n.node.uuid = n.node.uuid.substring(1, n.node.uuid.length-1);
          });
          this.servers = data['allServers']['edges'];
        }
    );
  }
}
</script>
