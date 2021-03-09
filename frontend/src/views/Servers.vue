<template>
  <div class="Servers">
    <h1>Servers</h1>
    <v-row>
      <v-col md="6">
        <v-list>
          <v-list-item
            v-for="server in servers"
            :key="server.node.uuid"
            :to="'/servers/' + server.node.uuid"
            link
          >
            <v-list-item-title>
              {{ server.node.name }}
            </v-list-item-title>
          </v-list-item>
        </v-list>
      </v-col>
      <v-col md="6">
        <ServerMembersChart :options="chartOptions" />
      </v-col>
    </v-row>
  </div>
</template>

<script>
import { client } from "@/utils";
import { gql } from "graphql-request";
import ServerMembersChart from "@/components/ServerMembersChart";

export default {
  name: "Servers",
  components: {
    ServerMembersChart
  },
  data: () => ({
    servers: [],
    chartOptions: {
      scales: {
        yAxes: [
          {
            id: "A",
            type: "linear",
            position: "left"
          },
          {
            id: "B",
            type: "linear",
            position: "right",
            ticks: {
              min: 0,
              max: 15
            }
          }
        ]
      }
    }
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
    `;
    client.request(query).then(data => {
      data["allServers"]["edges"].forEach(n => {
        n.node.uuid = n.node.uuid.substring(1, n.node.uuid.length - 1);
      });
      this.servers = data["allServers"]["edges"];
    });
  }
};
</script>
